#!/usr/bin/env python3
"""
The whole agent on the laptop with Laya in every bev slot and the mock everywhere
else (reports/laya_l1.md, Track A6).

    .venv/bin/python -m bench.run_laya [--laya-url http://127.0.0.1:8090] <run_demo.py arguments>

Same arguments as run_demo.py (add the overlays: configs/bev3.yaml for the decider,
configs/bev_ideas.yaml + --bev "...=shadow|on" for the bev ideas, then
configs/laya.yaml). The backend must be mock: every call whose role is `decider`
(the decider and every bev idea, fieldmind/multi/agents/{decider,bev}.py) goes over
HTTP to a /v1/systemone server (bench/laya_serve.py, or llama-server serving the
converted GGUF), everything else to the mock. Labelled "mock diagnosticians +
Laya": it measures Laya's slots, never Llama.

On the board (Track C) this script is not needed: with `llm.backend: llamaserver`
the decider lane's own `url` (configs/laya.yaml) already sends those calls there.

fieldmind/ is not changed: the router replaces bench.harness.make_backend for this
process only.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DECIDER_ROLE = "decider"


class RouterBackend:
    """Decider-role calls to `http`, every other call to `mock`. Looks like the
    backend it wraps (name, attributes), so the harness and telemetry see a mock run."""

    def __init__(self, mock, http):
        self.mock, self.http = mock, http
        self.routed = {"http": 0, "mock": 0}

    def generate(self, prompt, role="generic", max_tokens=512, mock_hint=None):
        if role == DECIDER_ROLE:
            self.routed["http"] += 1
            return self.http.generate(prompt, role=role, max_tokens=max_tokens, mock_hint=mock_hint)
        self.routed["mock"] += 1
        return self.mock.generate(prompt, role=role, max_tokens=max_tokens, mock_hint=mock_hint)

    def __getattr__(self, name):            # everything else is the mock's (name, close, ...)
        return getattr(self.mock, name)


def install(url: str, model_file: str = "laya") -> None:
    """Route the harness's backend through RouterBackend for this process."""
    import bench.harness as harness
    from fieldmind.runtime.llm_backend import BevDeciderBackend
    original = harness.make_backend

    def make_backend(llm_cfg: dict):
        inner = original(llm_cfg)
        if llm_cfg.get("backend", "mock") != "mock":
            raise SystemExit("bench.run_laya needs --backend mock (on llamaserver the lane url routes)")
        return RouterBackend(inner, BevDeciderBackend(url=url, lane="bev", model_file=model_file,
                                                      timeout_s=300.0))
    harness.make_backend = make_backend


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    url = "http://127.0.0.1:8090"
    if "--laya-url" in argv:
        i = argv.index("--laya-url")
        url = argv[i + 1]
        del argv[i:i + 2]
    install(url)
    import run_demo
    sys.argv = ["run_demo.py"] + argv
    return run_demo.main() or 0


if __name__ == "__main__":
    raise SystemExit(main())
