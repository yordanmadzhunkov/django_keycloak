from django.test import TestCase
from core.models import LegalEntity, StakeHolder, LegalEntitySources, create_legal_entity, canonize_name
from datetime import date
from decimal import Decimal


class TestLegalEntity(TestCase):
    def setUp(self):
        # Setup run before every test method.
        self.assertEqual(len(LegalEntity.objects.all()), 0)

    def tearDown(self):
        # Clean up run after every test method.
        pass

    def test_creating_one_company(self):
        new_company = LegalEntity(
            native_name="Дата Интнесив",
            latin_name="Data Intensive",
            legal_form="ЕООД",
            tax_id="84392233",
            founded=date(2021, 9, 9),
            person=False)
        new_company.save()
        self.assertEqual(len(LegalEntity.objects.all()), 1)

    def test_creating_company_with_ceo_and_owner(self):
        info = {
            "active": True,
            "eik": "200654055",
            "founded": date(2009, 3, 19),
            "href": "/eik/200654055/0934",
            "latin_name": "HOT - LAIT LTD",
            "legal_form": "ЕООД",
            "name": "ХОТ - ЛАЙТ",
            "people": [
                {
                    "href": "/person/53e5b573e558a80aa75a8052406760defb2f491e947c5740214ce226b291018f",
                    "name": "Иво Димитров Коларов",
                    "person": True,
                    "role": "ceo"
                },
                {
                    "href": "/person/53e5b573e558a80aa75a8052406760defb2f491e947c5740214ce226b291018f",
                    "name": "ИВО ДИМИТРОВ КОЛАРОВ",
                    "person": True,
                    "role": "Capital owner"
                }
            ]
        }

        self.assertEqual(len(LegalEntity.objects.all()), 0)

        num_new_entities = create_legal_entity(
            info, source='https://papagal.bg')
        self.assertEqual(num_new_entities, 2)
        people = LegalEntity.objects.filter(tax_id=None)
        companies = LegalEntity.objects.filter(tax_id__isnull=False)

        self.assertEqual(len(people), 1)
        self.assertEqual(people[0].native_name.upper(),
                         "ИВО ДИМИТРОВ КОЛАРОВ")
        self.assertEqual(people[0].person, True)

        self.assertEqual(len(companies), 1)
        self.assertEqual(companies[0].native_name.upper(), "ХОТ - ЛАЙТ")
        self.assertEqual(companies[0].latin_name.upper(), "HOT - LAIT")
        self.assertEqual(companies[0].legal_form, "ЕООД")
        self.assertEqual(companies[0].tax_id, "200654055")
        self.assertEqual(companies[0].founded, date(2009, 3, 19))
        self.assertEqual(companies[0].person, False)
        self.assertEqual(len(LegalEntity.objects.all()), 2)

        # check sources
        sources = LegalEntitySources.objects.all()
        self.assertEqual(len(sources), 2)

        person_urls = LegalEntitySources.objects.filter(
            url="https://papagal.bg/person/53e5b573e558a80aa75a8052406760defb2f491e947c5740214ce226b291018f")
        self.assertEqual(len(person_urls), 1)
        self.assertEqual(person_urls[0].entity.native_name.upper(),
                         "ИВО ДИМИТРОВ КОЛАРОВ")

        company_urls = LegalEntitySources.objects.filter(
            url="https://papagal.bg/eik/200654055/0934")
        self.assertEqual(len(company_urls), 1)
        self.assertEqual(company_urls[0].entity.native_name.upper(),
                         "ХОТ - ЛАЙТ")

        # check stakeholders in company
        holders = StakeHolder.objects.all()
        self.assertEqual(len(holders), 2)
        self.assertEqual(holders[0].company.native_name.upper(), "ХОТ - ЛАЙТ")
        self.assertEqual(
            holders[0].holder.native_name.upper(), "ИВО ДИМИТРОВ КОЛАРОВ")
        self.assertEqual(holders[0].end_date, None)
        self.assertEqual(len(holders.filter(stake_type=StakeHolder.CEO)), 1)
        self.assertEqual(len(holders.filter(stake_type=StakeHolder.OWNER)), 1)
        self.assertEqual(holders[1].company.native_name.upper(), "ХОТ - ЛАЙТ")
        self.assertEqual(
            holders[1].holder.native_name.upper(), "ИВО ДИМИТРОВ КОЛАРОВ")
        self.assertEqual(holders[1].end_date, None)

    def test_creating_company_with_multiple_ceos_and_owners(self):
        info = {
            "2019": {
                "currency": "лв",
                "profit": Decimal("265000"),
                "revenue": Decimal("1297000")
            },
            "active": True,
            "eik": "201794747",
            "founded": date(2011, 11, 21),
            "href": "/eik/201794747/d2cc",
            "latin_name": "MIROLESKOVI",
            "legal_form": "ООД",
            "name": "МИРОЛЕСКОВИ",
            "people": [
                {
                    "href": "/person/37b8ef2c44c37d61b3b9cc61f7557b54ed1448b81a1de9650e7a61986df5f9f9",
                    "name": "ЛЮБОМИР ЦВЕТКОВ МИРОЛЕСКОВ",
                    "person": True,
                    "role": "ceo"
                },
                {
                    "href": "/person/6adf158461ba59392b8ec67b1761fc29f76981a0445c4f70e6d018d318ad99a0",
                    "name": "КРИСТИАН ЛЮБОМИРОВ МИРОЛЕСКОВ",
                    "person": True,
                    "role": "ceo"
                },
                {
                    "href": "/person/655bfed8de73ce54e025da2fce60eab23381318ee12f3d86db9064efbb84b995",
                    "name": "ГАЛИНА ЛЮБОМИРОВА МИРОЛЕСКОВА",
                    "person": True,
                    "role": "ceo"
                },
                {
                    "href": "/person/37b8ef2c44c37d61b3b9cc61f7557b54ed1448b81a1de9650e7a61986df5f9f9",
                    "name": "ЛЮБОМИР ЦВЕТКОВ МИРОЛЕСКОВ",
                    "person": True,
                    "role": "owner",
                    "share": {
                        "capital": Decimal("60.00"),
                        "currency": "лв",
                        "percent": Decimal("60.00")
                    }
                },
                {
                    "href": "/person/6adf158461ba59392b8ec67b1761fc29f76981a0445c4f70e6d018d318ad99a0",
                    "name": "КРИСТИАН ЛЮБОМИРОВ МИРОЛЕСКОВ",
                    "person": True,
                    "role": "owner",
                    "share": {
                        "capital": Decimal("10.00"),
                        "currency": "лв",
                        "percent": Decimal("10.00")
                    }
                },
                {
                    "href": "/person/8102873cb59d6dbbc86434cf2b497efb67e02725d0f3aace6857d25353459e53",
                    "name": "РУМЯНА ХРИСТОВА МИРОЛЕСКОВА",
                    "person": True,
                    "role": "owner",
                    "share": {
                        "capital": Decimal("20.00"),
                        "currency": "лв",
                        "percent": Decimal("20.00")
                    }
                },
                {
                    "href": "/person/655bfed8de73ce54e025da2fce60eab23381318ee12f3d86db9064efbb84b995",
                    "name": "ГАЛИНА ЛЮБОМИРОВА МИРОЛЕСКОВА",
                    "person": True,
                    "role": "owner",
                    "share": {
                        "capital": Decimal("10.00"),
                        "currency": "лв",
                        "percent": Decimal("10.00")
                    }
                }
            ]
        }
        num_new_entities = create_legal_entity(
            info, source='https://papagal.bg')

        self.assertEqual(num_new_entities, 5)
        galina = LegalEntity.objects.get(
            native_name='ГАЛИНА ЛЮБОМИРОВА МИРОЛЕСКОВА')
        rumyana = LegalEntity.objects.get(
            native_name='РУМЯНА ХРИСТОВА МИРОЛЕСКОВА')
        self.assertEqual(StakeHolder.objects.filter(
            holder=galina).filter(stake_type=StakeHolder.OWNER)[0].percent, Decimal(10))

        self.assertEqual(StakeHolder.objects.filter(
            holder=rumyana).filter(stake_type=StakeHolder.OWNER)[0].percent, Decimal(20))

    def test_create_et(self):
        info = {'href': '/eik/102720414/e587',
                'name': 'ДИВЕКС-2 - ГЕОРГИ ГЕОРГИЕВ',
                'legal_form': 'ЕТ',
                'latin_name': '',
                'eik': '102720414',
                'active': True,
                'founded': date(2001, 1, 1),
                'people': [
                    {'name': 'ГЕОРГИ ДИМИТРОВ ГЕОРГИЕВ',
                     'href': '/person/DB6559CDB64FC117D8DEA4E2E2678C4A3B38B754EB2DC1BB5777004118C856BB',
                     'role': 'trader',
                     'person': True
                     }],
                'source': 'https://papagal.bg'
                }

        num_new_entities = create_legal_entity(
            info, info['source'])

        self.assertEqual(num_new_entities, 2)
        georgi = LegalEntity.objects.get(
            native_name='ГЕОРГИ ДИМИТРОВ ГЕОРГИЕВ')
        et = LegalEntity.objects.get(
            native_name='ДИВЕКС-2 - ГЕОРГИ ГЕОРГИЕВ')

        traders = StakeHolder.objects.filter(
            holder=georgi).filter(stake_type=StakeHolder.TRADER)

        owners = StakeHolder.objects.filter(
            holder=georgi).filter(stake_type=StakeHolder.OWNER)

        self.assertEqual(len(traders), 1)
        self.assertEqual(len(owners), 1)
        self.assertEqual(owners[0].percent, Decimal(100))
        self.assertEqual(owners[0].company.pk, et.pk)
        self.assertEqual(owners[0].holder.native_name,
                         'ГЕОРГИ ДИМИТРОВ ГЕОРГИЕВ')

    def test_create_ead(self):
        info = {
            'href': '/eik/101652946/2342',
            'name': 'ЛЪКИ     ЕНЕРГИЯ',
            'legal_form': 'ЕАД',
            'latin_name': 'LUCKY  ENERGY',
            'eik': '101652946',
            'active': True,
            'founded': date(2003, 1, 1),
            '2019': {'profit': '578000', 'revenue': '0', 'currency': 'лв'},
            'people': [
                {
                    'name': 'ЛЮДМИЛ ГЕОРГИЕВ АЛЕКСАНДРОВ',
                    'href': '/person/08e469b5ca31a615334fb9a1218950abcc9f49f17ea996fbf20e22924d1703b6',
                    'role': 'Director in board',
                    'person': True
                },
                {
                    'name': 'ДАНАИЛ МИХАЙЛОВ КАМЕНОВ',
                    'href': '/person/9fe6d760ad2529cd04c528170992bdadc2b1af7940a8a8421d0484d29054eb59',
                    'role': 'Director in board',
                    'person': True
                },
                {
                    'name': 'Гергана Стоичкова Маркова',
                    'href': '/person/954ae691776e8e451c790cdc8f08b8a025c5ed68e29e24cad3c493c26c0196b6',
                    'role': 'Director in board',
                    'person': True
                }, {
                    'name': 'ВЕНТЧЪР ЕКУИТИ БЪЛГАРИЯ ЕАД',
                    'href': '/person/200355640',
                    'role': 'Capital owner',
                    'person': False
                }
            ],
            'source': 'https://papagal.bg'
        }

        num_new_entities = create_legal_entity(
            info, info['source'])

        self.assertEqual(num_new_entities, 5)
        self.assertEqual(
            len(LegalEntity.objects.filter(native_name='ЛЪКИ ЕНЕРГИЯ')), 1)

        holdings = LegalEntity.objects.filter(
            native_name='ВЕНТЧЪР ЕКУИТИ БЪЛГАРИЯ')
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0].person, False)

    def test_legal_name_cannonization(self):
        self.assertEqual(canonize_name(
            'ВЕНТЧЪР ЕКУИТИ БЪЛГАРИЯ ЕАД'), 'ВЕНТЧЪР ЕКУИТИ БЪЛГАРИЯ')
        self.assertEqual(canonize_name(
            '"ВЕНТЧЪР ЕКУИТИ БЪЛГАРИЯ" ЕООД'), 'ВЕНТЧЪР ЕКУИТИ БЪЛГАРИЯ')
        self.assertEqual(canonize_name('"РИАЛ ТЕХ" ООД'), 'РИАЛ ТЕХ')

        self.assertEqual(canonize_name(
            'ЕТ "ДИВЕКС - 2 - ГЕОРГИ ГЕОРГИЕВ"'), 'ДИВЕКС - 2 - ГЕОРГИ ГЕОРГИЕВ')

        self.assertEqual(canonize_name('Миро-М-2008 ЕООД'), 'МИРО-М-2008')

        self.assertEqual(canonize_name(
            '“ВОДНИ ЕЛЕКТРИЧЕСКИ ЦЕНТРАЛИ – 94” ООД'), 'ВОДНИ ЕЛЕКТРИЧЕСКИ ЦЕНТРАЛИ – 94')
        self.assertEqual(canonize_name(
            '"ГОРУБСО - ЗЛАТОГРАД" АД'), 'ГОРУБСО - ЗЛАТОГРАД')

        self.assertEqual(canonize_name(
            '"СЕНТРАЛ ХИДРОЕЛЕКТРИК ДЬО БУЛГАРИ"ЕООД'), 'СЕНТРАЛ ХИДРОЕЛЕКТРИК ДЬО БУЛГАРИ')

        self.assertEqual(canonize_name('"КОНСУЛТХИДРО"ЕАД'), 'КОНСУЛТХИДРО')

        self.assertEqual(canonize_name('„ИНОС – 1”'), 'ИНОС – 1')

        self.assertEqual(canonize_name(
            'ЕВН БЪЛГАРИЯ РЕС ХОЛДИНГ ГМБХ'), 'ЕВН БЪЛГАРИЯ РЕС ХОЛДИНГ')

        self.assertEqual(canonize_name(
            '„ЕВЕРЕСТ РИНЮЪБЪЛ ЕНЕРДЖИС (БЪЛГАРИЯ)”'), 'ЕВЕРЕСТ РИНЮЪБЪЛ ЕНЕРДЖИС (БЪЛГАРИЯ)')

        self.assertEqual(canonize_name(
            '„АКУО БЪЛГАРИЯ СИ ЕЙЧ БИ“'), 'АКУО БЪЛГАРИЯ СИ ЕЙЧ БИ')
        self.assertEqual(canonize_name('„ВЕЦ МАЛУША“'), 'ВЕЦ МАЛУША')
        self.assertEqual(canonize_name(
            '„Гардения Холдинг“ ГмбХ'), 'ГАРДЕНИЯ ХОЛДИНГ')
        self.assertEqual(canonize_name(
            '„БЪЛГАРСКИ ВИК ХОЛДИНГ“'), 'БЪЛГАРСКИ ВИК ХОЛДИНГ')
        self.assertEqual(canonize_name(
            '„АКУО БЪЛГАРИЯ СИ ЕЙЧ БИ“'), 'АКУО БЪЛГАРИЯ СИ ЕЙЧ БИ')
        self.assertEqual(canonize_name(
            'КООПЕРАЦИЯ "ПАРАЛЕЛ 2000"'), 'ПАРАЛЕЛ 2000')
        self.assertEqual(canonize_name(
            '"УИНДКРАФТ СИМОНСФЕЛД" АГ'), 'УИНДКРАФТ СИМОНСФЕЛД')
        self.assertEqual(canonize_name('„ГАЛИТА 67 БГ" EООД'), 'ГАЛИТА 67 БГ')
        self.assertEqual(canonize_name(
            '„БИЛДИНГ ЕНТЕРПРАЙЗ" EООД'), 'БИЛДИНГ ЕНТЕРПРАЙЗ')
        self.assertEqual(canonize_name(
            'ДРУЖЕСТВО ПО ЗЗД "КАРДАМ 2"'), 'КАРДАМ 2')

    def test_creating_ex_owners(self):
        info = {'href': '/eik/127585860/b9fb',
                'name': 'ВТК',
                'legal_form': 'ЕООД',
                'latin_name': 'VTK',
                'eik': '127585860',
                'active': True,
                'founded': date(2004, 1, 1),
                'people': [
                    {
                        'name': 'ГАБРИЕЛА ЛЮДМИЛОВА НАЙДЕНОВА',
                        'href': '/person/D1ADF7CB5CFFC55B57D1F1A53F44FC26E6D51638570A2ABAED9439BCC7AB83C5',
                        'role': 'ceo',
                        'person': True
                    }, {
                        'name': 'ВАЛЕНТИН НЕДЕЛЧЕВ ГРОЗДЕВ',
                        'href': '/person/1DA9E12A55225D41FD4623321123D40694D5AADD786F3C3542C0F11EA8BD18B4',
                        'role': 'ex-owner',
                        'person': True,
                        'share': {
                            'capital': Decimal('108000.00'),
                            'currency': 'лв',
                            'percent': Decimal('90.00')
                        }}, {
                        'name': 'ТЕОДОРА НИКОЛОВА ГРОЗДЕВА',
                        'href': '/person/81A4A2054299C945EF87DC560A3542568BE655AD26A6A0B38CCB5D82318D7CA2',
                        'role': 'ex-owner',
                        'person': True,
                        'share': {
                            'capital': Decimal('12000.00'),
                            'currency': 'лв',
                                'percent': Decimal('10.00')
                        }}, {
                            'name': '"КАПТИВА ХИДРО" ЕООД',
                            'href': '/person/200621030',
                            'role': 'Capital owner',
                            'person': False
                    }],
                'source': 'https://papagal.bg'}

        num_new_entities = create_legal_entity(
            info, info['source'])

        self.assertEqual(num_new_entities, 5)
        v = LegalEntity.objects.filter(native_name='ВАЛЕНТИН НЕДЕЛЧЕВ ГРОЗДЕВ')
        self.assertEqual(len(v), 1)

        ex_owners = StakeHolder.objects.filter(
            holder=v[0]).filter(stake_type=StakeHolder.EX_OWNER)

        self.assertEqual(len(ex_owners), 1)
        self.assertEqual(ex_owners[0].percent, Decimal(90))
        # self.assertEqual(ex_owners[0].company.pk, et.pk)
        self.assertEqual(ex_owners[0].holder.native_name,
                         'ВАЛЕНТИН НЕДЕЛЧЕВ ГРОЗДЕВ')

        self.assertEqual(len(StakeHolder.objects.all()), 4)
        num_new_entities = create_legal_entity(
            info, info['source'])
        self.assertEqual(len(StakeHolder.objects.all()), 4)
