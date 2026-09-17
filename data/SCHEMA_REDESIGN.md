# Silent Shift — Schema Redesign (Architect Notes)

## Why redesign

The old engine scored abstract numbers (`volume_mb`, `spatial_moves`) against a
generic statistical baseline. It works, but it's not *explainable* to a judge
in one sentence, and it can't distinguish "this looks weird" from "this is
explicitly against policy."

The new design adds a **second, harder detection layer on top of the existing
statistical one**: a real Role-Based Access Control (RBAC) matrix, for a
fictional company — **Northwind Cloud Systems** — with real departments,
real employees, and real data resources. Now the engine can say, in plain
language: *"Ananya Iyer, an Accountant in Finance, opened
`infra_credentials.csv` — a resource her role has no legitimate reason to
touch."* That's a sentence a judge understands instantly, no math required.

The statistical engine (Z-scores, baselines) still runs underneath — it now
only has to catch *subtle drift within a person's own authorized scope*
(e.g., an engineer suddenly downloading way more than usual from repos they
ARE allowed to use). The RBAC layer catches the *obvious* boundary
violations. Two complementary signals, not one overloaded one.

---

## Company: Northwind Cloud Systems

5 departments, 10 employees, 8 sensitive data resources.

### Departments
| Dept ID | Name |
|---|---|
| D1 | Engineering |
| D2 | Finance & Accounting |
| D3 | Human Resources |
| D4 | Sales & Marketing |
| D5 | Legal & Compliance |

### Employees & Roles
| Emp ID | Name | Department | Role |
|---|---|---|---|
| E01 | Priya Nair | Engineering | Senior Software Engineer |
| E02 | Rahul Verma | Engineering | DevOps Engineer |
| E03 | Ananya Iyer | Finance & Accounting | Accountant |
| E04 | Vikram Shah | Finance & Accounting | Finance Manager |
| E05 | Meera Pillai | Human Resources | HR Generalist |
| E06 | Arjun Menon | Human Resources | HR Manager |
| E07 | Kavya Reddy | Sales & Marketing | Sales Executive |
| E08 | Rohan Kapoor | Sales & Marketing | Marketing Lead |
| E09 | Sanjana Rao | Legal & Compliance | Legal Counsel |
| E10 | Aditya Krishnan | Legal & Compliance | Compliance Officer |

### Data Resources (the CSVs each department owns)
| Resource ID | File | Owning Dept | Sensitivity |
|---|---|---|---|
| R1 | engineering_source_repos.csv | Engineering | Confidential |
| R2 | infra_credentials.csv | Engineering | Restricted |
| R3 | financial_ledger.csv | Finance | Confidential |
| R4 | payroll_records.csv | Finance | Restricted |
| R5 | employee_pii.csv | HR | Restricted |
| R6 | customer_crm_data.csv | Sales & Marketing | Confidential |
| R7 | legal_contracts.csv | Legal & Compliance | Confidential |
| R8 | compliance_audit_logs.csv | Legal & Compliance | Internal |

### Access Control Matrix (who's ALLOWED to touch what)
This is the ground truth the RBAC layer checks every access event against.

| Role | Authorized Resources |
|---|---|
| Senior Software Engineer | R1 (write), R2 (read) |
| DevOps Engineer | R1 (read), R2 (write) |
| Accountant | R3 (read), R4 (read) |
| Finance Manager | R3 (write), R4 (write), R8 (read) |
| HR Generalist | R5 (read) |
| **HR Business Partner – Engineering** *(post-promotion role)* | R5 (read), R1 (read) |
| HR Manager | R5 (write) |
| Sales Executive | R6 (read) |
| Marketing Lead | R6 (write) |
| Legal Counsel | R7 (write), R8 (read) |
| Compliance Officer | R7 (read), R8 (write) |

---

## The two demo scenarios (built into the generated data)

### 🔴 Scenario 1 — Real insider threat: Ananya Iyer (Accountant)
Days 1–19: normal — only touches `financial_ledger.csv` and
`payroll_records.csv`, exactly what an Accountant should access.

Day 20 onward: starts opening `engineering_source_repos.csv` and
`infra_credentials.csv`. **No role change was ever filed for her in HR.**
This is a flat-out RBAC violation with zero legitimate explanation —
the engine flags this as CRITICAL and the Context Resolver has nothing
to suppress, because there's no matching HR event for her.

### 🟢 Scenario 2 — Legitimate role change: Meera Pillai (HR Generalist)
Days 1–19: normal — only touches `employee_pii.csv`, standard for HR.

Day 20 onward: also starts opening `engineering_source_repos.csv`.
**On the surface, this looks identical to Ananya's pattern** — a
non-engineering employee suddenly touching engineering resources.

The difference: HR filed a real promotion event for Meera on day 20 —
she moved from **HR Generalist** to **HR Business Partner – Engineering**,
a role that legitimately includes read access to R1 (to support
performance reviews with the engineering team). The Context Resolver
checks `role_change_events.csv`, finds the match, updates her effective
role as of day 20, and the "violation" resolves to authorized access.
No alert.

**This is the pitch moment:** two employees, same-shaped behavior change,
same day — one is flagged forever, one clears the moment the system
checks HR. That's the entire value proposition in one side-by-side
comparison.

---

## New file schema

| File | Purpose | Feeds into |
|---|---|---|
| `departments.csv` | Department reference table | context/display |
| `employees.csv` | Employee roster, home department, original role | Baseline Builder |
| `data_resources.csv` | The sensitive files that exist and who owns them | RBAC layer |
| `access_control_matrix.csv` | Role → Resource → permission level | RBAC layer (ground truth) |
| `role_change_events.csv` | HR/Workday-style promotion log (replaces the old hardcoded `hr_context` dict) | Context Resolver |
| `access_logs.csv` | The actual telemetry — who accessed what, when, how much | Data Collector → Scoring Engine |

## Updated scoring formula

```
For each access event:

  1. RBAC CHECK (hard rule, not statistical):
     effective_role = employee's role as of that day
                       (checks role_change_events.csv for anything
                        effective on or before this date)
     authorized = (effective_role, resource) exists in access_control_matrix.csv

     if not authorized:
         RBAC_violation = True → flat +50 to threat score, CRITICAL badge,
         "why" shown in plain English: "{role} has no access to {resource}"

  2. STATISTICAL DRIFT (only computed on AUTHORIZED accesses):
     same Z-score pipeline as before — volume vs personal baseline,
     access timing vs personal baseline — catches subtle anomalies
     within a person's legitimate scope

  Final Threat Score = (RBAC_violation × 50) + (statistical Z-score × weights × 10)
```

The Context Resolver's job changes from "subtract a flat number" to
"determine which role was effective on this date" — which is a more
honest simulation of how a real HR-integrated system would work.
