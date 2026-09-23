"""Примеры по типам ПДн: голое значение, с меткой, в предложении, регистр, форматы."""

from blind_core import E
from blind_values import (AMEX, BAD_CARD, I10, I12, I12_BAD, MC, MIR16, MIR19, SN,
                          SN_BAD, UP, VISA, amex, dash, snd, snf, sns, sp)

# ---------------------------------------------------------------- PERSON
C = "PERSON"
E(C, "bare", "⟦Смирнова Ольга Викторовна|PER⟧")
E(C, "bare_lower", "⟦кузнецов дмитрий андреевич|PER⟧")
E(C, "bare_upper", "⟦ПЕТРОВА АННА СЕРГЕЕВНА|PER⟧")
E(C, "bare_initials_after", "⟦Иванов И.И.|PER⟧")
E(C, "initials_before_instrumental",
  "Заявление подписано клиентом ⟦В. А. Соколовым|PER⟧ ⟪12 сентября⟫ в отделении на ⟪Арбате⟫.")
E(C, "declension_dative_llm",
  "Подготовь вежливый ответ ⟦Иванову Ивану Ивановичу|PER⟧ на жалобу о двойном списании комиссии за обслуживание.")
E(C, "declension_instrumental_fem",
  "Свяжитесь с ⟦Петровой Анной Сергеевной|PER⟧ по вопросу реструктуризации кредита.")
E(C, "declension_genitive_initials",
  "Поступило обращение от ⟦Сидорова П.П.|PER⟧ о блокировке карты.")
E(C, "double_surname",
  "Клиент ⟦Римский-Корсаков Андрей Николаевич|PER⟧ просит увеличить кредитный лимит до ⟪300 000⟫ рублей.")
E(C, "non_slavic_instrumental",
  "Кредитный договор заключён с ⟦Ахмедовым Рустамом Ильдаровичем|PER⟧ в прошлый вторник.")
E(C, "non_slavic_korean", "Заёмщик: ⟦Ким Ен Хо|PER⟧. Статус заявки: на проверке.")
E(C, "non_slavic_kyzy",
  "Заявительница ⟦Мамедова Лейла Азер кызы|PER⟧ просит выдать справку об остатке по счёту.")
E(C, "name_surname_dative",
  "Перезвоните ⟦Екатерине Волковой|PER⟧ после обеда, она ждёт решения по ипотеке.")
E(C, "mixed_case", "ФИО: ⟦ЖуКоВа МаРиНа ОлЕгОвНа|PER⟧")
E(C, "latin_in_russian",
  "Письмо от ⟦Dmitry Orlov|PER⟧ пришло на общий ящик поддержки, ответьте ему сегодня.")
E(C, "declension_prepositional_name_first",
  "Речь идёт о ⟦Николае Петровиче Фёдорове|PER⟧, нашем клиенте с ⟪2012 года⟫.")
E(C, "two_persons_initials_spaced",
  "Заёмщик ⟦Белова Т. Н.|PER⟧ и поручитель ⟦Белов Н. К.|PER⟧ подписали договор в одном отделении.")
E(C, "name_is_common_noun",
  "Клиентка ⟦Вера Николаевна Белая|PER⟧ просит закрыть вклад «⟪Надёжный⟫» досрочно.")
E(C, "llm_prompt_dative",
  "Составь письмо клиенту ⟦Семёнову Петру Алексеевичу|PER⟧ с напоминанием, что платёж по кредиту нужно внести до ⟪25 сентября⟫.")
E(C, "name_roman", "Звонил ⟦Роман Лебедев|PER⟧, просил перенести встречу в офисе на пятницу.")
E(C, "upper_genitive", "ДОВЕРЕННОСТЬ ВЫДАНА НА ИМЯ ⟦КОЗЛОВОЙ ИРИНЫ ПАВЛОВНЫ|PER⟧")
E(C, "surname_only",
  "Клиент ⟦Тимофеев|PER⟧ снова пропустил платёж, передайте дело в отдел взыскания.")

# ------------------------------------------------------------ BIRTH_DATE
C = "BIRTH_DATE"
E(C, "bare_ddmmyyyy", "⟦15.03.1990|BD⟧")
E(C, "labeled_ddmmyyyy", "Дата рождения: ⟦07.11.1985|BD⟧")
E(C, "format_mmddyyyy", "Дата рождения: ⟦12.31.1978|BD⟧")
E(C, "format_mmddyyyy_sentence",
  "Клиентка родилась ⟦04.15.1988|BD⟧ — так дата записана в американской анкете.")
E(C, "format_yyyyddmm", "Дата рождения: ⟦1991.23.06|BD⟧")
E(C, "format_iso_json",
  'Запись из CRM: {"client_id": ⟪58213⟫, "birth_date": "⟦1987-02-14|BD⟧"}')
E(C, "format_ddmmyy_slash", "д.р. ⟦21/08/93|BD⟧")
E(C, "text_date", "Клиент родился ⟦15 марта 1990|BD⟧ года.")
E(C, "text_date_words",
  "Дата рождения прописью: ⟦пятнадцатое марта тысяча девятьсот девяностого|BD⟧ года.")
E(C, "year_gr", "Заёмщик, ⟦1975|BD⟧ г.р., просит отсрочку по платежу.")
E(C, "upper_text_date", "ДАТА РОЖДЕНИЯ: ⟦5 ИЮНЯ 1982|BD⟧ Г.")
E(C, "text_date_with_place", "Родилась ⟦2 января 2001|BD⟧ г. в ⟦Казани|BP⟧.")
E(C, "llm_prompt",
  "Посчитай, сколько полных лет клиенту на сегодня, если дата рождения ⟦29.02.1996|BD⟧.")
E(C, "single_digit_day_month", "Дата рожд.: ⟦1.9.1994|BD⟧")
E(C, "year_only_context",
  "Клиент родился в ⟦1964|BD⟧ году, поэтому пенсионная карта ему уже положена.")
E(C, "lower_text_words",
  "дата рождения — ⟦девятое мая одна тысяча девятьсот восемьдесят пятого|BD⟧ года")
E(C, "gr_no_space", "⟦Петров А. С.|PER⟧, ⟦1990|BD⟧г.р.")
E(C, "abbr_label_dr",
  "Клиентка ⟦Орлова Е. В.|PER⟧, д/р ⟦30.12.1968|BD⟧, просит сменить тариф.")

# ----------------------------------------------------------- BIRTH_PLACE
C = "BIRTH_PLACE"
E(C, "bare", "⟦Нижний Новгород|BP⟧")
E(C, "labeled_city", "Место рождения: г. ⟦Тула|BP⟧")
E(C, "village_region", "Место рождения: с. ⟦Покровское|BP⟧ ⟦Орловской|BP⟧ обл.")
E(C, "sentence_prepositional",
  "Клиент родился в ⟦Екатеринбурге|BP⟧, а паспорт получал уже в другом городе.")
E(C, "urozhenka_genitive", "Заявительница — уроженка ⟦Ташкента|BP⟧.")
E(C, "upper", "МЕСТО РОЖДЕНИЯ: ГОР. ⟦САНКТ-ПЕТЕРБУРГ|BP⟧")
E(C, "historical_name", "Место рождения: гор. ⟦Ленинград|BP⟧")
E(C, "rodom_iz",
  "Родом из ⟦Иркутска|BP⟧, клиент давно живёт за границей и просит дистанционное обслуживание.")
E(C, "country_and_city", "Место рождения: ⟦Республика Казахстан|BP⟧, г. ⟦Караганда|BP⟧")
E(C, "lower_settlement", "место рождения: пос. ⟦шушенское|BP⟧, ⟦красноярский|BP⟧ край")
E(C, "llm_prompt",
  "Проверь, совпадает ли место рождения ⟦Воронеж|BP⟧ в анкете с тем, что указано в паспорте.")
E(C, "city_country", "Место рождения: ⟦Минск|BP⟧, ⟦Беларусь|BP⟧")
E(C, "mixed_case", "мЕсТо РоЖдЕнИя: ⟦ВлАдИвОсТоК|BP⟧")

# -------------------------------------------------------------- PASSPORT
C = "PASSPORT"
E(C, "bare_4_6", "⟦4509 123456|PASS⟧")
E(C, "bare_2_2_6", "⟦45 09 381726|PASS⟧")
E(C, "bare_no_space", "⟦4613558210|PASS⟧")
E(C, "separator_words", "паспорт серия ⟦4509|PASS⟧ номер ⟦123456|PASS⟧")
E(C, "separator_colon_numsign", "Паспорт: серия: ⟦45 09|PASS⟧, №⟦274613|PASS⟧")
E(C, "upper_separator_words", "ПАСПОРТ СЕРИЯ ⟦4613|PASS⟧ НОМЕР ⟦558210|PASS⟧")
E(C, "labeled_series_number", "Серия и номер паспорта: ⟦4617 902114|PASS⟧")
E(C, "numsign_between", "Паспорт ⟦46 17|PASS⟧ № ⟦902114|PASS⟧")
E(C, "dash", "Паспорт: ⟦6004-381726|PASS⟧")
E(C, "llm_prompt",
  "Составь заявление на перевыпуск карты. Паспорт клиента: ⟦5211 473829|PASS⟧.")
E(C, "abbr_ser_numsign", "сер. ⟦4510|PASS⟧ № ⟦339201|PASS⟧")
E(C, "reversed_order", "номер ⟦339201|PASS⟧, серия ⟦45 10|PASS⟧")
E(C, "slash_separator", "Серия/номер: ⟦4012|PASS⟧/⟦667788|PASS⟧")
E(C, "digits_spaced", "паспорт ⟦4 5 0 9 1 2 3 4 5 6|PASS⟧")
E(C, "genitive_series",
  "Предъявлен паспорт серии ⟦3908|PASS⟧ № ⟦114455|PASS⟧, данные сверены.")
E(C, "lower_sentence",
  "клиент продиктовал паспорт ⟦7719 004512|PASS⟧ и попросил не звонить ему на работу")
E(C, "mixed_case_labels", "ПаСпОрТ: СеРиЯ ⟦6315|PASS⟧ нОмЕр ⟦708219|PASS⟧")

# ----------------------------------------------------------- CITIZENSHIP
C = "CITIZENSHIP"
E(C, "bare", "⟦Республика Беларусь|CIT⟧")
E(C, "labeled_abbr", "Гражданство: ⟦РФ|CIT⟧")
E(C, "grazhdanin_genitive", "Заявитель является гражданином ⟦Российской Федерации|CIT⟧.")
E(C, "labeled_full", "Гражданство: ⟦Республика Узбекистан|CIT⟧")
E(C, "grazhdanka_genitive", "Клиентка — гражданка ⟦Таджикистана|CIT⟧, работает по патенту.")
E(C, "upper", "ГРАЖДАНСТВО: ⟦РОССИЯ|CIT⟧")
E(C, "dual", "У клиента двойное гражданство: ⟦РФ|CIT⟧ и ⟦Израиль|CIT⟧.")
E(C, "adjective", "Гражданство — ⟦российское|CIT⟧.")
E(C, "latin_code", "Nationality: ⟦RUS|CIT⟧")
E(C, "llm_prompt",
  "Уточни, нужен ли нотариальный перевод документов, если клиент — гражданин ⟦Армении|CIT⟧.")
E(C, "lower_adjective", "гражданство: ⟦белорусское|CIT⟧")
E(C, "country_of_citizenship", "Страна гражданства: ⟦Кыргызстан|CIT⟧")
E(C, "mixed_case", "грАжДаНсТвО: ⟦кАзАхСтАн|CIT⟧")

# ---------------------------------------------------- PASSPORT_AUTHORITY
C = "PASSPORT_AUTHORITY"
E(C, "bare", "⟦ГУ МВД России по г. Москве|AUTH⟧")
E(C, "labeled_ufms",
  "Кем выдан: ⟦Отделом УФМС России по Московской обл. в Одинцовском р-не|AUTH⟧")
E(C, "with_date", "Паспорт выдан ⟦ОВД района Хамовники г. Москвы|AUTH⟧ ⟦12.05.2005|PDATE⟧.")
E(C, "upper",
  "КЕМ ВЫДАН: ⟦ОТДЕЛОМ ВНУТРЕННИХ ДЕЛ ЛЕНИНСКОГО РАЙОНА Г. ЕКАТЕРИНБУРГА|AUTH⟧")
E(C, "tp_ufms",
  "Паспорт выдан ⟦ТП УФМС России по Санкт-Петербургу и Ленинградской обл. в Приморском р-не|AUTH⟧.")
E(C, "lower", "кем выдан — ⟦гу мвд россии по краснодарскому краю|AUTH⟧")
E(C, "labeled_mvd_republic", "Орган, выдавший документ: ⟦МВД по Республике Татарстан|AUTH⟧")
E(C, "umvd_oblast", "Выдан ⟦УМВД России по Тульской области|AUTH⟧")
E(C, "llm_prompt",
  "Перенеси в анкету: паспорт выдан ⟦Отделением УФМС России по Новосибирской области в Центральном районе г. Новосибирска|AUTH⟧.")
E(C, "abbr_oufms", "Кем выдан: ⟦ОУФМС России по Ростовской обл. в г. Шахты|AUTH⟧")
E(C, "mezhrayon", "выдан: ⟦Межрайонным отделом УФМС России по Самарской области|AUTH⟧")
E(C, "with_dept_code",
  "Кем выдан: ⟦ГУ МВД России по Нижегородской обл.|AUTH⟧, код подразделения ⟦520-003|DEPT⟧")
E(C, "mixed_case", "Кем выдан: ⟦оВд КиРоВсКоГо РаЙоНа г. КаЗаНи|AUTH⟧")

# ------------------------------------------------------- DEPARTMENT_CODE
C = "DEPARTMENT_CODE"
E(C, "bare_dash", "⟦770-001|DEPT⟧")
E(C, "bare_no_dash", "⟦770001|DEPT⟧")
E(C, "labeled", "Код подразделения: ⟦500-112|DEPT⟧")
E(C, "abbr_kp", "к/п ⟦772-045|DEPT⟧")
E(C, "space_sep", "код подразделения ⟦230 007|DEPT⟧")
E(C, "upper", "КОД ПОДРАЗДЕЛЕНИЯ: ⟦660-004|DEPT⟧")
E(C, "abbr_kod_podr", "Код подр.: ⟦162-011|DEPT⟧")
E(C, "en_dash_llm",
  "Проверь, верно ли указан код подразделения ⟦540–005|DEPT⟧ в заявке на кредит.")
E(C, "in_parentheses",
  "Паспорт выдан ⟦ГУ МВД России по г. Санкт-Петербургу и Ленинградской области|AUTH⟧ (код ⟦780-022|DEPT⟧).")
E(C, "spaced_dash", "код подразделения: ⟦610 - 033|DEPT⟧")
E(C, "numsign", "Код подразделения №⟦502-043|DEPT⟧")
E(C, "abbr_k_p_dots", "к. п. ⟦910-002|DEPT⟧")
E(C, "mixed_case_label", "КоД пОдРаЗдЕлЕнИя ⟦150-001|DEPT⟧")

# --------------------------------------------------------- PASSPORT_DATE
C = "PASSPORT_DATE"
E(C, "bare", "⟦12.05.2015|PDATE⟧")
E(C, "labeled", "Дата выдачи: ⟦21.10.2019|PDATE⟧")
E(C, "text_date", "Паспорт выдан ⟦3 апреля 2012|PDATE⟧ г.")
E(C, "iso", "Дата выдачи паспорта: ⟦2016-08-30|PDATE⟧")
E(C, "format_mmddyyyy", "Дата выдачи: ⟦08.30.2016|PDATE⟧")
E(C, "format_yyyyddmm", "дата выдачи ⟦2018.15.03|PDATE⟧")
E(C, "format_ddmmyy_slash", "Паспорт выдан ⟦14/07/11|PDATE⟧")
E(C, "upper_text", "ДАТА ВЫДАЧИ: ⟦1 ДЕКАБРЯ 2020|PDATE⟧ Г.")
E(C, "text_words", "Дата выдачи: ⟦двадцатое мая две тысячи восемнадцатого|PDATE⟧ года")
E(C, "llm_prompt",
  "Паспорт клиента выдан ⟦17.09.2006|PDATE⟧. Проверь, не пора ли его заменить, и напиши клиенту.")
E(C, "kogda_vydan", "Когда выдан: ⟦05.02.2010|PDATE⟧")
E(C, "with_series", "паспорт ⟦4514 220981|PASS⟧ выдан ⟦06.06.2021|PDATE⟧")
E(C, "text_date_lower_genitive", "выдан ⟦девятого октября 2014|PDATE⟧ года")

# -------------------------------------------------------- DRIVER_LICENSE
C = "DRIVER_LICENSE"
E(C, "bare_2_2_6", "⟦77 01 482915|DL⟧")
E(C, "bare_4_6", "⟦7701 482915|DL⟧")
E(C, "old_cyrillic_letters", "ВУ ⟦77 АВ 123456|DL⟧")
E(C, "separator_words", "Водительское удостоверение серия ⟦99 16|DL⟧ номер ⟦482915|DL⟧")
E(C, "labeled_abbr", "Вод. удостоверение: ⟦5028 771204|DL⟧")
E(C, "upper_letters", "ВОДИТЕЛЬСКОЕ УДОСТОВЕРЕНИЕ ⟦78 ТК 004512|DL⟧")
E(C, "colloquial", "Скинул фото прав, номер ⟦9921 334455|DL⟧, проверьте, пожалуйста.")
E(C, "abbr_vu_numsign", "В/у №⟦16 30 559912|DL⟧")
E(C, "llm_prompt",
  "Проверь по базе ГИБДД, действительно ли водительское удостоверение ⟦9931 204816|DL⟧, и подготовь ответ для страховой.")
E(C, "english_label", "Driver license: ⟦5012 445566|DL⟧")
E(C, "lower_no_space", "ву: ⟦77ав123456|DL⟧")
E(C, "letters_numsign", "ВУ серия ⟦23 ХА|DL⟧ № ⟦776812|DL⟧")
E(C, "mixed_case", "вОдИтЕлЬсКоЕ уДоСтОвЕрЕнИе: ⟦6618 093274|DL⟧")

# --------------------------------------------------------------- ADDRESS
C = "ADDRESS"
E(C, "bare_full_with_service_words", "г. ⟦Москва|ADDR⟧, ул. ⟦Лесная|ADDR⟧, д. ⟦4|ADDR⟧, кв. ⟦2|ADDR⟧")
E(C, "labeled_full_index_country",
  "Адрес регистрации: ⟦125009|ADDR⟧, ⟦Россия|ADDR⟧, г. ⟦Москва|ADDR⟧, ул. ⟦Тверская|ADDR⟧, д. ⟦18|ADDR⟧, корп. ⟦2|ADDR⟧, кв. ⟦44|ADDR⟧")
E(C, "region_district_settlement",
  "Проживает по адресу: ⟦Московская|ADDR⟧ обл., ⟦Одинцовский|ADDR⟧ р-н, пос. ⟦Внуково|ADDR⟧, ул. ⟦Садовая|ADDR⟧, д. ⟦7|ADDR⟧")
E(C, "no_service_words", "Адрес: ⟦Казань|ADDR⟧, ⟦Баумана|ADDR⟧ ⟦15|ADDR⟧, кв ⟦8|ADDR⟧")
E(C, "index_only_labeled", "Почтовый индекс клиента: ⟦630099|ADDR⟧")
E(C, "prospekt_no_label",
  "⟦344002|ADDR⟧, г. ⟦Ростов-на-Дону|ADDR⟧, пр-кт ⟦Будённовский|ADDR⟧, д. ⟦12|ADDR⟧, кв. ⟦5|ADDR⟧")
E(C, "upper",
  "АДРЕС: Г. ⟦НОВОСИБИРСК|ADDR⟧, ⟦КРАСНЫЙ ПРОСПЕКТ|ADDR⟧, Д. ⟦25|ADDR⟧, КВ. ⟦101|ADDR⟧")
E(C, "lower",
  "адрес: г. ⟦самара|ADDR⟧, ул. ⟦ново-садовая|ADDR⟧, д. ⟦106|ADDR⟧, кв. ⟦17|ADDR⟧")
E(C, "pushkin_street_client",
  "Клиент живёт на улице ⟦Пушкина|ADDR⟧, дом ⟦10|ADDR⟧, квартира ⟦3|ADDR⟧, в ⟦Твери|ADDR⟧.")
E(C, "llm_prompt_republic",
  "Составь уведомление о смене тарифа и отправь по адресу клиента: ⟦420111|ADDR⟧, Республика ⟦Татарстан|ADDR⟧, г. ⟦Казань|ADDR⟧, ул. ⟦Кремлёвская|ADDR⟧, д. ⟦9|ADDR⟧, кв. ⟦31|ADDR⟧.")
E(C, "house_letter", "Адрес: г. ⟦Пермь|ADDR⟧, ул. ⟦Ленина|ADDR⟧, д. ⟦5А|ADDR⟧, кв. ⟦12|ADDR⟧")
E(C, "comma_house_no_d", "⟦Санкт-Петербург|ADDR⟧, ⟦Невский|ADDR⟧ пр., ⟦147|ADDR⟧, кв. ⟦6|ADDR⟧")
E(C, "stanitsa_kray",
  "Адрес доставки карты: ⟦Краснодарский|ADDR⟧ край, ст-ца ⟦Динская|ADDR⟧, ул. ⟦Красная|ADDR⟧, ⟦48|ADDR⟧")
E(C, "mkr_stroenie",
  "Адрес: мкр. ⟦Солнечный|ADDR⟧, д. ⟦3|ADDR⟧, стр. ⟦1|ADDR⟧, кв. ⟦77|ADDR⟧, г. ⟦Сургут|ADDR⟧")
E(C, "derevnya_d_ambiguity",
  "Прописан: д. ⟦Малые Вязёмы|ADDR⟧, ⟦Одинцовский|ADDR⟧ г.о., ул. ⟦Школьная|ADDR⟧, д. ⟦14|ADDR⟧")
E(C, "house_apt_dash",
  "Живу в ⟦Москве|ADDR⟧, ⟦Ленинский|ADDR⟧ проспект ⟦52-117|ADDR⟧, домофон не работает.")
E(C, "english", "Address: ⟦Moscow|ADDR⟧, ⟦Tverskaya|ADDR⟧ str. ⟦7|ADDR⟧, apt. ⟦15|ADDR⟧")
E(C, "street_house_sentence",
  "Курьер привезёт карту на ⟦Профсоюзную|ADDR⟧, ⟦84|ADDR⟧ завтра ⟪с 10 до 14⟫.")
E(C, "mixed_case", "г. ⟦ЕкАтЕрИнБуРг|ADDR⟧, уЛ. ⟦МаЛыШеВа|ADDR⟧, Д. ⟦51|ADDR⟧, кВ. ⟦9|ADDR⟧")
E(C, "district_city_sentence",
  "Клиентка проживает в ⟦Центральном|ADDR⟧ районе г. ⟦Сочи|ADDR⟧, на ⟦Курортном|ADDR⟧ проспекте, д. ⟦75|ADDR⟧.")
E(C, "country_city_residence", "Страна проживания: ⟦Германия|ADDR⟧, город: ⟦Мюнхен|ADDR⟧")
E(C, "zelenograd_korpus", "⟦Зеленоград|ADDR⟧, корп. ⟦1824|ADDR⟧, кв. ⟦310|ADDR⟧")
E(C, "region_only_labeled", "Регион проживания: ⟦Свердловская|ADDR⟧ область")

# ----------------------------------------------------------------- EMAIL
C = "EMAIL"
E(C, "bare", "⟦ivan.petrov@mail.ru|EMAIL⟧")
E(C, "plus_tag", "E-mail: ⟦a.smirnova+bank@gmail.com|EMAIL⟧")
E(C, "subdomain", "Почта для уведомлений: ⟦olga_k@hr.mail.romashka-group.ru|EMAIL⟧")
E(C, "cyrillic_domain_bare", "⟦почта@пример.рф|EMAIL⟧")
E(C, "cyrillic_full", "Мой адрес: ⟦иван.петров@почта.рф|EMAIL⟧")
E(C, "upper", "EMAIL: ⟦IVAN.PETROV@YANDEX.RU|EMAIL⟧")
E(C, "llm_prompt", "Отправь выписку за август клиенту на ⟦m.volkova1984@list.ru|EMAIL⟧ до конца дня.")
E(C, "trailing_period", "Если будут вопросы, пишите мне на ⟦sergey-orlov@bk.ru|EMAIL⟧.")
E(C, "angle_brackets_with_name", "От: ⟦Анна Белова|PER⟧ <⟦anna.belova@inbox.ru|EMAIL⟧>")
E(C, "obfuscated_at_dot", "Мой адрес: ⟦petrov.a [at] mail [dot] ru|EMAIL⟧, пишите туда.")
E(C, "mixed_case", "Контакт: ⟦Kirill.Sokolov@Gmail.Com|EMAIL⟧")
E(C, "digits_underscore", "Логин в личном кабинете: ⟦user_1987_ok@rambler.ru|EMAIL⟧")
E(C, "long_tld_hyphen",
  "Рабочая почта клиента ⟦t.nikolaev@my-company.online|EMAIL⟧ больше не активна.")
E(C, "parentheses", "Клиентка (⟦k.popova@mail.ru|EMAIL⟧) просит продублировать договор.")

# ----------------------------------------------------------------- PHONE
C = "PHONE"
E(C, "bare_plus7_parens", "⟦+7 (916) 482-15-37|PHONE⟧")
E(C, "bare_8_no_sep", "⟦89031234567|PHONE⟧")
E(C, "eight_parens_spaces", "тел.: ⟦8 (916) 123 45 67|PHONE⟧")
E(C, "plus7_no_sep", "Телефон: ⟦+79261234567|PHONE⟧")
E(C, "seven_no_plus", "Номер для связи: ⟦7 925 555 12 34|PHONE⟧")
E(C, "dots", "тел. ⟦8.916.123.45.67|PHONE⟧")
E(C, "dashes", "Моб.: ⟦8-903-765-43-21|PHONE⟧")
E(C, "plus7_space_7digits", "⟦+7 916 1234567|PHONE⟧")
E(C, "sentence", "Перезвоните мне на ⟦8 999 004 11 22|PHONE⟧ после шести вечера.")
E(C, "landline_city_code", "Домашний: ⟦+7 (495) 318-27-64|PHONE⟧")
E(C, "no_spaces_parens", "моб. ⟦+7(912)3456789|PHONE⟧")
E(C, "upper_label", "ТЕЛЕФОН КЛИЕНТА: ⟦+7 (905) 111-22-33|PHONE⟧")
E(C, "llm_prompt",
  "Отправь SMS клиенту на номер ⟦+7 964 250 18 73|PHONE⟧ с напоминанием о платеже.")
E(C, "two_phones",
  "Основной номер ⟦+7 916 300-40-50|PHONE⟧, резервный ⟦8 (926) 700-80-90|PHONE⟧.")
E(C, "local_7digits", "Домашний телефон: ⟦234-56-78|PHONE⟧, звонить только вечером.")
E(C, "foreign_by",
  "Клиент сейчас за границей, связь только по номеру ⟦+375 29 123-45-67|PHONE⟧.")
E(C, "foreign_uz_whatsapp", "WhatsApp: ⟦+998 90 123 45 67|PHONE⟧")
E(C, "mixed_spaces_dashes", "Телефон: ⟦8 916 123-45-67|PHONE⟧")
E(C, "eight_parens_no_space",
  "⟦8(985)7776655|PHONE⟧ — это мой новый номер, старый больше не обслуживается.")

# ------------------------------------------------------------------- INN
C = "INN"
E(C, "bare_12", f"⟦{I12[0]}|INN⟧")
E(C, "bare_10", f"⟦{I10[0]}|INN⟧")
E(C, "labeled_12", f"ИНН: ⟦{I12[1]}|INN⟧")
E(C, "labeled_client", f"ИНН клиента — ⟦{I12[2]}|INN⟧, других данных нет.")
E(C, "lower_label", f"инн физлица: ⟦{I12[3]}|INN⟧")
E(C, "llm_prompt",
  f"Проверь по базе ФНС, нет ли задолженности у налогоплательщика с ИНН ⟦{I12[4]}|INN⟧.")
E(C, "individual_entrepreneur",
  f"ИП ⟦Сергеев Андрей Викторович|PER⟧, ИНН ⟦{I12[5]}|INN⟧, просит открыть расчётный счёт.")
E(C, "invalid_checksum_labeled", f"ИНН: ⟦{I12_BAD[0]}|INN⟧")
E(C, "grouped_4_4_4",
  f"ИНН ⟦{I12[6][:4]} {I12[6][4:8]} {I12[6][8:]}|INN⟧")
E(C, "full_label", f"Идентификационный номер налогоплательщика: ⟦{I12[7]}|INN⟧")
E(C, "json", f'{{"client": "⟦Лебедева О. И.|PER⟧", "inn": "⟦{I12[8]}|INN⟧"}}')
E(C, "ten_digits_client_context",
  f"Клиент указал ИНН ⟦{I10[1]}|INN⟧ — проверь, не ошибся ли он в количестве цифр.")
E(C, "upper_label", f"ИНН НАЛОГОПЛАТЕЛЬЩИКА: ⟦{I12[9]}|INN⟧")
E(C, "mixed_case_label", f"иНн: ⟦{I12[10]}|INN⟧")
E(C, "grouped_2_2_6_2",
  f"ИНН ⟦{I12[11][:2]} {I12[11][2:4]} {I12[11][4:10]} {I12[11][10:]}|INN⟧")

# ------------------------------------------------------------- BANK_CARD
C = "BANK_CARD"
E(C, "bare_visa_spaces", f"⟦{sp(VISA[0])}|CARD⟧")
E(C, "bare_mc_no_sep", f"⟦{MC[0]}|CARD⟧")
E(C, "bare_dashes", f"⟦{dash(VISA[1])}|CARD⟧")
E(C, "mir16_labeled", f"Номер карты: ⟦{sp(MIR16[0])}|CARD⟧")
E(C, "mir19_spaces", f"Карта «Мир»: ⟦{sp(MIR19[0])}|CARD⟧")
E(C, "amex15", f"Amex ⟦{amex(AMEX[0])}|CARD⟧")
E(C, "numsign", f"карта № ⟦{sp(MC[1])}|CARD⟧")
E(C, "llm_prompt",
  f"Клиент пишет, что с карты ⟦{sp(MIR16[1])}|CARD⟧ дважды списали оплату за такси. Составь ему ответ.")
E(C, "luhn_invalid_labeled", f"Номер карты: ⟦{sp(BAD_CARD[0])}|CARD⟧")
E(C, "unionpay", f"Карта UnionPay ⟦{sp(UP[0])}|CARD⟧ не проходит в терминале.")
E(C, "line_break_inside",
  f"Номер карты: ⟦{VISA[2][:4]} {VISA[2][4:8]}\n{VISA[2][8:12]} {VISA[2][12:]}|CARD⟧")
E(C, "pan_label", f"PAN: ⟦{MIR16[2]}|CARD⟧")
E(C, "with_amount", f"Переведите ⟪5 000⟫ руб. на карту ⟦{sp(MIR16[3])}|CARD⟧ до пятницы.")
E(C, "mir19_no_sep", f"⟦{MIR19[1]}|CARD⟧")
E(C, "upper_label", f"НОМЕР КАРТЫ: ⟦{sp(VISA[3])}|CARD⟧")
E(C, "dashes_sentence", f"Сохраните карту ⟦{dash(MIR16[4])}|CARD⟧ в приложении для оплаты.")

# ------------------------------------------------------------------- CVV
C = "CVV"
E(C, "bare", "⟦847|CVV⟧")
E(C, "labeled_cvv", "CVV: ⟦512|CVV⟧")
E(C, "labeled_cvc2", "CVC2 ⟦904|CVV⟧")
E(C, "lower", "cvv2 — ⟦377|CVV⟧")
E(C, "russian_label", "Код безопасности: ⟦618|CVV⟧")
E(C, "descriptive", "Три цифры на обороте карты: ⟦245|CVV⟧")
E(C, "leading_zero", "CVV/CVC: ⟦031|CVV⟧")
E(C, "amex_cid_4_digits", "Amex CID: ⟦4821|CVV⟧")
E(C, "llm_prompt",
  "Клиент по ошибке прислал в чат свой CVV ⟦406|CVV⟧. Напиши ему, почему так делать нельзя и что теперь сделать с картой.")
E(C, "upper", "КОД CVV2: ⟦993|CVV⟧")
E(C, "mixed_case", "CvC ⟦280|CVV⟧")
E(C, "colloquial", "секретный код с обратной стороны карты — ⟦555|CVV⟧")
E(C, "value_first", "⟦719|CVV⟧ — это CVV, остальное пришлю позже")

# ------------------------------------------------------------------- PIN
C = "PIN"
E(C, "bare", "⟦4821|PIN⟧")
E(C, "labeled", "PIN: ⟦7305|PIN⟧")
E(C, "pin_kod_ru", "пин-код ⟦0852|PIN⟧")
E(C, "upper_ru", "ПИН ⟦6619|PIN⟧")
E(C, "english_lower", "pin code: ⟦2580|PIN⟧")
E(C, "pin_ot_karty", "ПИН-код от карты: ⟦9043|PIN⟧")
E(C, "six_digits", "Мой пин ⟦482913|PIN⟧, но банкомат его не принимает.")
E(C, "llm_prompt_two_values",
  "Клиент не помнит, какой PIN установил: то ли ⟦1357|PIN⟧, то ли ⟦7531|PIN⟧. Подскажи, как ему сбросить код.")
E(C, "pinkod_joined", "Пинкод ⟦3141|PIN⟧")
E(C, "new_old", "Новый ПИН — ⟦2468|PIN⟧, старый — ⟦8642|PIN⟧.")
E(C, "colloquial_parol", "пароль от карты ⟦5812|PIN⟧, только никому не говори")
E(C, "mixed_case", "PiN-КоД: ⟦1111|PIN⟧")
E(C, "value_first", "⟦0413|PIN⟧ — пин от зарплатной карты")

# ------------------------------------------------------------ CARDHOLDER
C = "CARDHOLDER"
E(C, "bare_upper_latin", "⟦ALEXEY SMIRNOV|HOLDER⟧")
E(C, "labeled_ru", "Держатель карты: ⟦MARIA PETROVA|HOLDER⟧")
E(C, "labeled_en_titlecase", "Cardholder: ⟦Dmitry Kozlov|HOLDER⟧")
E(C, "middle_initial", "Имя на карте: ⟦OLGA S. VOLKOVA|HOLDER⟧")
E(C, "with_card", f"Карта ⟦{sp(VISA[4])}|CARD⟧, ⟦SERGEY MOROZOV|HOLDER⟧")
E(C, "labeled:name_on_card_en", "Name on card: ⟦ANNA KUZNETSOVA|HOLDER⟧")
E(C, "lower", "держатель: ⟦elena orlova|HOLDER⟧")
E(C, "cyrillic_holder",
  "Владелец карты — ⟦Никитин Павел Олегович|HOLDER⟧, карта оформлена в ⟪2021 году⟫.")
E(C, "upper_label", "ИМЯ ДЕРЖАТЕЛЯ: ⟦TIMUR AKHMEDOV|HOLDER⟧")
E(C, "llm_prompt_compare",
  "Проверь, совпадает ли имя на карте ⟦KSENIA BELOVA|HOLDER⟧ с ФИО в анкете: ⟦Белова Ксения Андреевна|PER⟧.")
E(C, "format_variation:card_then_holder_newline", f"⟦{sp(MC[3])}|CARD⟧\n⟦YULIYA ZAYTSEVA|HOLDER⟧")
E(C, "hyphenated", "Держатель: ⟦ANNA-MARIA RIMSKAYA-KORSAKOVA|HOLDER⟧")
E(C, "sentence_payment",
  f"Оплата картой ⟦{sp(MIR16[5])}|CARD⟧ на имя ⟦IGOR VASILEV|HOLDER⟧ не прошла.")

# ----------------------------------------------------------------- SNILS
C = "SNILS"
E(C, "bare_std", f"⟦{snf(SN[0])}|SNILS⟧")
E(C, "bare_raw", f"⟦{SN[1]}|SNILS⟧")
E(C, "labeled", f"СНИЛС: ⟦{snf(SN[2])}|SNILS⟧")
E(C, "lower_spaces", f"снилс ⟦{sns(SN[3])}|SNILS⟧")
E(C, "all_dashes", f"СНИЛС ⟦{snd(SN[4])}|SNILS⟧")
E(C, "full_name_label",
  f"Страховой номер индивидуального лицевого счёта: ⟦{snf(SN[5])}|SNILS⟧")
E(C, "llm_prompt",
  f"Запроси в Социальном фонде сведения о стаже клиента по СНИЛС ⟦{snf(SN[6])}|SNILS⟧.")
E(C, "with_inn", f"СНИЛС клиента ⟦{snf(SN[7])}|SNILS⟧; ИНН ⟦{I12[12]}|INN⟧.")
E(C, "legacy_name", f"Страховое свидетельство № ⟦{snf(SN[8])}|SNILS⟧")
E(C, "english_label_raw", f"SNILS: ⟦{SN[9]}|SNILS⟧")
E(C, "upper_sentence", f"НОМЕР СНИЛС ⟦{snf(SN[10])}|SNILS⟧ УКАЗАН В ЗАЯВЛЕНИИ")
E(C, "invalid_checksum_labeled", f"СНИЛС: ⟦{snf(SN_BAD[0])}|SNILS⟧")
E(C, "parenthetical",
  f"Копия СНИЛС (⟦{snf(SN[11])}|SNILS⟧) приложена к заявлению на зарплатную карту.")

# ------------------------------------------------------ FOREIGN_DOCUMENT
C = "FOREIGN_DOCUMENT"
E(C, "zagran_bare", "⟦76 4518203|FDOC⟧")
E(C, "zagran_labeled", "Загранпаспорт: ⟦72 0419385|FDOC⟧")
E(C, "zagran_separator_words", "Заграничный паспорт серия ⟦75|FDOC⟧ № ⟦5566778|FDOC⟧")
E(C, "zagran_no_space", "Номер загранпаспорта ⟦770412958|FDOC⟧, фото страницы приложено.")
E(C, "zagran_lower", "загранпаспорт ⟦75 3344556|FDOC⟧")
E(C, "zagran_colloquial_numsign", "загран ⟦75|FDOC⟧ №⟦6612045|FDOC⟧")
E(C, "vnzh_labeled", "Вид на жительство: ⟦82 0123456|FDOC⟧")
E(C, "vnzh_separator_words", "ВНЖ серия ⟦83|FDOC⟧ № ⟦0045120|FDOC⟧")
E(C, "vnzh_upper", "ВИД НА ЖИТЕЛЬСТВО ⟦82|FDOC⟧ № ⟦1122334|FDOC⟧")
E(C, "vnzh_llm_prompt",
  "Клиент — иностранец, предъявил вид на жительство ⟦83 0098765|FDOC⟧. Какие ещё документы запросить для открытия счёта?")
E(C, "rvp_labeled", "Разрешение на временное проживание № ⟦045812|FDOC⟧")
E(C, "rvp_abbr", "РВП: ⟦2231/2025|FDOC⟧, миграционный учёт продлён.")
E(C, "birth_cert_bare", "⟦IV-МЮ 523641|FDOC⟧")
E(C, "birth_cert_separator_words", "Свидетельство о рождении серия ⟦II-АГ|FDOC⟧ № ⟦587412|FDOC⟧")
E(C, "birth_cert_child_sentence",
  "Для оформления детской карты приложено свидетельство о рождении ⟦III-ЛО|FDOC⟧ № ⟦721045|FDOC⟧.")
E(C, "military_id", "Военный билет ⟦АН 1234567|FDOC⟧")
E(C, "military_id_separator_words", "военный билет серия ⟦АК|FDOC⟧ № ⟦0458123|FDOC⟧")
E(C, "military_bare", "⟦АВ 7788990|FDOC⟧")
E(C, "foreign_passport_with_cit",
  "Паспорт иностранного гражданина: ⟦AC2045871|FDOC⟧, гражданство ⟦Узбекистан|CIT⟧")
E(C, "foreign_passport_latin_alnum", "Foreign passport No. ⟦C01X00T47|FDOC⟧")
E(C, "id_card_numeric", "Удостоверение личности (ID-карта) № ⟦045128934|FDOC⟧")
E(C, "id_card_prefixed", "ID-карта ⟦ID1234567|FDOC⟧ — основной документ клиента для идентификации.")
E(C, "foreign_passport_llm",
  "Проверь, подходит ли для открытия вклада национальный паспорт ⟦400123456|FDOC⟧ гражданина ⟦Таджикистана|CIT⟧.")
E(C, "mixed_case", "ЗаГрАнПаСпОрТ: ⟦71 2093847|FDOC⟧")
