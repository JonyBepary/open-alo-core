"""
Window management utilities for Wayland/GNOME

Provides window activation and listing via GNOME Shell D-Bus interface.
"""

import subprocess
from typing import Optional, List, Dict


def activate_window(window_title: str, timeout: int = 5) -> bool:
    """
    Activate (focus) a window by title using GNOME Shell D-Bus
    
    Args:
        window_title: Part of window title to match
        timeout: Command timeout in seconds
    
    Returns:
        True if activation succeeded, False otherwise
    
    Example:
        >>> activate_window("Text Editor")
        >>> activate_window("Brave")
    """
    try:
        cmd = [
            'gdbus', 'call', '--session',
            '--dest', 'org.gnome.Shell',
            '--object-path', '/org/gnome/Shell',
            '--method', 'org.gnome.Shell.Eval',
            f'global.get_window_actors().find(w => w.get_meta_window().get_title().includes("{window_title}"))?.get_meta_window().activate(0)'
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return result.returncode == 0
    except Exception:
        return False


def list_windows() -> List[Dict[str, str]]:
    """
    List all open windows
    
    Returns:
        List of dicts with 'title' and 'id' keys
    
    Example:
        >>> windows = list_windows()
        >>> for w in windows:
        ...     print(f"{w['title']} (ID: {w['id']})")
    """
    try:
        cmd = [
            'gdbus', 'call', '--session',
            '--dest', 'org.gnome.Shell',
            '--object-path', '/org/gnome/Shell',
            '--method', 'org.gnome.Shell.Eval',
            'JSON.stringify(global.get_window_actors().map(w => ({title: w.get_meta_window().get_title(), id: w.get_meta_window().get_id()})))'
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Parse the output (it's wrapped in GNOME Shell response format)
            import json
            # Output format: (true, '["..."]')
            output = result.stdout.strip()
            if output.startswith('(true,'):
                json_str = output[7:-1].strip().strip("'")
                return json.loads(json_str)
    except Exception:
        pass
    return []


def find_window(window_title: str) -> Optional[Dict[str, str]]:
    """
    Find a window by title
    
    Args:
        window_title: Part of window title to match
    
    Returns:
        Dict with 'title' and 'id', or None if not found
    
    Example:
        >>> window = find_window("Brave")
        >>> if window:
        ...     print(f"Found: {window['title']}")
    """
    windows = list_windows()
    for window in windows:
        if window_title.lower() in window['title'].lower():
            return window
    return None
