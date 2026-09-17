"""
FreightIQ Local Storage & Audit Log Module

Uses local SQLite database for software-only shipment workspace persistence,
decision versioning, operational audit trail, and workspace context without external cloud dependencies.
"""

import sqlite3
import json
import datetime
import os
from typing import Dict, Any, List, Optional, Union

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "freightiq_workspace.db"))


def init_db(db_path: str = DB_PATH):
    """Initializes SQLite database tables for shipments, decision versions, and audit logs."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Shipments Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shipments (
            shipment_id TEXT PRIMARY KEY,
            cargo_name TEXT,
            quantity_tonnes REAL,
            origin TEXT,
            destination TEXT,
            vessel_class TEXT,
            laytime_hours REAL,
            demurrage_rate REAL,
            risk_tolerance TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT,
            payload_json TEXT
        )
    """)

    # Decision Versioning Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decision_versions (
            version_id TEXT PRIMARY KEY,
            shipment_id TEXT,
            version_number INTEGER,
            recommended_date TEXT,
            vessel_class TEXT,
            destination TEXT,
            expected_cost_usd REAL,
            expected_cost_inr_cr REAL,
            robustness_score INTEGER,
            reason TEXT,
            created_at TEXT,
            payload_json TEXT
        )
    """)

    # Audit Trail Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            shipment_id TEXT,
            event_type TEXT,
            action TEXT,
            old_value TEXT,
            new_value TEXT,
            source_mode TEXT,
            reason TEXT,
            details TEXT,
            decision_version TEXT,
            snapshot_json TEXT
        )
    """)

    # Migrate stale schema: old DBs used 'log_id' as PK; current schema uses 'id'.
    cursor.execute("PRAGMA table_info(audit_logs)")
    existing_cols = [col[1] for col in cursor.fetchall()]
    if "log_id" in existing_cols and "id" not in existing_cols:
        cursor.execute("ALTER TABLE audit_logs RENAME COLUMN log_id TO id")
        # Re-read after rename
        cursor.execute("PRAGMA table_info(audit_logs)")
        existing_cols = [col[1] for col in cursor.fetchall()]

    expected_audit_cols = {
        "timestamp": "TEXT",
        "shipment_id": "TEXT",
        "event_type": "TEXT",
        "action": "TEXT",
        "old_value": "TEXT",
        "new_value": "TEXT",
        "source_mode": "TEXT",
        "reason": "TEXT",
        "details": "TEXT",
        "decision_version": "TEXT",
        "snapshot_json": "TEXT"
    }
    if existing_cols:
        for col_name, col_type in expected_audit_cols.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE audit_logs ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()




def initialize_storage(db_path: str = DB_PATH):
    """Alias for init_db."""
    init_db(db_path)


# Initialize DB on module load safely
init_db()


def save_shipment(shipment_data: Dict[str, Any], db_path: str = DB_PATH) -> str:
    """Saves or updates a shipment workspace in SQLite."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    shipment_id = shipment_data.get("shipment_id", "FIQ-2026-0001")
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO shipments (
            shipment_id, cargo_name, quantity_tonnes, origin, destination,
            vessel_class, laytime_hours, demurrage_rate, risk_tolerance,
            status, created_at, updated_at, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(shipment_id) DO UPDATE SET
            cargo_name=excluded.cargo_name,
            quantity_tonnes=excluded.quantity_tonnes,
            origin=excluded.origin,
            destination=excluded.destination,
            vessel_class=excluded.vessel_class,
            laytime_hours=excluded.laytime_hours,
            demurrage_rate=excluded.demurrage_rate,
            risk_tolerance=excluded.risk_tolerance,
            status=excluded.status,
            updated_at=excluded.updated_at,
            payload_json=excluded.payload_json
    """, (
        shipment_id,
        shipment_data.get("cargo_type", shipment_data.get("cargo_name", "Coking Coal")),
        float(shipment_data.get("quantity_tonnes", 75000.0)),
        shipment_data.get("origin", "Australia"),
        shipment_data.get("destination", "Paradip"),
        shipment_data.get("vessel_class", "Auto"),
        float(shipment_data.get("laytime_hours", 72.0)),
        float(shipment_data.get("demurrage_rate", 22000.0)),
        shipment_data.get("risk_tolerance", "Medium"),
        "Active Workspace",
        now_str,
        now_str,
        json.dumps(shipment_data)
    ))

    # Log Audit Record
    cursor.execute("""
        INSERT INTO audit_logs (timestamp, shipment_id, event_type, action, details, snapshot_json)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        now_str,
        shipment_id,
        "SAVE_SHIPMENT",
        "SAVE_SHIPMENT",
        f"Saved shipment {shipment_id} ({shipment_data.get('cargo_type', 'Coking Coal')} {shipment_data.get('quantity_tonnes', 75000.0):,.0f}t)",
        json.dumps(shipment_data)
    ))

    conn.commit()
    conn.close()
    return shipment_id


def save_shipment_to_db(
    shipment_id: str,
    cargo_type: str,
    quantity_tonnes: float,
    origin: str,
    destination: str,
    db_path: str = DB_PATH
) -> str:
    """Helper wrapper to save a shipment workspace to SQLite."""
    data = {
        "shipment_id": shipment_id,
        "cargo_type": cargo_type,
        "quantity_tonnes": quantity_tonnes,
        "origin": origin,
        "destination": destination
    }
    return save_shipment(data, db_path=db_path)


def load_shipment(shipment_id: str = "FIQ-2026-0001", db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Loads shipment workspace data from SQLite."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT payload_json FROM shipments WHERE shipment_id = ?", (shipment_id,))
    row = cursor.fetchone()
    conn.close()

    if row and row[0]:
        return json.loads(row[0])
    return None


def load_shipment_from_db(shipment_id: str = "FIQ-2026-0001", db_path: str = DB_PATH) -> Optional[Dict[str, Any]]:
    """Alias for load_shipment."""
    return load_shipment(shipment_id, db_path=db_path)


def list_shipments(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns all saved shipments."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT shipment_id, cargo_name, quantity_tonnes, origin, destination, updated_at FROM shipments ORDER BY updated_at DESC")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "shipment_id": r[0],
            "cargo_name": r[1],
            "quantity_tonnes": r[2],
            "origin": r[3],
            "destination": r[4],
            "updated_at": r[5]
        }
        for r in rows
    ]


def list_saved_shipments(db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Alias for list_shipments."""
    return list_shipments(db_path=db_path)


def get_active_shipment_context() -> Dict[str, Any]:
    """Returns active shipment workspace from Streamlit session_state or default."""
    try:
        import streamlit as st
        if "shipment_workspace" not in st.session_state:
            st.session_state["shipment_workspace"] = {
                "shipment_id": "FIQ-2026-0001",
                "cargo_type": "Coking Coal",
                "quantity_tonnes": 75000.0,
                "origin": "Australia",
                "destination": "Paradip",
                "vessel_class": "Auto",
                "laytime_hours": 72.0,
                "demurrage_rate": 22000.0,
                "risk_tolerance": "Medium"
            }
        return st.session_state["shipment_workspace"]
    except Exception:
        return {
            "shipment_id": "FIQ-2026-0001",
            "cargo_type": "Coking Coal",
            "quantity_tonnes": 75000.0,
            "origin": "Australia",
            "destination": "Paradip",
            "vessel_class": "Auto",
            "laytime_hours": 72.0,
            "demurrage_rate": 22000.0,
            "risk_tolerance": "Medium"
        }


def set_active_shipment_context(**kwargs) -> Dict[str, Any]:
    """Updates active shipment workspace context in Streamlit session_state."""
    ctx = get_active_shipment_context()
    for k, v in kwargs.items():
        if v is not None:
            ctx[k] = v
    try:
        import streamlit as st
        st.session_state["shipment_workspace"] = ctx
    except Exception:
        pass
    return ctx


def update_active_shipment_context(**kwargs) -> Dict[str, Any]:
    """Alias for set_active_shipment_context."""
    return set_active_shipment_context(**kwargs)


def append_audit_log(
    shipment_id: Optional[str] = "FIQ-2026-0001",
    action: str = "AUDIT_EVENT",
    details: str = "",
    event_type: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    source_mode: Optional[str] = "DEMO",
    reason: Optional[str] = None,
    decision_version: Optional[str] = None,
    db_path: str = DB_PATH
) -> int:
    """Appends an audit log record to SQLite database."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    evt = event_type or action

    cursor.execute("""
        INSERT INTO audit_logs (
            timestamp, shipment_id, event_type, action,
            old_value, new_value, source_mode, reason, details, decision_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        now_str,
        shipment_id,
        evt,
        action,
        old_value,
        new_value,
        source_mode,
        reason,
        details,
        decision_version
    ))

    log_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return log_id


def log_audit_event(shipment_id: str, action: str, details: str, db_path: str = DB_PATH):
    """Alias for append_audit_log."""
    append_audit_log(shipment_id=shipment_id, action=action, details=details, db_path=db_path)


def get_audit_trail(
    shipment_id: Optional[str] = None,
    limit: int = 100,
    db_path: str = DB_PATH
) -> List[Dict[str, Any]]:
    """
    Queries the audit_logs table and returns newest-first records.
    Returns [] if empty or table missing.
    """
    try:
        init_db(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        if shipment_id:
            cursor.execute("""
                SELECT id, timestamp, shipment_id, event_type, action, old_value, new_value, source_mode, reason, details, decision_version
                FROM audit_logs
                WHERE shipment_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (shipment_id, limit))
        else:
            cursor.execute("""
                SELECT id, timestamp, shipment_id, event_type, action, old_value, new_value, source_mode, reason, details, decision_version
                FROM audit_logs
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        records = []
        for r in rows:
            records.append({
                "id": r[0],
                "timestamp": r[1],
                "shipment_id": r[2],
                "event_type": r[3] or r[4] or "EVENT",
                "action": r[4] or r[3] or "ACTION",
                "old_value": r[5] or "-",
                "new_value": r[6] or "-",
                "source_mode": r[7] or "DEMO",
                "reason": r[8] or "-",
                "details": r[9] or "",
                "decision_version": r[10] or "-"
            })
        return records
    except sqlite3.OperationalError as exc:
        import sys
        print(f"[get_audit_trail] SQLite error: {exc}", file=sys.stderr)
        return []


def get_audit_logs(
    shipment_id: Optional[str] = None,
    limit: int = 100,
    db_path: str = DB_PATH
) -> List[Dict[str, Any]]:
    """Alias for get_audit_trail."""
    return get_audit_trail(shipment_id=shipment_id, limit=limit, db_path=db_path)


def save_decision_version(
    shipment_id: str,
    recommendation: Union[Dict[str, Any], int],
    version_number: Optional[int] = None,
    reason: str = "Baseline Optimization",
    db_path: str = DB_PATH
) -> str:
    """Logs a new decision version for an active shipment."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if isinstance(recommendation, int) and version_number is None:
        version_num = recommendation
        rec_dict = version_number if isinstance(version_number, dict) else {}
    elif isinstance(version_number, int):
        version_num = version_number
        rec_dict = recommendation if isinstance(recommendation, dict) else {}
    else:
        # Auto-query max version number for shipment
        cursor.execute("SELECT MAX(version_number) FROM decision_versions WHERE shipment_id = ?", (shipment_id,))
        row_max = cursor.fetchone()
        max_v = row_max[0] if (row_max and row_max[0] is not None) else 0
        version_num = max_v + 1
        rec_dict = recommendation if isinstance(recommendation, dict) else {}

    version_id = f"{shipment_id}_v{version_num}"

    tot_usd = float(rec_dict.get("expected_total_logistics_cost_usd", rec_dict.get("expected_cost_usd", 0.0)))
    tot_inr_cr = round((tot_usd * 84.0) / 1e7, 4) if tot_usd > 0 else 0.0
    rob_score = int(rec_dict.get("robustness_score")) if rec_dict.get("robustness_score") is not None else None

    cursor.execute("""
        INSERT INTO decision_versions (
            version_id, shipment_id, version_number, recommended_date,
            vessel_class, destination, expected_cost_usd, expected_cost_inr_cr,
            robustness_score, reason, created_at, payload_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(version_id) DO UPDATE SET
            recommended_date=excluded.recommended_date,
            vessel_class=excluded.vessel_class,
            destination=excluded.destination,
            expected_cost_usd=excluded.expected_cost_usd,
            expected_cost_inr_cr=excluded.expected_cost_inr_cr,
            robustness_score=excluded.robustness_score,
            reason=excluded.reason,
            created_at=excluded.created_at,
            payload_json=excluded.payload_json
    """, (
        version_id,
        shipment_id,
        version_num,
        rec_dict.get("recommended_charter_date", rec_dict.get("recommended_window", "-")),
        rec_dict.get("recommended_vessel", rec_dict.get("vessel_class", "-")),
        rec_dict.get("destination", "-"),
        tot_usd,
        tot_inr_cr,
        rob_score,
        reason,
        now_str,
        json.dumps(rec_dict)
    ))

    conn.commit()
    conn.close()

    # Append audit trail record
    append_audit_log(
        shipment_id=shipment_id,
        action="SAVE_DECISION_VERSION",
        details=f"Saved decision version v{version_num} ({reason})",
        decision_version=version_id,
        db_path=db_path
    )

    return version_id


def get_decision_versions(shipment_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Returns decision history for a shipment."""
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT version_number, reason, created_at, payload_json FROM decision_versions WHERE shipment_id = ? ORDER BY version_number DESC", (shipment_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"version": r[0], "reason": r[1], "created_at": r[2], "recommendation": json.loads(r[3]) if r[3] else {}} for r in rows]



def get_decision_history(shipment_id: str, db_path: str = DB_PATH) -> List[Dict[str, Any]]:
    """Alias for get_decision_versions."""
    return get_decision_versions(shipment_id, db_path=db_path)


def log_decision_version(shipment_id: str, recommendation: Union[Dict[str, Any], int], version_number: Optional[int] = None, reason: str = "Baseline Optimization", db_path: str = DB_PATH) -> str:
    """Alias for save_decision_version."""
    return save_decision_version(shipment_id, recommendation, version_number=version_number, reason=reason, db_path=db_path)

