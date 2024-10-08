from typing import Any
from django.db.models.base import Model as Model
from . import common_context

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


from vei_platform.models.profile import UserProfile, get_user_profile
from vei_platform.forms import UserProfileForm
from django.utils.translation import gettext as _
from django.views import View

from django.shortcuts import get_object_or_404
import pytz


class Profile(View):
    def get(self, request, pk=None, *args, **kwargs):
        context = common_context(request)
        context["user_profile"] = get_object_or_404(UserProfile, pk=pk)
        return render(request, "user_profile.html", context)


class MyProfileUpdate(View):
    def get(self, request):
        self.request = request
        context = common_context(self.request)
        if not "profile" in context.keys():
            return redirect("home")
        user_profile_form = UserProfileForm(
            None,
            None,
            initial={
                "last_name": request.user.last_name,
                "first_name": request.user.first_name,
                "timezone": context["profile"].timezone,
            },
        )
        context["avatar_form"] = user_profile_form
        self.add_token_info(request, context)
        self.add_last_login_and_date_joined(request, context)
        return render(self.request, "my_profile.html", context)

    def post(self, request):
        context = common_context(request)
        profile = context["profile"]
        if profile is None:
            return redirect("home")

        user = User.objects.get(username=request.user)
        user_profile_form = UserProfileForm(request.POST, request.FILES)

        if "save" in request.POST:
            if user_profile_form.is_valid():
                avatar = user_profile_form.cleaned_data.get("avatar")
                first_name = user_profile_form.cleaned_data.get("first_name")
                last_name = user_profile_form.cleaned_data.get("last_name")
                timezone = user_profile_form.cleaned_data.get("timezone")

                if profile.timezone != timezone:
                    profile.timezone = timezone
                    profile.save()
                    messages.success(
                        request, _("%s saved as default display timezone") % timezone
                    )

                if avatar is not None:
                    profile.avatar = avatar
                    profile.save()
                    messages.success(request, _("%s saved as avatar") % avatar)

                if (first_name is not None and first_name != user.first_name) or (
                    last_name is not None and last_name != user.last_name
                ):
                    user.first_name = first_name
                    user.last_name = last_name
                    user.save()
                    messages.success(
                        request, _("Full name set to: %s %s") % (first_name, last_name)
                    )
                    context["user"] = user
            else:
                messages.error(request, _("Profile error"))

        if "generate_token" in request.POST:
            tokens = Token.objects.filter(user=request.user)
            if len(tokens) > 0:
                new_key = tokens[0].generate_key()
                tokens.update(key=new_key)
                # token = tokens.first()
                # token.delete()
            else:
                token = Token.objects.create(user=user)

        self.add_token_info(request, context)
        self.add_last_login_and_date_joined(request, context)
        context["avatar_form"] = user_profile_form
        context["profile"] = get_user_profile(request.user)
        return render(request, "my_profile.html", context)

    def add_token_info(self, request, context):
        tokens = Token.objects.filter(user=request.user)
        context["user_token"] = tokens.first().key if len(tokens) > 0 else "None"

    def add_last_login_and_date_joined(self, request, context):
        requested_timezone = context["profile"].timezone
        if requested_timezone is None:
            requested_timezone = "UTC"
        tz = pytz.timezone(requested_timezone)
        dt_join = request.user.date_joined.astimezone(tz)
        dt_last = request.user.last_login.astimezone(tz)
        context["date_joined"] = (
            dt_join.strftime("%Y-%m-%d %H:%M:%S ") + requested_timezone
        )
        context["last_login"] = (
            dt_last.strftime("%Y-%m-%d %H:%M:%S ") + requested_timezone
        )
