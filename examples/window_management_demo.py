#!/usr/bin/env python3
"""
Comprehensive Window Management Example

Demonstrates all window management capabilities:
- Listing and finding windows
- Window activation
- Window state management (maximize, minimize, etc.)
- Window positioning and resizing
- Workspace management
"""
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'open_alo_core', 'src'))

from open_alo_core import WindowManager, WindowInfo, activate_window, get_focused_window

def main():
    print("=== OPEN_ALO Window Management Demo ===\n")

    # Initialize WindowManager
    wm = WindowManager()

    # 1. List all windows
    print("1. All Windows:")
    print("-" * 60)
    windows = wm.list_windows()
    for i, win in enumerate(windows[:10], 1):  # Show first 10
        focus_mark = "🎯" if win.focus else "  "
        print(f"{focus_mark} {i}. {win.wm_class[:30]:<30} | {win.title[:40]}")
    print(f"\nTotal: {len(windows)} windows\n")

    # 2. Current workspace windows only
    print("2. Current Workspace Windows:")
    print("-" * 60)
    current_windows = wm.list_windows(current_workspace_only=True)
    for win in current_windows[:5]:
        print(f"   {win.wm_class} - {win.title[:50]}")
    print()

    # 3. Get focused window
    print("3. Currently Focused Window:")
    print("-" * 60)
    focused = wm.get_focused_window()
    if focused:
        print(f"   Class: {focused.wm_class}")
        print(f"   Title: {focused.title}")
        print(f"   Position: ({focused.x}, {focused.y})")
        print(f"   Size: {focused.width}x{focused.height}")
        print(f"   Workspace: {focused.workspace}")
    print()

    # 4. Find specific window
    print("4. Finding Windows:")
    print("-" * 60)

    # Try to find common applications
    search_terms = ["text-editor", "nautilus", "terminal", "code", "brave"]
    found_windows = []

    for term in search_terms:
        win = wm.find_window(term)
        if win:
            found_windows.append(win)
            print(f"   ✓ Found: {win.wm_class} - {win.title[:40]}")

    if not found_windows:
        print("   No common apps found. Using first window...")
        found_windows = windows[:1]
    print()

    # 5. Window activation demo
    if found_windows:
        demo_window = found_windows[0]
        print("5. Window Activation Demo:")
        print("-" * 60)
        print(f"   Activating: {demo_window.wm_class}")

        if wm.activate(demo_window.id):
            print("   ✅ Window activated")
            time.sleep(1)
        else:
            print("   ❌ Failed to activate")
        print()

        # 6. Window state management
        print("6. Window State Management:")
        print("-" * 60)

        # Get detailed info
        details = wm.get_details(demo_window.id)
        if details:
            print(f"   Maximized: {details.get('maximized', 0)}")
            print(f"   Can maximize: {details.get('canmaximize', False)}")
            print(f"   Can minimize: {details.get('canminimize', False)}")

        # Demonstrate state changes (uncomment to test)
        # print("\n   Testing maximize...")
        # wm.maximize(demo_window.id)
        # time.sleep(1)
        # wm.unmaximize(demo_window.id)
        print()

        # 7. Window positioning
        print("7. Window Positioning Info:")
        print("-" * 60)
        frame = wm.get_frame_rect(demo_window.id)
        if frame:
            print(f"   Frame: {frame}")

        # Demonstrate positioning (uncomment to test)
        # print("\n   Moving window to (100, 100)...")
        # wm.move(demo_window.id, 100, 100)
        # time.sleep(1)

        # print("   Resizing to 800x600...")
        # wm.resize(demo_window.id, 800, 600)
        print()

    # 8. Convenience functions
    print("8. Convenience Functions:")
    print("-" * 60)

    # Simple activation by name
    print("   Using activate_window('text-editor')...")
    result = activate_window("org.gnome.TextEditor")
    print(f"   Result: {'✅ Success' if result else '❌ Not found'}")

    # Get focused window again
    focused = get_focused_window()
    if focused:
        print(f"   Focused: {focused.wm_class}")
    print()

    # 9. Summary of all available methods
    print("9. Available WindowManager Methods:")
    print("-" * 60)
    methods = [
        "Listing & Search:",
        "  • list_windows(current_workspace_only=False)",
        "  • find_window(query, match_title=True)",
        "  • find_all_windows(query, match_title=True)",
        "  • get_focused_window()",
        "  • get_details(window_id)",
        "  • get_title(window_id)",
        "",
        "State Management:",
        "  • activate(window_id)",
        "  • maximize(window_id)",
        "  • unmaximize(window_id)",
        "  • minimize(window_id)",
        "  • unminimize(window_id)",
        "  • close(window_id)",
        "",
        "Positioning:",
        "  • move(window_id, x, y)",
        "  • resize(window_id, width, height)",
        "  • move_resize(window_id, x, y, width, height)",
        "  • get_frame_rect(window_id)",
        "  • get_frame_bounds(window_id)",
        "",
        "Workspace:",
        "  • move_to_workspace(window_id, workspace_num)",
    ]
    for line in methods:
        print(f"   {line}")

    print("\n✅ Demo complete!\n")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(f"❌ Error: {e}")
        print("\nMake sure Window Calls extension is installed:")
        print("https://extensions.gnome.org/extension/4724/window-calls/")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
        sys.exit(0)
