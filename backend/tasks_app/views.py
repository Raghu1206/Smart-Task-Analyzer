import json
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from .serializers import TaskSerializer
from .scoring import compute_scores
from pathlib import Path

# Simple local store to hold last analyzed tasks
STORE_PATH = Path(__file__).resolve().parent / "tasks_store.json"


def save_store(data):
    try:
        STORE_PATH.write_text(json.dumps(data, default=str))
    except Exception:
        pass


def load_store():
    try:
        if STORE_PATH.exists():
            return json.loads(STORE_PATH.read_text())
    except Exception:
        return None
    return None


class AnalyzeTasksView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        payload = request.data

        # Allow both {tasks: [...]} or raw list
        if isinstance(payload, dict) and "tasks" in payload:
            tasks = payload["tasks"]
            strategy = payload.get("strategy", "smart_balance")
        elif isinstance(payload, list):
            tasks = payload
            strategy = request.query_params.get("strategy", "smart_balance")
        else:
            tasks = payload.get("tasks", [])
            strategy = payload.get("strategy", "smart_balance")

        validated = []
        for t in tasks:
            ser = TaskSerializer(data=t)
            if ser.is_valid():
                validated.append(ser.validated_data)
            else:
                # fallback for invalid data
                validated.append({
                    "title": t.get("title", "Untitled"),
                    "due_date": t.get("due_date", None),
                    "estimated_hours": t.get("estimated_hours", None),
                    "importance": t.get("importance", 5),
                    "dependencies": t.get("dependencies", []),
                })

        results = compute_scores(validated, strategy=strategy)

        save_store({"strategy": strategy, "results": results})

        return JsonResponse({"strategy": strategy, "results": results}, safe=False)


class SuggestTasksView(APIView):
    def get(self, request):
        store = load_store()
        if not store:
            return JsonResponse({"error": "No stored tasks. Run analyze first."}, status=400)

        results = store.get("results", [])

        suggested = results[:3]  # top 3

        explanations = []
        for t in suggested:
            sc = t["subscores"]
            top_factor = max(sc.items(), key=lambda x: x[1])
            reasons = [f"Top driver: {top_factor[0]} ({top_factor[1]})"]

            if "circular_dependency" in t.get("issues", []):
                reasons.append("In circular dependency — resolve manually")

            explanations.append({"task": t, "why": "; ".join(reasons)})

        return JsonResponse({"suggestions": explanations}, safe=False)
