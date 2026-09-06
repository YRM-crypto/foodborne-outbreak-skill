"""轻量 SQLite 事件存储：追加式审计、事务、修订号、定义版本化。无网络。

对齐《食品安全事故流行病学调查技术指南（2012 年版）》与附表 1-8。
原始材料（个案/暴露/食品/样本/卫生学/控制措施）随时可追加；派生指标由
core.analyze/classify/validate 从当前证据重算，不落库。
"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, lead TEXT,
    place_type TEXT, region TEXT, address TEXT,
    occurred_at TEXT, received_at TEXT, exposure_at TEXT, investigation_end TEXT,
    cross_region INTEGER DEFAULT 0, is_foodborne TEXT DEFAULT 'unknown',
    source_region TEXT, source_place_type TEXT, source_address TEXT,
    population_size INTEGER, population_basis TEXT, population_known INTEGER DEFAULT 0,
    study_design TEXT, timezone TEXT DEFAULT 'Asia/Shanghai',
    urgent_flags TEXT DEFAULT '[]', revision INTEGER DEFAULT 0, created_at TEXT
);
CREATE TABLE IF NOT EXISTS audit (
    seq INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT NOT NULL,
    revision INTEGER NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL,
    reason TEXT, payload TEXT, recorded_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS definition (
    event_id TEXT PRIMARY KEY, version INTEGER DEFAULT 1, label TEXT, text TEXT,
    start TEXT, end TEXT, locations TEXT DEFAULT '[]', populations TEXT DEFAULT '[]',
    symptoms_any TEXT DEFAULT '[]', minimum_symptoms INTEGER DEFAULT 1,
    probable TEXT DEFAULT '{}', confirmed TEXT DEFAULT '{}', evidence_ids TEXT DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS people (
    event_id TEXT, id TEXT, name TEXT, age REAL, sex TEXT, occupation TEXT,
    population TEXT, location TEXT, onset TEXT, recovery TEXT, illness_status TEXT,
    symptoms TEXT DEFAULT '{}', hospitalized INTEGER DEFAULT 0, died INTEGER DEFAULT 0,
    hospital TEXT, diagnosis TEXT, adjudication TEXT, evidence_ids TEXT DEFAULT '[]',
    notes TEXT, PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS exposures (
    event_id TEXT, id TEXT, person_id TEXT, meal_id TEXT, meal_at TEXT,
    food_id TEXT, consumed INTEGER, ate_at TEXT, incubation_anchor INTEGER DEFAULT 0,
    evidence_ids TEXT DEFAULT '[]', notes TEXT, PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS foods (
    event_id TEXT, id TEXT, category TEXT, meal_id TEXT, source TEXT,
    process_method TEXT, package TEXT, notes TEXT, PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS samples (
    event_id TEXT, id TEXT, category TEXT, source TEXT, person_id TEXT,
    laboratory TEXT, collected_at TEXT, tests TEXT DEFAULT '[]',
    evidence_ids TEXT DEFAULT '[]', notes TEXT, PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS hygiene (
    event_id TEXT, id TEXT, aspect TEXT, item TEXT, finding TEXT,
    problem INTEGER DEFAULT 0, evidence_ids TEXT DEFAULT '[]', notes TEXT,
    PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS controls (
    event_id TEXT, id TEXT, measure TEXT, target TEXT, implemented TEXT, date TEXT,
    evidence_ids TEXT DEFAULT '[]', notes TEXT, PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS evidence (
    event_id TEXT, id TEXT, title TEXT, status TEXT, uri TEXT, text TEXT, locator TEXT,
    collected_at TEXT, sha256 TEXT, notes TEXT, PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS conclusions (
    event_id TEXT, topic TEXT, status TEXT, statement TEXT, reason TEXT,
    limitations TEXT, link TEXT, factor TEXT, evidence_ids TEXT DEFAULT '[]',
    PRIMARY KEY (event_id, topic)
);
CREATE TABLE IF NOT EXISTS stages (
    event_id TEXT, stage TEXT, status TEXT DEFAULT 'pending', note TEXT,
    evidence_ids TEXT DEFAULT '[]', confirmed_at TEXT, updated_at TEXT,
    PRIMARY KEY (event_id, stage)
);
"""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _dumps(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def _enc(v):
    return _dumps(v) if isinstance(v, (list, dict)) else v


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self):
        self.conn.close()

    # —— 审计 ——
    def _audit(self, event_id, revision, actor, action, reason, payload=None):
        self.conn.execute(
            "INSERT INTO audit(event_id,revision,actor,action,reason,payload,recorded_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (event_id, revision, actor, action, reason, _dumps(payload or {}), now()))

    def _bump(self, event_id):
        self.conn.execute("UPDATE events SET revision = revision + 1 WHERE id=?", (event_id,))
        return self.conn.execute("SELECT revision FROM events WHERE id=?", (event_id,)).fetchone()["revision"]

    # —— 事件 ——
    def create_event(self, event_id, title, lead="", actor="system"):
        if not event_id.strip() or not title.strip():
            raise ValueError("事件编号和标题不能为空")
        self.conn.execute(
            "INSERT INTO events(id,title,lead,revision,created_at) VALUES(?,?,?,?,?)",
            (event_id, title, lead, 1, now()))
        self._audit(event_id, 1, actor, "init", "建立事件档案", {"title": title})
        self.conn.commit()
        return self.get_event(event_id)

    def list_events(self):
        rows = self.conn.execute("SELECT * FROM events ORDER BY revision DESC, id").fetchall()
        return [dict(r) for r in rows]

    def get_event(self, event_id):
        row = self.conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone()
        if row is None:
            raise ValueError(f"事件不存在：{event_id}")
        return dict(row)

    def timeline(self, event_id):
        rows = self.conn.execute("SELECT * FROM audit WHERE event_id=? ORDER BY seq DESC", (event_id,)).fetchall()
        return [dict(r) for r in rows]

    def update_event(self, event_id, fields, actor, reason):
        allowed = {
            "title", "lead", "place_type", "region", "address", "occurred_at", "received_at",
            "exposure_at", "investigation_end", "cross_region", "is_foodborne",
            "source_region", "source_place_type", "source_address",
            "population_size", "population_basis", "population_known", "study_design",
            "timezone", "urgent_flags",
        }
        bad = set(fields) - allowed
        if bad:
            raise ValueError(f"events 不可更新字段 {sorted(bad)}")
        self.get_event(event_id)
        if not fields:
            return self.get_event(event_id)["revision"]
        sets = ", ".join(f"{c}=?" for c in fields)
        self.conn.execute(f"UPDATE events SET {sets} WHERE id=?",
                          [*[_enc(fields[c]) for c in fields], event_id])
        rev = self._bump(event_id)
        self._audit(event_id, rev, actor, "update_event", reason, fields)
        self.conn.commit()
        return rev

    # —— 通用行 upsert（(event_id, keycol) 主键的表）——
    def _set_row(self, table, event_id, keycol, value, actor, action, reason):
        cols = [c["name"] for c in self.conn.execute(f"PRAGMA table_info({table})")]
        for c in value:
            if c not in cols:
                raise ValueError(f"{table} 未知字段 {c}")
        if keycol not in value:
            raise ValueError(f"缺少 {keycol}")
        ordered = ["event_id"] + [c for c in cols if c != "event_id"]
        self.conn.execute(
            f"INSERT INTO {table}({', '.join(ordered)}) VALUES({', '.join('?' * len(ordered))}) "
            f"ON CONFLICT(event_id,{keycol}) DO UPDATE SET "
            + ", ".join(f"{c}=excluded.{c}" for c in cols if c not in ("event_id", keycol)),
            [event_id] + [_enc(value.get(c)) for c in ordered if c != "event_id"])
        rev = self._bump(event_id)
        self._audit(event_id, rev, actor, action, reason, value)
        self.conn.commit()
        return rev

    # —— 病例定义（版本化：每次更新 version+1，便于追踪「分类变化」）——
    def set_definition(self, event_id, definition, actor, reason):
        cols = [c["name"] for c in self.conn.execute("PRAGMA table_info(definition)")]
        for c in definition:
            if c not in cols:
                raise ValueError(f"definition 未知字段 {c}")
        self.get_event(event_id)
        existing = self.conn.execute("SELECT version FROM definition WHERE event_id=?", (event_id,)).fetchone()
        version = (existing["version"] + 1) if existing else 1
        ordered = ["event_id", "version"] + [c for c in cols if c not in ("event_id", "version")]
        self.conn.execute(
            f"INSERT INTO definition({', '.join(ordered)}) VALUES({', '.join('?' * len(ordered))}) "
            f"ON CONFLICT(event_id) DO UPDATE SET version=excluded.version, "
            + ", ".join(f"{c}=excluded.{c}" for c in cols if c not in ("event_id", "version")),
            [event_id, version] + [_enc(definition.get(c)) for c in ordered if c not in ("event_id", "version")])
        rev = self._bump(event_id)
        self._audit(event_id, rev, actor, "set_definition", reason, dict(definition, version=version))
        self.conn.commit()
        return version

    def upsert_people(self, event_id, people, actor, reason):
        for p in people:
            self._set_row("people", event_id, "id", p, actor, "upsert_people", reason)
        return self.get_event(event_id)["revision"]

    def upsert_exposures(self, event_id, exposures, actor, reason):
        for e in exposures:
            self._set_row("exposures", event_id, "id", e, actor, "upsert_exposures", reason)
        return self.get_event(event_id)["revision"]

    def upsert_foods(self, event_id, foods, actor, reason):
        for f in foods:
            self._set_row("foods", event_id, "id", f, actor, "upsert_foods", reason)
        return self.get_event(event_id)["revision"]

    def upsert_samples(self, event_id, samples, actor, reason):
        for s in samples:
            self._set_row("samples", event_id, "id", s, actor, "upsert_samples", reason)
        return self.get_event(event_id)["revision"]

    def add_hygiene(self, event_id, records, actor, reason):
        for h in records:
            self._set_row("hygiene", event_id, "id", h, actor, "add_hygiene", reason)
        return self.get_event(event_id)["revision"]

    def add_control(self, event_id, records, actor, reason):
        for c in records:
            self._set_row("controls", event_id, "id", c, actor, "add_control", reason)
        return self.get_event(event_id)["revision"]

    def add_evidence(self, event_id, record, actor, reason):
        return self._set_row("evidence", event_id, "id", record, actor, "add_evidence", reason)

    def set_conclusion(self, event_id, topic, record, actor, reason):
        record = dict(record, topic=topic)
        return self._set_row("conclusions", event_id, "topic", record, actor, "set_conclusion", reason)

    # —— 阶段状态（13 阶段，非门禁，仅完成度）——
    def set_stage(self, event_id, stage, status, actor, note="", evidence_ids=None):
        if stage not in {"intake", "verify_dx", "case_def", "case_find", "individual",
                         "descriptive", "analytic", "food_hygiene", "sampling", "control",
                         "conclusion", "report", "archive"}:
            raise ValueError(f"无效阶段：{stage}")
        if status not in ("pending", "in_progress", "done", "na"):
            raise ValueError(f"无效阶段状态：{status}")
        rev = self.get_event(event_id)["revision"]
        self.conn.execute(
            "INSERT INTO stages(event_id,stage,status,note,evidence_ids,updated_at)"
            " VALUES(?,?,?,?,?,?) "
            "ON CONFLICT(event_id,stage) DO UPDATE SET status=excluded.status, note=excluded.note,"
            " evidence_ids=excluded.evidence_ids, updated_at=excluded.updated_at",
            (event_id, stage, status, note, _dumps(evidence_ids or []), now()))
        self._audit(event_id, rev, actor, "stage:" + stage, note or status, {"status": status})
        self.conn.commit()
        return rev

    # —— 读取 ——
    def _rows(self, table, event_id):
        return [dict(r) for r in self.conn.execute(
            f"SELECT * FROM {table} WHERE event_id=?", (event_id,)).fetchall()]

    def load(self, event_id):
        event = self.get_event(event_id)

        def _j(x):
            return json.loads(x) if isinstance(x, str) else (x or {})

        def _decode(row, keys):
            if row is None:
                return None
            row = dict(row)
            for k in keys:
                row[k] = _j(row.get(k))
            return row

        d = self.conn.execute("SELECT * FROM definition WHERE event_id=?", (event_id,)).fetchone()
        definition = _decode(d, ("locations", "populations", "symptoms_any",
                                 "probable", "confirmed", "evidence_ids"))
        people = [_decode(r, ("symptoms", "adjudication", "evidence_ids")) for r in self._rows("people", event_id)]
        exposures = [_decode(r, ("evidence_ids",)) for r in self._rows("exposures", event_id)]
        foods = self._rows("foods", event_id)
        samples = [_decode(r, ("tests", "evidence_ids")) for r in self._rows("samples", event_id)]
        hygiene = [_decode(r, ("evidence_ids",)) for r in self._rows("hygiene", event_id)]
        controls = [_decode(r, ("evidence_ids",)) for r in self._rows("controls", event_id)]
        evidence = self._rows("evidence", event_id)
        conclusions = [_decode(r, ("evidence_ids",)) for r in self._rows("conclusions", event_id)]
        stages = {r["stage"]: _decode(r, ("evidence_ids",)) for r in self._rows("stages", event_id)}
        return {"event": event, "definition": definition, "people": people,
                "exposures": exposures, "foods": foods, "samples": samples,
                "hygiene": hygiene, "controls": controls, "evidence": evidence,
                "conclusions": conclusions, "stages": stages}
