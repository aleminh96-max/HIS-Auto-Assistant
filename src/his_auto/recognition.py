"""Read-only Windows inspection and recognition primitives. No live write path."""
from dataclasses import asdict, dataclass
import hashlib
import json
import platform
from pathlib import Path
from .domain import SafetyError


def detect_his():
    if platform.system() != "Windows":
        return []
    from pywinauto import Desktop
    import win32process
    import ctypes
    results = []
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.QueryFullProcessImageNameW.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    for window in Desktop(backend="uia").windows():
        try:
            _, pid = win32process.GetWindowThreadProcessId(window.handle)
            handle = kernel.OpenProcess(0x1000, False, pid)
            if not handle:
                continue
            try:
                name = ctypes.create_unicode_buffer(32768)
                size = ctypes.c_uint32(len(name))
                if kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)) and Path(name.value).name.lower() == "ehospital.exe":
                    results.append({"pid": pid, "handle": window.handle, "title": window.window_text()})
            finally:
                kernel.CloseHandle(handle)
        except Exception:
            continue
    return results


def unique_control(window, automation_id, control_type):
    matches = [c for c in window.descendants(control_type=control_type)
               if c.element_info.automation_id == automation_id and c.is_visible() and c.is_enabled()]
    if len(matches) != 1:
        raise SafetyError("Điều khiển không tồn tại hoặc không duy nhất; dừng nhận diện.")
    return matches[0]


def match_image(image, template, threshold=0.95):
    import cv2
    if not 0 < threshold <= 1 or image is None or template is None:
        raise SafetyError("Thiếu ảnh / ngưỡng nhận diện không hợp lệ.")
    if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1] or template.std() < 1:
        raise SafetyError("Mẫu ảnh không hợp lệ.")
    scores = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, point = cv2.minMaxLoc(scores)
    if score < threshold:
        raise SafetyError("Độ tin cậy ảnh thấp; không nhấp thử.")
    # Suppress the winning neighborhood, then reject another plausible match.
    x, y = point
    h, w = template.shape[:2]
    scores[max(0,y-h//2):y+h//2+1, max(0,x-w//2):x+w//2+1] = -1
    if cv2.minMaxLoc(scores)[1] >= threshold:
        raise SafetyError("Có nhiều vị trí ảnh phù hợp.")
    return point, float(score)


@dataclass(frozen=True)
class Calibration:
    device: str
    width: int
    height: int
    dpi: float
    ui_signature: str
    anchors: dict
    schema: int = 1

    def validate(self, device, width, height, dpi, ui_signature):
        if self.schema != 1 or (self.device, self.width, self.height, self.dpi, self.ui_signature) != (device,width,height,dpi,ui_signature):
            raise SafetyError("Cấu hình máy / DPI / giao diện đã đổi. Cần hiệu chỉnh lại.")
        for point in self.anchors.values():
            if len(point) != 2 or any(not 0 <= n <= 1 for n in point):
                raise SafetyError("Mốc hiệu chỉnh phải là tọa độ tương đối.")

    def point(self, name, rect):
        x, y = self.anchors[name]
        left, top, width, height = rect
        return round(left + x*width), round(top + y*height)

    def save(self, path):
        self.validate(self.device, self.width, self.height, self.dpi, self.ui_signature)
        Path(path).write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")


class LiveAdapter:
    def __init__(self):
        raise SafetyError("Tích hợp ghi HIS thật đang khóa: chưa có ánh xạ UI và biên bản nghiệm thu tại bệnh viện.")
