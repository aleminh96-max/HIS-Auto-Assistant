"""User-supplied survey examples. Explicitly test data, never valid orders."""
from datetime import timedelta
from .domain import Medication, SafetyError

SURVEY_ITEMS = (
    ("TEST-BENZ", "Benzathin benzylpenicilin 1.200.000 UI (VCP, Việt Nam)", 2, "Tiêm bắp", True, "1.200.000 UI", "CHƯA DUYỆT"),
    ("TEST-WATER", "Nước cất pha tiêm 5ml", 4, ".", False, "5ml", "CHƯA DUYỆT"),
    ("TEST-SYR10", "Bơm tiêm sử dụng một lần 10ml/cc", 2, ".", False, "10ml/cc", "Vật tư"),
    ("TEST-SYR1", "Bơm tiêm sử dụng một lần 1ml/cc", 1, ".", False, "1ml/cc", "Vật tư"),
    ("TEST-N18", "Kim tiêm sử dụng một lần 18x1 1/2 Vina", 2, ".", False, "18x1 1/2", "Vật tư"),
    ("TEST-N20", "Kim tiêm sử dụng một lần 20x1 1/2 Vina", 2, ".", False, "20x1 1/2", "Vật tư"),
)


def survey_drafts(at):
    # Suggested reference time is displayed for review, never silently approved.
    return tuple(Medication(code,"[TEST] " + name,qty,route,at+timedelta(minutes=10),free,strength,dose)
                 for code,name,qty,route,free,strength,dose in SURVEY_ITEMS)


def validate_catalog(items, catalog):
    for item in items:
        if catalog.get(item.catalog_id) != item.name:
            raise SafetyError("Mặt hàng không khớp chính xác mã và tên danh mục mô phỏng.")
