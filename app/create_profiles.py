import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth.models import User
from app.models import UserProfile

# Создаем профили для всех существующих пользователей
for user in User.objects.all():
    UserProfile.objects.get_or_create(user=user)
    print(f"Создан профиль для {user.username}")

print("Все профили созданы!")