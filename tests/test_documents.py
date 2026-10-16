from dataclasses import replace
import pytest
from his_auto.documents import Document,SignatureManager,PrintManager,PrintConfig
from his_auto.domain import SafetyError


@pytest.fixture
def document(adapter):
    return Document(adapter.context(),"TEST-1","TEST","DỮ LIỆU GIẢ")


def test_sign_once_only_after_exact_review(adapter,store,document):
    s = SignatureManager(adapter,store)
    with pytest.raises(SafetyError): s.sign(document)
    s.approve(document)
    with pytest.raises(SafetyError): s.sign(replace(document,content="changed"))
    assert s.sign(document) == "SIGNED"
    s.approve(document)
    with pytest.raises(SafetyError): s.sign(document)
    assert adapter.calls.count("sign") == 1


def test_unknown_signature_not_retried(adapter,store,document):
    s = SignatureManager(adapter,store)
    adapter.unknown_signature = True
    s.approve(document)
    with pytest.raises(SafetyError): s.sign(document)
    adapter.unknown_signature = False
    s.approve(document)
    with pytest.raises(SafetyError): s.sign(document)
    assert adapter.calls.count("sign") == 1


def test_wrong_document_or_no_permission(adapter,store,document):
    s = SignatureManager(adapter,store)
    s.approve(document)
    with pytest.raises(SafetyError): s.sign(replace(document,document_id="OTHER"))
    adapter.patient = replace(adapter.patient,permissions=("write",))
    with pytest.raises(SafetyError): s.sign(document)


def test_print_missing_printer_unsigned_or_duplicate(adapter,store,document):
    p = PrintManager(adapter,store)
    c = PrintConfig("TEST-PRINTER")
    with pytest.raises(SafetyError): p.print(document,c,[],approved=True)
    with pytest.raises(SafetyError): p.print(document,c,[c.printer],approved=True)
    s = SignatureManager(adapter,store)
    s.approve(document)
    s.sign(document)
    with pytest.raises(SafetyError): p.print(document,c,[c.printer])
    assert p.print(document,c,[c.printer],approved=True).startswith("SIM-")
    with pytest.raises(SafetyError): p.print(document,c,[c.printer],approved=True)
    assert adapter.calls.count("print") == 1
