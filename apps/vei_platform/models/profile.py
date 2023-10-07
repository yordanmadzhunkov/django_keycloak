from django.db import models
from django.contrib.auth.models import User


def user_profile_image_upload_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "images/user_{0}/{1}".format(str(instance.user.username), filename)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    avatar = models.ImageField(
        upload_to=user_profile_image_upload_directory_path, default=None, null=True, blank=True)

    def __str__(self):
        return self.user.username

    @property
    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        else:
            return "/static/img/undraw_profile.svg"

    @property
    def get_display_name(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)

    @property
    def get_href(self):
        return "/profile/%d" % (self.pk)

    @property
    def last_login(self):
        return self.user.last_login

    @property
    def date_joined(self):
        return self.user.date_joined


def get_user_profile(user):
    profile = UserProfile.objects.filter(user=user)
    if len(profile) == 0:
        profile = None
    else:
        profile = profile[0]
    return profile


# def create_user_profile(sender, instance, created, **kwargs):
#    if created:
#        UserProfile.objects.create(user=instance)


# post_save.connect(create_user_profile, sender=User)
