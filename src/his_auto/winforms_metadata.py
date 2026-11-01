"""Read-only native WinForms metadata for authorized eHospital UI mapping.

No user-visible text, control values, images, patient data, or credentials
are read or exported. This does not click, type, sign, or save anything.
"""
from __future__ import annotations

from collections import Counter
import json
import os
from pathlib import Path
import platform
import subprocess


def relative_rect(rect: tuple[int, int, int, int], parent: tuple[int, int, int, int]) -> list[float]:
    w = max(1, parent[2] - parent[0])
    h = max(1, parent[3] - parent[1])
    return [
        round((rect[0] - parent[0]) / w, 4),
        round((rect[1] - parent[1]) / h, 4),
        round((rect[2] - rect[0]) / w, 4),
        round((rect[3] - rect[1]) / h, 4),
    ]


def inspect() -> dict:
    if platform.system() != "Windows":
        raise RuntimeError("Chỉ hỗ trợ Windows.")
    import win32gui
    import win32process

    output = subprocess.check_output(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
         "(Get-Process -Name eHospital -ErrorAction SilentlyContinue).Id"],
        text=True, timeout=8,
    )
    pids = {int(line) for line in output.splitlines() if line.strip().isdigit()}
    windows: list[int] = []

    def enumerate_windows(hwnd, _):
        if (win32process.GetWindowThreadProcessId(hwnd)[1] in pids
                and win32gui.IsWindowVisible(hwnd)
                and win32gui.GetClassName(hwnd).startswith("WindowsForms10.Window.8")):
            windows.append(hwnd)

    win32gui.EnumWindows(enumerate_windows, None)
    entries = []
    for hwnd in windows:
        bounds = win32gui.GetWindowRect(hwnd)
        counts: Counter[str] = Counter()
        visible_edits: list[list[float]] = []

        def enumerate_children(child, _):
            klass = win32gui.GetClassName(child).split(".app.")[0]
            counts[klass] += 1
            if klass.startswith("WindowsForms10.EDIT") and win32gui.IsWindowVisible(child):
                visible_edits.append(relative_rect(win32gui.GetWindowRect(child), bounds))

        win32gui.EnumChildWindows(hwnd, enumerate_children, None)
        entries.append({
            "window_size": [bounds[2] - bounds[0], bounds[3] - bounds[1]],
            "control_type_counts": dict(sorted(counts.items())),
            "visible_edit_count": len(visible_edits),
            "visible_edit_relative_rects": sorted(visible_edits),
        })
    return {
        "schema": 1,
        "mode": "READ_ONLY_METADATA",
        "ehospital_process_count": len(pids),
        "window_count": len(entries),
        "windows": entries,
        "no_patient_text_collected": True,
        "note": "Không xác nhận tên màn hình/khoa/BN chỉ bằng hình học điều khiển.",
    }


def main() -> int:
    try:
        result = inspect()
        folder = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "HISAutoAssistant"
        folder.mkdir(parents=True, exist_ok=True)
        file = folder / "winforms-metadata-only.json"
        file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Process:", result["ehospital_process_count"],
              "| Windows:", result["window_count"])
        for window in result["windows"]:
            print("Size:", window["window_size"],
                  "| Visible edit fields:", window["visible_edit_count"],
                  "| Control types:", window["control_type_counts"])
        print("Saved local report:", file)
        return 0
    except Exception:
        print("Khảo sát chưa hoàn thành; không trích xuất bất kỳ nội dung HIS nào.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
