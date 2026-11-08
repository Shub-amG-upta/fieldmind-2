"""Accuracy-fixes step 2a: StatePersistence publishes DEVIATION/ALARM only after N
consecutive ticks; NORMAL resets; TRIP_IMMINENT and DEGRADED pass at once. Checked
on the published state of the multi-agent TriageAgent (the emitted outcome)."""
from fieldmind.agent.world_model import StatePersistence


def _feed(n, states):
    p = StatePersistence(n)
    return [p(s) for s in states]


def test_n1_is_off_every_state_passes():
    seq = ["NORMAL", "DEVIATION", "ALARM", "NORMAL", "TRIP_IMMINENT", "DEGRADED"]
    assert _feed(1, seq) == seq


def test_n3_waits_two_ticks_and_a_normal_tick_resets():
    seq = ["DEVIATION", "DEVIATION", "DEVIATION", "ALARM", "NORMAL", "ALARM", "ALARM", "NORMAL"]
    assert _feed(3, seq) == ["NORMAL", "NORMAL", "DEVIATION", "ALARM", "NORMAL",
                             "NORMAL", "NORMAL", "NORMAL"]


def test_trip_imminent_and_degraded_pass_at_once_and_keep_the_count():
    seq = ["DEVIATION", "TRIP_IMMINENT", "DEGRADED", "ALARM"]
    assert _feed(3, seq) == ["NORMAL", "TRIP_IMMINENT", "DEGRADED", "NORMAL"]
    assert _feed(2, ["ALARM", "DEGRADED", "ALARM"]) == ["NORMAL", "DEGRADED", "ALARM"]


def test_triage_agent_reads_the_config_key():
    from fieldmind.multi.agents.triage import TriageAgent
    assert TriageAgent({"state_persistence_ticks": 3}).persist.n == 3
    assert TriageAgent({}).persist.n == 1


def test_on_for_cranfield_and_tep_off_for_the_boiler():
    import yaml
    base = yaml.safe_load(open("configs/base.yaml"))
    assert base["agent"].get("state_persistence_ticks", 1) == 1
    for f in ("configs/cranfield.yaml", "configs/tep.yaml"):
        assert yaml.safe_load(open(f))["agent"]["state_persistence_ticks"] == 3
