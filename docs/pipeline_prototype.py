"""
Silent Shift OS — Pipeline Prototype
Real implementation of Ingestion Worker -> Context Resolver ->
Threat Scoring Worker -> Alert Generator, run against the live
Part 2 Postgres schema. Collapsed into sequential calls for the
demo; in production each stage is a separate async worker
consuming its own queue.
"""
import psycopg2
import psycopg2.extras
import uuid
from datetime import datetime, timezone

conn = psycopg2.connect(dbname="silent_shift_test", user="postgres", host="/var/run/postgresql")
conn.autocommit = False
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# ══════════════════════════════════════════════════
# SETUP — seed one department, one employee, one resource
# (mirrors Ananya's scenario from the CSV dataset)
# ══════════════════════════════════════════════════
dept_id = str(uuid.uuid4())
emp_id = str(uuid.uuid4())
role_id = str(uuid.uuid4())
resource_id = str(uuid.uuid4())
device_id = str(uuid.uuid4())
session_id = str(uuid.uuid4())

cur.execute("INSERT INTO departments (department_id, name) VALUES (%s, %s)",
            (dept_id, "Finance & Accounting"))
cur.execute("""INSERT INTO employees (employee_id, full_name, email, department_id, hire_date)
                VALUES (%s, %s, %s, %s, %s)""",
            (emp_id, "Ananya Iyer", "ananya@northwind.io", dept_id, "2021-11-02"))
cur.execute("INSERT INTO roles (role_id, role_name) VALUES (%s, %s)", (role_id, "Accountant"))
cur.execute("INSERT INTO employee_role_history (employee_id, role_id, effective_from) VALUES (%s, %s, %s)",
            (emp_id, role_id, "2021-11-02"))
cur.execute("""INSERT INTO resources (resource_id, resource_type, name, sensitivity)
                VALUES (%s, %s, %s, %s)""",
            (resource_id, "file", "infra_credentials.csv", "restricted"))
cur.execute("""INSERT INTO devices (device_id, employee_id, device_type, ownership, fingerprint_hash, is_trusted)
                VALUES (%s, %s, %s, %s, %s, %s)""",
            (device_id, emp_id, "laptop", "company", "fp_ananya_01", True))
cur.execute("INSERT INTO sessions (session_id, employee_id, device_id, mfa_success) VALUES (%s, %s, %s, %s)",
            (session_id, emp_id, device_id, True))

# Permission matrix: Accountant has NO grant on this resource — intentional gap
# (in the real system, role_permissions would list what Accountant CAN access;
#  we deliberately leave infra_credentials.csv absent from it)

conn.commit()
print(f"Seeded: Ananya Iyer ({emp_id[:8]}...) as Accountant, resource infra_credentials.csv ({resource_id[:8]}...)")
print()


# ══════════════════════════════════════════════════
# STAGE 1 — INGESTION WORKER
# ══════════════════════════════════════════════════
def ingest_event(event_type, actor_id, target_resource, device, session, source_system, metadata):
    """Mirrors the Ingestion Worker: writes the append-only fact."""
    event_id = str(uuid.uuid4())
    occurred_at = datetime.now(timezone.utc)
    cur.execute("""
        INSERT INTO events (event_id, event_type, actor_employee_id, target_resource_id,
                             device_id, session_id, source_system, metadata, occurred_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (event_id, occurred_at) DO NOTHING
    """, (event_id, event_type, actor_id, target_resource, device, session,
          source_system, psycopg2.extras.Json(metadata), occurred_at))
    conn.commit()
    return event_id, occurred_at


# ══════════════════════════════════════════════════
# STAGE 2 — CONTEXT RESOLVER
# ══════════════════════════════════════════════════
def resolve_context(actor_id, resource_id):
    """Mirrors the Context Resolver: what role does this person hold
    right now, and does that role have any grant on this resource?"""
    cur.execute("""
        SELECT r.role_name
        FROM employee_role_history erh
        JOIN roles r ON r.role_id = erh.role_id
        WHERE erh.employee_id = %s AND erh.effective_to IS NULL
    """, (actor_id,))
    role_row = cur.fetchone()
    role_name = role_row["role_name"] if role_row else None

    cur.execute("""
        SELECT 1 FROM resource_permissions
        WHERE employee_id = %s AND resource_id = %s AND revoked_at IS NULL
        UNION
        SELECT 1 FROM temporary_permissions
        WHERE employee_id = %s AND resource_id = %s AND expires_at > now()
    """, (actor_id, resource_id, actor_id, resource_id))
    authorized = cur.fetchone() is not None

    return role_name, authorized


# ══════════════════════════════════════════════════
# STAGE 3 — ANOMALY + THREAT SCORING WORKER
# ══════════════════════════════════════════════════
def score_and_flag(event_id, occurred_at, actor_id, role_name, authorized, resource_name):
    """Mirrors the combined Anomaly + Threat Scoring Worker."""
    if not authorized:
        anomaly_id = str(uuid.uuid4())
        explanation = f"{role_name} accessed {resource_name} — no authorization on file"
        cur.execute("""
            INSERT INTO anomalies (anomaly_id, event_id, event_occurred_at, employee_id,
                                    anomaly_type, severity, confidence, explanation, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (anomaly_id, event_id, occurred_at, actor_id, "rbac_violation",
              "critical", 0.97, explanation, "open"))

        overall_risk = 92  # in production: weighted formula pulling device/network/behavioral risk too
        cur.execute("""
            INSERT INTO threat_scores (employee_id, overall_risk, identity_risk, device_risk)
            VALUES (%s, %s, %s, %s)
        """, (actor_id, overall_risk, 10, 5))

        conn.commit()
        print(f"  ANOMALY  severity=critical  {explanation}")
        print(f"  THREAT SCORE  overall_risk={overall_risk}")
        return anomaly_id, overall_risk
    else:
        conn.commit()
        print("  No anomaly — access authorized")
        return None, 0


# ══════════════════════════════════════════════════
# STAGE 4 — ALERT GENERATOR
# ══════════════════════════════════════════════════
def generate_alert(actor_id, anomaly_id, overall_risk, threshold=40):
    """Mirrors the Alert Generator: opens or extends an alert if
    risk crosses the configured threshold."""
    if overall_risk <= threshold or anomaly_id is None:
        return None

    cur.execute("""
        SELECT alert_id FROM alerts
        WHERE employee_id = %s AND status IN ('open', 'investigating')
        ORDER BY opened_at DESC LIMIT 1
    """, (actor_id,))
    existing = cur.fetchone()

    if existing:
        alert_id = existing["alert_id"]
        print(f"  ALERT  extending existing alert {alert_id[:8]}... with new evidence")
    else:
        alert_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO alerts (alert_id, employee_id, title, status)
            VALUES (%s, %s, %s, %s)
        """, (alert_id, actor_id, "Unauthorized access to restricted resource", "open"))
        print(f"  ALERT  new alert opened {alert_id[:8]}...")

    cur.execute("INSERT INTO alert_anomalies (alert_id, anomaly_id) VALUES (%s, %s)",
                (alert_id, anomaly_id))
    conn.commit()
    return alert_id


# ══════════════════════════════════════════════════
# RUN THE FULL PIPELINE — two events, showing both outcomes
# ══════════════════════════════════════════════════
print("═" * 60)
print("EVENT 1: Ananya downloads infra_credentials.csv (unauthorized)")
print("═" * 60)
event_id, occurred_at = ingest_event(
    "file_download", emp_id, resource_id, device_id, session_id,
    "file_server", {"volume_mb": 45}
)
print(f"  INGESTED  event_id={event_id[:8]}...  type=file_download")

role_name, authorized = resolve_context(emp_id, resource_id)
print(f"  CONTEXT   effective_role={role_name}  authorized={authorized}")

anomaly_id, risk = score_and_flag(event_id, occurred_at, emp_id, role_name, authorized, "infra_credentials.csv")
alert_id = generate_alert(emp_id, anomaly_id, risk)

print()
print("═" * 60)
print("EVENT 2: Ananya accesses financial_ledger.csv (authorized — grant it first)")
print("═" * 60)
ledger_id = str(uuid.uuid4())
cur.execute("""INSERT INTO resources (resource_id, resource_type, name, sensitivity)
                VALUES (%s, %s, %s, %s)""", (ledger_id, "file", "financial_ledger.csv", "confidential"))
cur.execute("""INSERT INTO resource_permissions (resource_id, employee_id, access_level)
                VALUES (%s, %s, %s)""", (ledger_id, emp_id, "read"))
conn.commit()

event_id2, occurred_at2 = ingest_event(
    "file_download", emp_id, ledger_id, device_id, session_id,
    "file_server", {"volume_mb": 12}
)
print(f"  INGESTED  event_id={event_id2[:8]}...  type=file_download")

role_name2, authorized2 = resolve_context(emp_id, ledger_id)
print(f"  CONTEXT   effective_role={role_name2}  authorized={authorized2}")

anomaly_id2, risk2 = score_and_flag(event_id2, occurred_at2, emp_id, role_name2, authorized2, "financial_ledger.csv")
generate_alert(emp_id, anomaly_id2, risk2)

# ══════════════════════════════════════════════════
# FINAL STATE CHECK — what actually landed in the database
# ══════════════════════════════════════════════════
print()
print("═" * 60)
print("FINAL DATABASE STATE")
print("═" * 60)
cur.execute("SELECT anomaly_type, severity, explanation FROM anomalies WHERE employee_id = %s", (emp_id,))
print("Anomalies:", cur.fetchall())
cur.execute("SELECT title, status FROM alerts WHERE employee_id = %s", (emp_id,))
print("Alerts:   ", cur.fetchall())
cur.execute("SELECT overall_risk FROM threat_scores WHERE employee_id = %s", (emp_id,))
print("Scores:   ", cur.fetchall())

conn.rollback()  # test run only, don't persist
cur.close()
conn.close()
print()
print("(rolled back — this was a verification run, not persisted)")
