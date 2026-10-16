from dataclasses import replace
import json
import pytest
from his_auto.domain import SafetyError
from his_auto.recognition import Calibration,LiveAdapter,match_image


def test_template_versions_import_backup(store,clinical,tmp_path):
    store.save_template(clinical)
    store.save_template(replace(clinical,plan="TEST"))
    assert len(store.history(clinical.name)) == 2
    assert store.templates()[0].plan == "TEST"
    store.export_templates(tmp_path/"templates.json")
    store.backup(tmp_path/"backup.sqlite3")
    with pytest.raises(SafetyError): store.delete_template(clinical.name)
    store.delete_template(clinical.name,confirmed=True)
    assert not store.templates()
    store.import_templates(tmp_path/"templates.json")
    assert store.templates()[0].plan == "TEST"
    assert (tmp_path/"backup.sqlite3").stat().st_size > 0


@pytest.mark.parametrize("width,height,dpi",[(1366,768,96),(1920,1080,120),(2560,1440,144)])
def test_calibration_relative_and_change_detection(width,height,dpi):
    c = Calibration("TEST",width,height,dpi,"ui-v1",{"save":(.5,.25)})
    c.validate("TEST",width,height,dpi,"ui-v1")
    assert c.point("save",(100,200,800,600)) == (500,350)
    with pytest.raises(SafetyError): c.validate("TEST",width,height,dpi+1,"ui-v1")


def test_vision_match_and_ambiguity():
    import numpy as np
    rng = np.random.default_rng(42)
    template = rng.integers(0,256,(12,12),dtype=np.uint8)
    screen = np.zeros((100,100),dtype=np.uint8)
    screen[30:42,40:52] = template
    point,score = match_image(screen,template)
    assert point == (40,30) and score > .99
    screen[70:82,70:82] = template
    with pytest.raises(SafetyError): match_image(screen,template)


def test_live_write_is_locked():
    with pytest.raises(SafetyError): LiveAdapter()
