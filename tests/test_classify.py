"""core/classify.py：三级判定（确诊/可能/疑似/未发病/排除/待定）。"""
from core.classify import classify

DEF = {
    "version": 1, "start": "2024-01-01T00:00:00", "end": "2024-01-06T23:59:59",
    "locations": ["某中学"], "populations": [], "symptoms_any": ["呕吐"],
    "minimum_symptoms": 1, "probable": {"require_epi_link": True},
    "confirmed": {"require_lab": True},
}

P = {"id": "P1", "illness_status": "ill", "onset": "2024-01-03T12:00:00",
     "location": "某中学", "symptoms": {"呕吐": True}}


def test_suspected():
    assert classify(P, DEF)[0] == "疑似"


def test_confirmed_via_lab():
    assert classify(P, DEF, lab_positive=True)[0] == "确诊"


def test_probable_via_epi_link():
    assert classify(P, DEF, epi_linked=True)[0] == "可能"


def test_out_of_time_scope_excluded():
    p = dict(P, onset="2023-12-31T12:00:00")
    assert classify(p, DEF)[0] == "排除"


def test_out_of_location_excluded():
    p = dict(P, location="某小学")
    assert classify(p, DEF)[0] == "排除"


def test_well_person():
    p = dict(P, illness_status="well", onset=None)
    assert classify(p, DEF)[0] == "未发病"


def test_missing_onset_pending():
    p = dict(P, onset=None)
    assert classify(p, DEF)[0] == "待定"


def test_no_definition_pending():
    assert classify(P, None)[0] == "待定"


def test_manual_adjudication_overrides():
    p = dict(P, adjudication={"status": "确诊", "reason": "人工复核", "definition_version": 1})
    st, reason = classify(p, DEF, lab_positive=False)
    assert st == "确诊" and "人工复核" in reason


def test_stale_adjudication_ignored():
    p = dict(P, adjudication={"status": "确诊", "reason": "旧", "definition_version": 0})
    assert classify(p, DEF)[0] == "疑似"
