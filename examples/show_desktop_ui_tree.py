#!/usr/bin/env python3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


from open_alo_core import UnifiedRemoteDesktop, WindowManager

with UnifiedRemoteDesktop() as remote:
    remote.initialize(persist_mode=2, enable_capture=True)

    wm = WindowManager()
    windows = wm.list_windows()

    print("\n=== Desktop UI Tree ===\n")
    print(f"Screen Size: {remote.get_screen_size()}")
    print(f"\nTotal Windows: {len(windows)}\n")

    for i, win in enumerate(windows, 1):
        frame = wm.get_frame_rect(win.id) or {}
        x = frame.get("x", win.x)
        y = frame.get("y", win.y)
        width = frame.get("width", win.width)
        height = frame.get("height", win.height)

        print(f"{i}. {win.title}")
        print(f"   ID: {win.id}")
        print(f"   App: {win.wm_class}")
        print(f"   Position: ({x}, {y})")
        print(f"   Size: {width}x{height}")
        print(f"   Workspace: {win.workspace}")
        print()
