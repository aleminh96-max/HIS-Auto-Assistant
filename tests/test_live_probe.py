"""No raw HIS field values may reach the exported UIA inventory."""
from his_auto.live_probe import safe_caption, safe_control_type, safe_geometry


class Rectangle:
    def __init__(self, left, top, right, bottom):
        self.left, self.top, self.right, self.bottom = left, top, right, bottom


def test_only_allowlisted_static_captions():
    assert safe_caption("  Xác nhận   ký số ") == "Xác nhận ký số"
    assert safe_caption("BA Nội trú - Ngoại Trú") == "BA Nội trú - Ngoại Trú"
    assert safe_caption("Nguyễn Văn A") is None
    assert safe_caption("Mã bệnh nhân: BN001") is None
    assert safe_caption("Bệnh ổn, họ tên Nguyễn Văn A") is None
    assert safe_caption(None) is None


def test_type_never_passes_arbitrary_text():
    assert safe_control_type("Button") == "Button"
    assert safe_control_type("Hospital patient Nguyễn Văn A") == "Other"


def test_geometry_is_relative_to_own_window():
    parent = Rectangle(400, 300, 1400, 800)
    item = Rectangle(650, 400, 850, 450)
    assert safe_geometry(item, parent) == {"x": 0.25, "y": 0.2, "w": 0.2, "h": 0.1}
