# Recall@k last run

```
Recall@k              k=1      k=3      k=5
hybrid=True       20.0%   20.0%   33.3%
hybrid=False      40.0%   60.0%   73.3%
```

## Disagreements at k=5
- ¿Cómo describe Pablo el amor en su carta a los Corintios?  |  hybrid@5=miss  dense@5=hit  (genérica, pasaje muy conocido)
- ¿Cómo empieza el evangelio de Juan?  |  hybrid@5=miss  dense@5=hit  (genérica)
- ¿Quién traicionó a Jesús y cómo?  |  hybrid@5=miss  dense@5=hit  (narrativa, nombre propio (Judas))
- ¿Qué le pasó a la esposa de Lot?  |  hybrid@5=miss  dense@5=hit  (referencia puntual, un solo versículo)
- ¿Cuál es el fruto del espíritu según Pablo?  |  hybrid@5=miss  dense@5=hit  (doctrinal, lista)
- ¿Qué le pasó a Job y a su familia?  |  hybrid@5=miss  dense@5=hit  (narrativa)

## Per question
- ¿Quién era Melquisedec?
  hybrid @1=N @3=N @5=N | dense @1=N @3=N @5=N | término propio raro
- ¿Cuál es el mandamiento más importante según Jesús?
  hybrid @1=Y @3=Y @5=Y | dense @1=Y @3=Y @5=Y | doctrinal, muy citado
- ¿Cómo describe Pablo el amor en su carta a los Corintios?
  hybrid @1=N @3=N @5=N | dense @1=N @3=N @5=Y | genérica, pasaje muy conocido
- ¿Cómo empieza el evangelio de Juan?
  hybrid @1=N @3=N @5=N | dense @1=N @3=Y @5=Y | genérica
- ¿Qué le pasó a Jonás en el mar?
  hybrid @1=N @3=N @5=Y | dense @1=N @3=N @5=Y | narrativa
- ¿Cuáles son las bienaventuranzas?
  hybrid @1=Y @3=Y @5=Y | dense @1=Y @3=Y @5=Y | doctrinal, lista
- ¿Qué le prometió Dios a Abraham?
  hybrid @1=N @3=N @5=N | dense @1=N @3=N @5=N | doctrinal
- ¿Quién traicionó a Jesús y cómo?
  hybrid @1=N @3=N @5=N | dense @1=N @3=Y @5=Y | narrativa, nombre propio (Judas)
- ¿Qué dice el salmo del buen pastor?
  hybrid @1=N @3=N @5=N | dense @1=N @3=N @5=N | genérica, muy conocido
- ¿Qué le pasó a la esposa de Lot?
  hybrid @1=N @3=N @5=N | dense @1=Y @3=Y @5=Y | referencia puntual, un solo versículo
- ¿Cuál es el fruto del espíritu según Pablo?
  hybrid @1=N @3=N @5=N | dense @1=Y @3=Y @5=Y | doctrinal, lista
- ¿Cómo define la fe la carta a los Hebreos?
  hybrid @1=N @3=N @5=N | dense @1=N @3=N @5=N | doctrinal, un versículo puntual
- ¿Quién fue Onán y qué hizo?
  hybrid @1=Y @3=Y @5=Y | dense @1=Y @3=Y @5=Y | término propio muy raro, poco frecuente
- ¿Qué le pasó a Job y a su familia?
  hybrid @1=N @3=N @5=N | dense @1=Y @3=Y @5=Y | narrativa
- ¿Qué era el efod que usaban los sacerdotes?
  hybrid @1=N @3=N @5=Y | dense @1=N @3=Y @5=Y | término técnico raro
