"""轻量 SQLite 事件存储：追加式审计、事务、修订号。无网络。"""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY, title TEXT NOT NULL, scenario TEXT NOT NULL,
    lead TEXT, received_at TEXT, location TEXT, data_cutoff TEXT,
    timezone TEXT DEFAULT 'Asia/Shanghai', population_size INTEGER,
    population_complete INTEGER DEFAULT 0, population_basis TEXT,
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
    require_lab INTEGER DEFAULT 0, evidence_ids TEXT DEFAULT '[]'
);
CREATE TABLE IF NOT EXISTS people (
    event_id TEXT, id TEXT, age REAL, sex TEXT, location TEXT, population TEXT,
    onset TEXT, recovery TEXT, observed_until TEXT, illness_status TEXT,
    symptoms TEXT DEFAULT '{}', hospitalized INTEGER, died INTEGER, lab_eligible INTEGER,
    adjudication TEXT, evidence_ids TEXT DEFAULT '[]', notes TEXT, PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS exposures (
    event_id TEXT, id TEXT, person_id TEXT, meal_id TEXT, food_id TEXT,
    consumed INTEGER, ate_at TEXT, incubation_anchor INTEGER,
    evidence_ids TEXT DEFAULT '[]', notes TEXT, PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS samples (
    event_id TEXT, id TEXT, kind TEXT, person_id TEXT, source TEXT, collected_at TEXT,
    laboratory TEXT, tests TEXT DEFAULT '[]', evidence_ids TEXT DEFAULT '[]', notes TEXT,
    PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS evidence (
    event_id TEXT, id TEXT, title TEXT, status TEXT, uri TEXT, text TEXT, locator TEXT,
    collected_at TEXT, sha256 TEXT, notes TEXT, PRIMARY KEY (event_id, id)
);
CREATE TABLE IF NOT EXISTS conclusions (
    event_id TEXT, topic TEXT, status TEXT, statement TEXT, reason TEXT, limitations TEXT,
    evidence_ids TEXT DEFAULT '[]', PRIMARY KEY (event_id, topic)
);
CREATE TABLE IF NOT EXISTS confirmations (
    event_id TEXT, node TEXT, actor TEXT, role TEXT, note TEXT, evidence_ids TEXT DEFAULT '[]',
    disposition TEXT, confirmed_at TEXT, recorded_at TEXT, based_on_revision INTEGER,
    PRIMARY KEY (event_id, node)
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

    def _audit(self, event_id, revision, actor, action, reason, payload=None):
        self.conn.execute(
            "INSERT INTO audit(event_id,revision,actor,action,reason,payload,recorded_at)"
            " VALUES(?,?,?,?,?,?,?)",
            (event_id, revision, actor, action, reason, _dumps(payload or {}), now()))

    def _bump(self, event_id):
        self.conn.execute("UPDATE events SET revision = revision + 1 WHERE id=?", (event_id,))
        return self.conn.execute("SELECT revision FROM events WHERE id=?", (event_id,)).fetchone()["revision"]

    def create_event(self, event_id, title, scenario, lead="", actor="system"):
        if scenario not in ("closed-cohort", "distributed-retail"):
            raise ValueError("unknown scenario")
        if not event_id.strip() or not title.strip():
            raise ValueError("事件编号和标题不能为空")
        self.conn.execute(
            "INSERT INTO events(id,title,scenario,lead,revision,created_at) VALUES(?,?,?,?,?,?)",
            (event_id, title, scenario, lead, 1, now()))
        self._audit(event_id, 1, actor, "init", "建立事件档案", {"title": title, "scenario": scenario})
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

    def set_definition(self, event_id, definition, actor, reason):
        cols = [c["name"] for c in self.conn.execute("PRAGMA table_info(definition)")]
        for c in definition:
            if c not in cols:
                raise ValueError(f"definition 未知字段 {c}")
        ordered = ["event_id"] + [c for c in cols if c != "event_id"]
        self.conn.execute(
            f"INSERT INTO definition({', '.join(ordered)}) VALUES({', '.join('?' * len(ordered))}) "
            f"ON CONFLICT(event_id) DO UPDATE SET "
            + ", ".join(f"{c}=excluded.{c}" for c in cols if c != "event_id"),
            [event_id] + [_enc(definition.get(c)) for c in ordered if c != "event_id"])
        rev = self._bump(event_id)
        self._audit(event_id, rev, actor, "set_definition", reason, definition)
        self.conn.commit()
        return rev

    def upsert_people(self, event_id, people, actor, reason):
        for p in people:
            self._set_row("people", event_id, "id", p, actor, "upsert_people", reason)
        return self.get_event(event_id)["revision"]

    def add_evidence(self, event_id, record, actor, reason):
        return self._set_row("evidence", event_id, "id", record, actor, "add_evidence", reason)

    def set_conclusion(self, event_id, topic, record, actor, reason):
        record = dict(record, topic=topic)
        return self._set_row("conclusions", event_id, "topic", record, actor, "set_conclusion", reason)

    def confirm(self, event_id, node, actor, role, note, evidence_ids, disposition="confirmed"):
        if node not in ("intake", "definition", "plan", "analysis", "evidence", "conclusion", "closure"):
            raise ValueError("无效节点")
        rev = self.get_event(event_id)["revision"]
        self.conn.execute(
            "INSERT INTO confirmations(event_id,node,actor,role,note,evidence_ids,disposition,"
            "confirmed_at,recorded_at,based_on_revision) VALUES(?,?,?,?,?,?,?,?,?,?) "
            "ON CONFLICT(event_id,node) DO UPDATE SET actor=excluded.actor, role=excluded.role,"
            " note=excluded.note, evidence_ids=excluded.evidence_ids, disposition=excluded.disposition,"
            " confirmed_at=excluded.confirmed_at, recorded_at=excluded.recorded_at,"
            " based_on_revision=excluded.based_on_revision",
            (event_id, node, actor, role, note, _dumps(evidence_ids), disposition, now(), now(), rev))
        self._audit(event_id, rev, actor, "confirm:" + node, note, {"node": node, "disposition": disposition})
        self.conn.commit()
        return rev

    def _rows(self, table, event_id):
        return [dict(r) for r in self.conn.execute(
            f"SELECT * FROM {table} WHERE event_id=?", (event_id,)).fetchall()]

    def load(self, event_id):
        event = self.get_event(event_id)
        def _j(x):
            return json.loads(x) if isinstance(x, str) else (x or {})
        d = self.conn.execute("SELECT * FROM definition WHERE event_id=?", (event_id,)).fetchone()
        people = self._rows("people", event_id)
        for p in people:
            p["symptoms"] = _j(p.get("symptoms"))
            p["evidence_ids"] = _j(p.get("evidence_ids"))
        exposures = self._rows("exposures", event_id)
        samples = self._rows("samples", event_id)
        for s in samples:
            s["tests"] = _j(s.get("tests"))
        evidence = self._rows("evidence", event_id)
        for e in evidence:
            e["evidence_ids"] = _j(e.get("evidence_ids"))
        conclusions = self._rows("conclusions", event_id)
        for c in conclusions:
            c["evidence_ids"] = _j(c.get("evidence_ids"))
        confirmations = {r["node"]: dict(r) for r in self._rows("confirmations", event_id)}
        return {"event": event, "definition": dict(d) if d else None, "people": people,
                "exposures": exposures, "samples": samples, "evidence": evidence,
                "conclusions": conclusions, "confirmations": confirmations}
