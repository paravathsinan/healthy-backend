from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import os

class Command(BaseCommand):
    help = 'Create a superuser automatically from environment variables'

    def handle(self, *args, **options):
        username = os.getenv('ADMIN_USERNAME', 'admin')
        email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser: {username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" already exists.'))
