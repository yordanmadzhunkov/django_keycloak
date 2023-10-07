from django.contrib.auth.models import User
from django.db import models
from django.conf import settings
# Create your models here.
from decimal import Decimal
from datetime import date
from django.core.validators import MaxValueValidator, MinValueValidator

from django.db.models.signals import post_save
from django.dispatch import receiver

from django_q.tasks import async_task

import re


class LegalEntity(models.Model):
    native_name = models.CharField(max_length=1024)
    latin_name = models.CharField(max_length=1024)
    legal_form = models.CharField(max_length=4, null=True)
    tax_id = models.CharField(max_length=48, unique=True, null=True)
    founded = models.DateField(null=True)
    person = models.BooleanField(default=False, null=False)

    def __str__(self):
        if self.tax_id:
            return self.native_name + ' / ' + self.tax_id
        return self.native_name


class LegalEntitySources(models.Model):
    entity = models.ForeignKey(
        LegalEntity, on_delete=models.CASCADE, default=1)
    url = models.CharField(max_length=1024)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['entity', 'url'], name='URL should be unique for each company')
        ]

    def __str__(self):
        return str(self.entity) + ' ( %s )' % self.url


class StakeHolder(models.Model):
    # Relationship  type
    OWNER = 'OWN'  # primary owner
    EX_OWNER = 'EOW'  # ex-owner usually when company is aquired by holding
    DIRECTOR_IN_BOARD = 'BoD'
    CEO = 'CEO'  # CEO of the company
    EMPLOYEE = 'EMP'  # works for the company
    INVESTOR = 'Inv'  # owns fraction of the company
    LOAN_ORIGNATOR = 'LOA'  # provided load to the company
    TRADER = 'TRD'

    STAKE_HOLDER_CHOISES = (
        (OWNER, 'Owner'),
        (EX_OWNER, 'Ex-Owner'),
        (DIRECTOR_IN_BOARD, 'Director in board'),
        (EMPLOYEE, 'Employee'),
        (CEO, 'CEO'),
        (INVESTOR, 'Investor'),
        (LOAN_ORIGNATOR, 'Loan provider'),
        (TRADER, 'Trader')
    )

    stake_type = models.CharField(
        max_length=3,
        choices=STAKE_HOLDER_CHOISES,
        null=False, blank=False, default=None,
        # default=OWNER,
    )
    # used to model ownership
    percent = models.DecimalField(
        default=None, decimal_places=6, max_digits=9, null=True)
    company = models.ForeignKey(
        LegalEntity, related_name='stakeholders', null=False, blank=False, default=None, on_delete=models.CASCADE)
    holder = models.ForeignKey(
        LegalEntity, null=False, blank=False, default=None, on_delete=models.DO_NOTHING)
    start_date = models.DateField(null=True, blank=True, default=None)
    end_date = models.DateField(null=True, blank=True, default=None)

    def __str__(self):
        return str(self.holder.native_name) + ' -> ' + self.str_stake() + ' -> ' + str(self.company)

    def str_stake(self):
        for t in self.STAKE_HOLDER_CHOISES:
            if t[0] == self.stake_type:
                return t[1]
        return "Unknown"


def get_stake_type(role):
    stake_map = {
        "Capital owner".upper(): StakeHolder.OWNER,
        "OWNER": StakeHolder.OWNER,
        "EX-OWNER": StakeHolder.EX_OWNER,
        "CEO": StakeHolder.CEO,
        "TRADER": StakeHolder.TRADER,
        "DIRECTOR IN BOARD": StakeHolder.DIRECTOR_IN_BOARD,
    }
    return stake_map[role.upper()]


def create_legal_entity_stakeholders(entity, info, source):
    for p in info['people']:
        holder = get_legal_entity(p)
        stake_type = get_stake_type(p['role'])
        stakers = StakeHolder.objects.filter(
            company=entity).filter(stake_type=stake_type).filter(holder=holder)
        if len(stakers) == 0:
            if 'share' in p.keys():
                percent = p['share']['percent']
            else:
                percent = None

            stakeholder = StakeHolder(
                company=entity,
                holder=holder,
                stake_type=stake_type,
                percent=percent,
                start_date=entity.founded,
                end_date=None
            )
            stakeholder.save()
            if info['legal_form'] == 'ЕТ' and stake_type == StakeHolder.TRADER:
                stakeholder = StakeHolder(
                    company=entity,
                    holder=holder,
                    stake_type=StakeHolder.OWNER,
                    percent=Decimal(100),
                    start_date=entity.founded,
                    end_date=None
                )
                stakeholder.save()
        else:
            pass


def isquote(char):
    return char in ["'", '"', '“', '”', '„', '”', '„', '“', '„', '"']


def extract_in_queotes(name):
    start = None
    for index, ch in enumerate(name):
        if isquote(ch):
            start = index

            break

    stop = None
    for index, ch in enumerate(name[::-1]):
        if isquote(ch):
            stop = len(name) - index
            break

    if start is not None and stop is not None and stop - 1 > start + 1:
        return name[start+1:stop-1]

    return name


def dequote(s):
    """
    If a string has single or double quotes around it, remove them.
    Make sure the pair of quotes match.
    If a matching pair of quotes is not found,
    or there are less than 2 characters, return the string unchanged.
    """
    if (len(s) >= 2) and ((s[0] == s[-1] and s.startswith(("'", '"')))
                          or (s[0] == '“' and s[-1] == '”')
                          or (s[0] == '„' and s[-1] == '”')
                          or (s[0] == '„' and s[-1] == '“')
                          or (s[0] == '„' and s[-1] == '"')
                          ):
        return s[1:-1]
    return s


def is_legal_form(word):
    return word in ['ЕООД', 'EООД', 'ЕАД', 'ООД', 'ЕТ', 'АД', 'LTD', 'ГМБХ', 'КООПЕРАЦИЯ', 'АГ']


def canonize_name(name):
    in_quotes = extract_in_queotes(name)
    if len(in_quotes) < len(name):
        return in_quotes.upper()

    r = re.compile('(\S)("|”)(\S)')
    name = r.sub(r'\1\2 \3', name)
    # "ВЕНТЧЪР ЕКУИТИ БЪЛГАРИЯ ЕАД" -> "ВЕНТЧЪР ЕКУИТИ БЪЛГАРИЯ"
    words = name.upper().split()
    l = len(words)
    if l > 1 and is_legal_form(words[l - 1]):
        words.pop(l - 1)
    if l > 1 and is_legal_form(words[0]):
        words.pop(0)
    return dequote(' '.join(words))


def get_legal_entity(info, source=None):
    native_name = canonize_name(info['name'])
    # search by name
    entites = LegalEntity.objects.filter(native_name=native_name)
    if len(entites) == 1:
        return entites[0]
    return None


def create_legal_entity(info, source):
    native_name = canonize_name(info['name'])
    count = 0

    if 'people' in info.keys():
        for p in info['people']:
            count += create_legal_entity(p, source)

    c = LegalEntity.objects.filter(native_name=native_name)
    if len(c) == 0:
        new_company = LegalEntity(
            native_name=native_name,
            latin_name=canonize_name(
                info['latin_name']) if 'latin_name' in info.keys() else '',
            legal_form=info['legal_form'] if 'legal_form' in info.keys(
            ) else None,
            tax_id=info['eik'] if 'eik' in info.keys() else None,
            founded=info['founded'] if 'founded' in info.keys() else None,
            person=info['person'] if 'person' in info.keys() else False)
        new_company.save()
        count = count + 1

        new_source = LegalEntitySources(
            entity=new_company,
            url=("%s%s" % (source, info['href'])))
        new_source.save()
    else:
        new_company = c[0]

    if 'people' in info.keys():
        create_legal_entity_stakeholders(new_company, info, source)

    return count


def add_legal_entity(task):
    result = task.result
    if result is not None:
        source = task.result['source']
        print(task)
        create_legal_entity(result, source)


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

    # Financial data related to the platform
    # Evealuation, P/E, available for investment, number of investors
    fraction_on_platform = models.DecimalField(
        default=0, decimal_places=6, max_digits=9)

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
        return self.name + ' listed ' + str(self.fraction_on_platform)

    def is_working(self):
        return self.status == self.WORKING

    def is_stopped(self):
        return self.status == self.STOPED

    @property
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

    @property
    def get_capacity_in_kw(self):
        return self.capacity_in_mw * 1000

    def get_absolute_url(self):
        return "/factory/%s" % self.pk

    @property
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


class ElectricityPricePlan(models.Model):
    name = models.CharField(max_length=128)

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

    def __str__(self) -> str:
        return self.name

    def get_price(self, month):
        prices = ElectricityPrice.objects.filter(
            plan=self).order_by('-month')
        if len(prices) > 0:
            for price in prices:
                if price.month <= month:
                    return price.number
            price = prices[len(prices)-1]
            return price.number
        return Decimal(0)

    def get_absolute_url(self):
        return "/electricity/%s" % self.pk


class ElectricityPrice(models.Model):
    month = models.DateField()
    number = models.DecimalField(max_digits=6, decimal_places=2)
    plan = models.ForeignKey(ElectricityPricePlan, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return "%s @ %.2f - plan = %s" % (str(self.month), self.number,  self.plan.name)


class BankLoan(models.Model):
    start_date = models.DateField()
    amount = models.DecimalField(
        default=10000, max_digits=12, decimal_places=2)
    duration = models.IntegerField(default=12*15)
    factory = models.ForeignKey(
        ElectricityFactory, null=True, blank=True, on_delete=models.DO_NOTHING)

    def __str__(self) -> str:
        return "%.0f start %s months=%d" % (self.amount, self.start_date.strftime('%b %y'), self.duration)

    def get_absolute_url(self):
        return "/bank_loan/%s" % self.pk

    def start_year(self):
        return self.start_date.year

    def end_year(self):
        return self.start_date.year + ((self.duration + self.start_date.month - 1) // 12)

    def get_interest(self, date):
        interests = BankLoanInterest.objects.filter(
            loan=self).order_by('-month')
        if len(interests) > 0:
            for interest in interests:
                if interest.month <= date:
                    return interest.number
            interest = interests[len(interests)-1]
            return interest.number
        return Decimal(5)

    def calculate_payment_amount(self, principal, interest_rate, period):
        x = (Decimal(1) + interest_rate) ** period
        return principal * (interest_rate * x) / (x - 1)

    def adjust_mountly_interest(self, yearly_interest):
        return (Decimal(1.0) + yearly_interest/Decimal(100))**Decimal(1.0/12) - Decimal(1.0)

    def offset_date_by_period(self, date1, period):
        dy = (period + date1.month - 1) // 12
        m = (period + date1.month - 1) % 12 + 1
        return date(year=date1.year + dy, month=m, day=date1.day)

    def offset_start_date(self, months):
        return self.offset_date_by_period(self.start_date, period=months)

    def amortization_schedule(self):
        # (index, payment, payment_interest, payment_principal, balance)
        # (0, Decimal('855.57'), Decimal('40.74'), Decimal('814.83'), Decimal('9185.17'))
        amortization_schedule = []
        balance = self.amount
        for number in range(self.duration):
            remaining_period = self.duration - number
            p = self.offset_date_by_period(self.start_date, number)
            interest_rate = self.get_interest(p)
            montly_interest = self.adjust_mountly_interest(interest_rate)
            payment = self.calculate_payment_amount(
                principal=balance,
                interest_rate=montly_interest,
                period=remaining_period,
            )
            payment = round(payment, 2)
            interest = round(balance * montly_interest, 2)
            if payment > interest + balance:
                payment = interest + balance
            principal = payment - interest
            balance = balance - principal
            row = (number, payment, interest, principal, balance)
            amortization_schedule.append(row)
            if balance == Decimal(0):
                break
        return amortization_schedule

    def total_amortization(self):
        total_payment = Decimal(0)
        total_interest = Decimal(0)
        total_principal = Decimal(0)
        for row in self.amortization_schedule():
            number, payment, interest, principal, balance = row
            total_payment = total_payment + payment
            total_interest = total_interest + interest
            total_principal = total_principal + principal
        return total_payment, total_interest, total_principal


class BankLoanInterest(models.Model):
    month = models.DateField()
    number = models.DecimalField(max_digits=6, decimal_places=2)
    loan = models.ForeignKey(BankLoan, on_delete=models.CASCADE)


class SolarEstateListing(models.Model):
    start_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    persent_from_profit = models.DecimalField(max_digits=2, decimal_places=2)
    duration = models.IntegerField(default=12*15)
    commision = models.DecimalField(
        default=1.5, max_digits=2, decimal_places=2)


class SolarEstateInvestor(models.Model):
    name = models.CharField(max_length=128)
    amount = models.DecimalField(
        default=10000, max_digits=12, decimal_places=2)
    solar_estates = models.ForeignKey(
        SolarEstateListing, null=True, blank=True, on_delete=models.DO_NOTHING)


class FinancialPlan(models.Model):
    name = models.TextField()
    factory = models.ForeignKey(
        ElectricityFactory, on_delete=models.DO_NOTHING)
    start_month = models.DateField()
    span_in_months = models.IntegerField()
    capitalization = models.DecimalField(max_digits=12, decimal_places=2)
    manager_capital = models.DecimalField(max_digits=12, decimal_places=2)
    loan = models.ForeignKey(
        BankLoan, null=True, blank=True, on_delete=models.DO_NOTHING)
    solar_estates = models.ForeignKey(
        SolarEstateListing, null=True, blank=True, on_delete=models.DO_NOTHING)
    working_hours = models.ForeignKey(
        FactoryProductionPlan, null=True, blank=True, on_delete=models.DO_NOTHING)
    prices = models.ForeignKey(
        ElectricityPricePlan, null=True, blank=True, on_delete=models.DO_NOTHING)

    @property
    def rows(self):
        res = []
        next_month = self.start_month
        for i in range(self.span_in_months):
            res.append({
                'month':  next_month.strftime('%b %y')
            })
            next_month = date(next_month.year + int(next_month.month / 12),
                              ((next_month.month % 12) + 1), next_month.day)
        return res


def user_profile_image_upload_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return "images/user_{0}/{1}".format(str(instance.user.username), filename)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    avatar = models.ImageField(
        upload_to=user_profile_image_upload_directory_path, default=None, null=True, blank=True)

    def __str__(self):
        return self.user.username

    @property
    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        else:
            return "/static/img/undraw_profile.svg"

    @property
    def get_display_name(self):
        return "%s %s" % (self.user.first_name, self.user.last_name)

    @property
    def get_href(self):
        return "/profile/%d" % (self.pk)

    @property
    def last_login(self):
        return self.user.last_login

    @property
    def date_joined(self):
        return self.user.date_joined


def get_user_profile(user):
    profile = UserProfile.objects.filter(user=user)
    if len(profile) == 0:
        profile = None
    else:
        profile = profile[0]
    return profile


# def create_user_profile(sender, instance, created, **kwargs):
#    if created:
#        UserProfile.objects.create(user=instance)


# post_save.connect(create_user_profile, sender=User)
