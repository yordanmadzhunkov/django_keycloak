from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction

from . import common_context
from vei_platform.models.profile import get_user_profile
from vei_platform.models.legal import LegalEntity,LegalEntitySources, canonize_name, find_legal_entity
from vei_platform.models.factory import ElectricityFactory
from vei_platform.models.platform import PlatformLegalEntity    
from vei_platform.forms import LegalEntityForm, SearchForm
from django.contrib import messages
from django.forms.models import model_to_dict

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


@login_required(login_url='/oidc/authenticate/')
def view_my_entity_detail(request):
    context = common_context()
    context['profile'] = get_user_profile(request.user)
    instance = find_legal_entity(user=request.user)
    if instance:
        form = LegalEntityForm(instance=instance) if request.method != "POST" else LegalEntityForm(request.POST, instance=instance)
    else:
        form = LegalEntityForm() if request.method != "POST" else LegalEntityForm(request.POST)

    if request.method == "POST":
        if form.is_valid():
            native_name = canonize_name(form.cleaned_data['native_name'])
            latin_name = canonize_name(form.cleaned_data['latin_name'])
            with transaction.atomic():
                my_entity = find_legal_entity(tax_id=form.cleaned_data['tax_id'])
                if my_entity is None:
                    my_entity = LegalEntity(native_name = native_name,
                            latin_name = latin_name,
                            legal_form = "",
                            tax_id = form.cleaned_data['tax_id'],
                            founded = form.cleaned_data['founded'],
                            person = True)
                    my_entity.save()
                    my_source_url=("user:%s" % request.user)
                    source = LegalEntitySources(entity=my_entity, url=my_source_url)
                    source.save()
                else:
                    form.instance.native_name = native_name
                    form.instance.latin_name = latin_name
                    form.instance.save()

            my_entity = find_legal_entity(tax_id=form.cleaned_data['tax_id'])
            messages.success(request, "Legal entity %s created" % str(my_entity))
        else:
            messages.error(request, 'Invalid form' + str(form.errors))
    context['form'] = form
    return render(request, "my_legal_entity.html", context)

@login_required(login_url='/oidc/authenticate/')
def view_entity_platform(request):
    context = common_context()
    context['profile'] = get_user_profile(request.user)
    form = SearchForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            if 'search' in request.POST:
                search_text = form.cleaned_data['search_text']
                entities = LegalEntity.objects.filter(tax_id=search_text)
                context['entities'] = entities
                if len(entities) == 0:
                    messages.info(request, "No matches for " + search_text)

            for key in request.POST.keys():
                if key.startswith('add_'):
                    tax_id_to_add = key[4:-1]
                    entity_to_add = LegalEntity.objects.get(tax_id=tax_id_to_add)
                    if len(PlatformLegalEntity.objects.filter(entity=entity_to_add)) == 0:
                        new_entity = PlatformLegalEntity(entity=entity_to_add)
                        new_entity.save()
                        messages.info(request, "Adding " + str(entity_to_add))
                    else:
                        messages.error(request, "Can't add " + str(entity_to_add) + "It's already owned by plaform")
    platform_entites_list = []
    for e in PlatformLegalEntity.objects.all():
        platform_entites_list.append( {'native_name': e.entity.native_name,
        'tax_id': e.entity.tax_id,})
    context['platform_entities'] = platform_entites_list
    context['form'] = form
    return render(request, "platform_entity.html", context)
