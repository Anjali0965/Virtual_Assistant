import os
import subprocess
import time
import ctypes
import sys
from pathlib import Path

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    from PIL import ImageGrab
except Exception:
    ImageGrab = None

from config import APP_PATHS


def open_app(name: str):
    key = name.lower()
    path = APP_PATHS.get(key)
    if not path:
        raise ValueError(f"Unknown app: {name}")
    # Expand environment variables like %USERNAME%
    path = os.path.expandvars(path)
    print(f"[debug] Opening app {name} -> {path}")
    try:
        if os.path.exists(path):
            subprocess.Popen([path])
        else:
            # fallback to startfile for apps like explorer
            os.startfile(path)
    except Exception as e:
        print(f"[debug] open_app failed: {e}")


def close_app(exe_name: str):
    # Attempt to close by process name using taskkill
    try:
        subprocess.run(["taskkill", "/F", "/IM", exe_name], check=True)
        print(f"[debug] Closed {exe_name}")
    except subprocess.CalledProcessError as e:
        print(f"[debug] Failed to close {exe_name}: {e}")


def open_folder(path: str):
    path = os.path.expanduser(path)
    print(f"[debug] Opening folder: {path}")
    os.startfile(path)


def shutdown():
    subprocess.Popen(["shutdown", "/s", "/t", "1"])


def restart():
    subprocess.Popen(["shutdown", "/r", "/t", "1"])


def lock():
    try:
        ctypes.windll.user32.LockWorkStation()
    except Exception as e:
        print(f"[debug] Lock failed: {e}")


def sleep():
    # Attempt proper Windows sleep without shutdown or hibernate.
    # Strategy:
    # 1. Try to disable hibernation (powercfg -h off) as a best-effort (may require admin).
    # 2. Call SetSuspendState from powrprof.dll via ctypes with (Hibernate=False, ForceCritical=False, DisableWakeEvent=False).
    # 3. Fallback to rundll32 call if ctypes approach fails.
    try:
        print("[debug] Sleep command starting")
        print("[debug] Calling SetSuspendState via ctypes")
        try:
            # Use the Win32 API directly. Arguments: Hibernate, ForceCritical, DisableWakeEvent
            ctypes.windll.powrprof.SetSuspendState(False, False, False)
            print("[debug] ctypes SetSuspendState call returned")
            return
        except Exception as e:
            print(f"[debug] ctypes SetSuspendState failed: {e}; falling back to rundll32")

        # First rundll32 fallback (standard)
        try:
            res = subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,0,0"], check=False)
            print(f"[debug] rundll32 SetSuspendState fallback exitcode={res.returncode}")
            if res.returncode == 0:
                return
        except Exception as e2:
            print(f"[debug] rundll32 fallback failed: {e2}")

        # Second rundll32 variant using ForceCritical flag — may require admin
        try:
            res = subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], check=False)
            print(f"[debug] rundll32 SetSuspendState (force) exitcode={res.returncode}")
            if res.returncode == 0:
                return
        except Exception as e3:
            print(f"[debug] rundll32 (force) fallback failed: {e3}")

        print("[debug] All sleep methods attempted and did not return success")
    except Exception as e:
        print(f"[debug] Sleep failed: {e}")


def _key_event(vk_code):
    # Simulate media key press for volume control
    try:
        ctypes.windll.user32.keybd_event(vk_code, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(vk_code, 0, 2, 0)
    except Exception as e:
        print(f"[debug] key_event failed: {e}")


def volume_up():
    VK_VOL_UP = 0xAF
    _key_event(VK_VOL_UP)


def volume_down():
    VK_VOL_DOWN = 0xAE
    _key_event(VK_VOL_DOWN)


def mute_toggle():
    VK_MUTE = 0xAD
    _key_event(VK_MUTE)


def type_text(text: str):
    if pyautogui:
        pyautogui.write(text)
    else:
        print(f"[type_text] {text}")


def press_key(key: str):
    if pyautogui:
        pyautogui.press(key)
    else:
        print(f"[press_key] {key}")


def screenshot(path: str = None) -> str:
    """Take a screenshot and save to `path` or the screenshots folder.

    Returns the absolute path where the screenshot was saved, or an empty
    string on failure.
    """
    try:
        # Always save screenshots to the user's Pictures\Screenshots folder
        output_dir = Path(os.path.expanduser(os.path.expandvars(r"C:\Users\Anjali\Pictures\Screenshots")))
        output_dir.mkdir(parents=True, exist_ok=True)
        if not path:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            path = str(output_dir / f"screenshot-{timestamp}.png")
        else:
            # Ensure any provided filename is saved inside the output_dir
            p = Path(path)
            path = str(output_dir / p.name)

        print(f"[debug] Taking screenshot -> {path}")

        # Primary method: pyautogui
        if pyautogui:
            try:
                img = pyautogui.screenshot()
                img.save(path)
                print(f"[debug] Screenshot saved: {path}")
                return path
            except Exception as e:
                print(f"[debug] pyautogui.screenshot failed: {e}")

        # Fallback: Pillow ImageGrab (works on Windows/macOS)
        if ImageGrab:
            try:
                img = ImageGrab.grab()
                img.save(path)
                print(f"[debug] Screenshot saved via ImageGrab: {path}")
                return path
            except Exception as e:
                print(f"[debug] ImageGrab.grab failed: {e}")

        print("[debug] No available screenshot method succeeded")
        return ""
    except Exception as e:
        print(f"[debug] screenshot failed: {e}")
        return ""
