from dataclasses import replace
from datetime import timedelta
import pytest
from his_auto.domain import (Group,SafetyError,Medication,prepare_dossier,reconcile_quantities)


def test_three_sheets_midnight(dossier):
    a,b,c = dossier.sheets
    assert a.at == b.at
    assert c.at == a.at + timedelta(minutes=30)
    assert c.at.day == 17
    assert not c.medications
    assert c.vitals.measured_at == a.vitals.measured_at


def test_early_requires_manual_icd(clinical):
    with pytest.raises(SafetyError): replace(clinical,group=Group.EARLY,icd="").validate()
    replace(clinical,group=Group.EARLY,icd="DOCTOR-CHOSEN").validate()


def test_latent_icd(clinical):
    clinical.validate()
    with pytest.raises(SafetyError): replace(clinical,icd="A00").validate()


@pytest.mark.parametrize("injection",[1,2,3])
def test_injection_history(adapter,clinical,vitals,at,injection):
    kwargs = dict(injection=injection,third_reviewed=True)
    with pytest.raises(SafetyError): prepare_dossier(adapter.context(),clinical,vitals,at,**kwargs)
    assert prepare_dossier(adapter.context(),clinical,vitals,at,history_confirmed=True,**kwargs).injection == injection


@pytest.mark.parametrize("field,value",[("pulse",float("nan")),("temperature",float("inf")),("weight",0),("spo2",101),("systolic",70)])
def test_invalid_vitals(vitals,field,value):
    with pytest.raises(SafetyError): replace(vitals,**{field:value}).validate()


def test_abnormal_needs_review(adapter,clinical,vitals,at):
    with pytest.raises(SafetyError,match="bất thường"):
        prepare_dossier(adapter.context(),clinical,replace(vitals,pulse=200),at,injection=1,history_confirmed=True,third_reviewed=True)


def test_third_review_required(adapter,clinical,vitals,at):
    with pytest.raises(SafetyError,match="tờ 3"):
        prepare_dossier(adapter.context(),clinical,vitals,at,injection=1,history_confirmed=True)


def test_separate_prescriptions(adapter,clinical,vitals,at):
    free = Medication("TEST-MED","DỮ LIỆU GIẢ — thuốc",2,"Tiêm bắp",at,True,"TEST","TEST")
    external = Medication("TEST-SUPPLY","DỮ LIỆU GIẢ — vật tư",4,".",at,False,"TEST","Vật tư")
    kwargs = dict(injection=1,history_confirmed=True,third_reviewed=True,medication_reviewed=True)
    d = prepare_dossier(adapter.context(),clinical,vitals,at,free=(free,),external=(external,),**kwargs)
    assert d.sheets[0].medications == (free,)
    assert d.sheets[1].medications == (external,)
    assert not d.sheets[2].medications
    with pytest.raises(SafetyError,match="Trùng"):
        prepare_dossier(adapter.context(),clinical,vitals,at,external=(external,external),**kwargs)
    with pytest.raises(SafetyError,match="trộn"):
        prepare_dossier(adapter.context(),clinical,vitals,at,external=(free,),**kwargs)


def test_quantity_discrepancy():
    assert reconcile_quantities({"TEST":2},{"TEST":2},{"TEST":2})
    with pytest.raises(SafetyError): reconcile_quantities({"TEST":2},{"TEST":1},{"TEST":1})
    with pytest.raises(SafetyError): reconcile_quantities({"TEST":2},{"WRONG":2},{"TEST":2})
