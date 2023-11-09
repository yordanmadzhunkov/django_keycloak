from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal

from django.dispatch import receiver
from django.db.models.signals import post_save


def user_profile_image_upload_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "images/user_{0}/{1}".format(str(instance.user.username), filename)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    avatar = models.ImageField(
        upload_to=user_profile_image_upload_directory_path, default=None, null=True, blank=True)
    show_balance = models.BooleanField(default=True, null=False, blank=False)

    def __str__(self):
        return self.user.username

    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        else:
            return "/static/img/undraw_profile.svg"

    def get_display_name(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)

    def get_href(self):
        return "/profile/%d" % (self.pk)

    def last_login(self):
        return self.user.last_login

    def date_joined(self):
        return self.user.date_joined
    

def get_user_profile(user):
    profile = UserProfile.objects.filter(user=user)
    if len(profile) == 0:
        profile = None
    else:
        profile = profile[0]
    return profile



@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    instance.profile.save()