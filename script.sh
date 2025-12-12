python3.12 -m venv venv

source venv/bin/activate

docker compose up -d

pip install -r requirements.txt

python manage.py migrate

gunicorn finance_tracker.wsgi

celery -A finance_tracker worker -l info
