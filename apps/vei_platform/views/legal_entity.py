from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator


from . import common_context
from vei_platform.models.profile import get_user_profile
from vei_platform.models.legal import LegalEntity
from vei_platform.models.factory import ElectricityFactory



@login_required(login_url='/oidc/authenticate/')
def view_entity_detail(request, pk=None):
    context = common_context()
    context['profile'] = get_user_profile(request.user)
    if pk is not None:
        legal_entity = LegalEntity.objects.get(pk=pk)
        context['legal_entity'] = legal_entity
        factories_list = ElectricityFactory.objects.all().filter(
            primary_owner=legal_entity).order_by('pk')
        paginator = Paginator(factories_list, 5)  # Show 25 contacts per page.
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
    return render(request, "legal_entity.html", context)