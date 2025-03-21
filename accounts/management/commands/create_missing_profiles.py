from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Creates user profiles for users that do not have one'

    def handle(self, *args, **kwargs):
        users_without_profile = []
        for user in User.objects.all():
            try:
                # Try to access the profile
                user.profile
            except UserProfile.DoesNotExist:
                users_without_profile.append(user)
                UserProfile.objects.create(user=user)
        
        if users_without_profile:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created profiles for {len(users_without_profile)} users: '
                    f'{", ".join(user.username for user in users_without_profile)}'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('All users already have profiles')
            ) 