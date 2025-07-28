# Activate virtual environment
source /root/projects/MovieStreaming/venv/bin/activate

# Go to project directory
cd /root/projects/MovieStreaming

# Start Celery worker and beat
celery -A utils.celery.celery_app.celery worker --loglevel=info &
celery -A utils.celery.celery_app.celery beat --loglevel=info