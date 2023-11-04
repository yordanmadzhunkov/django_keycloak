from django.db import models
from decimal import Decimal
import re


class LegalEntity(models.Model):
    native_name = models.CharField(max_length=1024)
    latin_name = models.CharField(max_length=1024)
    legal_form = models.CharField(max_length=48, null=True)
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
        #print(task)
        create_legal_entity(result, source)


def find_legal_entity_for_user(user):
    my_source_url=("user:%s" % user)
    sources = LegalEntitySources.objects.filter(url=my_source_url)
    if len(sources) > 0:
        my_source = sources[0]
        return my_source.entity
    return None


def find_legal_entity_by_tax_id(tax_id):
    if tax_id is not None:
        objects = LegalEntity.objects.filter(tax_id=tax_id)
        if len(objects) > 0:
            return objects[0]
    return None
    
def find_legal_entity(tax_id=None, user=None):
    res = find_legal_entity_by_tax_id(tax_id)
    if res is None:
        res = find_legal_entity_for_user(user)
    return res


