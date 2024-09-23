from vei_platform.models.profile import UserProfile, get_user_profile

from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory
from decimal import Decimal
from vei_platform.settings.base import VEI_PLATFORM_IMAGE, LANGUAGES


def common_context(request):
    context = {
        "platform_name": "Fraction Energy",
        "platform_logo": "/static/img/Fraction_Energy_logo.png",
        "copyright": "Solar Estates All right reserved",
        "head_title": "Fraction Energy",
    }
    if request:
        if request.user:
            if request.user.is_authenticated:
                if request.user.is_superuser:
                    context["platform_image"] = VEI_PLATFORM_IMAGE
                profile = get_user_profile(request.user)
                if profile:
                    context["profile"] = profile
    context["django_language"] = request.COOKIES.get("django_language", "bg")

    django_languages = []
    for lang in LANGUAGES:
        selected = lang[0] == context["django_language"]
        django_languages.append((lang[0], lang[1], "selected" if selected else ""))
    context["django_languages"] = django_languages
    return context
