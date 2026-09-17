"""
Northwind Cloud Systems — synthetic company dataset for Silent Shift.
Generates: departments, employees, data resources, RBAC matrix,
role change events, and 30 days of access logs with two embedded
scenarios (real insider threat vs. legitimate role change).
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)
OUT = "/home/claude/data"
os.makedirs(OUT, exist_ok=True)

BASE_DATE = datetime(2026, 8, 1)
DAYS = 30

# ══════════════════════════════════════════
# 1. DEPARTMENTS
# ══════════════════════════════════════════
departments = pd.DataFrame([
    {"department_id": "D1", "department_name": "Engineering"},
    {"department_id": "D2", "department_name": "Finance & Accounting"},
    {"department_id": "D3", "department_name": "Human Resources"},
    {"department_id": "D4", "department_name": "Sales & Marketing"},
    {"department_id": "D5", "department_name": "Legal & Compliance"},
])
departments.to_csv(f"{OUT}/departments.csv", index=False)

# ══════════════════════════════════════════
# 2. EMPLOYEES
# ══════════════════════════════════════════
employees = pd.DataFrame([
    {"employee_id": "E01", "name": "Priya Nair",       "department_id": "D1", "role": "Senior Software Engineer", "hire_date": "2022-03-14"},
    {"employee_id": "E02", "name": "Rahul Verma",       "department_id": "D1", "role": "DevOps Engineer",          "hire_date": "2023-01-09"},
    {"employee_id": "E03", "name": "Ananya Iyer",       "department_id": "D2", "role": "Accountant",               "hire_date": "2021-11-02"},
    {"employee_id": "E04", "name": "Vikram Shah",       "department_id": "D2", "role": "Finance Manager",          "hire_date": "2019-06-18"},
    {"employee_id": "E05", "name": "Meera Pillai",      "department_id": "D3", "role": "HR Generalist",            "hire_date": "2022-08-22"},
    {"employee_id": "E06", "name": "Arjun Menon",       "department_id": "D3", "role": "HR Manager",               "hire_date": "2020-02-11"},
    {"employee_id": "E07", "name": "Kavya Reddy",       "department_id": "D4", "role": "Sales Executive",          "hire_date": "2023-05-30"},
    {"employee_id": "E08", "name": "Rohan Kapoor",      "department_id": "D4", "role": "Marketing Lead",           "hire_date": "2021-09-13"},
    {"employee_id": "E09", "name": "Sanjana Rao",       "department_id": "D5", "role": "Legal Counsel",            "hire_date": "2020-10-05"},
    {"employee_id": "E10", "name": "Aditya Krishnan",   "department_id": "D5", "role": "Compliance Officer",       "hire_date": "2022-01-17"},
])
employees.to_csv(f"{OUT}/employees.csv", index=False)

# ══════════════════════════════════════════
# 3. DATA RESOURCES
# ══════════════════════════════════════════
data_resources = pd.DataFrame([
    {"resource_id": "R1", "filename": "engineering_source_repos.csv", "owning_department_id": "D1", "sensitivity": "Confidential"},
    {"resource_id": "R2", "filename": "infra_credentials.csv",        "owning_department_id": "D1", "sensitivity": "Restricted"},
    {"resource_id": "R3", "filename": "financial_ledger.csv",         "owning_department_id": "D2", "sensitivity": "Confidential"},
    {"resource_id": "R4", "filename": "payroll_records.csv",          "owning_department_id": "D2", "sensitivity": "Restricted"},
    {"resource_id": "R5", "filename": "employee_pii.csv",             "owning_department_id": "D3", "sensitivity": "Restricted"},
    {"resource_id": "R6", "filename": "customer_crm_data.csv",        "owning_department_id": "D4", "sensitivity": "Confidential"},
    {"resource_id": "R7", "filename": "legal_contracts.csv",          "owning_department_id": "D5", "sensitivity": "Confidential"},
    {"resource_id": "R8", "filename": "compliance_audit_logs.csv",    "owning_department_id": "D5", "sensitivity": "Internal"},
])
data_resources.to_csv(f"{OUT}/data_resources.csv", index=False)

# ══════════════════════════════════════════
# 4. ACCESS CONTROL MATRIX (RBAC ground truth)
# ══════════════════════════════════════════
access_control_matrix = pd.DataFrame([
    {"role": "Senior Software Engineer",             "resource_id": "R1", "permission": "write"},
    {"role": "Senior Software Engineer",             "resource_id": "R2", "permission": "read"},
    {"role": "DevOps Engineer",                       "resource_id": "R1", "permission": "read"},
    {"role": "DevOps Engineer",                       "resource_id": "R2", "permission": "write"},
    {"role": "Accountant",                            "resource_id": "R3", "permission": "read"},
    {"role": "Accountant",                            "resource_id": "R4", "permission": "read"},
    {"role": "Finance Manager",                       "resource_id": "R3", "permission": "write"},
    {"role": "Finance Manager",                       "resource_id": "R4", "permission": "write"},
    {"role": "Finance Manager",                       "resource_id": "R8", "permission": "read"},
    {"role": "HR Generalist",                         "resource_id": "R5", "permission": "read"},
    {"role": "HR Business Partner - Engineering",     "resource_id": "R5", "permission": "read"},
    {"role": "HR Business Partner - Engineering",     "resource_id": "R1", "permission": "read"},
    {"role": "HR Manager",                            "resource_id": "R5", "permission": "write"},
    {"role": "Sales Executive",                       "resource_id": "R6", "permission": "read"},
    {"role": "Marketing Lead",                        "resource_id": "R6", "permission": "write"},
    {"role": "Legal Counsel",                         "resource_id": "R7", "permission": "write"},
    {"role": "Legal Counsel",                         "resource_id": "R8", "permission": "read"},
    {"role": "Compliance Officer",                    "resource_id": "R7", "permission": "read"},
    {"role": "Compliance Officer",                    "resource_id": "R8", "permission": "write"},
])
access_control_matrix.to_csv(f"{OUT}/access_control_matrix.csv", index=False)

# ══════════════════════════════════════════
# 5. ROLE CHANGE EVENTS (HR/Workday webhook log)
# ══════════════════════════════════════════
role_change_events = pd.DataFrame([
    {
        "employee_id": "E05", "employee_name": "Meera Pillai",
        "old_role": "HR Generalist", "new_role": "HR Business Partner - Engineering",
        "effective_day": 20, "effective_date": (BASE_DATE + timedelta(days=19)).strftime("%Y-%m-%d"),
        "reason": "Promotion - embedded HR partner for Engineering org"
    },
])
role_change_events.to_csv(f"{OUT}/role_change_events.csv", index=False)

# ══════════════════════════════════════════
# 6. ACCESS LOGS (the telemetry)
# ══════════════════════════════════════════
# authorized resource sets per role (built from the matrix above)
role_resources = access_control_matrix.groupby("role")["resource_id"].apply(list).to_dict()

emp_role = dict(zip(employees.employee_id, employees.role))
emp_dept = dict(zip(employees.employee_id, employees.department_id))

logs = []
log_id = 1

def effective_role(emp_id, day):
    """Role change resolution: was this employee promoted by this day?"""
    ev = role_change_events[role_change_events.employee_id == emp_id]
    if not ev.empty and day >= ev.iloc[0]["effective_day"]:
        return ev.iloc[0]["new_role"]
    return emp_role[emp_id]

for emp_id in employees.employee_id:
    base_role = emp_role[emp_id]
    normal_resources = role_resources.get(base_role, [])

    for day in range(1, DAYS + 1):
        ts_base = BASE_DATE + timedelta(days=day - 1)

        # baseline daily activity: 0-2 normal access events
        n_events = np.random.choice([0, 1, 1, 2], p=[0.15, 0.45, 0.25, 0.15])

        # ── SCENARIO 1: Ananya Iyer (E03) — real insider threat ──
        if emp_id == "E03" and day >= 20:
            targets = normal_resources + (["R1", "R2"] if np.random.rand() < 0.7 else [])
        # ── SCENARIO 2: Meera Pillai (E05) — legitimate promotion ──
        elif emp_id == "E05" and day >= 20:
            eff_role = effective_role(emp_id, day)
            targets = role_resources.get(eff_role, normal_resources)
        else:
            targets = normal_resources

        for _ in range(n_events):
            if not targets:
                continue
            resource_id = np.random.choice(targets)
            action = np.random.choice(["view", "download", "export"], p=[0.6, 0.3, 0.1])
            volume_mb = round(max(0.5, np.random.normal(35, 12)), 2)
            if action == "export":
                volume_mb *= np.random.uniform(1.5, 3.0)
            hour = int(np.random.choice(
                [9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 22, 1],
                p=[0.13, 0.13, 0.12, 0.08, 0.08, 0.12, 0.12, 0.1, 0.06, 0.03, 0.02, 0.01]
            ))
            ts = ts_base.replace(hour=hour, minute=int(np.random.randint(0, 60)))

            logs.append({
                "log_id": f"L{log_id:05d}",
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "day": day,
                "employee_id": emp_id,
                "resource_id": resource_id,
                "action": action,
                "volume_mb": round(volume_mb, 2),
            })
            log_id += 1

access_logs = pd.DataFrame(logs).sort_values(["day", "timestamp"]).reset_index(drop=True)
access_logs.to_csv(f"{OUT}/access_logs.csv", index=False)

# ══════════════════════════════════════════
# Summary
# ══════════════════════════════════════════
print("Generated files:")
for f in ["departments", "employees", "data_resources", "access_control_matrix", "role_change_events", "access_logs"]:
    df = pd.read_csv(f"{OUT}/{f}.csv")
    print(f"  {f}.csv — {len(df)} rows")

print(f"\nTotal access log events: {len(access_logs)}")
print(f"Ananya Iyer (E03) unauthorized accesses (R1/R2) after day 20:")
print(access_logs[(access_logs.employee_id == "E03") & (access_logs.resource_id.isin(["R1", "R2"]))].shape[0], "events")
print(f"Meera Pillai (E05) R1 accesses after day 20 (now legitimate):")
print(access_logs[(access_logs.employee_id == "E05") & (access_logs.resource_id == "R1")].shape[0], "events")
