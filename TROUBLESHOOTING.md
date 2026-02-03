# Troubleshooting Guide

## Common Issues

### "No such method SelectSources"

**Cause:** Incorrect D-Bus interface used for source selection.

**Solution:** Fixed in v0.1.0. The RemoteDesktop portal inherits from ScreenCast and `SelectSources` must be called on the ScreenCast interface path, not RemoteDesktop.

If you encounter this, ensure you're using `open-alo-core >= 0.1.0`.

---

### "Failed to initialize"

**Symptoms:** `initialize()` returns `False` or raises `SessionError`.

**Possible Causes:**

1. **Not running on Wayland**
   ```bash
   echo $XDG_SESSION_TYPE
   # Should output: wayland
   ```

2. **XDG Desktop Portal not installed**
   ```bash
   # Ubuntu/Debian
   sudo apt install xdg-desktop-portal xdg-desktop-portal-gnome

   # Verify portal is running
   systemctl --user status xdg-desktop-portal
   ```

3. **User denied permission**
   - Check portal logs: `journalctl --user -u xdg-desktop-portal -n 50`
   - Re-run application to see permission dialog again

4. **Portal backend mismatch**
   ```bash
   # For GNOME
   ls /usr/share/xdg-desktop-portal/portals/gnome.portal

   # For KDE
   ls /usr/share/xdg-desktop-portal/portals/kde.portal
   ```

---

### "cannot unpack non-iterable NoneType" on `get_screen_size()`

**Cause:** Screen capture not initialized.

**Solution:** Ensure `enable_capture=True` when calling `initialize()`:

```python
remote.initialize(persist_mode=2, enable_capture=True)
```

---

### Typed text not appearing

**Symptoms:** `type_text()` executes but nothing appears in the target window.

**Solutions:**

1. **Ensure window is focused**
   ```python
   wm = WindowManager()
   window = wm.find_window("TextEditor")
   wm.activate(window.id)
   time.sleep(0.3)  # Wait for window activation
   remote.type_text("Hello")
   ```

2. **Slow down typing speed**
   ```python
   remote.type_text("Hello", interval=0.1)  # 100ms between keystrokes
   ```

3. **Check keyboard layout**
   - Ensure system keyboard layout matches expected input
   - Special characters may require specific layouts

---

### Screenshot is blank or black

**Cause:** Portal doesn't have screen access or compositor issue.

**Solutions:**

1. **Check portal permissions**
   ```bash
   # For Flatpak apps
   flatpak permissions | grep desktop-portal

   # Reset permissions
   flatpak permission-reset
   ```

2. **Verify PipeWire is running**
   ```bash
   systemctl --user status pipewire
   ```

3. **Test with portal test tool**
   ```bash
   # GNOME
   gnome-screenshot -i
   ```

4. **Check compositor support**
   - GNOME Shell: Should work on 40+
   - KDE Plasma: Requires 5.20+
   - Sway: Requires xdg-desktop-portal-wlr

---

### Mouse clicks not registering

**Symptoms:** `click()` executes but nothing happens.

**Solutions:**

1. **Verify coordinates are correct**
   ```python
   width, height = remote.get_screen_size()
   print(f"Screen: {width}x{height}")

   # Ensure click coordinates are within bounds
   remote.click(Point(100, 100))  # Top-left corner
   ```

2. **Check if input permission was granted**
   - Re-run application and approve the permission dialog
   - Look for "Input control" in the permission dialog

3. **Test with simple action**
   ```python
   # Click center of screen
   w, h = remote.get_screen_size()
   remote.click(Point(w // 2, h // 2))
   ```

---

### "GStreamer pipeline failed"

**Cause:** Missing GStreamer plugins or PipeWire issues.

**Solutions:**

1. **Install required plugins**
   ```bash
   sudo apt install \
       gstreamer1.0-pipewire \
       gstreamer1.0-plugins-base \
       gstreamer1.0-plugins-good
   ```

2. **Verify PipeWire**
   ```bash
   # Check PipeWire is running
   pw-cli info all

   # Restart if needed
   systemctl --user restart pipewire pipewire-pulse
   ```

3. **Enable debug logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)

   remote = UnifiedRemoteDesktop()
   remote.initialize(persist_mode=2, enable_capture=True)
   ```

---

### Window management not working

**Symptoms:** `WindowManager` methods fail or return empty results.

**Solutions:**

1. **Install Window Calls extension (GNOME only)**
   ```bash
   # From browser
   # Visit: https://extensions.gnome.org/extension/4724/window-calls/

   # Enable extension
   gnome-extensions enable window-calls@domandoman.github.com

   # Verify it's active
   gnome-extensions list --enabled | grep window-calls
   ```

2. **Check D-Bus interface**
   ```bash
   gdbus introspect --session \
       --dest org.gnome.Shell \
       --object-path /org/gnome/Shell/Extensions/WindowCalls
   ```

3. **KDE/Other DEs**
   - Window management currently only supports GNOME
   - KDE support is planned for future releases

---

### Performance Issues

**Symptoms:** High CPU usage, lag, or frame drops.

**Solutions:**

1. **Reduce frame capture frequency**
   ```python
   # Instead of continuous capture
   while True:
       frame = remote.get_frame()
       time.sleep(0.1)  # 10 FPS instead of max speed
   ```

2. **Use screenshots instead of frames**
   ```python
   # For static analysis
   screenshot = remote.capture_screenshot()  # Lower overhead
   ```

3. **Close session when done**
   ```python
   with UnifiedRemoteDesktop() as remote:
       # Use context manager for automatic cleanup
       remote.initialize(persist_mode=2, enable_capture=True)
       # ... work ...
   # Session closed automatically
   ```

---

### Anaconda/Conda Compatibility Issues

**Symptoms:** `ImportError: undefined symbol: g_once_init_leave_pointer`

**Cause:** Anaconda's PyGObject conflicts with system GLib libraries.

**Solutions:**

1. **Use system Python**
   ```bash
   /usr/bin/python3 -m pip install --user open-alo-core
   /usr/bin/python3 your_script.py
   ```

2. **Deactivate conda**
   ```bash
   conda deactivate
   python3 your_script.py
   ```

3. **Use PYTHONPATH with system packages**
   ```bash
   PYTHONPATH="$PWD/src:$PYTHONPATH" /usr/bin/python3 your_script.py
   ```

---

## Getting Help

If none of these solutions work:

1. **Enable debug logging**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check system logs**
   ```bash
   journalctl --user -u xdg-desktop-portal -f
   ```

3. **File an issue**
   - Visit: https://github.com/JonyBepary/Open-ALO/issues
   - Include: OS version, desktop environment, error messages, debug logs

---

**Last Updated:** February 2026
