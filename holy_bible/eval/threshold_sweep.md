# BM25 top-score threshold sweep

## Scores por pregunta

| question | top_sparse_score | note | hybrid last_run |
|---|---:|---|---|
| ¿Cómo describe Pablo el amor en su carta a los Corintios? | 26.2474 | genérica, pasaje muy conocido | hybrid@5 miss |
| ¿Qué le pasó a Jonás en el mar? | 24.3526 | narrativa | hybrid@5 hit |
| ¿Qué le pasó a Job y a su familia? | 24.2209 | narrativa | hybrid@5 miss |
| ¿Cómo define la fe la carta a los Hebreos? | 23.5671 | doctrinal, un versículo puntual | hybrid@5 miss |
| ¿Qué le pasó a la esposa de Lot? | 22.8345 | referencia puntual, un solo versículo | hybrid@5 miss |
| ¿Cómo empieza el evangelio de Juan? | 20.9009 | genérica | hybrid@5 miss |
| ¿Qué era el efod que usaban los sacerdotes? | 20.7262 | término técnico raro | hybrid@5 hit |
| ¿Cuál es el mandamiento más importante según Jesús? | 19.7240 | doctrinal, muy citado | hybrid@5 hit |
| ¿Qué dice el salmo del buen pastor? | 19.6503 | genérica, muy conocido | hybrid@5 miss |
| ¿Cuál es el fruto del espíritu según Pablo? | 18.7184 | doctrinal, lista | hybrid@5 miss |
| ¿Quién traicionó a Jesús y cómo? | 17.7570 | narrativa, nombre propio (Judas) | hybrid@5 miss |
| ¿Quién fue Onán y qué hizo? | 16.5571 | término propio muy raro, poco frecuente | hybrid@5 hit |
| ¿Cuáles son las bienaventuranzas? | 11.8363 | doctrinal, lista | hybrid@5 hit |
| ¿Qué le prometió Dios a Abraham? | 11.7570 | doctrinal | hybrid@5 miss |
| ¿Quién era Melquisedec? | 11.4843 | término propio raro | hybrid@5 miss |

## Umbrales candidatos

| umbral | activarían hybrid |
|---:|---:|
| 0.5 | 15 / 15 |
| 1.0 | 15 / 15 |
| 1.5 | 15 / 15 |
| 2.0 | 15 / 15 |
| 2.5 | 15 / 15 |
| 3.0 | 15 / 15 |
| 4.0 | 15 / 15 |
| 5.0 | 15 / 15 |
