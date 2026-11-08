"""Accuracy-fixes step 3 (REVERTED on dev, code kept, off by default): the retriever's
EWMA of the match score. Checked on the retrieved case order (the emitted outcome)."""
from fieldmind.agent.l3_retrieve import Retriever


class _Lib:
    """Stand-in library: scores per tick are set by the test."""
    def __init__(self):
        self.cases = [{"case_id": "A"}, {"case_id": "B"}]
        self.now = {}

    def match(self, signature, k=5, measure="jaccard"):
        out = [dict(c, score=self.now[c["case_id"]]) for c in self.cases if self.now.get(c["case_id"], 0) > 0.01]
        return sorted(out, key=lambda c: -c["score"])[:k]


def _ret(h):
    lib = _Lib()
    r = Retriever(None, lib, None, None, {"tick_period_s": 30, "retrieval": {"score_ewma_halflife_ticks": h}})
    return r, lib


def test_a_one_tick_blip_does_not_take_line_1_from_a_steady_case():
    r, lib = _ret(2)
    for t in range(5):
        lib.now = {"A": 0.5, "B": 0.1}
        r._smoothed_cases({}, t * 30.0, 2, 4)
    lib.now = {"A": 0.4, "B": 0.6}                    # one tick where B wins on its own
    top = r._smoothed_cases({}, 5 * 30.0, 2, 4)
    assert top[0]["case_id"] == "A" and top[0]["score_tick"] == 0.4


def test_a_constant_score_is_shown_unchanged_and_quiet_ticks_decay_it():
    r, lib = _ret(2)
    lib.now = {"A": 0.5}
    for t in range(4):
        top = r._smoothed_cases({}, t * 30.0, 2, 4)
    assert top[0]["score"] == 0.5
    lib.now = {"B": 0.3}                               # 10 quiet ticks, then only B matches
    top = r._smoothed_cases({}, 14 * 30.0, 2, 4)
    assert [c["case_id"] for c in top][0] == "B"

