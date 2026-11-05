"""
=============================================================================
 L1  --  THE DETERMINISTIC CHECK LAYER  (Plan §4)
=============================================================================

Ordinary Python with numeric thresholds.  No model involved.  Runs on every
tick regardless of what else is happening.

It produces FACTS: statements that are true by construction.  Everything
downstream is only allowed to INTERPRET facts, never to contradict them.

Five families:
    LIMIT     is a value outside its band right now?
    RATE      is it moving too fast, or steadily in one direction?
    BALANCE   do the physics still add up?          <- most of the value
    VALIDITY  is the instrument itself believable?
    PATTERN   does a known named signature match?

Thresholds live in the config (configs/base.yaml -> checks:) not in this file,
because tuning them against the normal episodes to hit the false-positive
target Q5 is an explicit phase-2 activity (Plan §A.5).

Pure stdlib -- this module runs on the device.
=============================================================================
"""

from __future__ import annotations

from statistics import median

from ..schemas import Fact


# -----------------------------------------------------------------------
#  Small numeric helpers (deliberately not numpy -- keeps the device path
#  dependency-free, and these windows are only a few hundred samples)
# -----------------------------------------------------------------------

def _slope_per_min(samples: list[float], dt_s: float) -> float:
    """Least-squares slope in units per minute.

    Least squares rather than (last - first) / n because a single noisy end
    sample would otherwise dominate, and RATE facts feed straight into
    triage.
    """
    n = len(samples)
    if n < 3:
        return 0.0
    mean_x = (n - 1) / 2.0
    mean_y = sum(samples) / n
    num = sum((i - mean_x) * (y - mean_y) for i, y in enumerate(samples))
    den = sum((i - mean_x) ** 2 for i in range(n))
    if den == 0:
        return 0.0
    return (num / den) * (60.0 / dt_s)          # per-sample -> per-minute


def _mad(samples: list[float]) -> float:
    """Median absolute deviation. Robust to the one-off spikes that a plain
    standard deviation would treat as a real excursion."""
    if not samples:
        return 0.0
    m = median(samples)
    return median([abs(x - m) for x in samples])


def _load_normalised_bed_slope(w, need: int, dt_s: float, coef: float) -> float:
    """Bed temperature slope with the load-following component removed.

    A healthy boiler's bed temperature tracks load: raise steam flow and the
    firing rate follows, so the bed runs hotter. Over a 40-minute window a
    slow load swing therefore looks EXACTLY like a fouling drift.

    `coef` (degC per TPH) is a plant characterisation constant, fitted from
    historical normal operation -- not a tuning knob. Subtracting the
    load-explained part is what lets family E be detected without drowning
    the normal episodes in false positives.
    """
    bed = _slope_per_min(w.series("bed_temp_avg")[-need:], dt_s)
    steam = _slope_per_min(w.series("steam_flow")[-need:], dt_s)
    return bed - coef * steam


class _FactIds:
    """Sequential fact ids within a tick: F1, F2, F3 ...

    Ids are tick-local by design. The LLM cites them inside one tick and the
    L6 gate resolves them inside the same tick, so there is no need for
    globally unique ids and short ones cost fewer prompt tokens.
    """
    def __init__(self):
        self.n = 0

    def next(self) -> str:
        self.n += 1
        return f"F{self.n}"


# =======================================================================
#  The check runner
# =======================================================================

class CheckLayer:
    """Runs all five families over the rolling window and returns Facts."""

    def __init__(self, cfg: dict, asset=None):
        self.cfg = cfg
        # The plant (fieldmind/assets): its balances and patterns. None = the
        # boiler, so unit tests built from the checks config alone are unchanged.
        if asset is None:
            from ..assets import default_asset
            asset = default_asset()
        self.asset = asset
        self.limits = cfg["limits"]
        self.rates = cfg["rates"]
        # Long-horizon drift: the ONLY thing that catches family E.
        self.rates_long = cfg.get("rates_long", {})
        # Signature magnitude bands (l1_symbolize.direction_and_band). Owned by
        # L1 config; the orchestrator hands them to build_signature. Required --
        # no silent default, so the config stays the single source.
        self.bands = cfg["bands"]
        self.balance = cfg["balance"]
        self.validity = cfg["validity"]
        self.dt_s = cfg.get("sample_period_s", 5.0)
        # degC per TPH, fitted from normal operation (see README). Used to
        # strip the load-following component out of the bed temperature.
        self.load_coef = cfg.get("load_coef_degc_per_tph", 2.75)

    # -------------------------------------------------------------------
    def run(self, window: "SensorWindow", tick: int,
            trusted: set[str], blowdown_tph: float = 1.0) -> list[Fact]:
        """window  : rolling buffer of the last N minutes of samples
           trusted : tags currently believed valid -- an untrusted tag is
                     excluded from limit/rate/balance so one dead instrument
                     does not manufacture a plant fault (Plan §9).
        """
        ids = _FactIds()
        facts: list[Fact] = []

        # ORDER MATTERS. Validity runs first: if an instrument is lying, every
        # other check over that tag is meaningless, and a balance that silently
        # includes a stuck tag is worse than no balance at all.
        facts += self._validity(window, tick, ids)
        live = {f.tags[0] for f in facts if f.check == "VALIDITY"}
        trusted = trusted - live

        facts += self._limits(window, tick, ids, trusted)
        facts += self._rates(window, tick, ids, trusted)
        facts += self._balances(window, tick, ids, trusted, blowdown_tph)
        facts += self._patterns(window, tick, ids, trusted, facts)
        return facts

    # ---------------- VALIDITY ------------------------------------------
    def _validity(self, w, tick, ids) -> list[Fact]:
        """Is the instrument itself believable?

        Three ways a tag can be disbelieved:
          stuck        variance ~= 0 for N minutes
          out of range value physically impossible
          step         jump larger than the process can produce in one tick
        """
        out = []
        mins = self.validity["stuck_minutes"]
        need = int(mins * 60 / self.dt_s)

        for tag in w.tags:
            s = w.series(tag)
            if not s:
                continue

            # -- stuck --
            if len(s) >= need:
                recent = s[-need:]
                eps = self.validity["stuck_mad_eps"]
                # a scalar (the boiler) or a per-tag dict (assets whose healthy
                # tags can sit flat, e.g. Cranfield's FT407 and PT417)
                eps = eps.get(tag, 0.0) if isinstance(eps, dict) else eps
                if _mad(recent) < eps:
                    out.append(Fact(ids.next(), "VALIDITY", [tag],
                                    w.window_ticks(tick), recent[-1],
                                    f"{tag} frozen at {recent[-1]:.2f} for "
                                    f"{mins:.0f} min (instrument suspect)",
                                    "ALARM", 1.0))
                    continue

            # -- physical range --
            lo, hi = self.validity["physical_range"][tag]
            if not (lo <= s[-1] <= hi):
                out.append(Fact(ids.next(), "VALIDITY", [tag],
                                w.window_ticks(tick), s[-1],
                                f"{tag} = {s[-1]:.2f} outside physical range "
                                f"[{lo}, {hi}]", "ALARM", 1.0))
                continue

            # -- impossible step --
            if len(s) >= 2:
                step = abs(s[-1] - s[-2])
                if step > self.validity["max_step"][tag]:
                    out.append(Fact(ids.next(), "VALIDITY", [tag],
                                    w.window_ticks(tick), step,
                                    f"{tag} stepped {step:.2f} in one sample "
                                    f"(physically impossible)", "ALARM", 1.0))
        return out

    # ---------------- LIMIT ---------------------------------------------
    def _limits(self, w, tick, ids, trusted) -> list[Fact]:
        """Is a value outside its band right now?

        Limit checks tell you something is ALREADY wrong. They are the least
        interesting family and the easiest to get right.
        """
        out = []
        for tag, bands in self.limits.items():
            if tag not in trusted:
                continue
            v = w.latest(tag)
            if v is None:
                continue
            for band_name, spec in bands.items():          # e.g. "alarm_hi"
                op, thr, sev = spec["op"], spec["value"], spec["severity"]
                hit = (v > thr) if op == ">" else (v < thr)
                if hit:
                    out.append(Fact(ids.next(), "LIMIT", [tag],
                                    w.window_ticks(tick), v,
                                    f"{tag} = {v:.1f} {op} {thr} ({band_name})",
                                    sev, 1.0))
        return out

    # ---------------- RATE ----------------------------------------------
    def _rates(self, w, tick, ids, trusted) -> list[Fact]:
        """Is it moving too fast, or moving steadily in one direction?

        Sustained-for-N-minutes is the important part. An instantaneous slope
        on a noisy tag fires constantly; a slope held for ten minutes is a
        process change.
        """
        out = []
        for tag, spec in self.rates.items():
            if tag not in trusted:
                continue
            mins = spec["sustained_min"]
            need = int(mins * 60 / self.dt_s)
            s = w.series(tag)
            if len(s) < need:
                continue
            slope = _slope_per_min(s[-need:], self.dt_s)

            thr, direction = spec["threshold"], spec.get("direction", "abs")
            hit = (abs(slope) > thr if direction == "abs" else
                   slope > thr if direction == "up" else slope < thr)
            if hit:
                # Confidence is discounted for slope estimates: unlike a limit,
                # a slope is inferred, and how noisy the tag is should show up
                # in how much weight the belief update gives it (Plan §4.3).
                noise = _mad(s[-need:])
                conf = max(0.5, min(1.0, abs(slope) / (thr + 1e-9) / 2))
                out.append(Fact(ids.next(), "RATE", [tag],
                                w.window_ticks(tick), slope,
                                f"{tag} {slope:+.2f} {spec['unit']} sustained "
                                f"{mins:.0f} min (noise MAD {noise:.2f})",
                                spec["severity"], round(conf, 2)))

        # ---- long-horizon drift ----------------------------------------
        # Family E is the case that separates a real monitoring agent from an
        # alarm repeater: NOTHING crosses a threshold, and the short-window
        # RATE checks above are all below their limits by construction. The
        # only signal is a slow change in the relationship between tags at
        # constant load, visible over 40+ minutes.
        #
        # This is also why the baseline FREEZE in world_model.update_baselines
        # matters. Without it an adaptive baseline learns the drift as normal
        # and this check goes quiet exactly when it is needed.
        for tag, spec in self.rates_long.items():
            if tag not in trusted:
                continue
            mins = spec["sustained_min"]
            need = int(mins * 60 / self.dt_s)
            s = w.series(tag)
            if len(s) < need:
                continue
            # Strip the load-following component out of bed temperature so a
            # slow load swing is not mistaken for a fouling drift.
            if tag == "bed_temp_avg":
                raw = _slope_per_min(s[-need:], self.dt_s)
                slope = _load_normalised_bed_slope(w, need, self.dt_s,
                                                   self.load_coef)
                # Guard against the normalisation inverting. When the FAULT
                # itself drives the load down (family B: pressure sags, the
                # turbine throttles back), -coef*steam_slope alone can
                # manufacture a large positive "drift" out of a flat bed.
                # Requiring genuine absolute rise as well removes that.
                if raw <= 0.3 * spec["threshold"]:
                    continue
                label = "DRIFTING (load-normalised)"
            else:
                slope = _slope_per_min(s[-need:], self.dt_s)
                label = "DRIFTING"
            thr, direction = spec["threshold"], spec.get("direction", "abs")
            hit = (abs(slope) > thr if direction == "abs" else
                   slope > thr if direction == "up" else slope < thr)
            if hit:
                out.append(Fact(ids.next(), "RATE", [tag],
                                w.window_ticks(tick), slope,
                                f"{tag} {label} {slope:+.3f} {spec['unit']} over "
                                f"{mins:.0f} min at steady load - no limit crossed",
                                spec["severity"], 0.7))
        return out

    # ---------------- BALANCE / PATTERN ---------------------------------
    # Plant physics lives in the asset pack (fieldmind/assets/<asset>.py):
    # the boiler's water and energy balances and its named patterns moved
    # there unchanged (breadth phase B1).
    def _balances(self, w, tick, ids, trusted, blowdown) -> list[Fact]:
        """Do the physics still add up?  (Plan §4.2) -- the asset's balances."""
        return self.asset.balances(self, w, tick, ids, trusted, blowdown)

    def _patterns(self, w, tick, ids, trusted, sofar) -> list[Fact]:
        """Does a known named signature match? -- the asset's patterns."""
        return self.asset.patterns(self, w, tick, ids, trusted, sofar)
