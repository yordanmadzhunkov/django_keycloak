from django.db import models
from .legal import LegalEntity, add_legal_entity
from .profile import get_user_profile
from django.db.models.signals import post_save
from django.conf import settings
from decimal import Decimal
from django.dispatch import receiver
from django_q.tasks import async_task

from django.core.validators import MaxValueValidator, MinValueValidator
from .restricted_file_field import RestrictedFileField
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from . import TimeStampMixin



def user_image_upload_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "images/user_{0}/{1}".format(str(instance.manager), filename)

def factory_component_file_upload_directory_path(instance, filename):
    return "documents/factory_{0}/{1}".format(instance.factory.pk, filename)

class ElectricityFactory(TimeStampMixin):
    name = models.CharField(max_length=128)

    # Factory type
    PHOTOVOLTAIC = 'FEV'
    WIND_TURBINE = 'WIN'
    HYDROPOWER = 'HYD'
    BIOMASS = 'BIO'
    REN_GAS = 'RGS'

    FACTORY_TYPE_CHOISES = (
        (PHOTOVOLTAIC, _('Photovoltaic')),
        (WIND_TURBINE, _('Wind turbine')),
        (HYDROPOWER, _('Hydropower')),
        (BIOMASS, _('Biomass')),
        (REN_GAS, _('Renewable gas')),
    )

    factory_type = models.CharField(
        max_length=3,
        choices=FACTORY_TYPE_CHOISES,
        default=PHOTOVOLTAIC,
    )

    # User that manages the data shown on the platform
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, default=None, on_delete=models.DO_NOTHING)

    # info
    location = models.CharField(max_length=100, default=_('Bulgaria'))
    opened = models.DateField(null=True)
    capacity_in_mw = models.DecimalField(
        default=0, decimal_places=3, max_digits=9)
    image = models.ImageField(
        upload_to=user_image_upload_directory_path, default=None, null=True, blank=True)

    # primary owner
    primary_owner = models.ForeignKey(
        LegalEntity, null=True, blank=True, default=None, on_delete=models.SET_NULL)

    tax_id = models.CharField(
        max_length=128, null=True, blank=True, default=None,)
    owner_name = models.CharField(max_length=128, default="Unknown")

    def __str__(self):
        return self.name

    def is_working(self):
        return self.status == self.WORKING

    def is_stopped(self):
        return self.status == self.STOPED

    def get_image_url(self):
        if self.image and hasattr(self.image, 'url'):
            return self.image.url
        if self.factory_type == self.PHOTOVOLTAIC:
            return "/static/img/password_img.jpg"
        if self.factory_type == self.WIND_TURBINE:
            return "/static/img/wind-turbine.jpg"
        if self.factory_type == self.HYDROPOWER:
            return "/static/img/wickramanayaka.jpg"
        print('type = ' + self.factory_type + '\n')
        return None
    

    def get_capacity_in_kw(self):
        return self.capacity_in_mw * Decimal(1000)

    def get_absolute_url(self):
        return reverse('view_factory', kwargs={'pk': self.pk})


    def get_manager_profile(self):
        if self.manager:
            return get_user_profile(self.manager)
        else:
            return None
        

    
def docfile_content_types():
    return 'application/pdf'

class ElectricityFactoryComponents(models.Model):
        # Factory type
    PHOTO_PANEL = 'PAN'
    INVERTOR   = 'INV'
    CONNECTOR  = 'CON'
    OTHER = 'OTH'

    COMPONENT_TYPE_CHOISES = (
        (PHOTO_PANEL, _('Photovoltaic Panel')),
        (INVERTOR, _('Invertor')),
        (CONNECTOR, _('Connector')),
        (OTHER, _('Other')),
    )

    name = models.CharField(max_length=128)
    component_type = models.CharField(
        max_length=3,
        choices=COMPONENT_TYPE_CHOISES,
        default=OTHER,
    )
    factory = models.ForeignKey(ElectricityFactory, null=True, blank=True, default=None, on_delete=models.DO_NOTHING)
    power_in_kw = models.DecimalField(null=True, blank=True, default=None, decimal_places=3, max_digits=9)
    count = models.IntegerField(default=1)
    docfile = RestrictedFileField(
        upload_to=factory_component_file_upload_directory_path,
        content_types=docfile_content_types(),#['application/pdf',],
        max_upload_size=5242880, # 5 MB
        default=None, 
        null=True, 
        blank=True)
    description = models.TextField(null=True, blank=True, default=None)
    


    def __str__(self) -> str:
        return '%s %s kW x %d' % (self.name, self.power_in_kw, self.count)
        

import os
from django.db import models

def _delete_file(path):
   """ Deletes file from filesystem. """
   if os.path.isfile(path):
        #print("cleaning " + path)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass


@receiver(models.signals.post_delete, sender=ElectricityFactoryComponents)
def delete_file(sender, instance, *args, **kwargs):
    """ Deletes image files on `post_delete` """
    if instance.docfile:
        _delete_file(instance.docfile.path)

@receiver(models.signals.pre_save, sender=ElectricityFactoryComponents)
def auto_delete_file_on_change(sender, instance, update_fields, **kwargs):
    """
    Deletes old file from filesystem
    when corresponding `ElectricityFactoryComponents` object is updated
    with new file.
    """
    #print(update_fields)
    if not instance.pk:
        return False

    try:
        old_instance = ElectricityFactoryComponents.objects.get(pk=instance.pk)
        old_file = old_instance.docfile
        should_delete = instance.docfile != old_instance.docfile
        if should_delete and old_file:
            _delete_file(old_file.path)   
    except ElectricityFactoryComponents.DoesNotExist:
        return False


def parse_energy(x):
    map = {
        'ВЕЦ': ElectricityFactory.HYDROPOWER,
        'МВЕЦ': ElectricityFactory.HYDROPOWER,
        'ПАВЕЦ': ElectricityFactory.HYDROPOWER,
        'Каскада': ElectricityFactory.HYDROPOWER,

        'БиоЕЦ': ElectricityFactory.BIOMASS,
        'БиоГЕЦ': ElectricityFactory.REN_GAS,
        'ФЕЦ': ElectricityFactory.PHOTOVOLTAIC,
        'ФтЦ': ElectricityFactory.PHOTOVOLTAIC,
        'ВтЕЦ': ElectricityFactory.WIND_TURBINE,
    }
    return map[x.replace('"', '')]


def add_factory(task):
    result = task.result
    factories = ElectricityFactory.objects.filter(name=result['name'])
    factory_type = parse_energy(result['energy'])
    if len(factories) == 0:
        factory = ElectricityFactory(
            name=result['name'],
            factory_type=factory_type,
            manager=None,
            location=result['location'],
            opened=result['opened'],
            capacity_in_mw=result['capacity'],
            primary_owner=None,
            tax_id=result['eik'],
            owner_name=result['owner'],
        )
        factory.save()
    else:
        factory = factories[0];
        if factory.manager is None:
            # trigger scriping of legal entity
            factory.save()
        print("Factory found name='%s' type='%s'" %
              (factory.name, factory.factory_type))


# FINANCIAL PLANNING
class FactoryProductionPlan(models.Model):
    name = models.CharField(max_length=128)
    factory = models.ForeignKey(
        ElectricityFactory, null=True, blank=True, on_delete=models.DO_NOTHING)
    start_year = models.IntegerField(
        default=2022,
        validators=[
            MaxValueValidator(2050),
            MinValueValidator(1990)
        ]
    )
    end_year = models.IntegerField(
        default=2025,
        validators=[
            MaxValueValidator(2050),
            MinValueValidator(1990)
        ]
    )

    def get_working_hours(self, month):
        objects = ElectricityWorkingHoursPerMonth.objects.filter(plan=self)
        s = objects.filter(
            month__month=month.month)
        y = s.filter(month__year=month.year)
        if len(y) > 0:
            return s[0].number

        count = len(s)
        sum = Decimal(0)
        for k in s:
            sum = sum + k.number

        if len(s) > 0:
            return sum / count

        return Decimal(100)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self):
        res = self.factory.get_absolute_url()
        return res + '/production/%s' % self.pk


class ElectricityWorkingHoursPerMonth(models.Model):
    month = models.DateField()
    number = models.DecimalField(max_digits=6, decimal_places=2)
    plan = models.ForeignKey(FactoryProductionPlan,
                             null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self) -> str:
        return "%s %s" % (self.month.strftime('%b %y'), self.number)
