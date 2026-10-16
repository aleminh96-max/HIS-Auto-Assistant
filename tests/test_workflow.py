from dataclasses import replace
import pytest
from his_auto.workflow import Workflow,State
from his_auto.domain import SafetyError


def approved(adapter,store,dossier):
    w = Workflow(adapter,store)
    w.prepare(dossier)
    w.approve(dossier.fingerprint)
    w.start()
    return w


def test_review_required(adapter,store,dossier):
    w = Workflow(adapter,store)
    w.prepare(dossier)
    with pytest.raises(SafetyError): w.start()
    with pytest.raises(SafetyError): w.approve("wrong")


def test_full_workflow_and_resume_without_duplicates(adapter,store,dossier):
    w = approved(adapter,store,dossier)
    w.tick()
    w.pause()
    w.tick()
    assert len(adapter.calls) == 1
    w.start()
    for _ in range(4): w.tick()
    assert w.state == State.COMPLETED
    assert adapter.calls == ["diagnosis","services","sheet1","sheet2","sheet3"]
    w = approved(adapter,store,dossier)
    for _ in range(5): w.tick()
    assert w.state == State.COMPLETED
    assert len(adapter.calls) == 5


@pytest.mark.parametrize("changes",[{"record_id":"OTHER"},{"episode_id":"OTHER"},{"department":"OTHER"},
    {"responsive":False},{"screen":"OTHER"},{"process":"OTHER"},{"permissions":()}])
def test_context_changes_stop(adapter,store,dossier,changes):
    w = approved(adapter,store,dossier)
    adapter.patient = replace(adapter.patient,**changes)
    w.tick()
    assert w.state == State.FAILED
    assert not adapter.calls


def test_ambiguous_outcome_never_retried(adapter,store,dossier):
    w = approved(adapter,store,dossier)
    adapter.fail_step = "diagnosis"
    w.tick()
    assert w.state == State.FAILED
    assert store.operation(adapter.operation_key(dossier,"diagnosis")) == "PENDING"
    adapter.fail_step = None
    w = approved(adapter,store,dossier)
    w.tick()
    assert w.state == State.FAILED
    assert not adapter.calls


def test_emergency_stop(adapter,store,dossier):
    w = approved(adapter,store,dossier)
    w.stop()
    w.tick()
    assert not adapter.calls
    with pytest.raises(SafetyError): w.start()


def test_changed_dossier_rejected(adapter,store,dossier):
    w = approved(adapter,store,dossier)
    w.dossier = replace(dossier,services=("TEST-NEW",))
    w.tick()
    assert w.state == State.FAILED
    assert not adapter.calls
