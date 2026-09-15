from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ExpectedPassage:
    book: str
    chapter: int
    verse_start: int
    verse_end: int

@dataclass
class EvalQuestion:
    question: str
    expected: list[ExpectedPassage]
    note: str = ""

EVAL_DATASET: list[EvalQuestion] = [
    EvalQuestion("¿Quién era Melquisedec?", [
        ExpectedPassage("Génesis", 14, 18, 20),
        ExpectedPassage("Hebreos", 7, 1, 10),
        ExpectedPassage("Salmos", 110, 4, 4),
    ], note="término propio raro"),
    EvalQuestion("¿Cuál es el mandamiento más importante según Jesús?", [
        ExpectedPassage("Mateo", 22, 37, 40),
        ExpectedPassage("Marcos", 12, 29, 31),
    ], note="doctrinal, muy citado"),
    EvalQuestion("¿Cómo describe Pablo el amor en su carta a los Corintios?", [
        ExpectedPassage("1 Corintios", 13, 1, 13),
    ], note="genérica, pasaje muy conocido"),
    EvalQuestion("¿Cómo empieza el evangelio de Juan?", [
        ExpectedPassage("Juan", 1, 1, 5),
    ], note="genérica"),
    EvalQuestion("¿Qué le pasó a Jonás en el mar?", [
        ExpectedPassage("Jonás", 1, 15, 17),
        ExpectedPassage("Jonás", 2, 1, 10),
    ], note="narrativa"),
    EvalQuestion("¿Cuáles son las bienaventuranzas?", [
        ExpectedPassage("Mateo", 5, 3, 12),
    ], note="doctrinal, lista"),
    EvalQuestion("¿Qué le prometió Dios a Abraham?", [
        ExpectedPassage("Génesis", 12, 1, 3),
        ExpectedPassage("Génesis", 15, 4, 6),
    ], note="doctrinal"),
    EvalQuestion("¿Quién traicionó a Jesús y cómo?", [
        ExpectedPassage("Mateo", 26, 14, 16),
        ExpectedPassage("Mateo", 26, 47, 50),
    ], note="narrativa, nombre propio (Judas)"),
    EvalQuestion("¿Qué dice el salmo del buen pastor?", [
        ExpectedPassage("Salmos", 23, 1, 6),
    ], note="genérica, muy conocido"),
    EvalQuestion("¿Qué le pasó a la esposa de Lot?", [
        ExpectedPassage("Génesis", 19, 26, 26),
    ], note="referencia puntual, un solo versículo"),
    EvalQuestion("¿Cuál es el fruto del espíritu según Pablo?", [
        ExpectedPassage("Gálatas", 5, 22, 23),
    ], note="doctrinal, lista"),
    EvalQuestion("¿Cómo define la fe la carta a los Hebreos?", [
        ExpectedPassage("Hebreos", 11, 1, 1),
    ], note="doctrinal, un versículo puntual"),
    EvalQuestion("¿Quién fue Onán y qué hizo?", [
        ExpectedPassage("Génesis", 38, 8, 10),
    ], note="término propio muy raro, poco frecuente"),
    EvalQuestion("¿Qué le pasó a Job y a su familia?", [
        ExpectedPassage("Job", 1, 13, 19),
    ], note="narrativa"),
    EvalQuestion("¿Qué era el efod que usaban los sacerdotes?", [
        ExpectedPassage("Éxodo", 28, 6, 14),
    ], note="término técnico raro"),
]
