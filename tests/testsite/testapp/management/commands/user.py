from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from tastypie.models import ApiKey


class Command(BaseCommand):
    help = 'Create an API key for testuser'

    def handle(self, *args, **options):
        User.objects.create_user('testuser1', 'noemail1@nothing.com', 'password')
        User.objects.create_user('testuser2', 'noemail2@nothing.com', 'password')
        User.objects.create_user('testuser3', 'noemail3@nothing.com', 'password')
        User.objects.create_user('testuser4', 'noemail4@nothing.com', 'password')
        api_key = ApiKey.objects.get_or_create(user=User.objects.get(username='testuser'))
