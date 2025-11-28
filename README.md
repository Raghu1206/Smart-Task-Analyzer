# Smart-Task-Analyzer

# How to run:
cd Smart-Task-Analyzer\backend
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000

cd Smart-Task-Analyzer\frontend (in a different terminal for frontend)
python -m http.server 5500

Backend now works at:
http://127.0.0.1:8000/api/tasks/analyze/
http://127.0.0.1:8000/api/tasks/suggest/

Frontend is here:
http://127.0.0.1:8000/static/index.html

Results:
