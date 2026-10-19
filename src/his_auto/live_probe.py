"""Read-only eHospital UIA inventory.

No mouse/keyboard input, screenshots, raw window titles, clinical values, credentials,
or arbitrary UIA text are persisted. Only exact allowlisted interface captions
are included, with control types and window-relative geometry.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import unicodedata

# Only static HIS user-interface labels, never names/identifiers from records.
SAFE_CAPTIONS = (
    "QLBA Nội Trú - Ngoại Trú",
    "BA Nội trú - Ngoại Trú",
    "Khoa Điều trị Nội trú ban ngày",
    "Chẩn đoán",
    "Tổng kết Bệnh án",
    "Tình trạng ra viện",
    "Tình trạng người bệnh ra viện",
    "Đăng ký dịch vụ",
    "Công chích STD",
    "Test lẫy da",
    "Phiếu theo dõi điều trị",
    "Phiếu lĩnh dược",
    "Tổng Hợp Y Lệnh",
    "Chọn y lệnh",
    "In phiếu theo dõi điều trị",
    "In phiếu công khai thuốc",
    "Xác nhận ký số",
    "Xem ký số",
    "Chọn In",
    "Không tính tiền",
    "Cấp thuốc",
    "Mua ngoài",
    "Nơi nhận thuốc",
    "Nơi sẽ giao",
    "Sửa",
    "Thêm",
    "Lưu",
    "Đóng",
    "Đồng ý",
    "In",
    "Print Report",
)
SAFE_TYPES = {
    "Button", "CheckBox", "ComboBox", "DataGrid", "DataItem",
    "Edit", "Group", "List", "ListItem", "Menu", "MenuItem",
    "Pane", "RadioButton", "ScrollBar", "Tab", "TabItem",
    "Table", "Text", "Tree", "TreeItem", "Window",
}


def _key(value: str) -> str:
    return unicodedata.normalize("NFC", " ".join(value.split())).casefold()


SAFE_LABEL_MAP = {_key(label): label for label in SAFE_CAPTIONS}


def safe_caption(value: str | None) -> str | None:
    """Accept only exact static labels. Never log arbitrary UI text."""
    if not isinstance(value, str):
        return None
    return SAFE_LABEL_MAP.get(_key(value))


def safe_control_type(value: str | None) -> str:
    return value if value in SAFE_TYPES else "Other"


def safe_geometry(control_rect, parent_rect):
    """Return window-relative bounds; no screen coordinates are exported."""
    try:
        width = max(1, parent_rect.right - parent_rect.left)
        height = max(1, parent_rect.bottom - parent_rect.top)
        return {
            "x": round((control_rect.left - parent_rect.left) / width, 4),
            "y": round((control_rect.top - parent_rect.top) / height, 4),
            "w": round((control_rect.right - control_rect.left) / width, 4),
            "h": round((control_rect.bottom - control_rect.top) / height, 4),
        }
    except Exception:
        return None


def inspect_ehospital(max_windows: int = 8, max_labels: int = 80) -> dict:
    if platform.system() != "Windows":
        raise RuntimeError("Chỉ hỗ trợ Windows.")
    # Import only on Windows, so pure sanitization tests work on CI elsewhere.
    from pywinauto import Desktop
    from his_auto.recognition import detect_his

    matches = detect_his()[:max_windows]
    summary = {
        "schema": 1,
        "mode": "READ_ONLY",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "windows_detected": len(matches),
        "windows": [],
        "note": "Không chứa tiêu đề cửa sổ, tên BN, hồ sơ, thuốc, text nhập, hoặc ảnh.",
    }
    desktop = Desktop(backend="uia")
    for window_info in matches:
        window_result = {
            "controls_by_type": {},
            "static_labels": [],
            "inspection_status": "OK",
        }
        try:
            window = desktop.window(handle=window_info["handle"])
            rect = window.rectangle()
            window_result["window_size"] = {
                "width": max(0, rect.right - rect.left),
                "height": max(0, rect.bottom - rect.top),
            }
            counts = Counter()
            for control in window.descendants():
                try:
                    ctl_type = safe_control_type(control.element_info.control_type)
                    counts[ctl_type] += 1
                    if len(window_result["static_labels"]) >= max_labels:
                        continue
                    label = safe_caption(control.window_text())
                    if not label or not control.is_visible():
                        continue
                    window_result["static_labels"].append({
                        "label": label,
                        "control_type": ctl_type,
                        "enabled": bool(control.is_enabled()),
                        "geometry_relative": safe_geometry(control.rectangle(), rect),
                    })
                except Exception:
                    # Never include exception messages: they can contain UI text.
                    continue
            window_result["controls_by_type"] = dict(sorted(counts.items()))
        except Exception:
            window_result["inspection_status"] = "UNAVAILABLE"
        summary["windows"].append(window_result)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Khảo sát UIA eHospital, chỉ đọc và loại bỏ thông tin bệnh nhân")
    parser.add_argument("--out", type=Path, help="Đường dẫn JSON. Mặc định lưu vào LOCALAPPDATA ngoài repository.")
    args = parser.parse_args()
    path = args.out or (Path(os.getenv("LOCALAPPDATA") or Path.home()) / "HISAutoAssistant" / "ehospital-uia-safe.json")
    try:
        data = inspect_ehospital()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Đã tạo báo cáo chỉ đọc: {path}")
        print(f"Số cửa sổ eHospital nhận diện: {data['windows_detected']}")
        print("Chỉ chia sẻ báo cáo sau khi bộ phận CNTT kiểm tra.")
        return 0
    except Exception:
        # Do not expose raw Windows/UIA errors that may include clinical text.
        print("Không thể khảo sát eHospital. Kiểm tra máy, quyền và cài đặt pywinauto.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
