-- ══════════════════════════════════════════════════════════════
-- INVESTIGATOR EXPLAIN QUERY
-- What a SOC analyst's dashboard runs the moment they click into
-- an alert. One parameterized query reconstructs the entire story:
-- who, what, when, on what device, under what role, was it
-- authorized, and why the score landed where it did.
-- ══════════════════════════════════════════════════════════════

-- Usage: replace :alert_id with the actual UUID from the alerts table

WITH alert_context AS (
    SELECT
        al.alert_id,
        al.title AS alert_title,
        al.status AS alert_status,
        al.opened_at,
        e.employee_id,
        e.full_name,
        e.email,
        d.name AS department
    FROM alerts al
    JOIN employees e ON e.employee_id = al.employee_id
    JOIN departments d ON d.department_id = e.department_id
    WHERE al.alert_id = :alert_id
),
triggering_anomalies AS (
    SELECT
        a.anomaly_id,
        a.anomaly_type,
        a.severity,
        a.confidence,
        a.explanation,
        a.event_id,
        a.event_occurred_at
    FROM alert_anomalies aa
    JOIN anomalies a ON a.anomaly_id = aa.anomaly_id
    WHERE aa.alert_id = :alert_id
),
event_detail AS (
    SELECT
        ta.anomaly_id,
        ev.event_type,
        ev.occurred_at,
        r.name AS resource_name,
        r.sensitivity AS resource_sensitivity,
        dev.device_type,
        dev.is_trusted AS device_trusted,
        dev.hostname
    FROM triggering_anomalies ta
    JOIN events ev ON ev.event_id = ta.event_id AND ev.occurred_at = ta.event_occurred_at
    LEFT JOIN resources r ON r.resource_id = ev.target_resource_id
    LEFT JOIN devices dev ON dev.device_id = ev.device_id
),
role_at_time_of_event AS (
    -- The critical explainability step: what role did this person
    -- hold AT THE MOMENT the flagged event happened -- not their
    -- role today, their role THEN.
    SELECT DISTINCT ON (ed.anomaly_id)
        ed.anomaly_id,
        r.role_name,
        erh.effective_from,
        erh.effective_to,
        erh.change_reason
    FROM event_detail ed
    JOIN triggering_anomalies ta ON ta.anomaly_id = ed.anomaly_id
    JOIN alert_context ac ON true
    JOIN employee_role_history erh ON erh.employee_id = ac.employee_id
        AND erh.effective_from <= ed.occurred_at
        AND (erh.effective_to IS NULL OR erh.effective_to > ed.occurred_at)
    JOIN roles r ON r.role_id = erh.role_id
    ORDER BY ed.anomaly_id, erh.effective_from DESC
),
permission_check AS (
    -- Did that role -- the one held at event time -- have any grant
    -- on the resource that was touched?
    SELECT
        ed.anomaly_id,
        EXISTS (
            SELECT 1 FROM role_permissions rp
            JOIN roles r ON r.role_id = rp.role_id
            JOIN permissions p ON p.permission_id = rp.permission_id
            WHERE r.role_name = rat.role_name
        ) AS role_had_permission,
        EXISTS (
            SELECT 1 FROM resource_permissions rp2
            WHERE rp2.employee_id = (SELECT employee_id FROM alert_context)
              AND rp2.revoked_at IS NULL
        ) AS had_direct_resource_grant
    FROM event_detail ed
    JOIN role_at_time_of_event rat ON rat.anomaly_id = ed.anomaly_id
),
score_history AS (
    SELECT overall_risk, identity_risk, device_risk, computed_at
    FROM threat_scores
    WHERE employee_id = (SELECT employee_id FROM alert_context)
    ORDER BY computed_at DESC
    LIMIT 1
)
SELECT
    ac.full_name,
    ac.department,
    ac.alert_title,
    ac.alert_status,
    ta.anomaly_type,
    ta.severity,
    ta.confidence,
    ta.explanation,
    ed.event_type,
    ed.resource_name,
    ed.resource_sensitivity,
    ed.device_trusted,
    rat.role_name AS role_held_at_event_time,
    rat.change_reason AS role_change_context,
    pc.role_had_permission,
    sh.overall_risk AS current_threat_score
FROM alert_context ac
JOIN triggering_anomalies ta ON true
JOIN event_detail ed ON ed.anomaly_id = ta.anomaly_id
JOIN role_at_time_of_event rat ON rat.anomaly_id = ta.anomaly_id
JOIN permission_check pc ON pc.anomaly_id = ta.anomaly_id
CROSS JOIN score_history sh;
