from django.db import models
from vei_platform.models.profile import UserProfile

def user_team_image_upload_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "images/team/{0}".format(filename)

class TeamMember(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.DO_NOTHING, default=None, null=True, blank=True)
    image = models.ImageField(
        upload_to=user_team_image_upload_directory_path, default=None, null=True, blank=True)
    name = models.CharField(max_length=128)
    role = models.CharField(max_length=128)
    description = models.TextField()
    twitter = models.URLField(default=None, null=True, blank=True)
    facebook = models.URLField(default=None, null=True, blank=True)
    instagram = models.URLField(default=None, null=True, blank=True)
    linkedin = models.URLField(default=None, null=True, blank=True)
    order = models.IntegerField(default=100)

    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        else:
            return "/static/img/undraw_profile.svg"
        
    def get_profile_href(self):
        if self.profile:
            return self.profile.get_href()
        return '#'

    