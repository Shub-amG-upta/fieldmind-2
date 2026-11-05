"""Breadth B1, Step 0: the Cranfield episodes carry exactly the paper's fault
windows, and the column order is the paper's Table 1.

Skipped when the source archive is not on this machine (it is not in git:
third-party data, data/reference/cranfield/, see reports/b1_cranfield_data.md).
"""
import json

import pytest

from data.cranfield import convert as cv

pytestmark = pytest.mark.skipif(not cv.ZIP.exists(), reason="Cranfield archive not present")


@pytest.fixture(scope="module")
def mats():
    pytest.importorskip("scipy")
    cv._unpack()
    return cv._load()


def test_shapes_and_set_points_match_the_paper(mats):
    """Durations (Tables 4-9) and, on the steady sets, the measured water and
    air flows before the fault (columns 9 and 8) vs the paper's set points."""
    assert cv.check(mats) == []


def test_flag_type_evofault_agrees_with_the_tables(mats):
    """Second source for the fault windows: where EvoFault is an on/off flag
    (cases 4-6; for 1-3 it is a valve angle) its segments must start and end
    within 6 s of the paper's table."""
    import numpy as np
    for s, (_d, _o, _w, _a, wins, _t) in cv.SETS.items():
        if s[0] not in "456":
            continue
        e = mats[int(s[0])][f"EvoFault{s}"].ravel() > 0
        dd = np.diff(np.r_[0, e.astype(int), 0])
        segs = list(zip(np.where(dd == 1)[0], np.where(dd == -1)[0]))
        assert len(segs) == len(wins), s
        for (a, b), (ta, tb) in zip(segs, wins):
            assert abs(a - ta) <= 6 and abs(b - tb) <= 6, (s, (a, b), (ta, tb))


def test_written_episodes_carry_the_table_windows():
    for out in (cv.OUT_DEV, cv.OUT_REPORT):
        if not out.exists():
            pytest.skip("episodes not converted yet (python -m data.cranfield.convert)")
    seen = set()
    for out, split in ((cv.OUT_DEV, "dev"), (cv.OUT_REPORT, "report")):
        for d in out.iterdir():
            gt = json.loads((d / "ground_truth.json").read_text())
            s = gt["dataset"].split("Set")[1]
            seen.add(s)
            dur, _o, _w, _a, wins, _t = cv.SETS[s]
            assert gt["fault_windows"] == [list(w) for w in wins]
            assert gt["fault_onset_t"] == wins[0][0] and gt["duration_s"] == dur
            assert gt["split"] == split == ("dev" if s in cv.DEV_SETS else "report")
            assert all(0 <= a < b <= dur for a, b in wins)
            header = (d / "timeseries.csv").open().readline().strip().split(",")
            assert header == ["t"] + cv.TAGS
    assert seen == set(cv.SETS)


def test_every_fault_has_a_dev_and_the_split_is_the_preregistered_one():
    assert cv.DEV_SETS == {"1_2", "2_2", "3_2", "4_2", "5_1", "6_1"}
    assert {s[0] for s in cv.DEV_SETS} == {"1", "2", "3", "4", "5", "6"}
