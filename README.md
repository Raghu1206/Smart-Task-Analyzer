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
<img width="1290" height="850" alt="Screenshot 2025-11-28 193954" src="https://github.com/user-attachments/assets/975b8325-0d19-45b5-9bf2-d54558a0fc15" />
<img width="1265" height="758" alt="Screenshot 2025-11-28 194012" src="https://github.com/user-attachments/assets/991cd1a6-48ac-4de1-a86b-ce8197d83b67" />
<img width="1259" height="766" alt="Screenshot 2025-11-28 194026" src="https://github.com/user-attachments/assets/0cd0f363-b8e9-4db0-b738-f88ff1a88a49" />


