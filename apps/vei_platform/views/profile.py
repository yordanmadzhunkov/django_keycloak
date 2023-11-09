from . import common_context

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.models import User


from vei_platform.models.profile import UserProfile, get_user_profile
from vei_platform.forms import UserProfileForm


@login_required(login_url='/oidc/authenticate/')
def view_user_profile(request, pk=None):
    context = common_context(request)
    context['user_profile'] = UserProfile.objects.get(pk=pk)
    return render(request, "user_profile.html", context)


@login_required(login_url='/oidc/authenticate/')
def view_my_profile(request):
    context = common_context(request)
    profile = get_user_profile(user=request.user)
    user = User.objects.get(username=request.user)
    user_profile_form = UserProfileForm(request.POST or None, request.FILES or None, 
                                        initial={
                                            'show_balance': (profile.show_balance if profile else False),
                                            'last_name': user.last_name,
                                            'first_name': user.first_name,
                                        })
    if user_profile_form.is_valid():
        avatar = user_profile_form.cleaned_data.get('avatar')
        if avatar is not None:
            if profile is None:
                profile = UserProfile(user=request.user, avatar=avatar)
            else:
                profile.avatar = avatar
            profile.save()
            messages.success(
                request, '%s uploaded and set as profile picture successfully' % avatar)

        first_name = user_profile_form.cleaned_data.get('first_name')
        last_name = user_profile_form.cleaned_data.get('last_name')

        if (first_name is not None and first_name != user.first_name) or (last_name is not None and last_name != user.last_name):
            user.first_name = first_name
            user.last_name = last_name
            user.save()
            messages.success(request, 'Name set to %s %s' %
                             (first_name, last_name))
            context['user'] = user

        show_balance = user_profile_form.cleaned_data.get('show_balance')
        if show_balance != profile.show_balance:
            messages.success(request, 'Show balance in profile set to %s' % show_balance)
            profile.show_balance = show_balance
            profile.save()
    else:
        if request.method == "POST":
            messages.error(request, 'Profile error')
    context['avatar_form'] = user_profile_form
    context['profile'] = get_user_profile(request.user)
    return render(request, "my_profile.html", context)