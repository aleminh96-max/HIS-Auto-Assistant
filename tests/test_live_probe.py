"""No raw HIS field values may reach the exported UIA inventory."""
from his_auto.live_probe import read_safe_static_caption, safe_caption, safe_control_type, safe_geometry


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


class Control:
    def __init__(self, control_type, value):
        self.element_info = type("Info", (), {"control_type": control_type})()
        self.value = value
        self.read_count = 0

    def window_text(self):
        self.read_count += 1
        return self.value


def test_patient_value_control_types_are_never_read():
    for control_type in ("Edit", "Text", "DataItem", "ListItem", "Table"):
        control = Control(control_type, "Patient data must not be read")
        assert read_safe_static_caption(control) is None
        assert control.read_count == 0


def test_only_allowlisted_caption_on_static_control_is_returned():
    control = Control("Button", "Lưu")
    assert read_safe_static_caption(control) == "Lưu"
    assert control.read_count == 1


def test_live_adapter_is_read_only():
    import pytest
    from his_auto.domain import SafetyError
    from his_auto.recognition import LiveAdapter

    adapter = LiveAdapter()
    assert adapter.write_enabled is False
    assert adapter.verify("any operation") is False
    with pytest.raises(SafetyError, match="chỉ đọc"):
        adapter.execute("save")


def test_geometry_is_relative_to_own_window():
    parent = Rectangle(400, 300, 1400, 800)
    item = Rectangle(650, 400, 850, 450)
    assert safe_geometry(item, parent) == {"x": 0.25, "y": 0.2, "w": 0.2, "h": 0.1}
