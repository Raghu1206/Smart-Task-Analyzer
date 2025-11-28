"""
Scoring algorithm and utilities for Smart Task Analyzer.

- Normalizes sub-scores to 0..1 for urgency, importance, effort, dependency.
- final_score = weighted sum of sub-scores (weights configurable by strategy)
- Past-due tasks get an urgency boost.
- Circular dependency detection via DFS.
"""

from datetime import date
from dateutil.parser import parse as parse_date

def parse_due_date(val):
    if val is None or val == '':
        return None
    if isinstance(val, date):
        return val
    try:
        return parse_date(val).date()
    except Exception:
        return None

def detect_cycles(tasks):
    """
    tasks: dict id->task
    Returns (cycles_list, in_cycle_map)
    cycles_list: list of sets of task ids involved in cycles
    in_cycle_map: dict tid->bool
    """
    graph = {tid: list(task.get('dependencies', [])) for tid, task in tasks.items()}
    visited = {}
    in_cycle = {tid: False for tid in tasks}
    cycles = []

    def dfs(node, stack):
        if node not in graph:
            return False
        if visited.get(node) == 1:
            # back-edge found
            if node in stack:
                idx = stack.index(node)
                cyc = stack[idx:]
                cycles.append(set(cyc))
                for n in cyc:
                    in_cycle[n] = True
            return True
        if visited.get(node) == 2:
            return False
        visited[node] = 1
        stack.append(node)
        for nb in graph.get(node, []):
            dfs(nb, stack)
        stack.pop()
        visited[node] = 2
        return False

    for n in graph:
        if visited.get(n) is None:
            dfs(n, [])

    return cycles, in_cycle

def compute_scores(task_list, strategy='smart_balance', weights=None, today=None):
    """
    task_list: list of task dicts
    strategy: 'fastest', 'high_impact', 'deadline', 'smart_balance'
    weights: optional dict to override weights
    today: date object (defaults to date.today())
    Returns: list of results with keys: id, title, raw, score, subscores, explanation, issues
    """
    if today is None:
        today = date.today()

    base_weights = {
        'smart_balance': {'urgency': 0.35, 'importance': 0.35, 'effort': 0.15, 'dependency': 0.15},
        'fastest': {'urgency': 0.2, 'importance': 0.2, 'effort': 0.45, 'dependency': 0.15},
        'high_impact': {'urgency': 0.2, 'importance': 0.6, 'effort': 0.1, 'dependency': 0.1},
        'deadline': {'urgency': 0.7, 'importance': 0.15, 'effort': 0.1, 'dependency': 0.05},
    }

    w = base_weights.get(strategy, base_weights['smart_balance']).copy()
    if weights:
        w.update(weights)

    # Normalize tasks and build id map
    id_map = {}
    default_hours = 4.0
    for i, t in enumerate(task_list):
        tid = str(t.get('id') or t.get('title') or f"task-{i}")
        cleaned = dict(t)
        cleaned['id'] = tid
        cleaned['title'] = t.get('title') or f'Untitled {i}'
        try:
            cleaned['importance'] = int(t.get('importance') or 5)
        except Exception:
            cleaned['importance'] = 5
        try:
            cleaned['estimated_hours'] = float(t.get('estimated_hours') if t.get('estimated_hours') is not None else default_hours)
        except Exception:
            cleaned['estimated_hours'] = default_hours
        cleaned['due_date'] = parse_due_date(t.get('due_date'))
        cleaned['dependencies'] = [str(x) for x in (t.get('dependencies') or [])]
        id_map[tid] = cleaned

    # detect cycles
    cycles, in_cycle = detect_cycles(id_map)

    # compute dependents count
    dependents_count = {tid: 0 for tid in id_map}
    for tid, t in id_map.items():
        for dep in t.get('dependencies', []):
            if dep in dependents_count:
                dependents_count[dep] += 1
    max_dependents = max(dependents_count.values()) if dependents_count else 1

    results = []
    for tid, t in id_map.items():
        issues = []
        expl = []

        # Urgency
        if t['due_date'] is None:
            urgency = 0.0
            expl.append('No due date → low urgency')
        else:
            days = (t['due_date'] - today).days
            if days < 0:
                # past due: boost urgency (cap near 0.99)
                urgency = min(0.99, 0.9 + min(30, -days) / 100.0)
                expl.append(f'Past due by {-days} days → urgency boosted')
            else:
                horizon = 30.0
                urgency = max(0.0, 1.0 - (days / horizon))
                urgency = min(1.0, urgency)
                expl.append(f'Due in {days} days → urgency {urgency:.2f}')

        # Importance normalized 1-10 -> 0..1
        imp = max(1, min(10, int(t.get('importance', 5)))) / 10.0
        expl.append(f'Importance {t.get("importance")} → {imp:.2f}')

        # Effort: lower hours -> higher score (quick wins)
        hours = max(0.1, float(t.get('estimated_hours') or default_hours))
        if hours <= 1.0:
            effort = 1.0
        elif hours >= 16.0:
            effort = 0.0
        else:
            effort = 1.0 - ((hours - 1.0) / 15.0)
        expl.append(f'Estimated {hours}h → effort-score {effort:.2f}')

        # Dependency score: how many tasks depend on this task
        dep_score = (dependents_count.get(tid, 0) / max_dependents) if max_dependents > 0 else 0.0
        expl.append(f'Blocks {dependents_count.get(tid,0)} tasks → dependency-score {dep_score:.2f}')

        # Weighted sum
        final = (w['urgency'] * urgency + w['importance'] * imp + w['effort'] * effort + w['dependency'] * dep_score)

        # Cycle penalty/flag
        if in_cycle.get(tid):
            issues.append('circular_dependency')
            final *= 0.9
            expl.append('In circular dependency → slight penalty applied')

        # Missing data flags
        if t['due_date'] is None:
            issues.append('no_due_date')
        if 'estimated_hours' not in t or t['estimated_hours'] is None:
            issues.append('no_estimated_hours')

        results.append({
            'id': tid,
            'title': t['title'],
            'raw': t,
            'score': round(final, 4),
            'subscores': {
                'urgency': round(urgency, 4),
                'importance': round(imp, 4),
                'effort': round(effort, 4),
                'dependency': round(dep_score, 4),
            },
            'explanation': '; '.join(expl),
            'issues': issues,
        })

    # sort by score descending
    results.sort(key=lambda x: x['score'], reverse=True)
    return results
