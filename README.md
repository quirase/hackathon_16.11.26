# Наближена оцінка CEFR англійської транскрипції

Python-модуль для командного конвеєра: приймає текст і необов'язковий DataFrame
`word, time_code`, повертає словник із рівнем A1–C2, лексикою, граматикою,
фрагментами, таймкодами, невідомими словами та джерелами оцінок.

Потрібен **Python 3.10+**. Основний аналізатор не має зовнішніх залежностей,
не викликає LLM і працює без інтернету. Підготовлені словники вже включено.

```bash
# З кореня репозиторію, встановлення не потрібне:
python -m cefr_analyzer analyze --text "She turned it down. It must have been exciting."
python -m cefr_analyzer analyze --words examples/words.csv --json
python -m cefr_analyzer analyze --file calibration_data/V7bOxiNM3kc_C1.txt --output report.json
python -m unittest discover -s tests -v
```

Для встановлення пакета та команди `cefr`:

```bash
python -m pip install .
# Лише якщо команда використовує pandas:
python -m pip install ".[dataframe]"
cefr analyze --text "That's annoying. She is annoying me." --json
```

Інтеграція:

```python
from cefr_analyzer import Analyzer

analyzer = Analyzer()  # Створити один раз і повторно використовувати.
result = analyzer.analyze(
    text="She turned it down.",
    words=[
        {"word": "She", "time_code": 0.0},
        {"word": "turned", "time_code": 0.2},
        {"word": "it", "time_code": 0.5},
        {"word": "down.", "time_code": 0.7},
    ],  # Тут також може бути pandas.DataFrame з такими колонками.
    ignore_terms=["John", "New York"],
)
print(result["assessment"]["level"])
print(result["unknown_words"])
```

Можна передати тільки `text`, тільки `words`, або обидва. Коли надано обидва,
послідовності слів повинні збігатися після нормалізації; інакше буде `ValueError`.
Невідомі слова залишаються без CEFR. Автоматичні словникові оцінки позначено
і за замовчуванням виключено з підсумкової оцінки.

Підтримуються змінені й розділені фрази, відомі неправильні та регулярні форми,
розбір допоміжних ланцюжків і консервативне трактування неоднозначностей.
Це евристична оцінка складності **тексту**, а не вимірювання рівня мовця чи
складності аудіювання. Калібрування показує помітні похибки, особливо на B2–C1.

- [Документація: API, алгоритм, JSON і обмеження](docs/how-it-works.md)
- [Джерела, схеми даних та ліцензійні примітки](docs/sources.md)
- [Результати перевірки на 8 приблизно розмічених текстах](calibration_report.json)
- [Приклад інтеграції з таймкодами](examples/integration.py)

Оновлення та розділення словників:

```bash
python -m cefr_analyzer prepare-data --download
python -m cefr_analyzer export-dictionaries --output-dir exported_dictionaries
python -m cefr_analyzer calibrate --output calibration_report.json
```

Експорт створює окремі каталоги джерел і файли `A1.json` … `C2.json` у кожному.
Сирі завантаження зберігаються в `words_data/` та виключені з Git;
нормалізовані дані й SHA-256 джерел знаходяться в `cefr_analyzer/data/`.
