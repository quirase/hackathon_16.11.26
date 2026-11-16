# Джерела й підготовка словників

Аналіз використовує підготовлені локальні файли. Під час звичайного
виклику `analyze` жодні зовнішні сервіси не потрібні.

## Адаптери

| Джерело | Поля/особливості | Політика |
|---|---|---|
| [CEFR-J Vocabulary 1.5](https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/cefrj-vocabulary-profile-1.5.csv) | `headword,pos,CEFR`, альтернативи зі слешами | Словникові A1–B2, збереження POS |
| [Octanove C1/C2](https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/octanove-vocabulary-profile-c1c2-1.0.csv) | Та сама базова схема | Окреме джерело C1/C2 |
| [CEFR-J Grammar](https://raw.githubusercontent.com/openlanguageprofiles/olp-en-cefrj/master/cefrj-grammar-profile-20180315.csv) | Кілька колонок, підрівні, діапазони, порожні клітинки | Мінімум із рівневих колонок; точне посилання на рядок |
| [OpenJam words](https://raw.githubusercontent.com/amirj4m/openjam/main/data/json/words_en.json) | JSON-масив, `id,english,level,senses` | CEFR позначено як автоматичний |
| [OpenJam forms](https://raw.githubusercontent.com/amirj4m/openjam/main/data/json/word_forms.json) | `form,word_id,form_type` | З'єднання через ID; джерело форм, не нових рівнів |
| [Mega Dataset](https://raw.githubusercontent.com/kamronsaparbaev/cefr-dataset/main/cefr_mega_dataset.csv) | `Word,CEFR,Definition,Synonyms` | CEFR автоматичний; визначення/синоніми не імпортуються |
| [Pearson GSE API](https://www.english.com/gse/teacher-toolkit/user/api/v1/vocabulary/search?page=0&size=50000) | `count,data[]`, `expression,cefr,gse,grammaticalCategories,itemId` | Береться готове `cefr`; числова GSE не конвертується |
| [Kaikki/Wiktextract](https://kaikki.org/dictionary/rawdata.html) | Великий JSONL або JSONL.gz, багато мов, `forms[].tags` | Опційні англійські словоформи, **без CEFR** |

Повторне посилання `word_forms.json` зі вхідного переліку не призводить
до повторного імпорту. Словники залишаються окремими за полем `source`.
Повні завантажені CSV/JSON лишаються в `words_data/`, а в робочі артефакти
потрапляють терміни, частини мови, рівні, форми й метадані походження.

## Чому автоматичні оцінки відокремлені

У [генераторі OpenJam](https://github.com/amirj4m/openjam/blob/main/scripts/generate_seed.py)
функція `cefr_for_rank` призначає рівні за порогами частотного рангу.
Це не підтверджена експертна CEFR-розмітка кожного слова.
[README Mega Dataset](https://github.com/kamronsaparbaev/cefr-dataset)
описує `CEFR` як оцінку через `cefrpy`. Обидва адаптери встановлюють
`automatic=true`; морфологічні дані OpenJam використовуються незалежно
від того, чи включено його рівні в скоринг.

`--include-automatic` або `ScoringConfig(include_automatic=True)` явно
включає ці оцінки до підсумку. Це не призначає CEFR невідомим словам:
використовуються тільки вже наявні записи конкретних джерел.

## Конфлікти

Усі джерела запису зберігаються. Вибирається найнижчий CEFR серед усіх
джерел, значень і частин мови, включно з автоматичними. Якщо мінімум
підтримує хоча б одне неавтоматичне джерело, вибраний рівень має
`automatic=false`. Якщо мінімум є тільки автоматичним — `automatic=true`.
За замовчуванням такий збіг не бере участі у скорингу; вищий ручний
рівень замість нього не підставляється.

Приклад: Cambridge позначає `turn out` B2, а GSE має B1 і B1+ для різних
значень. Після згортання підрівнів вибирається B1, `level_conflict=true`.
Визначення значення за контекстом не використовується для підвищення рівня.
`B1+` згортaється до B1; `B2.1` — до B2; з діапазону береться мінімум.

## Перевірені додаткові вирази

У `data/phrase_seeds.json` є три невеликі правила без копіювання
словникових визначень та прикладів:

- [turn out — Cambridge Learner's Dictionary](https://dictionary.cambridge.org/dictionary/learner-english/turn-out), B2;
- [turn something/someone down — Cambridge](https://dictionary.cambridge.org/dictionary/english/turn-down?topic=refusing-and-rejecting), B2;
- [give up something — Cambridge Essential](https://dictionary.cambridge.org/dictionary/essential-british-english/give-up-something), B1.

Після об'єднання їхні рівні також підпорядковуються правилу мінімуму.
Посилання збережено в самих записах.

## Побудова й відтворюваність

```bash
# Явно завантажити перелічені джерела й побудувати локальні артефакти:
python -m cefr_analyzer prepare-data --download

# Побудувати тільки з раніше завантажених файлів:
python -m cefr_analyzer prepare-data --raw-dir words_data

# Опційно додати локальний Kaikki-дамп:
python -m cefr_analyzer prepare-data --kaikki /path/to/english.jsonl.gz

# Подивитися словники окремо за джерелами й рівнями:
python -m cefr_analyzer export-dictionaries --output-dir exported_dictionaries
```

Базові CSV і OpenJam потрібні для побудови. GSE імпортується за наявності
його JSON. У відповіді GSE перевіряється, що завантажено `count` записів;
неповна сторінка викликає помилку. Поточний знімок містить усі 41 402 записи.
Якщо майбутня відповідь перевищить запитуваний розмір сторінки, її потрібно
зібрати з усіх сторінок перед побудовою: адаптер не прийме частковий файл.

Kaikki не завантажується автоматично: повний багатомовний дамп дуже великий
і не має CEFR. Його опційний адаптер читає файл потоково, вибирає тільки
`lang_code=en`, зберігає форми й не додає слова до рівневого словника.
Невідома у CEFR-словниках лема після такого імпорту лишається невідомою.
Без додаткового дампа неправильні форми вже доступні через OpenJam.

Артефакти:

- `lexicon.json.gz` — записи термінів із джерелами та прапорцями;
- `forms.json.gz` — відповідності словоформ до лем;
- `phrases.json` — правила розривів і шаблони GSE;
- `grammar.json` — рівні підтримуваних граматичних правил і точні джерела;
- `manifest.json` — URL і SHA-256 сирих файлів, кількості та розподіли.

Gzip генерується з фіксованим `mtime=0`, JSON має стабільне сортування.
Однакові вхідні файли дають однакові робочі артефакти. Нове завантаження
за URL може змінити дані; маніфест дозволяє виявити це.
У цьому знімку 159 015 нормалізованих термінів і 16 723 ключі словоформ.
Кількості за джерелом і рівнем у маніфесті — кількості окремих записів,
які можуть відрізнятися від кількості унікальних термінів.

## Атрибуція

[Умови Open Language Profiles](https://github.com/openlanguageprofiles/olp-en-cefrj)
дозволяють дослідницьке й комерційне використання CEFR-J з належним цитуванням.
CEFR-J Wordlist Version 1.5 і Grammar Profile Version 20180315 уклав
Yukio Tono, Tokyo University of Foreign Studies; copyright Tono Laboratory.
Octanove Vocabulary Profile C1/C2 Version 1.0 створено Octanove Labs,
ліцензія [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
Нормалізовані дані Octanove зберігають атрибуцію та ту саму ліцензію.

[OpenJam](https://github.com/amirj4m/openjam) декларує MIT;
його [ATTRIBUTION.md](https://github.com/amirj4m/openjam/blob/main/ATTRIBUTION.md)
містить відомості про WordNet та інші складові.
Pearson GSE, Cambridge, Mega Dataset та опційні Kaikki/Wiktionary
мають власні умови джерел; ця реалізація не надає нових прав на їхні дані.
Ліцензії окремих наборів не замінюються ліцензією програмного коду.
