#!/usr/bin/env python3
"""
Advanced Desktop UI Tree with Accessibility Hierarchy

Builds a graph-friendly UI tree with:
- Window-level metadata (id, app, position, size, workspace, monitor hint)
- Element-level accessibility hierarchy (role, name, value, states, geometry)
- Parent/children and semantic relationships (labeled-by, controls, etc.)

Requirements:
- GNOME on Wayland
- Window Calls extension (window metadata)
- AT-SPI Python bindings (typically package: python3-pyatspi)
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from open_alo_core import UnifiedRemoteDesktop, WindowManager

try:
    import pyatspi
except Exception:
    pyatspi = None


@dataclass
class UIElement:
    id: str
    role: str
    name: str
    value: str
    state: Dict[str, bool]
    position: Tuple[int, int]
    size: Tuple[int, int]
    parent_id: str
    children: List[str]
    relationships: Dict[str, str]


def _to_str(value) -> str:
    if value is None:
        return ""
    return str(value)


def _norm_text(value) -> str:
    return _to_str(value).strip().lower()


def _extract_value(node) -> str:
    try:
        value_iface = node.queryValue()
        current = getattr(value_iface, "currentValue", None)
        if current is not None:
            return _to_str(current)
    except Exception:
        pass

    try:
        text_iface = node.queryText()
        count = int(getattr(text_iface, "characterCount", 0))
        if count > 0:
            return _to_str(text_iface.getText(0, min(count, 120)))
    except Exception:
        pass

    return ""


def _extract_state(node) -> Dict[str, bool]:
    names = set()
    try:
        states = node.getState().getStates()
        names = {_to_str(s).lower() for s in states}
    except Exception:
        pass

    def has(token: str) -> bool:
        return any(token in name for name in names)

    return {
        "enabled": has("enabled") or has("sensitive"),
        "visible": has("visible") or has("showing"),
        "focused": has("focused"),
        "checked": has("checked"),
        "editable": has("editable"),
        "selected": has("selected"),
        "expanded": has("expanded"),
    }


def _extract_geometry(node) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    try:
        component = node.queryComponent()
        extents = component.getExtents(pyatspi.DESKTOP_COORDS)
        return (int(extents.x), int(extents.y)), (
            int(extents.width),
            int(extents.height),
        )
    except Exception:
        return (0, 0), (0, 0)


def _rect_intersection_area(
    a: Tuple[int, int, int, int], b: Tuple[int, int, int, int]
) -> int:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return 0

    left = max(ax, bx)
    top = max(ay, by)
    right = min(ax + aw, bx + bw)
    bottom = min(ay + ah, by + bh)

    if right <= left or bottom <= top:
        return 0
    return (right - left) * (bottom - top)


def _extract_relationships(node) -> Dict[str, str]:
    rels: Dict[str, str] = {}
    try:
        relation_set = node.getRelationSet()
    except Exception:
        return rels

    for rel in relation_set:
        try:
            rel_name = _to_str(rel.getRelationType()).lower()
            targets = []
            for idx in range(rel.getNTargets()):
                target = rel.getTarget(idx)
                targets.append(_to_str(getattr(target, "name", "")))
            rels[rel_name] = ", ".join([t for t in targets if t])
        except Exception:
            continue
    return rels


def _traverse_accessibility_tree(
    root, max_depth: int, max_nodes: int
) -> Tuple[Dict[str, UIElement], str]:
    elements: Dict[str, UIElement] = {}
    counter = {"value": 0}

    def walk(node, parent_id: str, depth: int) -> Optional[str]:
        if counter["value"] >= max_nodes:
            return None
        if depth > max_depth:
            return None

        counter["value"] += 1
        element_id = f"el_{counter['value']}"

        role = _to_str(getattr(node, "getRoleName", lambda: "")())
        name = _to_str(getattr(node, "name", ""))
        value = _extract_value(node)
        state = _extract_state(node)
        position, size = _extract_geometry(node)
        relationships = _extract_relationships(node)

        elements[element_id] = UIElement(
            id=element_id,
            role=role,
            name=name,
            value=value,
            state=state,
            position=position,
            size=size,
            parent_id=parent_id,
            children=[],
            relationships=relationships,
        )

        try:
            child_count = int(getattr(node, "childCount", 0))
        except Exception:
            child_count = 0

        for idx in range(child_count):
            if counter["value"] >= max_nodes:
                break
            try:
                child = node.getChildAtIndex(idx)
            except Exception:
                continue
            child_id = walk(child, element_id, depth + 1)
            if child_id:
                elements[element_id].children.append(child_id)

        return element_id

    root_id = walk(root, "", 0) or ""
    return elements, root_id


def _normalize_window_geometry(window, wm: WindowManager) -> Tuple[int, int, int, int]:
    frame = wm.get_frame_rect(window.id) or {}
    x = int(frame.get("x", window.x))
    y = int(frame.get("y", window.y))
    width = int(frame.get("width", window.width))
    height = int(frame.get("height", window.height))
    return x, y, width, height


def _build_monitor_hints(windows: List[Dict]) -> List[Dict]:
    bands: List[Dict] = []
    for win in sorted(windows, key=lambda w: w["x"]):
        left = win["x"]
        right = win["x"] + max(1, win["width"])
        matched = None
        for band in bands:
            overlaps = not (right < band["min_x"] or left > band["max_x"])
            if overlaps:
                matched = band
                break
        if matched is None:
            matched = {"min_x": left, "max_x": right, "windows": 0}
            bands.append(matched)
        else:
            matched["min_x"] = min(matched["min_x"], left)
            matched["max_x"] = max(matched["max_x"], right)
        matched["windows"] += 1

    for idx, band in enumerate(sorted(bands, key=lambda b: b["min_x"])):
        band["monitor_hint"] = idx
    return sorted(bands, key=lambda b: b["min_x"])


def _monitor_for_window(x: int, width: int, bands: List[Dict]) -> int:
    center = x + max(1, width) // 2
    for band in bands:
        if band["min_x"] <= center <= band["max_x"]:
            return int(band["monitor_hint"])
    return 0


def _is_utility_window(win: Dict) -> bool:
    title = _norm_text(win.get("title"))
    wm_class = _norm_text(win.get("wm_class"))
    width = int(win.get("width", 0))
    height = int(win.get("height", 0))

    # Tray/popover/utility windows are often tiny and unnamed.
    if not title and not wm_class and width <= 128 and height <= 128:
        return True

    # Hide very small unnamed windows by default.
    if not title and width <= 32 and height <= 32:
        return True

    return False


def _find_accessible_window_for_desktop_window(
    desktop_window: Dict, desktop_root
) -> Optional[object]:
    window_title = _norm_text(desktop_window.get("title"))
    wm_class = _norm_text(desktop_window.get("wm_class"))

    # If we have no semantic hints, skip matching to avoid random shell/global picks.
    if not window_title and not wm_class:
        return None

    window_rect = (
        int(desktop_window.get("x", 0)),
        int(desktop_window.get("y", 0)),
        int(desktop_window.get("width", 0)),
        int(desktop_window.get("height", 0)),
    )

    best = None
    best_score = -1

    app_count = int(getattr(desktop_root, "childCount", 0))
    for app_idx in range(app_count):
        try:
            app = desktop_root.getChildAtIndex(app_idx)
        except Exception:
            continue

        app_name = _norm_text(getattr(app, "name", ""))
        window_count = int(getattr(app, "childCount", 0))
        for win_idx in range(window_count):
            try:
                candidate = app.getChildAtIndex(win_idx)
            except Exception:
                continue

            acc_name = _norm_text(getattr(candidate, "name", ""))
            role = _norm_text(getattr(candidate, "getRoleName", lambda: "")())

            score = 0
            has_semantic_match = False
            if window_title and acc_name == window_title:
                score += 100
                has_semantic_match = True
            elif window_title and (
                window_title in acc_name or acc_name in window_title
            ):
                score += 55
                has_semantic_match = True

            if wm_class and (wm_class in app_name or app_name in wm_class):
                score += 35
                has_semantic_match = True

            # Weak semantic signal: token overlap between class/title and accessible names.
            if not has_semantic_match:
                semantic_text = f"{window_title} {wm_class}".strip()
                for token in semantic_text.split():
                    if len(token) < 4:
                        continue
                    if token in acc_name or token in app_name:
                        score += 15
                        has_semantic_match = True
                        break

            if "window" in role or "frame" in role:
                score += 5

            try:
                component = candidate.queryComponent()
                extents = component.getExtents(pyatspi.DESKTOP_COORDS)
                acc_rect = (
                    int(extents.x),
                    int(extents.y),
                    int(extents.width),
                    int(extents.height),
                )
                overlap = _rect_intersection_area(window_rect, acc_rect)
                if overlap > 0:
                    score += 40
            except Exception:
                pass

            if not has_semantic_match:
                continue

            if score > best_score:
                best_score = score
                best = candidate

    # Require a meaningful signal to avoid matching shell/root artifacts.
    if best_score < 20:
        return None
    return best


def _print_tree(elements: Dict[str, UIElement], root_id: str, max_lines: int) -> None:
    lines: List[str] = []

    def render(node_id: str, prefix: str, is_last: bool) -> None:
        if node_id not in elements:
            return
        node = elements[node_id]
        marker = "└── " if is_last else "├── "
        label = node.name if node.name else "<unnamed>"
        state_tokens = [k for k, v in node.state.items() if v]
        states = ", ".join(state_tokens) if state_tokens else "none"
        lines.append(
            f"{prefix}{marker}{label} [{node.role}] "
            f"pos={node.position} size={node.size} state={states}"
        )
        child_prefix = f"{prefix}{'    ' if is_last else '│   '}"
        for idx, child_id in enumerate(node.children):
            render(child_id, child_prefix, idx == len(node.children) - 1)

    render(root_id, "", True)

    if len(lines) > max_lines:
        for line in lines[:max_lines]:
            print(line)
        print(f"... truncated {len(lines) - max_lines} more nodes")
    else:
        for line in lines:
            print(line)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Advanced desktop UI tree with accessibility hierarchy"
    )
    parser.add_argument(
        "--all-windows",
        action="store_true",
        help="Traverse accessibility tree for all windows",
    )
    parser.add_argument(
        "--window",
        type=str,
        default=None,
        help="Filter windows by title/class substring or glob (e.g. 'brave*', 'code', 'Telegram')",
    )
    parser.add_argument(
        "--skip-utility",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Skip tiny/unnamed utility windows (default: enabled)",
    )
    parser.add_argument(
        "--max-depth", type=int, default=8, help="Maximum tree depth per window"
    )
    parser.add_argument(
        "--max-nodes", type=int, default=500, help="Maximum nodes per window"
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=160,
        help="Maximum printed tree lines per window",
    )
    parser.add_argument(
        "--json", action="store_true", help="Also print machine-readable JSON summary"
    )
    args = parser.parse_args()

    if pyatspi is None:
        print("❌ AT-SPI Python bindings not found.")
        print("Install package: python3-pyatspi")
        return 1

    wm = WindowManager()

    screen_size = None
    try:
        with UnifiedRemoteDesktop() as remote:
            remote.initialize(persist_mode=2, enable_capture=True)
            screen_size = remote.get_screen_size()
    except Exception as exc:
        print(f"⚠️ Could not initialize capture session for screen size: {exc}")

    windows_raw = wm.list_windows()
    windows: List[Dict] = []
    for win in windows_raw:
        x, y, width, height = _normalize_window_geometry(win, wm)
        windows.append(
            {
                "id": win.id,
                "title": _to_str(win.title),
                "wm_class": _to_str(win.wm_class),
                "workspace": win.workspace,
                "focused": bool(win.focus),
                "x": x,
                "y": y,
                "width": width,
                "height": height,
            }
        )

    monitor_bands = _build_monitor_hints(windows)
    for win in windows:
        win["monitor_hint"] = _monitor_for_window(win["x"], win["width"], monitor_bands)

    total_windows_before_filter = len(windows)
    if args.skip_utility:
        windows = [win for win in windows if not _is_utility_window(win)]

    # Window-level attention: filter by --window substring/glob
    if args.window:
        import fnmatch

        pattern = args.window.strip()

        def matches(win):
            t = _norm_text(win.get("title"))
            c = _norm_text(win.get("wm_class"))
            return (
                fnmatch.fnmatch(t, pattern)
                or fnmatch.fnmatch(c, pattern)
                or pattern in t
                or pattern in c
            )

        windows = [w for w in windows if matches(w)]
        if not windows:
            print(f"No windows matched --window '{pattern}'")
            return 1
    elif not args.all_windows:
        focused = [w for w in windows if w["focused"]]
        if focused:
            windows = focused
        elif windows:
            windows = [windows[0]]

    desktop_root = pyatspi.Registry.getDesktop(0)

    print("\n=== Advanced Desktop UI Tree ===\n")
    print(f"Screen Size: {screen_size}")
    print(f"Monitor Hints: {len(monitor_bands)}")
    for band in monitor_bands:
        print(
            f"  - monitor_hint={band['monitor_hint']} x=[{band['min_x']}, {band['max_x']}] "
            f"windows={band['windows']}"
        )
    if args.skip_utility:
        skipped = total_windows_before_filter - len(windows)
        print(f"Utility Windows Skipped: {skipped}")
    print(f"\nWindows Selected: {len(windows)}\n")

    output_windows = []

    for idx, win in enumerate(windows, 1):
        print(f"Window {idx}: {win['title']}")
        print(f"  ID: {win['id']}")
        print(f"  App: {win['wm_class']}")
        print(f"  Position: ({win['x']}, {win['y']})")
        print(f"  Size: {win['width']}x{win['height']}")
        print(f"  Workspace: {win['workspace']}")
        print(f"  Monitor Hint: {win['monitor_hint']}")
        print(f"  Focused: {win['focused']}")

        acc_window = _find_accessible_window_for_desktop_window(win, desktop_root)
        if acc_window is None:
            print("  Accessibility Tree: not matched\n")
            output_windows.append({"window": win, "root_id": "", "elements": {}})
            continue

        elements, root_id = _traverse_accessibility_tree(
            acc_window,
            max_depth=args.max_depth,
            max_nodes=args.max_nodes,
        )

        print("  Accessibility Tree:")
        _print_tree(elements, root_id, max_lines=args.max_lines)
        print()

        output_windows.append(
            {
                "window": win,
                "root_id": root_id,
                "elements": {k: asdict(v) for k, v in elements.items()},
            }
        )

    if args.json:
        payload = {
            "screen_size": screen_size,
            "monitor_hints": monitor_bands,
            "windows": output_windows,
        }
        print("=== JSON ===")
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
        raise SystemExit(1)
