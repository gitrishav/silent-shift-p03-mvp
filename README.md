# 🛡️ Silent Shift — Catching the Insider Before the Incident

**Manipal Hackathon 2026 · Team P03 · Track: Peace, Justice & Strong Institutions**

---

## What problem are we solving?

Imagine a company employee slowly stealing sensitive data over weeks — a little more each day. No single action looks suspicious on its own, but the pattern adds up to a serious data leak.

Traditional security tools are bad at catching this. They either:
1. **Miss it entirely** — because they only flag obvious rule-breaks (like 10 failed logins in a row), not slow drift.
2. **Cry wolf too often** — flooding security teams with false alarms whenever an employee's behavior changes for a *legitimate* reason (like a promotion), until the team starts ignoring every alert — including real threats.

**Silent Shift** is our answer to both problems.

---

## What does it actually do?

Think of it like a smart security guard for company systems. Instead of using the same rulebook for every employee, it:

1. **Checks a hard boundary first.** Every single action is checked against a real permission matrix — does this person's role have any business touching this resource? If not, that's flagged immediately, no statistics required.
2. **Learns each employee's personal "normal"** for everything *inside* their legitimate scope — how much data they usually download, when they usually log in.
3. **Watches for drift** away from that personal normal, purely within what they're actually allowed to touch.
4. **Double-checks with HR before raising an alarm** — if someone's behavior changed because they got promoted or switched teams, the system recognizes that and stays quiet instead of triggering a false alert.

The result: real threats get caught by a hard rule that can't be talked around, subtle threats get caught by behavioral drift, and false alarms caused by legitimate role changes disappear — all three, in one engine.

---

## The company behind the demo

Rather than testing this on abstract random numbers, we built it against a realistic simulated company: **Northwind Cloud Systems** — 5 departments, 10 employees, 8 real sensitive data resources (`financial_ledger.csv`, `infra_credentials.csv`, `employee_pii.csv`, and so on), and a real role-based permission matrix defining exactly who's allowed to touch what.

Two employees anchor the live demo:

- 🔴 **Ananya Iyer (Accountant)** — starts accessing engineering resources with no HR record justifying it. A real insider threat. Stays flagged, permanently, with a plain-English reason.
- 🟢 **Meera Pillai (HR Generalist)** — starts touching the *exact same* engineering resource, on the *exact same day* — but she was legitimately promoted to "HR Business Partner – Engineering" that day, logged in the system's role-change record. The engine recognizes this and clears her automatically.

Same-shaped behavior, same day, opposite outcomes — and the only way to tell them apart is checking context. That comparison is the heart of the whole pitch.

---

## How it works, step by step

We built this as four connected stages, like an assembly line.

### 1️⃣ Data Collector
Every access event gets logged — who touched what resource, when, and how much data moved.

### 2️⃣ Baseline Builder
For the first 15 days, the system just observes each employee's normal volume and timing patterns — no judging yet.

### 3️⃣ RBAC + Drift Scoring Engine
Every event gets checked two ways:
- **Is this access authorized at all?** (a hard yes/no against the real permission matrix — if not, that's an instant critical flag)
- **If it is authorized, is the volume or timing unusual for this person?** (the statistical drift check, same personal-baseline idea as before)

### 4️⃣ Context Resolver
Before any alarm reaches a human, the system checks whether HR filed a role change that would explain the behavior. If it matches, the "violation" resolves to authorized access instead of a false alarm.

---

## The Dashboard (what you actually see)

We built a live control-room-style dashboard where you can:

- **See the org roster** — every simulated employee, their department, and their role
- **Watch the money comparison** — Ananya vs. Meera's threat scores side by side, both starting to drift on the same day, one clearing and one staying critical
- **Flip the HR Context switch on and off** and literally watch a false alarm disappear once the system checks the role-change record
- **Adjust the weighting sliders** live — decide on the fly how much unusual volume vs. odd-hour activity should matter, and how harsh the penalty for an outright unauthorized access should be
- **Read the RBAC violation log** — every flagged event comes with a plain-English reason, not just a number

---

## Why this is different from a typical AI security tool

Most anomaly-detection tools are a **"black box"** — they spit out a risk score with no explanation. Security teams can't act on a score they can't justify.

Our system is **fully transparent**. Every single score can be traced back to plain math and plain facts: *"this role has no grant on this resource"* or *"this person downloaded X amount, Y standard deviations above their own normal."* A human can look at any alert and immediately understand why it fired.

---

## Running it yourself

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the link it gives you (usually `localhost:8501`) in your browser. Make sure the `data/` folder (with the six CSVs) sits in the same directory as `app.py` — the app reads from it directly.

---

## Repository structure

```
├── app.py                          # The live Streamlit dashboard + engine
├── requirements.txt
├── data/                           # Northwind Cloud Systems dataset
│   ├── departments.csv
│   ├── employees.csv
│   ├── data_resources.csv
│   ├── access_control_matrix.csv   # RBAC ground truth
│   ├── role_change_events.csv      # HR/Workday-style promotion log
│   ├── access_logs.csv             # 30 days of simulated access events
│   ├── generate_dataset.py         # Regenerates the dataset (seeded, reproducible)
│   └── SCHEMA_REDESIGN.md          # Architect notes on the RBAC redesign
└── docs/                           # Production architecture (beyond the demo)
    ├── PART1_DATABASE_DESIGN.md    # Full 35-table ER model, 12 architectural layers
    ├── part2_schema.sql            # Runnable PostgreSQL DDL — verified against a live DB
    ├── schema_diagram.jpg          # The full ER diagram, rendered
    ├── PART3_ARCHITECTURE.md       # Real-time ingestion pipeline design
    ├── pipeline_prototype.py       # Working ingestion → scoring → alert code
    ├── PART4_EXPLAINABILITY.md     # How an investigator reconstructs "why flagged"
    ├── investigator_explain.sql    # The actual query behind that
    ├── per_event_explain.sql
    └── PART5_SCALABILITY.md        # Load-tested from 20 to 20,000 employees
```

---

## Beyond the demo: production architecture

What's running in `app.py` is a simplified, faithful subset of a production design we've already built out and tested in `docs/`:

- A complete **35-table, 12-layer PostgreSQL schema** — Identity, Permissions (RBAC+ABAC), real-time Events, Behavioral Baselines, full SOC Investigation workflow
- A **real-time ingestion pipeline** design (Kafka → FastAPI → async scoring workers → WebSocket → dashboard)
- **Explainability queries** that reconstruct the full "why was this flagged" story from the schema alone
- **Load-tested scalability** — benchmarked on a live PostgreSQL instance from 20 to 20,000 simulated employees; dashboard query time held under **7 milliseconds** across a 1000x increase in data volume

None of that is theoretical — every number in `PART5_SCALABILITY.md` came from an actual `EXPLAIN ANALYZE` run against real inserted data.

---

## Tech Stack

- **Python** — core language
- **Pandas / NumPy** — the math behind the scoring engine
- **Streamlit** — the live dashboard
- **Plotly** — the interactive charts
- **PostgreSQL** — the production schema (see `docs/`)

---

## Team

Team P03 — Ethan Robin · Rishav · Aditya · Aryan
Manipal Hackathon 2026