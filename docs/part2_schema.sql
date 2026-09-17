-- ══════════════════════════════════════════════════════════════
-- SILENT SHIFT OS — PostgreSQL Schema
-- Part 2: Runnable DDL
-- ══════════════════════════════════════════════════════════════

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- for gen_random_uuid()

-- ══════════════════════════════════════════════════════════════
-- LAYER 1: IDENTITY
-- ══════════════════════════════════════════════════════════════

CREATE TABLE departments (
    department_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                 TEXT NOT NULL UNIQUE,
    head_employee_id     UUID,  -- FK added after employees exists (circular ref)
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE employees (
    employee_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name            TEXT NOT NULL,
    email                TEXT NOT NULL UNIQUE,
    department_id        UUID NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    manager_id           UUID REFERENCES employees(employee_id) ON DELETE SET NULL,
    employment_type      TEXT NOT NULL DEFAULT 'employee'
                          CHECK (employment_type IN ('employee', 'contractor')),
    hire_date            DATE NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- circular FK now that employees exists
ALTER TABLE departments
    ADD CONSTRAINT fk_departments_head
    FOREIGN KEY (head_employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL;

CREATE TABLE teams (
    team_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                 TEXT NOT NULL,
    department_id        UUID NOT NULL REFERENCES departments(department_id) ON DELETE CASCADE
);

CREATE TABLE team_members (
    team_member_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id              UUID NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    employee_id          UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    joined_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    left_at              TIMESTAMPTZ,
    UNIQUE (team_id, employee_id, joined_at)
);

CREATE TABLE roles (
    role_id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name            TEXT NOT NULL UNIQUE,
    description          TEXT
);

-- Append-only. Never UPDATE a row here — close it with effective_to and insert a new one.
CREATE TABLE employee_role_history (
    role_history_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id          UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    role_id              UUID NOT NULL REFERENCES roles(role_id) ON DELETE RESTRICT,
    effective_from        TIMESTAMPTZ NOT NULL,
    effective_to          TIMESTAMPTZ,  -- NULL = currently active
    change_reason         TEXT,
    changed_by_employee_id UUID REFERENCES employees(employee_id) ON DELETE SET NULL,
    CONSTRAINT chk_role_history_dates CHECK (effective_to IS NULL OR effective_to > effective_from)
);

-- Only one currently-active role per employee
CREATE UNIQUE INDEX uq_employee_current_role
    ON employee_role_history (employee_id)
    WHERE effective_to IS NULL;

CREATE TABLE employment_status_history (
    status_history_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id          UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    status                TEXT NOT NULL CHECK (status IN ('active', 'suspended', 'terminated', 'leave')),
    effective_from        TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_to          TIMESTAMPTZ
);

CREATE TABLE auth_identities (
    identity_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id          UUID NOT NULL UNIQUE REFERENCES employees(employee_id) ON DELETE CASCADE,
    sso_subject           TEXT NOT NULL UNIQUE,
    auth_provider          TEXT NOT NULL CHECK (auth_provider IN ('okta', 'google', 'azure_ad')),
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE mfa_status (
    mfa_id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identity_id           UUID NOT NULL REFERENCES auth_identities(identity_id) ON DELETE CASCADE,
    enrolled               BOOLEAN NOT NULL DEFAULT false,
    method                 TEXT CHECK (method IN ('totp', 'push', 'hardware_key')),
    last_verified_at       TIMESTAMPTZ
);

-- ══════════════════════════════════════════════════════════════
-- LAYER 2: ORG CONTEXT
-- ══════════════════════════════════════════════════════════════

CREATE TABLE projects (
    project_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                   TEXT NOT NULL,
    owning_department_id   UUID NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    sensitivity_level      TEXT NOT NULL DEFAULT 'internal'
                            CHECK (sensitivity_level IN ('public', 'internal', 'confidential', 'restricted')),
    start_date             DATE NOT NULL,
    end_date               DATE,
    CONSTRAINT chk_project_dates CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE TABLE project_members (
    project_member_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id              UUID NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
    employee_id             UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    is_temporary            BOOLEAN NOT NULL DEFAULT false,
    assigned_from            TIMESTAMPTZ NOT NULL DEFAULT now(),
    assigned_to              TIMESTAMPTZ,
    UNIQUE (project_id, employee_id, assigned_from)
);

-- ══════════════════════════════════════════════════════════════
-- LAYER 3: DEVICE
-- ══════════════════════════════════════════════════════════════

CREATE TABLE devices (
    device_id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id            UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    device_type             TEXT NOT NULL CHECK (device_type IN ('laptop', 'mobile', 'tablet')),
    ownership                TEXT NOT NULL CHECK (ownership IN ('company', 'personal')),
    fingerprint_hash          TEXT NOT NULL UNIQUE,
    os                        TEXT,
    browser                   TEXT,
    hostname                  TEXT,
    is_trusted                 BOOLEAN NOT NULL DEFAULT false,
    first_seen_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE device_trust_history (
    trust_history_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id                 UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    trust_score                SMALLINT NOT NULL CHECK (trust_score BETWEEN 0 AND 100),
    reason                     TEXT,
    recorded_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE device_health_snapshots (
    health_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id                    UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
    antivirus_enabled              BOOLEAN NOT NULL,
    disk_encrypted                 BOOLEAN NOT NULL,
    os_up_to_date                  BOOLEAN NOT NULL,
    captured_at                    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════
-- LAYER 4: NETWORK
-- ══════════════════════════════════════════════════════════════

CREATE TABLE ip_addresses (
    ip_id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address                     INET NOT NULL UNIQUE,
    country                         TEXT,
    city                            TEXT,
    asn                             TEXT,
    network_type                    TEXT NOT NULL DEFAULT 'unknown'
                                    CHECK (network_type IN ('office', 'home', 'vpn', 'public_wifi', 'unknown'))
);

CREATE TABLE network_sessions (
    network_session_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id                     UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    ip_id                           UUID NOT NULL REFERENCES ip_addresses(ip_id) ON DELETE RESTRICT,
    connection_type                  TEXT NOT NULL CHECK (connection_type IN ('vpn', 'direct')),
    connected_at                     TIMESTAMPTZ NOT NULL DEFAULT now(),
    disconnected_at                  TIMESTAMPTZ,
    CONSTRAINT chk_network_session_times CHECK (disconnected_at IS NULL OR disconnected_at > connected_at)
);

CREATE TABLE impossible_travel_flags (
    travel_flag_id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    network_session_id                UUID NOT NULL REFERENCES network_sessions(network_session_id) ON DELETE CASCADE,
    prior_network_session_id          UUID NOT NULL REFERENCES network_sessions(network_session_id) ON DELETE CASCADE,
    distance_km                        NUMERIC(10,2) NOT NULL,
    implied_speed_kmh                  NUMERIC(10,2) NOT NULL,
    flagged_at                          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════
-- LAYER 5: RESOURCE
-- ══════════════════════════════════════════════════════════════

CREATE TABLE resources (
    resource_id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type                    TEXT NOT NULL
                                     CHECK (resource_type IN ('file', 'git_repo', 'database', 'api', 'dashboard', 'document', 'cloud_object')),
    name                             TEXT NOT NULL,
    owning_department_id             UUID REFERENCES departments(department_id) ON DELETE SET NULL,
    owning_project_id                UUID REFERENCES projects(project_id) ON DELETE SET NULL,
    owner_employee_id                UUID REFERENCES employees(employee_id) ON DELETE SET NULL,
    sensitivity                      TEXT NOT NULL DEFAULT 'internal'
                                     CHECK (sensitivity IN ('public', 'internal', 'confidential', 'restricted')),
    created_at                       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE resource_tags (
    tag_id                            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id                        UUID NOT NULL REFERENCES resources(resource_id) ON DELETE CASCADE,
    tag                                 TEXT NOT NULL,
    UNIQUE (resource_id, tag)
);

-- ══════════════════════════════════════════════════════════════
-- LAYER 6: PERMISSION (RBAC + ABAC)
-- ══════════════════════════════════════════════════════════════

CREATE TABLE permissions (
    permission_id                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    permission_name                       TEXT NOT NULL UNIQUE,
    description                           TEXT
);

CREATE TABLE role_permissions (
    role_permission_id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_id                                 UUID NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id                           UUID NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    UNIQUE (role_id, permission_id)
);

CREATE TABLE resource_permissions (
    resource_permission_id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id                                UUID NOT NULL REFERENCES resources(resource_id) ON DELETE CASCADE,
    employee_id                                UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    access_level                                TEXT NOT NULL CHECK (access_level IN ('read', 'write', 'admin')),
    granted_at                                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at                                  TIMESTAMPTZ,
    granted_by_employee_id                      UUID REFERENCES employees(employee_id) ON DELETE SET NULL
);

CREATE TABLE temporary_permissions (
    temp_permission_id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_id                                   UUID NOT NULL REFERENCES resources(resource_id) ON DELETE CASCADE,
    employee_id                                   UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    access_level                                   TEXT NOT NULL CHECK (access_level IN ('read', 'write', 'admin')),
    expires_at                                     TIMESTAMPTZ NOT NULL,
    justification                                  TEXT,
    is_jit                                          BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE permission_audit_log (
    audit_id                                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_permission_id                           UUID REFERENCES resource_permissions(resource_permission_id) ON DELETE SET NULL,
    action                                            TEXT NOT NULL CHECK (action IN ('granted', 'revoked', 'expired', 'escalated')),
    performed_by_employee_id                          UUID REFERENCES employees(employee_id) ON DELETE SET NULL,
    occurred_at                                        TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════
-- LAYER 8: SESSION  (created before events — events FK into it)
-- ══════════════════════════════════════════════════════════════

CREATE TABLE sessions (
    session_id                                         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id                                          UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    device_id                                            UUID NOT NULL REFERENCES devices(device_id) ON DELETE RESTRICT,
    network_session_id                                   UUID REFERENCES network_sessions(network_session_id) ON DELETE SET NULL,
    login_at                                              TIMESTAMPTZ NOT NULL DEFAULT now(),
    logout_at                                             TIMESTAMPTZ,
    mfa_success                                            BOOLEAN NOT NULL DEFAULT false,
    session_risk_score                                     SMALLINT DEFAULT 0 CHECK (session_risk_score BETWEEN 0 AND 100),
    CONSTRAINT chk_session_times CHECK (logout_at IS NULL OR logout_at > login_at)
);

-- ══════════════════════════════════════════════════════════════
-- LAYER 7: EVENT — the core append-only feed
-- Partitioned by month (occurred_at) for scale. See Part 14 for
-- the partition-management strategy.
-- ══════════════════════════════════════════════════════════════

CREATE TABLE events (
    event_id                                                UUID NOT NULL DEFAULT gen_random_uuid(),
    event_type                                               TEXT NOT NULL,
    actor_employee_id                                        UUID NOT NULL REFERENCES employees(employee_id) ON DELETE RESTRICT,
    target_resource_id                                       UUID REFERENCES resources(resource_id) ON DELETE SET NULL,
    device_id                                                UUID REFERENCES devices(device_id) ON DELETE SET NULL,
    network_session_id                                       UUID REFERENCES network_sessions(network_session_id) ON DELETE SET NULL,
    session_id                                               UUID REFERENCES sessions(session_id) ON DELETE SET NULL,
    source_system                                            TEXT NOT NULL,
    metadata                                                 JSONB NOT NULL DEFAULT '{}'::jsonb,
    trace_id                                                 UUID NOT NULL DEFAULT gen_random_uuid(),
    occurred_at                                              TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (event_id, occurred_at)   -- composite PK required for partitioning on occurred_at
) PARTITION BY RANGE (occurred_at);

-- Example partitions (a background job creates these monthly — see Part 14)
CREATE TABLE events_2026_08 PARTITION OF events
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
CREATE TABLE events_2026_09 PARTITION OF events
    FOR VALUES FROM ('2026-09-01') TO ('2026-10-01');
CREATE TABLE events_2026_10 PARTITION OF events
    FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');

-- ══════════════════════════════════════════════════════════════
-- LAYER 9: BEHAVIORAL BASELINE
-- ══════════════════════════════════════════════════════════════

CREATE TABLE behavioral_baselines (
    baseline_id                                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id                                                UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    metric_type                                                TEXT NOT NULL,
    distribution                                               JSONB NOT NULL,
    window_period                                              TEXT NOT NULL CHECK (window_period IN ('7d', '30d', 'lifetime')),
    computed_at                                                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (employee_id, metric_type, window_period)
);

CREATE TABLE baseline_snapshots (
    snapshot_id                                                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    baseline_id                                                  UUID NOT NULL REFERENCES behavioral_baselines(baseline_id) ON DELETE CASCADE,
    snapshot_data                                                JSONB NOT NULL,
    snapshot_at                                                  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════
-- LAYER 10: SEQUENCE CORRELATION
-- ══════════════════════════════════════════════════════════════

CREATE TABLE event_sequences (
    sequence_id                                                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id                                                    UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    pattern_name                                                   TEXT NOT NULL,
    mitre_technique                                                TEXT,
    confidence                                                     NUMERIC(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    window_start                                                    TIMESTAMPTZ NOT NULL,
    window_end                                                      TIMESTAMPTZ NOT NULL,
    CONSTRAINT chk_sequence_window CHECK (window_end > window_start)
);

-- No FK to events(event_id) alone — events has a composite PK (event_id, occurred_at)
-- for partitioning, so this join table stores both.
CREATE TABLE sequence_events (
    sequence_event_id                                                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sequence_id                                                        UUID NOT NULL REFERENCES event_sequences(sequence_id) ON DELETE CASCADE,
    event_id                                                           UUID NOT NULL,
    event_occurred_at                                                  TIMESTAMPTZ NOT NULL,
    step_order                                                         SMALLINT NOT NULL,
    FOREIGN KEY (event_id, event_occurred_at) REFERENCES events(event_id, occurred_at) ON DELETE CASCADE,
    UNIQUE (sequence_id, step_order)
);

-- ══════════════════════════════════════════════════════════════
-- LAYER 11: ANOMALY / THREAT SCORE / ALERT
-- ══════════════════════════════════════════════════════════════

CREATE TABLE anomalies (
    anomaly_id                                                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id                                                              UUID,
    event_occurred_at                                                     TIMESTAMPTZ,
    sequence_id                                                           UUID REFERENCES event_sequences(sequence_id) ON DELETE CASCADE,
    employee_id                                                           UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    anomaly_type                                                          TEXT NOT NULL,
    severity                                                              TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    confidence                                                            NUMERIC(4,3) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    explanation                                                           TEXT NOT NULL,
    trigger_rule                                                          TEXT,
    statistical_score                                                     NUMERIC(6,2),
    context_score                                                         NUMERIC(6,2),
    status                                                                TEXT NOT NULL DEFAULT 'open'
                                                                          CHECK (status IN ('open', 'acknowledged', 'dismissed', 'escalated')),
    detected_at                                                           TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (event_id, event_occurred_at) REFERENCES events(event_id, occurred_at) ON DELETE SET NULL,
    CONSTRAINT chk_anomaly_source CHECK (event_id IS NOT NULL OR sequence_id IS NOT NULL)
);

-- Versioned history — never update overall_risk in place, always insert.
CREATE TABLE threat_scores (
    threat_score_id                                                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id                                                              UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    overall_risk                                                             SMALLINT NOT NULL CHECK (overall_risk BETWEEN 0 AND 100),
    identity_risk                                                            SMALLINT CHECK (identity_risk BETWEEN 0 AND 100),
    device_risk                                                              SMALLINT CHECK (device_risk BETWEEN 0 AND 100),
    network_risk                                                             SMALLINT CHECK (network_risk BETWEEN 0 AND 100),
    resource_risk                                                            SMALLINT CHECK (resource_risk BETWEEN 0 AND 100),
    behavioral_drift                                                         NUMERIC(6,3),
    historical_decay_factor                                                  NUMERIC(4,3) DEFAULT 1.0,
    final_confidence                                                         NUMERIC(4,3) CHECK (final_confidence BETWEEN 0 AND 1),
    computed_at                                                              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE alerts (
    alert_id                                                                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id                                                               UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    title                                                                     TEXT NOT NULL,
    status                                                                    TEXT NOT NULL DEFAULT 'open'
                                                                              CHECK (status IN ('open', 'investigating', 'resolved', 'false_positive')),
    assigned_analyst_id                                                       UUID REFERENCES employees(employee_id) ON DELETE SET NULL,
    sla_due_at                                                                TIMESTAMPTZ,
    resolution_notes                                                          TEXT,
    opened_at                                                                 TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at                                                                 TIMESTAMPTZ
);

CREATE TABLE alert_anomalies (
    alert_anomaly_id                                                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id                                                                    UUID NOT NULL REFERENCES alerts(alert_id) ON DELETE CASCADE,
    anomaly_id                                                                  UUID NOT NULL REFERENCES anomalies(anomaly_id) ON DELETE CASCADE,
    UNIQUE (alert_id, anomaly_id)
);

CREATE TABLE alert_evidence (
    evidence_id                                                                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id                                                                     UUID NOT NULL REFERENCES alerts(alert_id) ON DELETE CASCADE,
    evidence_type                                                                TEXT NOT NULL,
    payload                                                                      JSONB NOT NULL DEFAULT '{}'::jsonb,
    added_at                                                                     TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════
-- LAYER 12: INVESTIGATION / AUDIT
-- ══════════════════════════════════════════════════════════════

CREATE TABLE investigations (
    investigation_id                                                             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_id                                                                       UUID NOT NULL UNIQUE REFERENCES alerts(alert_id) ON DELETE CASCADE,
    investigator_employee_id                                                       UUID NOT NULL REFERENCES employees(employee_id) ON DELETE RESTRICT,
    root_cause                                                                     TEXT,
    resolution                                                                     TEXT,
    status                                                                         TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'closed')),
    linked_incident_id                                                             UUID,
    opened_at                                                                      TIMESTAMPTZ NOT NULL DEFAULT now(),
    closed_at                                                                      TIMESTAMPTZ
);

CREATE TABLE investigation_evidence (
    evidence_id                                                                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id                                                                 UUID NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    evidence_type                                                                    TEXT NOT NULL,
    payload                                                                          JSONB NOT NULL DEFAULT '{}'::jsonb,
    added_at                                                                         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE investigation_comments (
    comment_id                                                                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id                                                                  UUID NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    author_employee_id                                                                UUID NOT NULL REFERENCES employees(employee_id) ON DELETE SET NULL,
    comment_text                                                                      TEXT NOT NULL,
    posted_at                                                                         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE investigation_timeline (
    timeline_id                                                                       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    investigation_id                                                                    UUID NOT NULL REFERENCES investigations(investigation_id) ON DELETE CASCADE,
    action_taken                                                                        TEXT NOT NULL,
    performed_by_employee_id                                                            UUID REFERENCES employees(employee_id) ON DELETE SET NULL,
    occurred_at                                                                          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Immutable — application layer should REVOKE UPDATE/DELETE on this table for all roles.
CREATE TABLE audit_log (
    audit_log_id                                                                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type                                                                           TEXT NOT NULL
                                                                                          CHECK (entity_type IN ('permission', 'role', 'project', 'admin_action', 'investigation')),
    entity_id                                                                             UUID NOT NULL,
    action                                                                                TEXT NOT NULL,
    before_state                                                                          JSONB,
    after_state                                                                           JSONB,
    performed_by_employee_id                                                              UUID REFERENCES employees(employee_id) ON DELETE SET NULL,
    occurred_at                                                                           TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ══════════════════════════════════════════════════════════════
-- INDEX STRATEGY
-- ══════════════════════════════════════════════════════════════

-- Identity lookups
CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_employees_manager ON employees(manager_id);
CREATE INDEX idx_role_history_employee ON employee_role_history(employee_id, effective_from);

-- Events — the highest-volume table, indexed for the queries that actually run:
-- "show me this person's recent activity", "what happened on this resource",
-- "what happened in this session"
CREATE INDEX idx_events_actor_time ON events(actor_employee_id, occurred_at DESC);
CREATE INDEX idx_events_resource_time ON events(target_resource_id, occurred_at DESC);
CREATE INDEX idx_events_session ON events(session_id);
CREATE INDEX idx_events_type_time ON events(event_type, occurred_at DESC);
-- GIN index for querying inside the flexible metadata blob (e.g. metadata->>'download_size_mb')
CREATE INDEX idx_events_metadata_gin ON events USING GIN (metadata);

-- Permissions — the RBAC/ABAC check runs on every single event, so this must be fast
CREATE INDEX idx_role_permissions_role ON role_permissions(role_id);
CREATE INDEX idx_resource_permissions_employee ON resource_permissions(employee_id, resource_id)
    WHERE revoked_at IS NULL;
CREATE INDEX idx_temp_permissions_active ON temporary_permissions(employee_id, resource_id, expires_at);

-- Baselines — looked up by (employee, metric, window) constantly
CREATE INDEX idx_baselines_lookup ON behavioral_baselines(employee_id, metric_type, window_period);

-- Anomalies / Threat scores / Alerts — the SOC dashboard's primary queries
CREATE INDEX idx_anomalies_employee_time ON anomalies(employee_id, detected_at DESC);
CREATE INDEX idx_anomalies_status ON anomalies(status) WHERE status = 'open';
CREATE INDEX idx_threat_scores_employee_time ON threat_scores(employee_id, computed_at DESC);
CREATE INDEX idx_alerts_status ON alerts(status) WHERE status IN ('open', 'investigating');
CREATE INDEX idx_alerts_employee ON alerts(employee_id, opened_at DESC);
CREATE INDEX idx_alerts_analyst ON alerts(assigned_analyst_id) WHERE status IN ('open', 'investigating');

-- Sessions — for "what happened in this login window" and risk rollups
CREATE INDEX idx_sessions_employee_time ON sessions(employee_id, login_at DESC);

-- Audit log — compliance queries filter by entity and time range
CREATE INDEX idx_audit_log_entity ON audit_log(entity_type, entity_id, occurred_at DESC);

-- ══════════════════════════════════════════════════════════════
-- MATERIALIZED VIEW — current effective role per employee
-- Refreshed by the same worker that processes role_change events.
-- Avoids re-deriving "what role is this person right now" on every
-- single permission check.
-- ══════════════════════════════════════════════════════════════

CREATE MATERIALIZED VIEW current_employee_roles AS
SELECT DISTINCT ON (employee_id)
    employee_id,
    role_id,
    effective_from
FROM employee_role_history
WHERE effective_to IS NULL
ORDER BY employee_id, effective_from DESC;

CREATE UNIQUE INDEX idx_current_roles_employee ON current_employee_roles(employee_id);
