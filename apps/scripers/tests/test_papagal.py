from django.test import TestCase
from scripers.papagal import *
from decimal import Decimal


class PapagalScriperTest(TestCase):
    def test_parse_ceo_and_owners_1(self):
        dd = '''<dd class="col-sm-9">
 Управител:
 <a class="underlined" href="/person/088846C589308B44CB79FC3E1C28B39DC89BE51513CEA5DC93E4B6D0E4F20FB4">
  Димитър Иванов Николов
 </a>
 (свързан с 7
фирми)
 <br/>
 Управител:
 <a class="underlined" href="/person/BE9D62707BF400C839AE879A7FD6DC754F791D7B94C6EB21B2BD270098C62242">
  Стойчо Захариев Иванов
 </a>
 (свързан с 14
фирми)
 <br/>
 <div class="w-100 pt-3">
  <script async="" crossorigin="anonymous" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5464136730279304">
  </script>
  <!-- persons rectangle -->
  <ins class="adsbygoogle" data-ad-client="ca-pub-5464136730279304" data-ad-format="auto" data-ad-slot="1114200888" data-full-width-responsive="true" style="display:block">
  </ins>
  <script>
   (adsbygoogle = window.adsbygoogle || []).push({});
  </script>
 </div>
 Съдружник:
 <a class="underlined" href="/person/088846C589308B44CB79FC3E1C28B39DC89BE51513CEA5DC93E4B6D0E4F20FB4">
  Димитър Иванов Николов
 </a>
 <b>
  2,500.00 лв - 50.00% дял
 </b>
 (свързан с 7
фирми)
 <br/>
 Съдружник:
 <a class="underlined" href="/person/201060956">
  "СЕЙКОН - БГ" ООД
 </a>
 <b>
  2,500.00 лв - 50.00% дял
 </b>
 (свързан с 4
фирми)
 <br/>
</dd>'''
        soup = BeautifulSoup(dd, 'html.parser')
        info = parse_ceo_and_owners(soup)
        self.assertTrue('people' in info.keys())
        self.assertEqual(len(info['people']), 4)
        self.assertEqual(info['people'][0]['name'], 'Димитър Иванов Николов')
        self.assertEqual(info['people'][0]['person'], True)
        self.assertEqual(info['people'][0]['role'], 'ceo')
        self.assertEqual(info['people'][0]['href'],
                         '/person/088846C589308B44CB79FC3E1C28B39DC89BE51513CEA5DC93E4B6D0E4F20FB4')

        self.assertEqual(info['people'][1]['name'], 'Стойчо Захариев Иванов')
        self.assertEqual(info['people'][1]['person'], True)
        self.assertEqual(info['people'][1]['role'], 'ceo')
        self.assertEqual(info['people'][1]['href'],
                         '/person/BE9D62707BF400C839AE879A7FD6DC754F791D7B94C6EB21B2BD270098C62242')

        self.assertEqual(info['people'][2]['name'], 'Димитър Иванов Николов')
        self.assertEqual(info['people'][2]['person'], True)
        self.assertEqual(info['people'][2]['role'], 'owner')
        self.assertEqual(info['people'][2]['href'],
                         '/person/088846C589308B44CB79FC3E1C28B39DC89BE51513CEA5DC93E4B6D0E4F20FB4')
        self.assertEqual(info['people'][2]['share'],
                         {
            'percent': Decimal('50.0'),
            'capital': Decimal('2500.0'),
            'currency': 'лв',
        })

        self.assertEqual(info['people'][3]['name'], '"СЕЙКОН - БГ" ООД')
        self.assertEqual(info['people'][3]['person'], False)
        self.assertEqual(info['people'][3]['role'], 'owner')
        self.assertEqual(info['people'][3]['href'], '/person/201060956')
        self.assertEqual(info['people'][3]['share'],
                         {
            'percent': Decimal('50.0'),
            'capital': Decimal('2500.0'),
            'currency': 'лв',
        })

    def test_parse_ceo_and_owners_2(self):
        dd = '''<dd class="col-sm-9">
                                        Управител: <a class="underlined" href="/person/088846C589308B44CB79FC3E1C28B39DC89BE51513CEA5DC93E4B6D0E4F20FB4">Димитър Иванов Николов</a> (свързан с 7
фирми)<br/>
                                            Управител: <a class="underlined" href="/person/BE9D62707BF400C839AE879A7FD6DC754F791D7B94C6EB21B2BD270098C62242">Стойчо Захариев Иванов</a> (свързан с 14
фирми)<br/>
<div class="w-100 pt-3">
<script async="" crossorigin="anonymous" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5464136730279304"></script>
<!-- persons rectangle -->
<ins class="adsbygoogle" data-ad-client="ca-pub-5464136730279304" data-ad-format="auto" data-ad-slot="1114200888" data-full-width-responsive="true" style="display:block"></ins>
<script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
</div>

                                                Съдружник: <a class="underlined" href="/person/088846C589308B44CB79FC3E1C28B39DC89BE51513CEA5DC93E4B6D0E4F20FB4">Димитър Иванов Николов</a>
<b>24.00 лв - 50.00% дял</b>

        (свързан с 7
фирми)<br/>
                                        Съдружник: <a class="underlined" href="/person/201060956">"СЕЙКОН - БГ" ООД</a>
<b>24.00 лв - 50.00% дял</b>

        (свързан с 4
фирми)<br/>
</dd>
'''
        soup = BeautifulSoup(dd, 'html.parser')
        info = parse_ceo_and_owners(soup)
        self.assertTrue('people' in info.keys())
        self.assertEqual(len(info['people']), 4)
        self.assertEqual(info['people'][0]['name'], 'Димитър Иванов Николов')
        self.assertEqual(info['people'][0]['person'], True)
        self.assertEqual(info['people'][0]['role'], 'ceo')
        self.assertEqual(info['people'][0]['href'],
                         '/person/088846C589308B44CB79FC3E1C28B39DC89BE51513CEA5DC93E4B6D0E4F20FB4')

        self.assertEqual(info['people'][1]['name'], 'Стойчо Захариев Иванов')
        self.assertEqual(info['people'][1]['person'], True)
        self.assertEqual(info['people'][1]['role'], 'ceo')
        self.assertEqual(info['people'][1]['href'],
                         '/person/BE9D62707BF400C839AE879A7FD6DC754F791D7B94C6EB21B2BD270098C62242')

        self.assertEqual(info['people'][2]['name'], 'Димитър Иванов Николов')
        self.assertEqual(info['people'][2]['person'], True)
        self.assertEqual(info['people'][2]['role'], 'owner')
        self.assertEqual(info['people'][2]['href'],
                         '/person/088846C589308B44CB79FC3E1C28B39DC89BE51513CEA5DC93E4B6D0E4F20FB4')
        self.assertEqual(info['people'][2]['share'],
                         {
            'percent': Decimal('50.0'),
            'capital': Decimal('24.0'),
            'currency': 'лв',
        })

        self.assertEqual(info['people'][3]['name'], '"СЕЙКОН - БГ" ООД')
        self.assertEqual(info['people'][3]['person'], False)
        self.assertEqual(info['people'][3]['role'], 'owner')
        self.assertEqual(info['people'][3]['href'], '/person/201060956')
        self.assertEqual(info['people'][3]['share'],
                         {
            'percent': Decimal('50.0'),
            'capital': Decimal('24.0'),
            'currency': 'лв',
        })

    def test_parse_ceo_and_owners_3(self):
        dd = '''<dd class="col-sm-9">
                                        Управител: <a class="underlined" href="/person/a0dec8c8f3e1a5b00b56cb92c9395419ca625ae2d1ff987320f5d0de6fcb7ae0">ВЕСЕЛА ЦОЧЕВА НЕСТОРОВА</a> (свързан с 6
фирми)<br/>
<div class="w-100 pt-3">
<script async="" crossorigin="anonymous" src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5464136730279304"></script>
<!-- persons rectangle -->
<ins class="adsbygoogle" data-ad-client="ca-pub-5464136730279304" data-ad-format="auto" data-ad-slot="1114200888" data-full-width-responsive="true" style="display:block"></ins>
<script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
</div>

                                                Съдружник: <a class="underlined" href="/person/175277813">"ВЕЛЕСТОВО" ЕООД</a>
<b>16.00 лв - 33.33% дял</b>

        (свързан с 3
фирми)<br/>
                                        Съдружник: <a class="underlined" href="/person/a0dec8c8f3e1a5b00b56cb92c9395419ca625ae2d1ff987320f5d0de6fcb7ae0">Весела Цочева Несторова</a>
<b>16.00 лв - 33.33% дял</b>

        (свързан с 6
фирми)<br/>
                                        Съдружник: <a class="underlined" href="/person/b1046d07ccb7b206da7e9c6b3eadaf8f14002e871d28356d88272846fa32b1d4">СТОЯН НЕДЯЛКОВ БРАДИНОВ</a>
<b>16.00 лв - 33.33% дял</b>

        (свързан с 10
фирми)<br/>
</dd>
'''
        soup = BeautifulSoup(dd, 'html.parser')
        info = parse_ceo_and_owners(soup)
        self.assertTrue('people' in info.keys())
        self.assertEqual(len(info['people']), 4)
        self.assertEqual(info['people'][0]['name'], 'ВЕСЕЛА ЦОЧЕВА НЕСТОРОВА')
        self.assertEqual(info['people'][0]['person'], True)
        self.assertEqual(info['people'][0]['role'], 'ceo')
        self.assertEqual(info['people'][0]['href'],
                         '/person/a0dec8c8f3e1a5b00b56cb92c9395419ca625ae2d1ff987320f5d0de6fcb7ae0')

        self.assertEqual(info['people'][1]['name'], '"ВЕЛЕСТОВО" ЕООД')
        self.assertEqual(info['people'][1]['person'], False)
        self.assertEqual(info['people'][1]['role'], 'owner')
        self.assertEqual(info['people'][1]['href'], '/person/175277813')
        self.assertEqual(info['people'][1]['share'],
                         {
            'percent': Decimal('33.33'),
            'capital': Decimal('16.0'),
            'currency': 'лв',
        })

        self.assertEqual(info['people'][2]['name'], 'Весела Цочева Несторова')
        self.assertEqual(info['people'][2]['person'], True)
        self.assertEqual(info['people'][2]['role'], 'owner')
        self.assertEqual(info['people'][2]['href'],
                         '/person/a0dec8c8f3e1a5b00b56cb92c9395419ca625ae2d1ff987320f5d0de6fcb7ae0')
        self.assertEqual(info['people'][2]['share'],
                         {
            'percent': Decimal('33.33'),
            'capital': Decimal('16.0'),
            'currency': 'лв',
        })

        self.assertEqual(info['people'][3]['name'], 'СТОЯН НЕДЯЛКОВ БРАДИНОВ')
        self.assertEqual(info['people'][3]['person'], True)
        self.assertEqual(info['people'][3]['role'], 'owner')
        self.assertEqual(info['people'][3]['href'],
                         '/person/b1046d07ccb7b206da7e9c6b3eadaf8f14002e871d28356d88272846fa32b1d4')
        self.assertEqual(info['people'][3]['share'],
                         {
            'percent': Decimal('33.33'),
            'capital': Decimal('16.0'),
            'currency': 'лв',
        })

    def test_is_person(self):
        self.assertFalse(is_person(name="\"Гардения Холдинг\" ГмбХ",
                                   href=u'/person/DF78B1993EAEE1F9356585D7B0DBEE2E1875DACAB002821903508F01D81EF426/%22%D0%93%D0%B0%D1%80%D0%B4%D0%B5%D0%BD%D0%B8%D1%8F%20%D0%A5%D0%BE%D0%BB%D0%B4%D0%B8%D0%BD%D0%B3%22%20%D0%93%D0%BC%D0%B1%D0%A5'
                                   ))
        self.assertFalse(is_person(name="\"Гардения Холдинг\" ГмбХ",
                                   href=u'/person/DF78B1993EAEE1F9356585D7B0DBEE2E1875DACAB002821903508F01D81EF426'))

    def test_strip_person_href(self):

        self.assertEqual(strip_person_href('/person/DF78B1993EAEE1F9356585D7B0DBEE2E1875DACAB002821903508F01D81EF426'),
                         '/person/DF78B1993EAEE1F9356585D7B0DBEE2E1875DACAB002821903508F01D81EF426')

        self.assertEqual(strip_person_href(href=u'/person/DF78B1993EAEE1F9356585D7B0DBEE2E1875DACAB002821903508F01D81EF426/%22%D0%93%D0%B0%D1%80%D0%B4%D0%B5%D0%BD%D0%B8%D1%8F%20%D0%A5%D0%BE%D0%BB%D0%B4%D0%B8%D0%BD%D0%B3%22%20%D0%93%D0%BC%D0%B1%D0%A5'),
                         '/person/DF78B1993EAEE1F9356585D7B0DBEE2E1875DACAB002821903508F01D81EF426')

    def test_weird_page(self):
        content = '''<!doctype html>
<html>
    <head>
        <!-- Global site tag (gtag.js) - Google Analytics -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=UA-30224987-3"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());

            gtag('config', 'UA-30224987-3');
        </script>


        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

        <title>Фирма ВТК ЕООД (VTK)  ЕИК 127585860</title>


        <link rel="canonical" href="https://papagal.bg/eik/127585860/b9fb" />



        <meta name="description" content="ВТК ЕООД - управители, съдружници, свързани фирми, финансови отчети, ЕИК/ДДС номера, адрес, хронология на промени">

        <link rel="icon" type="image/png" href="/favicon.png" />

                    <link rel="stylesheet" href="/build/app.d7205117.css">


    </head>
    <body>
            <div class='container inner-page'>
        <div class='bg-white rounded shadow-sm p-3 mt-4'>
            <div class='row'>
                <div class='col-md-3 text-center text-sm-left'>
                    <a href='/' class='logo-text'>Papagal.BG</a><br />
                    Търсачка търговски регистър
                </div>
                <div class='col-md-9'>
                        <form class='row search-form ' action='/s' method='POST'>
        <div class='col-12 '>
            <div class="input-group">
                <input type="text" name="query" id="search" value="" placeholder="Търси в над 900,000 фирми" class="form-control form-control-lg rounded search-input" autocomplete="off">

                <span class="input-group-btn">
                    <button type="submit" class="btn btn-primary btn-lg ml-2">
                        <span class='d-none d-md-block'>
                            Търси
                        </span>
                        <i class="fa fa-search d-md-none" aria-hidden="true"></i>
                    </button>
                </span>
            </div>

            <div class='mt-2 choice-labels'>
                <div class="btn-group" data-toggle="buttons">
                    <label class="btn btn-info btn-sm active">
                        <input  type="radio" name="type" value='company' autocomplete="off" checked> <span class='d-none d-sm-inline'>Търси</span> Фирми
                    </label>
                    <label class="btn btn-info btn-sm">
                        <input  type="radio" name="type" value='person' autocomplete="off"> <span class='d-none d-sm-inline'>Търси</span> Лица
                    </label>
                </div>
                <div class="btn-group">
                    <label>
                        <a href='/advanced_search' class="btn btn-warning btn-sm ml-1">
                            Разширено търсене
                            <span class='badge badge-danger'>ново</span>
                        </a>
                    </label>
                </div>
            </div>
        </div>
    </form>

                </div>
            </div>
        </div>
        <div class='mt-4 p-3 bg-white rounded shadow-sm'>
                    <ol vocab="https://schema.org/" typeof="BreadcrumbList" class='breadcrumbs'>
        <li property="itemListElement" typeof="ListItem">
            <a property="item" typeof="WebPage" href="https://papagal.bg/">
            <span property="name">Начало</span></a>
            <meta property="position" content="1">
        </li>

                ›
        <li property="itemListElement" typeof="ListItem">
            <a property="item" typeof="WebPage" href="https://papagal.bg/bg/">
            <span property="name">БГ</span></a>
            <meta property="position" content="2">
        </li>


                ›
        <li property="itemListElement" typeof="ListItem">
            <a property="item" typeof="WebPage" href="https://papagal.bg/bg/1-sofiya-stolitsa">
            <span property="name">Област София (столица)</span></a>
            <meta property="position" content="3">
        </li>



                        ›
        <li property="itemListElement" typeof="ListItem">
            <a property="item" typeof="WebPage" href="https://papagal.bg/bg/1-sofiya-stolitsa/1-stolichna">
            <span property="name">Община Столична</span></a>
            <meta property="position" content="4">
        </li>


                ›
        <li property="itemListElement" typeof="ListItem">
            <a property="item" typeof="WebPage" href="https://papagal.bg/bg/1-sofiya-stolitsa/1-stolichna/1-sofiya">
            <span property="name">гр. София</span></a>
            <meta property="position" content="5">
        </li>
            </ol>

    <div class=''>
    <h1 class='smaller-size'>
                ВТК
                        ЕООД
            </h1>

                    <div class='d-none d-md-block text-center'>
    <script async src="//pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
    <!-- header banner desktop billboard -->
    <ins class="adsbygoogle"
         style="display:inline-block;width:970px;height:250px"
         data-ad-client="ca-pub-5464136730279304"
         data-ad-slot="7599189897"></ins>
    <script>
    (adsbygoogle = window.adsbygoogle || []).push({});
    </script>
</div>
<div class='d-xxs-block d-md-none'>
        <script async src="//pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
        <!-- header banner -->
        <ins class="adsbygoogle"
            style="display:block"
            data-ad-client="ca-pub-5464136730279304"
            data-ad-slot="7105287374"
            data-ad-format="auto"
            data-full-width-responsive="true"></ins>
        <script>
        (adsbygoogle = window.adsbygoogle || []).push({});
        </script>
</div>

            <dl class="row mt-1">
                <dt class="col-sm-3">Статус</dt>
        <dd class="col-sm-9">
                        <div class='text-success'>
                Активен
            </div>
                    </dd>

                <dt class="col-sm-3">ЕИК/ПИК</dt>
        <dd class="col-sm-9">127585860</dd>

        <dt class="col-sm-3">Регистрация по ЗДДС</dt>
        <dd class="col-sm-9">
                Да - BG127585860
                        от
            2005-11-18
                                    на основание чл. 96 от ЗДДС
                                    (Задължителна регистрация)
                            </dd>

                <dt class="col-sm-3">Дата на регистрация</dt>
        <dd class="col-sm-9">
                    2004 година
                </dd>

                <dt class="col-sm-3">Наименование</dt>
        <dd class="col-sm-9">ВТК</dd>

                <dt class="col-sm-3">Транслитерация</dt>
        <dd class="col-sm-9">VTK</dd>

                <dt class="col-sm-3">Оборот</dt>
        <dd class="col-sm-9">
        82,000 лв. оборот
                за 2019 г.
        </dd>

                <dt class="col-sm-3">Служители</dt>
        <dd class="col-sm-9">
        1
                служител
                към 2019 г.
        </dd>

                <dt class="col-sm-3">Правна форма</dt>
        <dd class="col-sm-9">
            Еднолично дружество с ограничена отговорност (ЕООД)
        </dd>


                <dt class="col-sm-3">Седалище адрес</dt>
        <dd class="col-sm-9">
        БЪЛГАРИЯ, гр. София, р-н Лозенец, ул. ГОРСКИ ПЪТНИК, 56, ет. 1

        <a href='https://www.google.bg/maps/search/%D0%91%D0%AA%D0%9B%D0%93%D0%90%D0%A0%D0%98%D0%AF+%D0%B3%D1%80.+%D0%A1%D0%BE%D1%84%D0%B8%D1%8F+%D1%80-%D0%BD+%D0%9B%D0%BE%D0%B7%D0%B5%D0%BD%D0%B5%D1%86+%D1%83%D0%BB.+%D0%93%D0%9E%D0%A0%D0%A1%D0%9A%D0%98+%D0%9F%D0%AA%D0%A2%D0%9D%D0%98%D0%9A+56+' class='btn btn-info btn-sm check-on-map' target='_blank'>
            <i class="fas fa-map-marked-alt"></i>
            Виж на картата
        </a>

                        <br />Има <b>36</b> фирми на този адрес
        <a href='/seat/1/5352/%D1%83%D0%BB.%20%D0%93%D0%9E%D0%A0%D0%A1%D0%9A%D0%98%20%D0%9F%D0%AA%D0%A2%D0%9D%D0%98%D0%9A/56/none/7d4' class='underlined' rel='nofollow'>виж фирмите</a>

        </dd>

                        <dt class="col-sm-3">Контакти</dt>
            <dd class="col-sm-9">
                                <button type='button' class='btn btn-success btn-sm' data-toggle="modal" data-target="#smsModal">
                    <i class="fa fa-phone-square" aria-hidden="true"></i>
                    Виж телефонен номер
                                        и имейл адрес
                                    </button>
                            </dd>


                <dt class="col-sm-3">Код на икономическа дейност</dt>
        <dd class="col-sm-9">
        3511
                        - ПРОИЗВОДСТВО НА ЕЛ. ЕНЕРГИЯ
                    </dd>

                <dt class="col-sm-3">Предмет на дейност</dt>
        <dd class="col-sm-9">
                    <span class='short-subject-of-activity'>ПРОИЗВОДСТВО НА ЕЛЕКТРОЕНЕРГИЯ И ЕНЕРГИЙНИ МОЩНОСТИ,   ПОКУПКА НА СТОКИ ИЛИ ДРУГИ ВЕЩИ С ЦЕЛ ПРОДАЖБА В ПЪРВОНАЧАЛЕН,   ПРЕРАБОТЕН ИЛИ ОБРАБОТЕН ВИД,   ПРОДАЖБА НА СТОКИ ОТ СОБСТВЕНО ПРОИЗВОДСТВО В СТ...</span>
            <span class='full-subject-of-activity d-none'>
                ПРОИЗВОДСТВО НА ЕЛЕКТРОЕНЕРГИЯ И ЕНЕРГИЙНИ МОЩНОСТИ,   ПОКУПКА НА СТОКИ ИЛИ ДРУГИ ВЕЩИ С ЦЕЛ ПРОДАЖБА В ПЪРВОНАЧАЛЕН,   ПРЕРАБОТЕН ИЛИ ОБРАБОТЕН ВИД,   ПРОДАЖБА НА СТОКИ ОТ СОБСТВЕНО ПРОИЗВОДСТВО В СТРАНАТА И В ЧУЖБИНА,   ПРОИЗВОДСТВО И ТЪРГОВИЯ С РАЗРЕШЕНИ ПРОМИШЛЕНИ СТОКИ,   ИЗДЕЛИЯ ЗА БИТА,   ИЗКУПУВАНЕ,   ПРОИЗВОДСТВО,   ПРЕРАБОТКА И РЕАЛИЗАЦИЯ НА СЕЛСКОСТОПАНСКА ПРОДУКЦИЯ ОТ РАСТИТЕЛЕН ИЛИ ЖИВОТИНСКИ ПРОИЗХОД,   ЖИВИ ЖИВОТНИ,   ГОРИВА,   ДЪРВЕСИНА,   РИБА И РИБНИ ПРОДУКТИ,   БИЛКИ,   МЕД И ПЧЕЛНИ ПРОДУКТИ,   СТРОИТЕЛНИ МАТЕРИАЛИ,   ОКАЗИОННА И КОМИСИОННА ТЪРГОВИЯ С ПОСОЧЕНИТЕ И ДРУГИ СТОКИ,   ТЪРГОВСКО ПРЕДСТАВИТЕЛСТВО,   ПОСРЕДНИЧЕСТВО И АГЕНТСТВО НА МЕСТНИ И ЧУЖДЕСТРАННИ ФИРМИ И ЛИЦА,   РЕСТОРАНТЬОРСТВО И ХОТЕЛИЕРСТВО,   ЗАВЕДЕНИЯ ЗА БЪРЗО ХРАНЕНЕ,   ИЗВЪРШВАНЕ НА ВСИЧКИ ВИДОВЕ ТРАНСПОРТНИ,   ТОВАРНИ,   ТАКСИМЕТРОВИ,   АВТОБУСНИ И АВТОСЕРВИЗНИ УСЛУГИ,   ТЪРГОВИЯ И РЕЦИКЛИРАНЕ НА РЕЗЕРВНИ ЧАСТИ,   СТРОИТЕЛНИ,   КОМИСИОННИ,   СПЕДИТОРСКИ,   РЕКЛАМНИ,   ИНФОРМАЦИОННИ,   СКЛАДОВИ,   ТУРИСТИЧЕСКИ УСЛУГИ,   ПОКУПКА,   СТРОЕЖ И ОБЗАВЕЖДАНЕ НА ЖИЛИЩА С ЦЕЛ ПРОДАЖБА,   ИЗВЪРШВАНЕ НА ВСЯКАКВА ДРУГА ТЪРГОВСКА ДЕЙНОСТ НЕЗАБРАНЕНА ОТ ЗАКОНА,   А ТАКА СЪЩО,   ИМПОРТ,   ЕКСПОРТ,   РЕЕКСПОРТ И СДЕЛКИ НА БАРТЕРНА ОСНОВА СЪС СТОКИ И УСЛУГИ ОТ ЦЕЛИЯ ПРЕДМЕТ НА ДЕЙНОСТ.
            </span>
            <a href='javascript:;' class='underlined read-more'>прочети още</a>
            <a href='javascript:;' class='underlined read-less d-none'>скрии</a>
                </dd>





        <dt class="col-sm-3">Управители/Съдружници</dt>
        <dd class="col-sm-9">
                                        Управител: <a class='underlined' href='/person/D1ADF7CB5CFFC55B57D1F1A53F44FC26E6D51638570A2ABAED9439BCC7AB83C5'>ГАБРИЕЛА ЛЮДМИЛОВА НАЙДЕНОВА</a> (свързан с 6
фирми)<br />

                <div class='w-100 pt-3'>

            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-5464136730279304"
                crossorigin="anonymous"></script>
            <!-- persons rectangle -->
            <ins class="adsbygoogle"
                style="display:block"
                data-ad-client="ca-pub-5464136730279304"
                data-ad-slot="1114200888"
                data-ad-format="auto"
                data-full-width-responsive="true"></ins>
            <script>
                (adsbygoogle = window.adsbygoogle || []).push({});
            </script>

                    </div>

                        <span style='color:red;'>ЗАЛИЧЕН</span>                        Съдружник: <a class='underlined' href='/person/1DA9E12A55225D41FD4623321123D40694D5AADD786F3C3542C0F11EA8BD18B4'>ВАЛЕНТИН НЕДЕЛЧЕВ ГРОЗДЕВ</a>

                <b>108,000.00 лв - 90.00% дял</b>

        (свързан с 4
фирми)<br />
                <span style='color:red;'>ЗАЛИЧЕН</span>                        Съдружник: <a class='underlined' href='/person/81A4A2054299C945EF87DC560A3542568BE655AD26A6A0B38CCB5D82318D7CA2'>ТЕОДОРА НИКОЛОВА ГРОЗДЕВА</a>

                <b>12,000.00 лв - 10.00% дял</b>

        (свързан с 3
фирми)<br />

        </dd>


                <dt class="col-sm-3">Едноличен собственик на капитала</dt>
        <dd class="col-sm-9">
        <a class='underlined' href='/person/200621030' >&quot;КАПТИВА ХИДРО&quot; ЕООД</a>
            (свързан с 1
фирма)
        </dd>

                <dt class="col-sm-3">Капитал размер</dt>
        <dd class="col-sm-9">
        120,000 лева
                        (120,000 лева внесен)
                    </dd>
            </dl>
    <hr>
    <h3>Финансови показатели</h3>
        <div class='col-md-9'>
                <div id="financial_chart" style="width: 100%;"></div>
                <table class='table table-bordered table-sm mt-4'>
            <tr>
                <th>Година</th>
                <th><div class='revenue_dot'></div> Оборот</th>
                <th><div class='profit_dot'></div> Печалба</th>
                <th>Марж на печалбата</th>
            </tr>
                        <tr>
                <td>2019</td>
                <td>
                    82,000
                                                            <span class='pl-1 text-danger text-sm d-block d-sm-inline'>
                    <i class="fas fa-arrow-alt-circle-down"></i>
                                        -6.82%
                    </span>
                                    </td>
                <td>
                                        0
                                    </td>
                <td>
                                        -
                                    </td>
            </tr>
                        <tr>
                <td>2018</td>
                <td>
                    88,000
                                                            <span class='pl-1 text-danger text-sm d-block d-sm-inline'>
                    <i class="fas fa-arrow-alt-circle-down"></i>
                                        -12.87%
                    </span>
                                    </td>
                <td>
                                        -
                                    </td>
                <td>
                                        -
                                    </td>
            </tr>
                        <tr>
                <td>2017</td>
                <td>
                    101,000
                                                            <span class='pl-1 text-success text-sm d-block d-sm-inline'>
                    <i class="fas fa-arrow-alt-circle-up"></i>
                                        6.32%
                    </span>
                                    </td>
                <td>
                                        -
                                    </td>
                <td>
                                        -
                                    </td>
            </tr>
                        <tr>
                <td>2016</td>
                <td>
                    95,000
                                                            <span class='pl-1 text-danger text-sm d-block d-sm-inline'>
                    <i class="fas fa-arrow-alt-circle-down"></i>
                                        -5.94%
                    </span>
                                    </td>
                <td>
                                        -
                                    </td>
                <td>
                                        -
                                    </td>
            </tr>
                        <tr>
                <td>2015</td>
                <td>
                    101,000
                                    </td>
                <td>
                                        -
                                    </td>
                <td>
                                        -
                                    </td>
            </tr>
                        <tr>
                <td>2014</td>
                <td>
                    101,000
                                                            <span class='pl-1 text-success text-sm d-block d-sm-inline'>
                    <i class="fas fa-arrow-alt-circle-up"></i>
                                        5.21%
                    </span>
                                    </td>
                <td>
                                        -
                                    </td>
                <td>
                                        -
                                    </td>
            </tr>
                        <tr>
                <td>2013</td>
                <td>
                    96,000
                                    </td>
                <td>
                                        -
                                    </td>
                <td>
                                        -
                                    </td>
            </tr>
                    </table>
    </div>
        <hr>

    <h3>Служители</h3>
        <div class='col-md-9'>
                <div id="employee_chart" style="width: 100%;"></div>
                <table class='table table-bordered table-sm mt-4'>
            <tr>
                <th>Година</th>
                <th><div class='employee_dot'></div> Служители</th>
            </tr>
                        <tr>
                <td>2019</td>
                <td>
                    1

                                    </td>
            </tr>
                        <tr>
                <td>2012</td>
                <td>
                    1

                                                            <span class='pl-1 text-danger text-sm'>
                    <i class="fas fa-arrow-alt-circle-down"></i>
                                        -50%
                    </span>
                                    </td>
            </tr>
                        <tr>
                <td>2011</td>
                <td>
                    2

                                    </td>
            </tr>
                        <tr>
                <td>2010</td>
                <td>
                    2

                                    </td>
            </tr>
                        <tr>
                <td>2009</td>
                <td>
                    2

                                    </td>
            </tr>
                        <tr>
                <td>2008</td>
                <td>
                    2

                                    </td>
            </tr>
                        <tr>
                <td>2007</td>
                <td>
                    2

                                    </td>
            </tr>
                    </table>
    </div>
        <hr>

    <h3>Мнения</h3>
    <div class='pb-2'>
        <div class='pb-2'>
            Все още няма добавени мнения за тази фирма.
            </div>

    <div class='row'>
        </div>

        </div>

    <a rel='nofollow' href='/eik/127585860/b9fb/add-review' class='btn btn-info'><i class="fas fa-plus-circle"></i> Добави мнение</a>
    <hr>
    <h3>Резюме</h3>
    <div>
        Фирма ВТК ЕООД на латиница &quot;VTK&quot; с ЕИК/ПИК 127585860 е основана на 16 Ноември 2009 година с правна форма &quot;Дружество с ограничена отговорност&quot; или на кратко &quot;ООД&quot;. Седалището на компанията се намира в гр. София, а началният внесен капитал е в размер на 120,000 лева.<br />
<br />
 Оборота на фирмата за 2019 година е в размер на 82,000 лв. което е с 7% по-малко от предходната 2018 година (88,000 лв.), а средният годишен ръст е -3%.
            </div>
    <hr>
    <h3>Хронология</h3>
    <div class='mt-3'>
                    <div class='h4'>2004</div>
                            <div class='mb-3 pl-3'>
                    <b>Регистрация на фирмата</b><br />







                                    </div>
                                    <hr>
                                <div class='h4'>2005-11-18</div>
                            <div class='mb-3 pl-3'>
                    <b>Регистрация по ЗДДС</b><br />
                                        Фирмата се регистрира по ЗДДС с номер BG127585860 на основание чл. 96 от ЗДДС - Задължителна регистрация







                                    </div>
                                    <hr>
                                <div class='h4'>2012-09-24</div>
                            <div class='mb-3 pl-3'>
                    <b>Промяна съдружници</b><br />






                                        <div class='text-danger'>
                                                - <a href='/person/1DA9E12A55225D41FD4623321123D40694D5AADD786F3C3542C0F11EA8BD18B4' class='underlined text-danger'>ВАЛЕНТИН НЕДЕЛЧЕВ ГРОЗДЕВ</a>

                                                    - <b>4500 лв - 3.75% дял</b>

                        <br />
                                                - <a href='/person/81A4A2054299C945EF87DC560A3542568BE655AD26A6A0B38CCB5D82318D7CA2' class='underlined text-danger'>ТЕОДОРА НИКОЛОВА ГРОЗДЕВА</a>

                                                    - <b>500 лв - 0.42% дял</b>

                        <br />
                                            </div>

                                        <div class='text-success'>
                                                + <a href='/person/81A4A2054299C945EF87DC560A3542568BE655AD26A6A0B38CCB5D82318D7CA2'  class='underlined text-success'>ТЕОДОРА НИКОЛОВА ГРОЗДЕВА</a>

                                                    - <b>12000 лв - 10.00% дял</b>
                                                <br />
                                                + <a href='/person/1DA9E12A55225D41FD4623321123D40694D5AADD786F3C3542C0F11EA8BD18B4'  class='underlined text-success'>ВАЛЕНТИН НЕДЕЛЧЕВ ГРОЗДЕВ</a>

                                                    - <b>108000 лв - 90.00% дял</b>
                                                <br />
                                            </div>
                                    </div>
                                    <hr>
                                <div class='h4'>2013-02-05</div>
                            <div class='mb-3 pl-3'>
                    <b>Промяна седалище</b><br />




                                        <div class='text-danger'>
                        - БЪЛГАРИЯ, гр. Шумен, УЛ. &quot;ПАНАЙОТ ВОЛОВ&quot;, 14
                    </div>

                                        <div class='text-success'>
                        + БЪЛГАРИЯ, гр. София, р-н Лозенец, ул. ГОРСКИ ПЪТНИК, 56, ет. 1
                    </div>


                                    </div>
                            <div class='mb-3 pl-3'>
                    <b>Промяна легална форма</b><br />
                                        Легалната форма се сменя от ООД на ЕООД







                                    </div>
                            <div class='mb-3 pl-3'>
                    <b>Промяна управители</b><br />






                                        <div class='text-danger'>
                                                - <a href='/person/1DA9E12A55225D41FD4623321123D40694D5AADD786F3C3542C0F11EA8BD18B4' class='underlined text-danger'>ВАЛЕНТИН НЕДЕЛЧЕВ ГРОЗДЕВ</a>


                        <br />
                                            </div>

                                        <div class='text-success'>
                                                + <a href='/person/D1ADF7CB5CFFC55B57D1F1A53F44FC26E6D51638570A2ABAED9439BCC7AB83C5'  class='underlined text-success'>ГАБРИЕЛА ЛЮДМИЛОВА НАЙДЕНОВА</a>

                                                <br />
                                            </div>
                                    </div>
                            <div class='mb-3 pl-3'>
                    <b>Заличаване съдружници</b><br />






                                        <div class='text-danger'>
                                                - <a href='/person/81A4A2054299C945EF87DC560A3542568BE655AD26A6A0B38CCB5D82318D7CA2' class='underlined text-danger'>ТЕОДОРА НИКОЛОВА ГРОЗДЕВА</a>

                                                    - <b>12000 лв - 10.00% дял</b>

                        <br />
                                                - <a href='/person/1DA9E12A55225D41FD4623321123D40694D5AADD786F3C3542C0F11EA8BD18B4' class='underlined text-danger'>ВАЛЕНТИН НЕДЕЛЧЕВ ГРОЗДЕВ</a>

                                                    - <b>108000 лв - 90.00% дял</b>

                        <br />
                                            </div>

                                        <div class='text-success'>
                                            </div>
                                    </div>
                            <div class='mb-3 pl-3'>
                    <b>Промяна предмет на дейност</b><br />


                                        <div class='text-danger' style='overflow-wrap: break-word;'>
                        - ПРОИЗВОДСТВО НА ЕЛЕКТРОЕНЕРТИЯ И ЕНЕРГИЙНИ МОЩНОСТИ; ПОКУПКА НА СТОКИ ИЛИ ДРУГИ ВЕЩИ С ЦЕЛ ПРЕПРОДАЖБА В ПЪРВОНАЧАЛЕН, ПРЕРАБОТЕН ИЛИ ОБРАБОТЕН ВИД; ПРОДАЖБА НА СТОКИ ОТ СОБСТВЕНО ПРОИЗВОДСТВО В СТРАНАТА И В ЧУЖБИНА; ПРОИЗВОДСТВО И ТЪРГОВИЯ С РАЗРЕШЕНИ ПРОМИШЛЕНИ СТОКИ, ИЗДЕЛИЯ ЗА БИТА; ИЗКУПУВАНЕ, ПРОИЗВОДСТВО, ПРЕРАБОТКА И РЕАЛИЗАЦИЯ НА СЕЛСКОСТОПАНСКА ПРОДУКЦИЯ ОТ РАСТИТЕЛЕН ИЛИ ЖИВОТИНСКИ ПРОИЗХОД, ЖИВИ ЖИВОТНИ, ГОРИВА, ДЪРВА, ДЪРВЕСИНА, РИБА И РИБНИ ПРОДУКТИ, БИЛКИ, МЕД И ПЧЕЛНИ ПРОДУКТИ, СТРОИТЕЛНИ МАТЕРИАЛИ; ОКАЗИОННА И КОМИСИОННА ТЪРГОВИЯ С ПОСОЧЕНИТЕ И ДРУГИ СТОКИ; ТЪРГОВСКО ПРЕДСТАВИТЕЛСТВО, ПОСРЕДНИЧЕСТВО И АГЕНТСТВО НА МЕСТНИ И ЧУЖДЕСТРАННИ ФИРМИ И ЛИЦА; РЕСТОРАНТЬОРСТВО И ХОТЕЛИЕРСТВО; ЗАВЕДЕНИЯ ЗА БЪРЗО ХРАНЕНЕ; ИЗВЪРШВАНЕ НА ВСИЧКИ ВИДОВЕ МЕТАЛООБРАБОТВАЩИ, ТРАНСПОРТНИ, ТОВАРНИ, ТАКСИМЕТРОВИ, АВТОБУСНИ И АВТОСЕРВИЗНИ УСЛУГИ; ТЪРГОВИЯ И РЕЦИКЛИРАНЕ НА РЕЗЕРВНИ ЧАСТИ; СТРОИТЕЛНИ, КОМИСИОННИ, СПЕДИТОРСКИ, РЕКЛАМНИ, ИНФОРМАЦИОННИ, СКЛАДОВИ, ТУРИСТИЧЕСКИ УСЛУГИ; ПОКУПКА, СТРОЕЖ И ОБЗАВЕЖДАНЕ НА ЖИЛИЩА С ЦЕЛ ПРОДАЖБА; ИЗВЪРШВАНЕ НА ВСЯКАКВА ДРУГА ТЪРГОВСКА ДЕЙНОСТ, НЕЗАБРАНЕНА ОТ ЗАКОНА, А ТАКА СЪЩО ИМПОРТ, ЕКСПОРТ, РЕЕКСПОРТ И СДЕЛКИ НА БАРТЕРНА ОСНОВА СЪС СТОКИ И УСЛУГИ ПО ЦЕЛИЯ ПРЕДМЕТ НА ДЕЙНОСТ.
                    </div>

                                        <div class='text-success' style='overflow-wrap: break-word;'>
                        + ПРОИЗВОДСТВО НА ЕЛЕКТРОЕНЕРГИЯ И ЕНЕРГИЙНИ МОЩНОСТИ, ПОКУПКА НА СТОКИ ИЛИ ДРУГИ ВЕЩИ С ЦЕЛ ПРОДАЖБА В ПЪРВОНАЧАЛЕН, ПРЕРАБОТЕН ИЛИ ОБРАБОТЕН ВИД, ПРОДАЖБА НА СТОКИ ОТ СОБСТВЕНО ПРОИЗВОДСТВО В СТРАНАТА И В ЧУЖБИНА, ПРОИЗВОДСТВО И ТЪРГОВИЯ С РАЗРЕШЕНИ ПРОМИШЛЕНИ СТОКИ, ИЗДЕЛИЯ ЗА БИТА, ИЗКУПУВАНЕ, ПРОИЗВОДСТВО, ПРЕРАБОТКА И РЕАЛИЗАЦИЯ НА СЕЛСКОСТОПАНСКА ПРОДУКЦИЯ ОТ РАСТИТЕЛЕН ИЛИ ЖИВОТИНСКИ ПРОИЗХОД, ЖИВИ ЖИВОТНИ, ГОРИВА, ДЪРВЕСИНА, РИБА И РИБНИ ПРОДУКТИ, БИЛКИ, МЕД И ПЧЕЛНИ ПРОДУКТИ, СТРОИТЕЛНИ МАТЕРИАЛИ, ОКАЗИОННА И КОМИСИОННА ТЪРГОВИЯ С ПОСОЧЕНИТЕ И ДРУГИ СТОКИ, ТЪРГОВСКО ПРЕДСТАВИТЕЛСТВО, ПОСРЕДНИЧЕСТВО И АГЕНТСТВО НА МЕСТНИ И ЧУЖДЕСТРАННИ ФИРМИ И ЛИЦА, РЕСТОРАНТЬОРСТВО И ХОТЕЛИЕРСТВО, ЗАВЕДЕНИЯ ЗА БЪРЗО ХРАНЕНЕ, ИЗВЪРШВАНЕ НА ВСИЧКИ ВИДОВЕ ТРАНСПОРТНИ, ТОВАРНИ, ТАКСИМЕТРОВИ, АВТОБУСНИ И АВТОСЕРВИЗНИ УСЛУГИ, ТЪРГОВИЯ И РЕЦИКЛИРАНЕ НА РЕЗЕРВНИ ЧАСТИ, СТРОИТЕЛНИ, КОМИСИОННИ, СПЕДИТОРСКИ, РЕКЛАМНИ, ИНФОРМАЦИОННИ, СКЛАДОВИ, ТУРИСТИЧЕСКИ УСЛУГИ, ПОКУПКА, СТРОЕЖ И ОБЗАВЕЖДАНЕ НА ЖИЛИЩА С ЦЕЛ ПРОДАЖБА, ИЗВЪРШВАНЕ НА ВСЯКАКВА ДРУГА ТЪРГОВСКА ДЕЙНОСТ НЕЗАБРАНЕНА ОТ ЗАКОНА, А ТАКА СЪЩО, ИМПОРТ, ЕКСПОРТ, РЕЕКСПОРТ И СДЕЛКИ НА БАРТЕРНА ОСНОВА СЪС СТОКИ И УСЛУГИ ОТ ЦЕЛИЯ ПРЕДМЕТ НА ДЕЙНОСТ.
                    </div>




                                    </div>
                                    </div>
    <hr>
    <h3>Свързани фирми</h3>
            <script async src="//pagead2.googlesyndication.com/pagead/js/adsbygoogle.js"></script>
        <!-- related firms -->
        <ins class="adsbygoogle"
            style="display:block"
            data-ad-client="ca-pub-5464136730279304"
            data-ad-slot="3157710605"
            data-ad-format="auto"
            data-full-width-responsive="true"></ins>
        <script>
        (adsbygoogle = window.adsbygoogle || []).push({});
        </script>
            <div class='mt-3'>
                                <a class='underlined' href='/eik/131417256/2e48'>УИНКОМ</a>
            <br />
                        <a class='underlined' href='/eik/200620754/ef31'>КАПТИВА СОЛАР</a>
            <br />
                        <a class='underlined' href='/eik/200621030/888c'>КАПТИВА ХИДРО</a>
            <br />
                        <a class='underlined' href='/eik/200627040/3b69'>АЛ - ЕКО - ЕНЕРГИЯ</a>
            <br />
                        <a class='underlined' href='/eik/127570965/8f6e'>ГРОЗДЕВ</a>
            <br />
                        <a class='underlined' href='/eik/837028464/3300'>ВАЛЕНТИН ГРОЗДЕВ</a>
            <br />
                        <a class='underlined' href='/eik/131403299/b263'>АНЕМОС</a>
            <br />
                        <a class='underlined' href='/eik/127021151/b7d4'>Стройекспрес</a>
            <br />

                        <a href='/eik/127585860/b9fb/related' class='btn btn-warning btn-sm mt-2' rel='nofollow'><i class="fas fa-network-wired"></i> Виж всички свързани фирми</a>

            </div>




    <hr class='mt-3'>
        <a href='/eik/127585853/c742' class='btn btn-secondary btn-sm'>
        <i class="fas fa-caret-square-left"></i>
        Предишна фирма
    </a>

        <a href='/eik/127585878/f17f' class='btn btn-secondary btn-sm'>
        Следваща фирма
        <i class="fas fa-caret-square-right"></i>
    </a>
        <hr>

        <!-- Modal -->
    <div class="modal fade" id="smsModal" tabindex="-1" role="dialog" aria-labelledby="exampleModalLabel" aria-hidden="true" data-generate-sms-token-url='/generate_sms_token/127585860'>
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="exampleModalLabel">
                        Телефонен номер
                                                и имейл адрес
                                            </h5>
                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                    </button>
                </div>
                <div class="modal-body text-center d-none">
                    Тази услуга е платена!<br /><br />
                    Изпратете SMS на номер <b>1092</b> с код <b>info<span class='token'></span></b><br /><br />
                    След като изпратите съобщението, ще получите обратен SMS
                    с телефонния номер  и имейл адреса на фирмата.
                    <Br /><br />
                    <div class='text-success'>Цената е <b>2.40 лв с ДДС</b></div>
                    * не носим отговорност за сгрешени SMS-и.<br />
                    <a href='/pages/sms_info' target='_blank'>повече информация за услугата</a>

                </div>
                <div class="modal-footer text-center d-none">
                    <button type="button" class="btn btn-secondary" data-dismiss="modal">Затвори</button>
                </div>
            </div>
        </div>
    </div>


    </div>
<script type="application/ld+json">
{
    "@context": "http://schema.org",
    "@type": "Organization",
"url": "http://papagal.bg/eik/127585860/b9fb","foundingDate": "2009-11-16","duns": "127585860","leiCode": "127585860","address": "БЪЛГАРИЯ, гр. София, р-н Лозенец, ул. ГОРСКИ ПЪТНИК, 56, ет. 1","founder": "ГАБРИЕЛА ЛЮДМИЛОВА НАЙДЕНОВА","name": "ВТК ЕООД","legalName": "ВТК ЕООД"}
</script>
        </div>
    </div>

        <div class='footer mt-4 mb-4 text-center'>
            <div class='container'>
                2023, ПАПАГАЛ.БГ ООД, papagal.bg<br />
                                <a href='/contacts'>За контакти</a>
                                <div class='footer-small-text'>
                    Данните използвани в сайта са взети от <a href='https://data.egov.bg/' target='_blank' rel='nofollow'>портала за отворени данни на Република България - egov.bg</a><br />
                    Последно обновяване на данните: Януари 2023
                </div>
            </div>
        </div>

                            <script>
            var RECAPTCHA_SITE_KEY = "6LdG88USAAAAAByvat3xKDgckVNTPitTh7ScSMlZ";
            var AUTOCOMPLETE_URL = "/autocomplete/";
            var globalFlashMessages = [];


                    </script>
        <script src="/build/runtime.18a02a75.js"></script><script src="/build/app.8e5c73e9.js"></script>
        <script src="/build/homepage.ffb7a392.js"></script>

    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>

    <script>
        var financialData =
        [
                {year: 2019, revenue: 82000, profit: 0},                {year: 2018, revenue: 88000, profit: 0},                {year: 2017, revenue: 101000, profit: 0},                {year: 2016, revenue: 95000, profit: 0},                {year: 2015, revenue: 101000, profit: 0},                {year: 2014, revenue: 101000, profit: 0},                {year: 2013, revenue: 96000, profit: 0}                ];

        var employeeData =
        [
                {year: 2019, employees: 1},                {year: 2012, employees: 1},                {year: 2011, employees: 2},                {year: 2010, employees: 2},                {year: 2009, employees: 2},                {year: 2008, employees: 2},                {year: 2007, employees: 2}                ];
    </script>
    <script src="/build/company.976e3f88.js"></script>
    </body>
</html>'''

        soup = BeautifulSoup(content, 'html.parser')
        scriper = PapagalScriper()
        info = scriper.parse_soup(soup, info={})
        self.assertEqual(info['active'], True)
        self.assertEqual(info['founded'], date(2004, 1, 1))
        self.assertEqual(info['name'], 'ВТК')
        self.assertEqual(info['latin_name'], 'VTK')
        self.assertEqual(info['legal_form'], 'ЕООД')

        self.assertTrue('people' in info.keys())
        self.assertEqual(len(info['people']), 4)
        self.assertEqual(info['people'][0]['name'],
                         'ГАБРИЕЛА ЛЮДМИЛОВА НАЙДЕНОВА')
        self.assertEqual(info['people'][0]['person'], True)
        self.assertEqual(info['people'][0]['role'], 'ceo')
        self.assertEqual(info['people'][0]['href'],
                         '/person/D1ADF7CB5CFFC55B57D1F1A53F44FC26E6D51638570A2ABAED9439BCC7AB83C5')

        self.assertEqual(info['people'][1]['name'],
                         'ВАЛЕНТИН НЕДЕЛЧЕВ ГРОЗДЕВ')
        self.assertEqual(info['people'][1]['person'], True)
        self.assertEqual(info['people'][1]['role'], 'ex-owner')
        self.assertEqual(info['people'][1]['href'],
                         '/person/1DA9E12A55225D41FD4623321123D40694D5AADD786F3C3542C0F11EA8BD18B4')
        self.assertEqual(info['people'][1]['share'],
                         {
            'percent': Decimal('90'),
            'capital': Decimal('108000'),
            'currency': 'лв',
        })

        self.assertEqual(info['people'][2]['name'],
                         'ТЕОДОРА НИКОЛОВА ГРОЗДЕВА')
        self.assertEqual(info['people'][2]['person'], True)
        self.assertEqual(info['people'][2]['role'], 'ex-owner')
        self.assertEqual(info['people'][2]['href'],
                         '/person/81A4A2054299C945EF87DC560A3542568BE655AD26A6A0B38CCB5D82318D7CA2')

        self.assertEqual(info['people'][2]['share'],
                         {
            'percent': Decimal('10'),
            'capital': Decimal('12000'),
            'currency': 'лв',
        })

        self.assertEqual(info['people'][3]['name'], '"КАПТИВА ХИДРО" ЕООД')
        self.assertEqual(info['people'][3]['person'], False)
        self.assertEqual(info['people'][3]['role'], 'Capital owner')
        self.assertEqual(info['people'][3]['href'], '/person/200621030')
