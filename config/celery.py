import os
from celery import Celery

# Указываем Django использовать настройки из config.settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('lms_project')

# Загружаем настройки Celery из Django settings с префиксом CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи (tasks.py) во всех установленных приложениях
app.autodiscover_tasks()