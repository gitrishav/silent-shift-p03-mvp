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

1. **Learns each employee's personal "normal"** — how much data they usually download, which systems they usually touch, when they usually log in.
2. **Watches for drift away from that personal normal** — not compared to everyone else, just compared to their own past behavior.
3. **Double-checks with HR before raising an alarm** — if someone's behavior changed because they got promoted or switched teams, the system recognizes that and stays quiet instead of triggering a false alert.

The result: real threats get caught earlier, and security teams stop drowning in noise.

---

## How it works, step by step

We built this as four separate stages, like an assembly line. Each stage does one job and passes its output to the next.

### 1️⃣ Data Collector
Watches what an employee does and logs it — how much data they downloaded that day, whether they accessed unusual areas of the system, whether they logged in outside normal work hours.

### 2️⃣ Baseline Builder
For the first 15 days, the system just observes — no judging yet. It calculates each employee's personal "normal range" for each behavior (e.g., "this person usually downloads 50MB a day, give or take 10MB").

### 3️⃣ Scoring Engine (the math brain)
Every day after that, the system compares the employee's *current* behavior to *their own* normal range and calculates how unusual it is. This produces a single number: the **Threat Score**.

Three things are measured and combined into that score:
- How much extra data they're downloading (**Velocity Risk**)
- How much they're accessing unfamiliar parts of the system (**Spatial Risk**)
- Whether they're active at odd hours (**Temporal Risk**)

Each factor can be weighted differently — in our engine, unusual system access counts for more than extra downloads, because sneaking into new areas is a stronger red flag than downloading a bit more than usual.

### 4️⃣ Context Resolver (the "don't cry wolf" step)
Before sounding any alarm, the system checks: *did this person's role or team change recently?* If HR confirms a legitimate reason for the behavior shift (like a promotion), the system automatically lowers the threat score for that period — preventing a false alarm.

---

## The Dashboard (what you actually see)

We built a live control-room-style dashboard where you can:

- **Watch threat scores change over time** for each employee, like a heart-rate monitor
- **See real-time alerts** when someone crosses the danger threshold
- **Flip the HR Context switch on and off** and literally watch a false alarm disappear once the system realizes "oh, this was just a promotion"
- **Adjust the weighting sliders** live — decide on the fly whether unusual access, data volume, or odd-hour activity should matter more

---

## Why this is different from a typical AI security tool

Most anomaly-detection tools are a **"black box"** — they spit out a risk score with no explanation. Security teams can't act on a score they can't justify.

Our system is **fully transparent**. Every single score can be traced back to plain math: *"this person downloaded X amount, which is Y standard deviations above their normal, weighted by Z."* A human can look at any alert and immediately understand why it fired — and adjust the model if it doesn't seem right.

---

## The one-line pitch

> Instead of one-size-fits-all security rules, Silent Shift learns each employee's personal "normal," catches slow and sneaky shifts away from it, and automatically filters out false alarms caused by legitimate changes like promotions — all while staying fully explainable, never a black box.

---

## Running it yourself

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the link it gives you (usually `localhost:8501`) in your browser.

---

## Tech Stack

- **Python** — core language
- **Pandas / NumPy** — the math behind the scoring engine
- **Streamlit** — the live dashboard
- **Plotly** — the interactive charts

---

## Team

P03 — Silent Shift · Manipal Hackathon 2026