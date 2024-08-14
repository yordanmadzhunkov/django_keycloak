from django.db import models
from django.contrib.auth.models import User
from .timezone_choises import TIMEZONE_CHOICES


def user_profile_image_upload_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "images/user_{0}/{1}".format(str(instance.user.username), filename)


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
    )
    avatar = models.ImageField(
        upload_to=user_profile_image_upload_directory_path,
        default=None,
        null=True,
        blank=True,
    )

    timezone = models.CharField(
        verbose_name="Timezone",
        max_length=50,
        default="UTC",
        choices=TIMEZONE_CHOICES,
    )

    def __str__(self):
        return self.user.username

    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        else:
            return "/static/img/undraw_profile.svg"

    def get_display_name(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)

    def get_href(self):
        return "/profile/%d" % (self.pk)


def get_user_profile(user):
    if user is None:
        profile = None
    else:
        profile = UserProfile.objects.filter(user=user)
        if len(profile) == 0:
            profile = None
        else:
            profile = profile[0]
    return profile
