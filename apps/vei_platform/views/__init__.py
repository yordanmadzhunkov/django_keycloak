from vei_platform.models.profile import UserProfile, get_user_profile

from vei_platform.models.legal import find_legal_entity
from vei_platform.models.factory import ElectricityFactory
from decimal import Decimal
from vei_platform.templatetags.vei_platform_utils import balance_from_transactions
from vei_platform.settings.base import VEI_PLATFORM_IMAGE, LANGUAGES


def common_context(request):
    context = {
        'platform_name': 'Fraction Energy',
        'platform_logo': '/static/img/Fraction_Energy_logo.png',
        'copyright': 'Data Intensive 2023',
        'head_title': 'Fraction Energy',
    }
    if request:
        if request.user:
            if request.user.is_authenticated:
                if request.user.is_superuser:
                    context['platform_image'] = VEI_PLATFORM_IMAGE
                profile = get_user_profile(request.user)
                if profile:
                    context['profile'] = profile
    context['django_language'] = request.COOKIES.get('django_language', 'bg')

    django_languages = []
    for lang in LANGUAGES:
        selected = (lang[0] == context['django_language'])
        django_languages.append((lang[0], lang[1], "selected" if selected else ""))
    context['django_languages'] = django_languages
    return context


def generate_formset_table(years, objects, NumberPerMonthFormSet, prefix):
    initial = []
    index = 0
    for year in years:
        for month in range(12):
            s = objects.filter(month__year=year).filter(
                month__month=month+1)
            if len(s) == 0:
                initial.append(
                    {'month': date(year=year, month=month+1, day=1)})
            else:
                initial.append({
                    'number': s[0].number,
                    'month': s[0].month
                })
            index = index + 1
    formset = NumberPerMonthFormSet(initial=initial, prefix=prefix)

    rows = []
    index = 0
    for year in years:
        row = []
        row.append(str(year))
        for month in range(12):
            val = formset[index].as_table()
            input = re.search(r'<td>(.*)</td>', val)
            if input:
                row.append(input.group(1))
            index = index + 1
        rows.append(row)
    table = {
        'labels': ['Year', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        'rows': rows
    }
    return formset, table
