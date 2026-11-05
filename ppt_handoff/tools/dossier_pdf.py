#!/usr/bin/env python3
"""reports/fieldmind_research_dossier.md -> reports/fieldmind_research_dossier.pdf, with the charts and
flow diagrams placed at the end of the section they belong to. Stdlib only; prints with headless Chrome.

    /usr/bin/python3 -I ppt_handoff/tools/dossier_pdf.py

The figures come from ppt_handoff/figures/ and ppt_handoff/bev3_slides/figures/ (make_figures.py,
bev3_slides_figures.py); regenerate those first if the run data changed."""
from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "reports/fieldmind_research_dossier.md"
OUT_PDF = ROOT / "reports/fieldmind_research_dossier.pdf"
FIG_DIRS = [ROOT / "ppt_handoff/figures", ROOT / "ppt_handoff/bev3_slides/figures"]

# section number -> figures shown at the end of that section, with captions
FIGS = {
    "1.": [("20_accuracy_first4", "Group top-1 of every configuration on the same four fault episodes; dashed line = belief (code only)."),
           ("29_accuracy_vs_time", "Accuracy against total wall time for the four fault episodes.")],
    "5.1": [("01_flow_single_agent", "Single-agent pipeline (L0–L7): one long model call per tick on the NPU.")],
    "5.8": [("10_bench_single", "Single agent on the board: accuracy against belief, wall time and model calls per episode.")],
    "6.1": [("06_board_deployment", "Deployment: the agent on the laptop, persistent model servers on the QIDK (NPU and CPU).")],
    "6.3": [("35_npu_model_screening", "Four models on the Hexagon NPU: prefill and decode speed, and one verified diagnosis.")],
    "7.1": [("02_flow_multi_v2", "Multi-agent v2: hard path in code, small model jobs on two lanes, merge rule in the gate.")],
    "7.3": [("25_wall_time_first4", "Wall time per episode and in total, four fault episodes."),
            ("27_tick_latency", "Distribution of non-quiet tick times against the 30 s budget."),
            ("26_call_latency", "Model call time by agent, lane and model (log scale)."),
            ("28_tokens_first4", "Prompt and answer tokens processed on the board, four fault episodes.")],
    "8.1": [("11_bench_v2_model", "Multi v2 with merge rule `model`: the published ranking falls below belief."),
            ("24_helped_harmed_first4", "Ticks the model fixed (green) and broke (red) relative to belief, per configuration.")],
    "8.2": [("12_bench_v2_tiebreak", "Multi v2 with merge rule `tiebreak`."),
            ("13_bench_v2_nudge", "Multi v2 with merge rule `nudge`.")],
    "8.3": [("32_group_letter_shortcut", "The group-letter shortcut: Llama's first pick with and without group letters, five runs.")],
    "8.4": [("03_flow_multi_v3", "Multi-agent v3: no group letters, raw notes, merge rule `hybrid` with the filler-case guard."),
            ("14_bench_v3", "v3 on the board: accuracy against belief, wall time and model calls per episode."),
            ("21_accuracy_all10", "Accuracy on all ten fault episodes: v2 nudge, v3, bev-decider-2, bev-decider-3, belief."),
            ("23_quality_metrics_all10", "Five quality metrics on the ten fault episodes."),
            ("33_timeline_A01", "Tick by tick, A01: right (green) or wrong (red) top cause per system."),
            ("34_timeline_B01", "Tick by tick, B01.")],
    "9.2": [("05_flow_bev_decider_3", "bev-decider-3: v3 plus the System One decider on its own server (HTP0, port 8082)."),
            ("04_flow_bev_decider_2", "bev-decider-2: the accuracy setup (nudge) plus the decider.")],
    "9.3": [("40_bev3_vs_v3_accuracy", "bev-decider-3 against v3 per episode, with the same-run replay without the decider."),
            ("30_decider_effect", "What the decider changed inside the same runs: ticks fixed and broken (top: bev-3, bottom: bev-2)."),
            ("31_decider_picks_by_family", "How often the decider, Llama's first pick and belief name the right cause, by fault family."),
            ("16_bench_bev3", "bev-decider-3 on the board, per episode."),
            ("15_bench_bev2", "bev-decider-2 on the board, per episode.")],
    "9.4": [("41_call_time_split", "One model call split into prefill and decode; total model time for v3 and bev-decider-3.")],
    "10.": [("22_heatmap_group_top1", "Group top-1 of every configuration on every fault episode."),
            ("36_chip_temperature", "Chip temperature before and after each episode (v3, bev-decider-2, bev-decider-3).")],
}

CSS = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }
body { font-family: 'DejaVu Sans', 'Liberation Sans', Arial, sans-serif; font-size: 9.6pt; line-height: 1.42;
       color: #1d1d1f; }
h1 { font-size: 20pt; margin: 0 0 6pt; color: #0b3d6b; }
h2 { font-size: 14.5pt; color: #0b3d6b; border-bottom: 1.5px solid #0b3d6b; padding-bottom: 3pt;
     margin-top: 18pt; page-break-after: avoid; }
h2.major { page-break-before: always; }
h3 { font-size: 11.5pt; color: #155a8a; margin-top: 12pt; page-break-after: avoid; }
p { margin: 5pt 0; }
ul, ol { margin: 4pt 0 4pt 0; padding-left: 16pt; }
li { margin: 2pt 0; }
code { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.4pt; background: #f2f4f7; padding: 0 2pt;
       border-radius: 2pt; }
pre { background: #f2f4f7; padding: 6pt 8pt; border-radius: 3pt; font-size: 8.2pt; white-space: pre-wrap;
      page-break-inside: avoid; }
pre code { background: none; padding: 0; }
td code { word-break: break-all; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 8pt; font-size: 8.2pt; page-break-inside: auto; }
tr { page-break-inside: avoid; }
th { background: #e6eef6; color: #0b3d6b; font-weight: bold; text-align: left; }
th, td { border: 0.6pt solid #b9c6d3; padding: 2.5pt 4pt; vertical-align: top; }
tbody tr:nth-child(even) td { background: #fafbfc; }
hr { border: none; border-top: 0.6pt solid #c8d0d8; margin: 10pt 0; }
figure { margin: 10pt 0 12pt; page-break-inside: avoid; text-align: center; }
figure img { max-width: 100%; max-height: 205mm; border: 0.5pt solid #e1e5ea; }
figcaption { font-size: 8.4pt; color: #444; margin-top: 3pt; text-align: left; }
.cover { border-left: 5pt solid #0b3d6b; padding: 4pt 0 4pt 10pt; margin-bottom: 10pt; }
.note { font-size: 8.4pt; color: #555; }
"""


def inline(t: str) -> str:
    """Code spans first (as placeholders), then bold / italic / links over the whole text, so bold may
    wrap a code span."""
    t = t.replace("\\*", "\x00STAR\x00").replace("\\|", "\x00PIPE\x00")
    codes = []

    def keep(m):
        codes.append("<code>" + html.escape(m.group(1)) + "</code>")
        return f"\x00C{len(codes) - 1}\x00"
    t = re.sub(r"`([^`]+)`", keep, t)
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<em>\1</em>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\x00C(\d+)\x00", lambda m: codes[int(m.group(1))], t)
    return t.replace("\x00STAR\x00", "*").replace("\x00PIPE\x00", "|")


def table(lines: list[str]) -> str:
    def cells(l):
        l = l.strip().replace("\\|", "\x00PIPE\x00")
        if l.startswith("|"):
            l = l[1:]
        if l.endswith("|"):
            l = l[:-1]
        return [c.strip().replace("\x00PIPE\x00", "\\|") for c in l.split("|")]
    rows = [cells(l) for l in lines]
    head, body = rows[0], [r for r in rows[1:] if not all(re.fullmatch(r":?-{2,}:?", c or "--") for c in r)]
    h = "<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
    for r in body:
        h += "<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>"
    return h + "</tbody></table>"


def find_fig(stem: str) -> Path:
    for d in FIG_DIRS:
        p = d / f"{stem}.png"
        if p.exists():
            return p
    raise SystemExit(f"figure {stem}.png not found in {FIG_DIRS}")


class Doc:
    def __init__(self):
        self.out: list[str] = []
        self.para: list[str] = []
        self.para_li = False                       # the paragraph is a list item's first text
        self.stack: list[dict] = []                # open lists: indent, tag
        self.pending_figs: list = []
        self.fig_no = 0

    def flush(self):
        if self.para:
            text = inline(" ".join(s.strip() for s in self.para))
            self.out.append(text if self.para_li else f"<p>{text}</p>")
        self.para, self.para_li = [], False

    def close_lists(self, to_indent: int = -1):
        while self.stack and self.stack[-1]["indent"] > to_indent:
            top = self.stack.pop()
            self.out.append(f"</li></{top['tag']}>")

    def emit_figs(self):
        for stem, cap in self.pending_figs:
            self.fig_no += 1
            p = find_fig(stem)
            self.out.append(f'<figure><img src="{p.as_uri()}" alt="{html.escape(stem)}">'
                            f"<figcaption><strong>Figure {self.fig_no}.</strong> {inline(cap)}</figcaption></figure>")
        self.pending_figs = []

    def render(self, md: str) -> str:
        lines = md.splitlines()
        i, blank = 0, False
        while i < len(lines):
            line = lines[i]
            ind = len(line) - len(line.lstrip())
            s = line.strip()
            if s.startswith("```"):
                self.flush(); self.close_lists()
                code = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith("```"):
                    code.append(lines[i]); i += 1
                self.out.append("<pre><code>" + html.escape("\n".join(code)) + "</code></pre>")
                i += 1; blank = False
                continue
            if not s:
                self.flush(); blank = True; i += 1
                continue
            if s.startswith("|"):
                self.flush()
                if self.stack and blank and ind < self.stack[-1]["indent"] + 2:
                    self.close_lists(ind - 1)
                rows = []
                while i < len(lines) and lines[i].strip().startswith("|"):
                    rows.append(lines[i]); i += 1
                self.out.append(table(rows)); blank = False
                continue
            m = re.match(r"^(#{1,4})\s+(.*)$", s)
            if m and ind == 0:
                self.flush(); self.close_lists(); self.emit_figs()
                level, text = len(m.group(1)), m.group(2)
                key = re.match(r"^(\d+\.\d*)", text)
                k = key.group(1) if key else None
                if k and k.endswith(".") is False and k not in FIGS and k.rstrip("0123456789").endswith("."):
                    pass
                self.pending_figs = list(FIGS.get(k, [])) if k else []
                cls = ' class="major"' if level == 2 and re.match(r"^(4|5|6|7|8|9|10|11|12|16|17|19)\.", text) else ""
                self.out.append(f"<h{level}{cls}>{inline(text)}</h{level}>")
                i += 1; blank = False
                continue
            if re.fullmatch(r"-{3,}", s) and ind == 0:
                self.flush(); self.close_lists(); self.out.append("<hr>")
                i += 1; blank = False
                continue
            m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)$", line)
            if m:
                self.flush()
                ind, tag = len(m.group(1)), ("ol" if m.group(2)[0].isdigit() else "ul")
                self.close_lists(ind)
                if self.stack and self.stack[-1]["indent"] == ind:
                    if self.stack[-1]["tag"] == tag:
                        self.out.append("</li><li>")
                    else:
                        self.close_lists(ind - 1)
                        self.out.append(f"<{tag}><li>"); self.stack.append({"indent": ind, "tag": tag})
                else:
                    start = m.group(2)[:-1] if tag == "ol" else None
                    self.out.append(f"<{tag}" + (f' start="{start}"' if start and start != "1" else "") + "><li>")
                    self.stack.append({"indent": ind, "tag": tag})
                self.para, self.para_li = [m.group(3)], True
                i += 1; blank = False
                continue
            # plain text: a list item's continuation, or a paragraph
            if self.stack and (ind == 0 and blank):
                self.flush(); self.close_lists()
            elif self.stack and blank:
                self.flush()                       # a new paragraph inside the item
            self.para.append(s)
            i += 1; blank = False
        self.flush(); self.close_lists(); self.emit_figs()
        return "\n".join(self.out)


def main() -> int:
    md = SRC.read_text()
    title, rest = md.split("\n", 1)
    body = Doc().render(rest)
    doc = (f"<!doctype html><html><head><meta charset='utf-8'><title>FieldMind research record</title>"
           f"<style>{CSS}</style></head><body><div class='cover'><h1>{inline(title.lstrip('# '))}</h1>"
           f"<div class='note'>Generated from <code>reports/fieldmind_research_dossier.md</code> with the board-run "
           f"figures from <code>ppt_handoff/</code>. All plant data synthetic; energy not measured.</div></div>"
           f"{body}</body></html>")
    tmp = ROOT / "reports/.fieldmind_research_dossier.html"
    tmp.write_text(doc)
    chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
    if not chrome:
        raise SystemExit("google-chrome not found")
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox", "--allow-file-access-from-files",
           "--no-pdf-header-footer", "--print-to-pdf-no-header", f"--print-to-pdf={OUT_PDF}", tmp.as_uri()]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    tmp.unlink(missing_ok=True)
    if not OUT_PDF.exists():
        print(r.stdout[-2000:], r.stderr[-2000:], file=sys.stderr)
        return 1
    n = sum(len(v) for v in FIGS.values())
    print(f"wrote {OUT_PDF.relative_to(ROOT)} ({OUT_PDF.stat().st_size / 1e6:.1f} MB, {n} figures)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
