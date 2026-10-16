"""Check frozen native windows without showing them or using real HIS."""
import os
from pathlib import Path
import subprocess
import time
from pywinauto import Desktop

root = Path(__file__).resolve().parents[1]
for name, title in (("HIS-Auto-Assistant","HIS Auto Assistant"),("HIS-Simulator","HIS Simulator")):
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    env = dict(os.environ)
    env.pop("QT_QPA_PLATFORM", None)
    process = subprocess.Popen([str(root/"dist"/name/(name+".exe"))],startupinfo=startup,env=env)
    try:
        deadline = time.monotonic()+20
        found = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"{name} exited early: {process.returncode}")
            windows = [w for w in Desktop(backend="win32").windows(visible_only=False)
                       if w.element_info.process_id == process.pid and title in w.window_text()]
            if windows:
                found = windows[0]
                break
            time.sleep(.2)
        if found is None:
            raise RuntimeError(f"{name} did not create its native window")
        found.post_message(0x10)  # WM_CLOSE; no forced kill on the successful path.
        if process.wait(timeout=10) != 0:
            raise RuntimeError(f"{name} did not exit cleanly")
        print(f"PASS {name}: native window created and closed cleanly")
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)
