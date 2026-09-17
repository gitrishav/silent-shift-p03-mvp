-- ══════════════════════════════════════════════════════════════
-- PER-EVENT EXPLAIN QUERY
-- Works for ANY event, flagged or not -- this is what proves the
-- system isn't just explaining alerts after the fact, it can show
-- its reasoning for every single authorization decision it makes.
-- ══════════════════════════════════════════════════════════════

WITH target_event AS (
    SELECT ev.event_id, ev.occurred_at, ev.event_type, ev.actor_employee_id,
           ev.target_resource_id, r.name AS resource_name
    FROM events ev
    JOIN resources r ON r.resource_id = ev.target_resource_id
    WHERE ev.actor_employee_id = :employee_id
      AND ev.target_resource_id = :resource_id
),
role_at_event_time AS (
    SELECT DISTINCT ON (te.event_id)
        te.event_id,
        ro.role_name,
        erh.effective_from,
        erh.change_reason
    FROM target_event te
    JOIN employee_role_history erh ON erh.employee_id = te.actor_employee_id
        AND erh.effective_from <= te.occurred_at
        AND (erh.effective_to IS NULL OR erh.effective_to > te.occurred_at)
    JOIN roles ro ON ro.role_id = erh.role_id
    ORDER BY te.event_id, erh.effective_from DESC
),
authorization_check AS (
    SELECT
        te.event_id,
        EXISTS (
            SELECT 1 FROM role_permissions rp
            JOIN roles r2 ON r2.role_id = rp.role_id
            WHERE r2.role_name = raet.role_name
        ) AS role_grants_it,
        EXISTS (
            SELECT 1 FROM resource_permissions rpm
            WHERE rpm.employee_id = te.actor_employee_id
              AND rpm.resource_id = te.target_resource_id
              AND rpm.revoked_at IS NULL
        ) AS direct_grant_exists
    FROM target_event te
    JOIN role_at_event_time raet ON raet.event_id = te.event_id
),
resulting_anomaly AS (
    SELECT a.anomaly_id, a.explanation
    FROM target_event te
    LEFT JOIN anomalies a ON a.event_id = te.event_id AND a.event_occurred_at = te.occurred_at
)
SELECT
    te.event_type,
    te.resource_name,
    te.occurred_at,
    raet.role_name AS role_held_at_the_time,
    raet.change_reason AS what_justified_that_role,
    ac.role_grants_it,
    ac.direct_grant_exists,
    (ac.role_grants_it OR ac.direct_grant_exists) AS final_decision_authorized,
    ra.explanation AS anomaly_written
FROM target_event te
JOIN role_at_event_time raet ON raet.event_id = te.event_id
JOIN authorization_check ac ON ac.event_id = te.event_id
LEFT JOIN resulting_anomaly ra ON true;
