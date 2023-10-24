from django.db import models
from .legal import LegalEntity
from .profile import get_user_profile
from django.db.models.signals import post_save
from django.conf import settings
from decimal import Decimal
from django.dispatch import receiver

from django.core.validators import MaxValueValidator, MinValueValidator


def user_image_upload_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "images/user_{0}/{1}".format(str(instance.manager), filename)


class ElectricityFactory(models.Model):
    name = models.CharField(max_length=128)

    # Factory type
    PHOTOVOLTAIC = 'FEV'
    WIND_TURBINE = 'WIN'
    HYDROPOWER = 'HYD'
    BIOMASS = 'BIO'
    REN_GAS = 'RGS'

    FACTORY_TYPE_CHOISES = (
        (PHOTOVOLTAIC, 'Photovoltaic'),
        (WIND_TURBINE, 'Wind turbine'),
        (HYDROPOWER, 'Hydropower'),
        (BIOMASS, 'Biomass'),
        (REN_GAS, 'Renewable gas'),
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
    location = models.CharField(max_length=100, default="България")
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
        return "/factory/%s" % self.pk

    def get_manager_profile(self):
        if self.manager:
            return get_user_profile(self.manager)
        else:
            return None
        



@receiver(post_save, sender=ElectricityFactory)
def electical_factory_post_save(sender, **kwargs):
    instance = kwargs.get('instance')
    if instance.primary_owner is None:
        owner_name = instance.owner_name
        tax_id = instance.tax_id
        print("Search for name='%s' or tax_id=%s" % (owner_name, tax_id))
        legal_entities = LegalEntity.objects.filter(tax_id=tax_id)
        if len(legal_entities) > 0:
            legal_entity = legal_entities[0]
            instance.primary_owner = legal_entity
            print("Saving the instance with new primary owner = %s" %
                  str(legal_entity))
            instance.save()
        else:
            print('not found, spawning scripe task')
            async_task("vei_platform.tasks.scripe_factory_legal_entity",
                       instance,
                       task_name="LegalEntity-for-%s" % instance.name,
                       hook=add_legal_entity)


@receiver(post_save, sender=LegalEntity)
def legal_entity_post_save(sender, **kwargs):
    instance = kwargs.get('instance')
    tax_id = instance.tax_id
    factories_for_upgrade = ElectricityFactory.objects.filter(
        tax_id=tax_id).filter(primary_owner=None)
    for factory in factories_for_upgrade:
        factory.primary_owner = instance
        factory.save()


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
        print("Factory found name='%s' type='%s'" %
              (factories[0].name, factories[0].factory_type))


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
        return "/production/%s" % self.pk


class ElectricityWorkingHoursPerMonth(models.Model):
    month = models.DateField()
    number = models.DecimalField(max_digits=6, decimal_places=2)
    plan = models.ForeignKey(FactoryProductionPlan,
                             null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self) -> str:
        return "%s %s" % (self.month.strftime('%b %y'), self.number)
