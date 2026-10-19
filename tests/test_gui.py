from his_auto.ui import AssistantWindow
from his_auto.workflow import State


def test_gui_prepare_review_three_sheets(qtbot,store):
    window = AssistantWindow(store)
    qtbot.addWidget(window)
    window.timer.stop()
    window.demo_data()
    window.history_confirm.setChecked(True)
    window.third.setChecked(True)
    window.prepare()
    window.update_status()
    assert "DEMO-0001" in window.preview.toPlainText()
    assert window.workflow.state == State.WAITING_FOR_REVIEW
    window.approve()
    window.start()
    for _ in range(5): window.advance()
    assert window.workflow.state == State.COMPLETED
    window.open_simulator()
    qtbot.addWidget(window.sim_window)
    window.sim_window.refresh()
    assert "sheet3" in window.sim_window.pages["F7 — Tờ điều trị"].toPlainText()


def test_gui_edits_after_approval_stop(qtbot,store):
    window = AssistantWindow(store)
    qtbot.addWidget(window)
    window.timer.stop()
    window.demo_data()
    window.history_confirm.setChecked(True)
    window.third.setChecked(True)
    window.prepare()
    window.approve()
    window.start()
    window.fields["diagnosis"].setText("Changed")
    window.advance()
    assert window.workflow.state == State.FAILED
    assert not window.adapter.calls


def test_gui_survey_requires_review_and_has_separate_prescriptions(qtbot,store):
    import pytest
    from his_auto.domain import SafetyError
    window = AssistantWindow(store)
    qtbot.addWidget(window)
    window.timer.stop()
    window.demo_data()
    window.history_confirm.setChecked(True)
    window.third.setChecked(True)
    window.load_survey()
    with pytest.raises(SafetyError): window.current_dossier()
    window.med_review.setChecked(True)
    with pytest.raises(SafetyError): window.current_dossier()
    window.order_table.item(0,7).setText("TEST — tổng liều người thử nhập")
    window.order_table.item(1,7).setText("TEST — tổng liều người thử nhập")
    window.prepare()
    assert len(window.dossier.sheets[0].medications) == 1
    assert len(window.dossier.sheets[1].medications) == 5
    assert not window.dossier.sheets[2].medications


def test_dashboard_twelve_items_never_claims_unverified_completion(qtbot,store):
    window = AssistantWindow(store)
    qtbot.addWidget(window)
    window.timer.stop()
    assert window.timeline.topLevelItemCount() == 12
    assert window.progress.value() == 0
    window.demo_data()
    window.history_confirm.setChecked(True)
    window.third.setChecked(True)
    window.prepare()
    window.update_status()
    assert window.timeline.topLevelItem(0).text(1) == "ĐÃ XÁC MINH"
    assert window.progress.value() == 1
    assert window.tabs.currentIndex() == 0
    assert "DỮ LIỆU GIẢ" in window.inline_preview.toPlainText()
    window.approve()
    window.start()
    for _ in range(5):
        window.advance()
    assert window.workflow.state == State.COMPLETED
    assert window.progress.value() == 6
    assert window.progress.maximum() == 12
    assert window.progress.value() < window.progress.maximum()
    assert window.timeline.topLevelItem(3).text(1) == "CHƯA HỖ TRỢ"
    assert window.timeline.topLevelItem(11).text(1) == "CHƯA HỖ TRỢ"
    from dataclasses import replace
    window.adapter.patient = replace(window.adapter.patient, record_id="DEMO-OTHER")
    window.update_status()
    assert window.timeline.topLevelItem(0).text(1) == "LỖI / CẦN KIỂM TRA"
    assert window.progress.value() == 5
