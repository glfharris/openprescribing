from django.contrib.auth.models import User
from frontend.models import Profile


class SecretKeyBackend(object):
    def authenticate(self, key=None):
        try:
            profile = Profile.objects.get(key=key)
            return profile.user
        except Profile.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
