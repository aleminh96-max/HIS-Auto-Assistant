from datetime import datetime, timezone
import pytest
from his_auto.domain import ClinicalTemplate, PatientContext, Vitals, prepare_dossier
from his_auto.storage import Store
from his_auto.simulator import SimulatorAdapter


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "test.sqlite3")
    yield s
    s.db.close()


@pytest.fixture
def adapter():
    return SimulatorAdapter()


@pytest.fixture
def clinical():
    return ClinicalTemplate("DEMO", diagnosis="DỮ LIỆU GIẢ")


@pytest.fixture
def at():
    return datetime(2026,10,16,23,45,tzinfo=timezone.utc)


@pytest.fixture
def vitals(at):
    return Vitals(at,80,120,80,37,18,98,60,165)


@pytest.fixture
def dossier(adapter,clinical,vitals,at):
    return prepare_dossier(adapter.context(),clinical,vitals,at,injection=1,history_confirmed=True,third_reviewed=True)
