"""Executable Pumping Lemma adversary for the unbounded queue language."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PumpingLemmaResult:
    pumping_length: int
    witness: str
    pumped_word: str
    pump_index: int
    pump_count: int
    balance_preserved: bool
    proves_non_regular: bool
    bounded_capacity: int | None = None


def pumping_lemma_adversary(pumping_length: int, pump_count: int = 2) -> PumpingLemmaResult:
    """Choose ``w = enq^p deq^p`` and pump a non-empty prefix segment.

    For every decomposition ``xyz`` with ``|xy| <= p`` and ``|y| > 0``,
    ``y`` consists only of enqueues. Pumping it changes the two counts, so the
    word leaves ``{enq^n deq^n}``. ``pump_count`` is the number of copies of
    the pumped segment; the standard witness uses 2 (one extra enqueue).
    """
    if not isinstance(pumping_length, int) or pumping_length < 1:
        raise ValueError("pumping_length must be a positive integer")
    if not isinstance(pump_count, int) or pump_count < 0:
        raise ValueError("pump_count must be a non-negative integer")
    witness = "enq" * pumping_length + "deq" * pumping_length
    y = "enq"
    pumped_word = "enq" * (pumping_length + pump_count - 1) + "deq" * pumping_length
    return PumpingLemmaResult(pumping_length, witness, pumped_word, 0, pump_count,
                              pumped_word.count("enq") == pumped_word.count("deq"),
                              pumped_word.count("enq") != pumped_word.count("deq"))


def prove_unbounded_non_regular(pumping_length: int) -> PumpingLemmaResult:
    result = pumping_lemma_adversary(pumping_length)
    if not result.proves_non_regular:
        raise AssertionError("adversary failed to separate the pumped word")
    return result


PumpingLemmaAdversary = pumping_lemma_adversary
