from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3
from .domain import ClinicalTemplate, SafetyError


class Store:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS templates(name TEXT, version INTEGER, body TEXT NOT NULL,
          PRIMARY KEY(name,version));
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, at TEXT, event TEXT, status TEXT);
        CREATE TABLE IF NOT EXISTS operations(key TEXT PRIMARY KEY, status TEXT NOT NULL);
        """)

    def save_template(self, template):
        template.validate()
        version = self.db.execute("SELECT COALESCE(MAX(version),0)+1 FROM templates WHERE name=?", (template.name,)).fetchone()[0]
        template = replace(template, version=version)
        with self.db:
            self.db.execute("INSERT INTO templates VALUES(?,?,?)", (template.name, version, json.dumps(asdict(template), ensure_ascii=False)))
        return template

    def templates(self):
        return [ClinicalTemplate(**json.loads(r[0])) for r in self.db.execute(
            "SELECT body FROM templates t WHERE version=(SELECT MAX(version) FROM templates WHERE name=t.name) ORDER BY name")]

    def history(self, name):
        return [ClinicalTemplate(**json.loads(r[0])) for r in self.db.execute("SELECT body FROM templates WHERE name=? ORDER BY version", (name,))]

    def delete_template(self, name, confirmed=False):
        if not confirmed:
            raise SafetyError("Cần xác nhận xóa mẫu.")
        with self.db:
            self.db.execute("DELETE FROM templates WHERE name=?", (name,))
            if self.setting("default_template") == name:
                self.setting("default_template", "")

    def setting(self, key, value=None):
        if value is not None:
            with self.db:
                self.db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, json.dumps(value, ensure_ascii=False)))
            return value
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def export_templates(self, path):
        Path(path).write_text(json.dumps({"schema": 1, "templates": [asdict(t) for t in self.templates()]}, ensure_ascii=False, indent=2), encoding="utf-8")

    def import_templates(self, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if data.get("schema") != 1:
            raise SafetyError("Không hỗ trợ phiên bản tệp mẫu.")
        templates = [ClinicalTemplate(**item) for item in data["templates"]]
        for t in templates:
            t.validate()
        for t in templates:
            self.save_template(t)

    def backup(self, path):
        with sqlite3.connect(path) as target:
            self.db.backup(target)

    def audit(self, event, status):
        # Deliberately no clinical text, patient identity, credentials or document body.
        with self.db:
            self.db.execute("INSERT INTO audit(at,event,status) VALUES(?,?,?)", (datetime.now(timezone.utc).isoformat(), event, status))
            self.db.execute("DELETE FROM audit WHERE id NOT IN (SELECT id FROM audit ORDER BY id DESC LIMIT 1000)")

    def operation(self, key):
        row = self.db.execute("SELECT status FROM operations WHERE key=?", (key,)).fetchone()
        return row[0] if row else None

    def mark(self, key, status):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO operations VALUES(?,?)", (key, status))
