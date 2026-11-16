# Результати після виправлення заниження

Пороги скориговано на цій малій добірці. Результати не є незалежною перевіркою точності.

| Файл | Мітка | Було | Стало |
|---|---|---|---|
| A1_daily_life.txt | A1 | A1 | A1 |
| A2_countryside.txt | A2 | A2 | A2 |
| A2_memorable_journey.txt | A2 | A2 | A2 |
| B1_cooking.txt | B1 | A2 | A2 |
| B1_learning_guitar.txt | B1 | B1 | B1 |
| B2_remote_work.txt | B2 | B1 | B1 |
| B2_technology_balance.txt | B2 | B1 | B2 |
| C1_changing_your_mind.txt | C1 | B1 | B2 |
| C1_productivity.txt | C1 | B1 | B2 |
| C2_community_decisions.txt | C2 | B1 | B2 |
| C2_technology.txt | C2 | B2 | B2 |
| erjMgola4fQ_A1.txt | A1 | A2 | A2 |
| gOMypAhVaXE_A2.txt | A2 | B1 | B1 |
| ME7CECwNks4_B1.txt | B1 | B2 | B2 |
| OX-XEa50fFw_B2.txt | B2 | A2 | B1 |
| ozi4FPic4QI_B2.txt | B2 | B1 | B2 |
| tnvj7e1n5xk_B1.txt | B1 | B1 | B2 |
| uVGV8LG3HHM_A1.txt | A1 | A2 | A2 |
| V7bOxiNM3kc_C1.txt | C1 | B1 | B2 |

Загальна MAE: 1,105 → 0,789. Синтетичні тексти: 1,091 → 0,727, 9/11 у межах одного ступеня. Транскрипції: 1,125 → 0,875, усі 8 у межах одного ступеня.

Виправлено хибну неоднозначність інфлекційних родин. Введено частотні пороги 7% / 5% / 3% для A2–B1 / B2 / C1–C2 та захист від підвищення одним повторюваним терміном (потрібні 3 різні леми для B2–C2). Невідомі слова, автоматичні словникові оцінки та справді неоднозначні форми не стали підставою для підвищення.

Обмеження: C1–C2 все ще переважно оцінюються як B2. Їх не можна чесно підняти до C1/C2 лише за міткою файла: для цього бракує надійних ознак у поточному аналізі. Один попередній B1-текст (tnvj7e1n5xk) підвищився з B1 до B2 — це регресія відносно його приблизної мітки.

Повне порівняння: [calibration_comparison.json](../calibration_comparison.json). Поточний звіт: [calibration_report.json](../calibration_report.json).
