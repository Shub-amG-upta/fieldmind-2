#!/usr/bin/env python3
"""
Laya behind bev-decide's protocol (reports/laya_l1.md, Track A3). Runs in
.venv-laya (torch, transformers 5.x), never on the device and never imported by
fieldmind/.

    .venv-laya/bin/python -m bench.laya_serve [--checkpoint convaiinnovations/laya]
        [--subfolder typed-decisions|multilingual] [--revision SHA]
        [--port 8090] [--shuffle-seed N]

POST /v1/systemone takes the body every bev slot already sends
({"state", "questions"}: choice and noul questions) and replies in bev-decide's
shape (bench.system_one.to_bev_reply), so the decider and every bev idea use
Laya when their `kind: decider` lane's url points here: no agent code changes.

The reply also carries what Laya did to the request:
  usage.prompt_tokens   tokens through the encoder, summed over the questions
  truncated             the state lost tokens in at least one question
  options_cut           choice options longer than Laya's 48-token option cap
  layout                the checkpoint's option layout: "sequential" lets option
                        order reach the encoder, "parallel" does not
--shuffle-seed N gives every choice question its options in a seeded other
order (bench.system_one.shuffle_request, seed per request), for the order test.

GET /health: the checkpoint, its revision and layout.
Single-threaded on purpose: one request at a time, as bev-decide.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from bench.system_one import ReplyError, request_seed, shuffle_request, to_bev_reply  # noqa: E402

OPTION_CAP = 48     # CITED: laya/common.py build_head, max_length=48 per option (laya 0.4.27)


def options_cut(tok, questions: dict) -> int:
    from laya.common import encode_text
    n = 0
    for q in questions.values():
        if q.get("type") != "choice":
            continue
        for k, v in (q.get("criteria") or {}).items():
            text = f" {k}: {v}" if v not in (None, "") else f" {k}"
            n += len(encode_text(tok, text, add_special_tokens=False)["input_ids"]) > OPTION_CAP
    return n


class Laya:
    def __init__(self, checkpoint: str, subfolder: str | None, revision: str | None, device: str):
        import laya
        self.agent = laya.load(checkpoint, subfolder=subfolder, revision=revision, device=device)
        self.name = checkpoint + (f"/{subfolder}" if subfolder else "") + (f"@{revision}" if revision else "")
        self.layout = "parallel" if getattr(self.agent, "parallel_options", False) else "sequential"

    def answer(self, body: str, shuffle_seed: int | None) -> dict:
        req = json.loads(body)
        if not isinstance(req, dict) or not isinstance(req.get("questions"), dict) or not req["questions"]:
            raise ReplyError("request needs a non-empty questions object")
        asked = req
        if shuffle_seed is not None:
            asked = shuffle_request(req, request_seed(body, shuffle_seed))
        t0 = time.perf_counter()
        r = self.agent.predict(asked["state"], asked["questions"])
        ms = (time.perf_counter() - t0) * 1000
        usage = r.get("usage") or {}
        reply = to_bev_reply(r.get("answers") or {}, req["questions"], model=self.name,
                             prompt_tokens=usage.get("input_tokens"), model_ms=ms,
                             truncated=bool(usage.get("truncated") or usage.get("truncated_questions")))
        reply["options_cut"] = options_cut(self.agent.tok, req["questions"])
        reply["layout"] = self.layout
        reply["shuffled"] = shuffle_seed is not None
        if shuffle_seed is not None:
            reply["asked_order"] = {qid: list(q.get("criteria") or {})
                                    for qid, q in asked["questions"].items() if q.get("type") == "choice"}
        return reply


def make_handler(model: Laya, shuffle_seed: int | None):
    class H(BaseHTTPRequestHandler):
        def _send(self, code: int, obj: dict):
            data = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/health":
                self._send(200, {"model": model.name, "layout": model.layout,
                                 "shuffle_seed": shuffle_seed})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/v1/systemone":
                self._send(404, {"error": "not found"})
                return
            body = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode()
            try:
                self._send(200, model.answer(body, shuffle_seed))
            except (ValueError, KeyError, TypeError) as e:     # ReplyError is a ValueError
                self._send(400, {"error": f"{type(e).__name__}: {e}"})

        def log_message(self, fmt, *args):      # quiet: one line per request is noise at 1,000s
            pass
    return H


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Laya behind bev-decide's /v1/systemone protocol")
    ap.add_argument("--checkpoint", default="convaiinnovations/laya")
    ap.add_argument("--subfolder", default=None)
    ap.add_argument("--revision", default=None)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8090)
    ap.add_argument("--shuffle-seed", type=int, default=None)
    a = ap.parse_args(argv)
    model = Laya(a.checkpoint, a.subfolder, a.revision, a.device)
    srv = HTTPServer((a.host, a.port), make_handler(model, a.shuffle_seed))
    print(f"laya_serve: {model.name} ({model.layout} layout) on http://{a.host}:{a.port}"
          f"{' shuffled seed ' + str(a.shuffle_seed) if a.shuffle_seed is not None else ''}", flush=True)
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
