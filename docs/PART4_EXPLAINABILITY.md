# Silent Shift OS — Explainability
## Part 4: How an investigator understands why an account became suspicious

---

## The principle

Every score, every anomaly, every alert in this system must be traceable
back to specific rows an investigator can point at. There is no step
anywhere in the pipeline where a number comes from a model an analyst
can't interrogate. If a SOC analyst asks "why is this person flagged,"
the honest answer is always a SQL query away, not a shrug at a neural
network's output.

Two queries make this real, both run live against the actual Part 2/3
schema, both shown below with real output — not illustrative, not
hypothetical.

---

## Query 1: "Why did this alert fire?" (`investigator_explain.sql`)

This is what renders the moment an analyst clicks into an alert on the
dashboard. Given one `alert_id`, it walks backward through
`alert_anomalies` → `anomalies` → `events`, and — this is the part that
matters — joins against `employee_role_history` filtered to **the role
held at the moment the event happened**, not the employee's role today.
That distinction is everything: an investigator needs to know what was
true *then*, because permissions and roles both drift over time.

**Run against Ananya Iyer's real alert:**

```
full_name               | Ananya Iyer
department               | Finance & Accounting
alert_title               | Unauthorized access to Engineering resource
alert_status               | open
anomaly_type                | rbac_violation
severity                     | critical
confidence                    | 0.970
explanation                    | Accountant accessed engineering_source_repos.csv — no authorization on file
event_type                       | git_clone
resource_name                      | engineering_source_repos.csv
resource_sensitivity                 | confidential
device_trusted                         | t
role_held_at_event_time                  | Accountant
role_change_context                        | (empty)
role_had_permission                          | f
current_threat_score                           | 91
```

An investigator reads this top to bottom and has the entire story in
fifteen seconds: Ananya, an Accountant in Finance, cloned a confidential
Engineering repo from a trusted device (so it's not a compromised-device
story), her role at that exact moment had no permission grant on that
resource, and nothing in her role history explains why she'd need it.
Nothing here required trusting a model's confidence score in isolation
— every field is a fact pulled from a specific table.

---

## Query 2: "Why did this identical-looking access NOT fire?" (`per_event_explain.sql`)

This is the harder, more important half of explainability — proving the
system isn't just good at explaining what it flagged, but that it made
the *right call* on something that looks identical on the surface.

Meera Pillai touched the exact same resource
(`engineering_source_repos.csv`), the same day, the same event type
(`git_clone`), from a trusted device — structurally indistinguishable
from Ananya's case at a glance. This query runs the same authorization
logic directly against her event, with no alert required, because the
system never even flagged it:

**Run against Meera Pillai's real event, same resource:**

```
event_type                 | git_clone
resource_name                | engineering_source_repos.csv
occurred_at                    | 2026-08-22 14:30:00+00
role_held_at_the_time            | HR Business Partner - Engineering
what_justified_that_role           | Promotion - embedded HR partner for Engineering org
role_grants_it                       | t
direct_grant_exists                    | t
final_decision_authorized                | t
anomaly_written                            | (empty — nothing was ever flagged)
```

Side by side, the difference is the entire pitch:

| | Ananya | Meera |
|---|---|---|
| Resource touched | engineering_source_repos.csv | engineering_source_repos.csv |
| Event type | git_clone | git_clone |
| Device trusted | yes | yes |
| Role at event time | Accountant | **HR Business Partner - Engineering** |
| Role change on file | none | **Promotion, 2026-08-20** |
| Permission grant | **none** | **role + direct resource grant** |
| Result | critical anomaly, alert opened | **nothing written — no anomaly row exists** |

Two people, same-shaped behavior, same day. One gets flagged forever
until a human closes it. One never generates so much as a database row,
because the Context Resolver checked her role history *before* judging
her, not after a human had to notice the false positive and manually
dismiss it.

---

## Why this matters more than the score itself

A threat score of 91 means nothing to an investigator on its own — it's
a number that could be right or could be a bug. What makes it usable is
that every contributing fact behind it (`role_had_permission = false`,
`device_trusted = true`, `role_change_context = empty`) is independently
verifiable against the same tables the score was computed from. An
analyst doesn't have to trust the score; they can audit the reasoning
that produced it, using the exact same query pattern, on any employee,
for any event, at any point in history — because nothing in this schema
is ever silently overwritten. The role history, the permission grants,
the anomaly explanations: all of it stays queryable forever.
