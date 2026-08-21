#!/usr/bin/env python3
"""
AT-SPI recall probe — task-sliced usability check for harness planning.

Walks every element that a target task needs to click/type into and
reports whether AT-SPI gives a usable (role, name, bbox).

Usage:
  python tools/recall_probe.py --apps Nautilus papers Brave --depth 12
  python tools/recall_probe.py --tasks tasks.json   # task-sliced mode
  python tools/recall_probe.py --apps Nautilus --json out.json --csv out.csv

Exit 0 = all queried apps found; non-zero = probe infra failed (not recall low).
Recall <70% is reported but does NOT fail the process — the harness decides
vision-primary vs hybrid per-task.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

try:
    import gi
    gi.require_version("Atspi", "2.0")
    from gi.repository import Atspi  # type: ignore
except Exception as e:  # pragma: no cover
    print(f"AT-SPI unavailable: {e}", file=sys.stderr)
    sys.exit(2)

OFFSCREEN_SENTINEL = -2147483648
ACTIONABLE_ROLES = {
    "push button", "toggle button", "menu", "menu item", "entry", "text",
    "document frame", "combo box", "check box", "radio button", "link",
    "list item", "page tab", "slider", "spin button", "table cell",
}

@dataclass
class NodeReport:
    depth: int
    role: str
    name: str
    bbox: str
    has_bbox: bool
    visible: bool
    showing: bool
    enabled: bool
    actionable: bool
    usable: bool
    offscreen: bool

@dataclass
class AppReport:
    app: str
    found: bool
    scanned: int
    actionable: int
    usable_visible: int
    has_name: int
    has_bbox: int
    offscreen: int
    recall_usable: float
    verdict: str  # "hybrid-ok" | "vision-primary" | "not-found"
    nodes: List[NodeReport]

def _classify(node, depth: int) -> NodeReport:
    try:
        role = node.get_role_name() or ""
        name = (node.get_name() or "").strip()
        iface = node.get_component_iface()
        has_bbox = False
        bbox = "(no component)"
        offscreen = True
        if iface:
            try:
                ext = iface.get_extents(Atspi.CoordType.SCREEN)
                x, y, w, h = ext.x, ext.y, ext.width, ext.height
                has_bbox = not (w <= 1 and h <= 1) and x != OFFSCREEN_SENTINEL
                bbox = f"({x},{y} {w}x{h})"
                offscreen = not has_bbox
            except Exception:
                pass
        else:
            bbox = "(no component)"
        states = node.get_state_set()
        visible = bool(states and states.contains(Atspi.StateType.VISIBLE))
        showing = bool(states and states.contains(Atspi.StateType.SHOWING))
        enabled = bool(states and states.contains(Atspi.StateType.ENABLED))
        if not has_bbox:
            offscreen = True
        elif not visible:
            offscreen = True
        actionable = role in ACTIONABLE_ROLES
        usable = bool(has_bbox and visible)
        # keep name-less but bbox-visible buttons as usable (icon-only UI)
        # — mirrors browser_tree: 7 unnamed buttons still usable via bbox
        # Name check is reported separately; usable requires bbox+visible only.
        return NodeReport(depth, role, name[:80], bbox, has_bbox, visible, showing, enabled, actionable, usable, offscreen)
    except Exception as e:
        return NodeReport(depth, "ERR", str(e)[:80], "?", False, False, False, False, False, False, True)

def _find_app(name_substr: str):
    d = Atspi.get_desktop(0)
    if not d:
        return None
    needle = name_substr.lower()
    for i in range(d.get_child_count()):
        c = d.get_child_at_index(i)
        if not c:
            continue
        n = (c.get_name() or "").lower()
        # also try application name via Atspi app name
        if needle in n or needle in (c.get_toolkit_name() or "").lower():
            return c
        # Brave reports as "Brave Origin Beta" etc — also match role application children
        try:
            # some apps expose wm_class via description
            desc = (c.get_description() or "").lower()
            if needle in desc:
                return c
        except Exception:
            pass
    return None

def probe_app(app: str, max_nodes: int = 4000, max_depth: int = 20) -> AppReport:
    Atspi.init()
    target = _find_app(app)
    if not target:
        return AppReport(app, False, 0, 0, 0, 0, 0, 0, 0.0, "not-found", [])
    # BFS capped
    q: List[tuple] = [(target, 0)]
    rows: List[NodeReport] = []
    scanned = 0
    head = 0
    while head < len(q) and scanned < max_nodes:
        node, depth = q[head]; head += 1
        scanned += 1
        info = _classify(node, depth)
        # keep actionable + shallow chrome (depth<2) for summary; full tree would be huge for Brave
        if info.actionable or depth < 2:
            rows.append(info)
        if depth >= max_depth:
            continue
        try:
            for j in range(node.get_child_count()):
                ch = node.get_child_at_index(j)
                if ch is not None:
                    q.append((ch, depth + 1))
        except Exception:
            pass
    total_actionable = len(rows)
    usable_visible = sum(1 for r in rows if r.usable and r.visible)
    has_name = sum(1 for r in rows if r.name)
    has_bbox = sum(1 for r in rows if r.has_bbox)
    offscreen = sum(1 for r in rows if r.offscreen)
    recall = usable_visible / max(1, total_actionable)
    verdict = "hybrid-ok" if recall >= 0.70 else "vision-primary"
    if not target:
        verdict = "not-found"
    return AppReport(app, True, scanned, total_actionable, usable_visible, has_name, has_bbox, offscreen, recall, verdict, rows)

def probe_tasks(tasks_path: Path):
    data = json.loads(tasks_path.read_text())
    # tasks.json: {"tasks": [{"id":"nautilus-create-file","app":"Nautilus","elements":[{"role":"push button","name":"New Folder"}]}]}
    # For now, just union per-app
    apps = sorted({t["app"] for t in data.get("tasks", [])})
    return [probe_app(a) for a in apps]

def main() -> int:
    p = argparse.ArgumentParser(description="AT-SPI recall probe for harness planning")
    p.add_argument("--apps", nargs="+", default=[], help="app name substrings (e.g. Nautilus papers Brave)")
    p.add_argument("--tasks", type=Path, help="tasks.json for task-sliced mode")
    p.add_argument("--max-nodes", type=int, default=4000)
    p.add_argument("--max-depth", type=int, default=20)
    p.add_argument("--json", type=Path, help="write full report JSON")
    p.add_argument("--csv", type=Path, help="write per-app summary CSV")
    p.add_argument("--show-nodes", type=int, default=30, help="print top N nodes per app")
    args = p.parse_args()

    if args.tasks:
        reports = probe_tasks(args.tasks)
    elif args.apps:
        reports = [probe_app(a, args.max_nodes, args.max_depth) for a in args.apps]
    else:
        # default demo suite from scope doc
        reports = [probe_app(a, args.max_nodes, args.max_depth) for a in ["Nautilus", "papers", "Brave", "Terminal"]]

    # human table
    print(f"{'app':22s} {'found':5s} {'action':7s} {'usable':7s} {'recall':7s} {'verdict':16s} {'scanned':7s}")
    print("-"*82)
    for r in reports:
        print(f"{r.app:22s} {str(r.found):5s} {r.actionable:7d} {r.usable_visible:7d} {r.recall_usable:6.0%}  {r.verdict:16s} {r.scanned:7d}")
    print()
    for r in reports:
        if not r.found:
            print(f"--- {r.app}: NOT FOUND (is the app running? try --apps with a substring of its AT-SPI name) ---\n")
            continue
        print(f"--- {r.app} top nodes (actionable + shallow chrome) — OK=usable bbox+visible, GAP=missing/offscreen ---")
        for n in r.nodes[: args.show_nodes]:
            mark = "OK " if (n.usable and n.visible and n.has_bbox) else "GAP"
            print(f"  {mark} depth{n.depth}  {n.role:16s}  name={n.name!r:42s}  bbox={n.bbox:22s}  vis={n.visible} en={n.enabled}")
        if r.verdict == "vision-primary":
            print(f"  → VERDICT vision-primary (recall {r.recall_usable:.0%} < 70%): harness must generate vision-grounded trajectory (OCR bbox + patch) for this app; keep a11y as hint only.")
        print()

    if args.json:
        # strip full node lists to keep file small unless --show-nodes == all
        out = [asdict(r) for r in reports]
        args.json.write_text(json.dumps(out, indent=2))
        print(f"Wrote {args.json}")
    if args.csv:
        with args.csv.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["app","found","scanned","actionable","usable_visible","recall_usable","verdict","has_name","has_bbox","offscreen"])
            for r in reports:
                w.writerow([r.app, r.found, r.scanned, r.actionable, r.usable_visible, f"{r.recall_usable:.3f}", r.verdict, r.has_name, r.has_bbox, r.offscreen])
        print(f"Wrote {args.csv}")

    # exit 0 even when vision-primary — that is expected, not infra failure
    # exit 2 only when AT-SPI infra failed
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
