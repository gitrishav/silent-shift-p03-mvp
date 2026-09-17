import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime, timedelta

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Silent Shift | Northwind Cloud Systems",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# GLOBAL STYLES — dark cyber SOC theme
# ==========================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');

.stApp { background-color: #0A0E1A; color: #C8CDD5; }
header[data-testid="stHeader"] { background-color: #0A0E1A !important; }
section[data-testid="stSidebar"] { background-color: #0D1224 !important; border-right: 1px solid #1A2040; }
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stCheckbox label,
section[data-testid="stSidebar"] .stToggle label,
section[data-testid="stSidebar"] .stSelectbox label { color: #A0AEC0 !important; }

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #111827 0%, #0D1224 100%);
    border: 1px solid #1E293B; border-radius: 12px; padding: 20px 24px;
    transition: border-color 0.2s ease;
}
div[data-testid="stMetric"]:hover { border-color: #7B61FF; }
div[data-testid="stMetric"] label {
    color: #64748B !important; font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important; text-transform: uppercase; letter-spacing: 0.08em;
}
div[data-testid="stMetricValue"] {
    color: #F1F5F9 !important; font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important; font-size: 2rem !important;
}

.hero-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #0F172A 100%);
    border: 1px solid #2E1065; border-radius: 16px; padding: 32px 40px;
    margin-bottom: 24px; position: relative; overflow: hidden;
}
.hero-banner::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, transparent, #7B61FF, #A78BFA, #7B61FF, transparent);
}
.hero-banner h1 { font-family: 'Inter', sans-serif; font-size: 2rem; font-weight: 700; color: #F1F5F9; margin: 0 0 4px 0; }
.hero-banner p { font-family: 'Inter', sans-serif; color: #94A3B8; font-size: 0.95rem; margin: 0; }
.hero-tag {
    display: inline-block; background: rgba(123, 97, 255, 0.15); color: #A78BFA;
    font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; padding: 3px 10px;
    border-radius: 999px; border: 1px solid rgba(123, 97, 255, 0.3);
    margin-bottom: 12px; letter-spacing: 0.05em;
}

.section-header {
    font-family: 'Inter', sans-serif; font-weight: 600; font-size: 1.1rem; color: #E2E8F0;
    padding-bottom: 8px; margin-top: 8px; margin-bottom: 16px; border-bottom: 1px solid #1E293B;
}

.alert-critical {
    background: linear-gradient(135deg, #1C0A0A 0%, #2D0F0F 100%);
    border: 1px solid #7F1D1D; border-left: 4px solid #EF4444; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 8px;
}
.alert-clear {
    background: linear-gradient(135deg, #052E16 0%, #0A1F0D 100%);
    border: 1px solid #14532D; border-left: 4px solid #22C55E; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 8px;
}
.alert-suppressed {
    background: linear-gradient(135deg, #1A1523 0%, #1E1B2E 100%);
    border: 1px solid #3B2E6E; border-left: 4px solid #A78BFA; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 8px;
}
.alert-title { font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 0.85rem; margin-bottom: 4px; }
.alert-detail { font-family: 'Inter', sans-serif; font-size: 0.8rem; color: #94A3B8; }

.pipeline-stage {
    display: inline-flex; align-items: center; gap: 6px; background: #111827;
    border: 1px solid #1E293B; border-radius: 8px; padding: 8px 14px;
    font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #94A3B8;
}
.pipeline-stage .dot { width: 8px; height: 8px; border-radius: 50%; background: #22C55E; box-shadow: 0 0 6px #22C55E; }
.pipeline-arrow { color: #334155; font-size: 1.2rem; display: inline-flex; align-items: center; padding: 0 4px; }

.threat-badge {
    font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 0.7rem;
    padding: 3px 10px; border-radius: 6px; letter-spacing: 0.04em;
}
.threat-critical { background: #7F1D1D; color: #FCA5A5; }
.threat-high     { background: #78350F; color: #FCD34D; }
.threat-medium   { background: #1E3A5F; color: #7DD3FC; }
.threat-low      { background: #14532D; color: #86EFAC; }

.stDataFrame { border-radius: 10px; overflow: hidden; }

.sidebar-brand {
    font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: #475569;
    letter-spacing: 0.1em; text-transform: uppercase; padding: 4px 0 16px 0;
}
.sidebar-section {
    font-family: 'Inter', sans-serif; font-weight: 600; font-size: 0.85rem;
    color: #CBD5E1; margin-top: 16px; margin-bottom: 8px;
}

hr { border-color: #1E293B !important; }
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# DATA LOADING
# ==========================================
DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    required = ["departments", "employees", "data_resources",
                "access_control_matrix", "role_change_events", "access_logs"]
    missing = [f for f in required if not (DATA_DIR / f"{f}.csv").exists()]
    if missing:
        return None, missing
    dfs = {f: pd.read_csv(DATA_DIR / f"{f}.csv") for f in required}
    return dfs, []

dfs, missing_files = load_data()

if dfs is None:
    st.error(
        f"Missing data files: {', '.join(missing_files)}.\n\n"
        f"Place the 6 CSVs (departments, employees, data_resources, "
        f"access_control_matrix, role_change_events, access_logs) inside "
        f"a `data/` folder next to app.py."
    )
    st.stop()

departments = dfs["departments"]
employees = dfs["employees"]
data_resources = dfs["data_resources"]
access_control_matrix = dfs["access_control_matrix"]
role_change_events = dfs["role_change_events"]
access_logs = dfs["access_logs"]

DAYS = int(access_logs["day"].max())
BASE_DATE = datetime(2026, 8, 1)

emp_name = dict(zip(employees.employee_id, employees.name))
emp_role = dict(zip(employees.employee_id, employees.role))
emp_dept = dict(zip(employees.employee_id, employees.department_id))
dept_name = dict(zip(departments.department_id, departments.department_name))
resource_file = dict(zip(data_resources.resource_id, data_resources.filename))
resource_sensitivity = dict(zip(data_resources.resource_id, data_resources.sensitivity))

# authorized (role, resource_id) pairs
authorized_pairs = set(zip(access_control_matrix.role, access_control_matrix.resource_id))

# access_logs: derive hour + after_hours flag
access_logs = access_logs.copy()
access_logs["timestamp"] = pd.to_datetime(access_logs["timestamp"])
access_logs["hour"] = access_logs["timestamp"].dt.hour
access_logs["after_hours"] = ((access_logs["hour"] < 9) | (access_logs["hour"] >= 19)).astype(int)


# ==========================================
# ENGINE — Data Collector already = access_logs
# ==========================================

def effective_role(employee_id, day, context_active):
    """Context Resolver: which role was this employee operating under on `day`?"""
    if context_active:
        ev = role_change_events[role_change_events.employee_id == employee_id]
        if not ev.empty and day >= ev.iloc[0]["effective_day"]:
            return ev.iloc[0]["new_role"]
    return emp_role[employee_id]


class BaselineBuilder:
    """Learns each employee's personal normal from days 1-15."""
    def __init__(self, window=15):
        self.window = window
        self.profiles = {}

    def build_profiles(self, logs):
        for emp_id in employees.employee_id:
            bl = logs[(logs.employee_id == emp_id) & (logs.day <= self.window)]
            self.profiles[emp_id] = {
                "mean_V": bl["volume_mb"].mean() if len(bl) else 30.0,
                "std_V": (bl["volume_mb"].std() if len(bl) else 10.0) + 0.1,
                "mean_T": bl["after_hours"].mean() if len(bl) else 0.1,
                "std_T": (bl["after_hours"].std() if len(bl) else 0.2) + 0.1,
            }


class ScoringEngine:
    """RBAC hard-rule layer + statistical drift layer, combined."""
    def __init__(self, w_volume, w_temporal, rbac_penalty):
        self.w_V = w_volume
        self.w_T = w_temporal
        self.rbac_penalty = rbac_penalty

    def score_event(self, row, profile, context_active):
        role = effective_role(row["employee_id"], row["day"], context_active)
        authorized = (role, row["resource_id"]) in authorized_pairs

        sigma_V = max(0, (row["volume_mb"] - profile["mean_V"]) / profile["std_V"])
        sigma_T = max(0, (row["after_hours"] - profile["mean_T"]) / profile["std_T"])
        drift = (self.w_V * sigma_V + self.w_T * sigma_T) * 10

        if not authorized:
            score = self.rbac_penalty + drift
            reason = (f"{role} accessed {resource_file[row['resource_id']]} "
                      f"({resource_sensitivity[row['resource_id']]}) — no authorization on file")
        else:
            score = drift
            reason = (f"Authorized access to {resource_file[row['resource_id']]}"
                      + (f" — volume/timing deviates from personal baseline" if drift > 15 else ""))

        return round(score, 1), not authorized, reason, role


# ==========================================
# HERO + TOP CONTROLS
# ==========================================
st.markdown("""
<div class="hero-banner">
    <span class="hero-tag">P03 · QUALIFIER ENGINE · MANIPAL HACKATHON 2026</span>
    <h1>🛡️ Silent Shift — Northwind Cloud Systems</h1>
    <p>RBAC-grounded insider threat detection — real departments, real roles, real access boundaries</p>
</div>
""", unsafe_allow_html=True)

with st.container():
    top_left, top_right = st.columns([3, 1])
    with top_left:
        st.markdown('<div class="sidebar-brand">SILENT SHIFT ENGINE V3.0 — RBAC</div>', unsafe_allow_html=True)
    with top_right:
        st.caption(f"**Northwind Cloud Systems** · {len(departments)} depts · {len(employees)} employees · {len(data_resources)} resources")

    with st.expander("⚙️  Engine Controls", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown('<div class="sidebar-section">Statistical Drift Weights</div>', unsafe_allow_html=True)
            w_volume = st.slider("Velocity Risk (Data Volume)", 0.1, 1.0, 0.4, help="Weight for volume deviation within an employee's own authorized resources")
            w_temporal = st.slider("Temporal Risk (After-Hours)", 0.1, 1.0, 0.3, help="Weight for off-hours access deviation")
        with c2:
            st.markdown('<div class="sidebar-section">🔒 RBAC Enforcement</div>', unsafe_allow_html=True)
            rbac_penalty = st.slider("Unauthorized Access Penalty", 20, 80, 50, help="Flat score added when an employee accesses a resource outside their role's permissions")
            alert_threshold = st.slider("Alert Threshold (TS)", 20, 80, 40)
        with c3:
            st.markdown('<div class="sidebar-section">🏢 Context Engine</div>', unsafe_allow_html=True)
            apply_context = st.toggle("Enable HR/Workday Integration", value=False)
            st.caption("Checks logged role changes before flagging cross-department access as unauthorized.")
        with c4:
            st.markdown('<div class="sidebar-section">Build Info</div>', unsafe_allow_html=True)
            st.markdown("""
            <div style="font-family: 'JetBrains Mono'; font-size: 0.7rem; color: #64748B; line-height: 1.8;">
            TEAM P03 · MANIPAL HACKATHON 2026<br/>
            Engine: RBAC + Z-Score Hybrid<br/>
            Build: qualifier-v3.0
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# RUN PIPELINE
# ==========================================
builder = BaselineBuilder()
builder.build_profiles(access_logs)
scorer = ScoringEngine(w_volume, w_temporal, rbac_penalty)

results = []
for _, row in access_logs.iterrows():
    profile = builder.profiles[row["employee_id"]]
    score, violation, reason, role_at_time = scorer.score_event(row, profile, apply_context)
    results.append({**row.to_dict(), "threat_score": score, "rbac_violation": violation,
                     "reason": reason, "role_at_time": role_at_time})

scored = pd.DataFrame(results)

# daily aggregate: worst event per employee per day
daily = scored.groupby(["employee_id", "day"], as_index=False).agg(
    threat_score=("threat_score", "max"),
    rbac_violation=("rbac_violation", "max"),
)

def get_threat_level(score, threshold):
    if score > threshold * 1.5:
        return "CRITICAL", "#EF4444"
    elif score > threshold:
        return "HIGH", "#F59E0B"
    elif score > threshold * 0.5:
        return "MEDIUM", "#3B82F6"
    return "LOW", "#22C55E"


# ==========================================
# CHART HELPERS
# ==========================================
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#94A3B8", size=12),
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis=dict(gridcolor="#1E293B", zerolinecolor="#1E293B", tickfont=dict(size=10, color="#64748B")),
    yaxis=dict(gridcolor="#1E293B", zerolinecolor="#1E293B", tickfont=dict(size=10, color="#64748B")),
    legend=dict(font=dict(size=11, color="#94A3B8"), bgcolor="rgba(0,0,0,0)"),
    hoverlabel=dict(bgcolor="#1E293B", font_size=12, font_family="JetBrains Mono, monospace",
                     font_color="#E2E8F0", bordercolor="#334155"),
)

def make_user_chart(df_user, color_main, color_fill, threshold):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_user["day"], y=df_user["threat_score"], mode="lines",
        line=dict(color=color_main, width=2.5), fill="tozeroy", fillcolor=color_fill,
        hovertemplate="Day %{x}<br>Score: %{y:.1f}<extra></extra>"
    ))
    fig.add_hline(y=threshold, line_dash="dot", line_color="#EF4444",
                  annotation_text="ALERT THRESHOLD",
                  annotation_font=dict(size=10, color="#EF4444", family="JetBrains Mono"),
                  annotation_position="top right")
    fig.add_vline(x=20, line_dash="dash", line_color="#7B61FF", opacity=0.5,
                  annotation_text="ROLE EVENT DAY 20",
                  annotation_font=dict(size=9, color="#7B61FF", family="JetBrains Mono"),
                  annotation_position="top left")
    fig.add_vrect(x0=1, x1=15, fillcolor="rgba(123,97,255,0.05)", line_width=0)
    fig.update_layout(**PLOTLY_LAYOUT, height=280, showlegend=False)
    return fig

def make_comparison_chart(daily, threshold):
    a = daily[daily.employee_id == "E03"]  # Ananya
    m = daily[daily.employee_id == "E05"]  # Meera
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=a["day"], y=a["threat_score"], mode="lines",
                              name="E03 · Ananya Iyer (Accountant)",
                              line=dict(color="#EF4444", width=2.5),
                              hovertemplate="Day %{x}<br>Score: %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=m["day"], y=m["threat_score"], mode="lines",
                              name="E05 · Meera Pillai (HR)",
                              line=dict(color="#22C55E", width=2),
                              hovertemplate="Day %{x}<br>Score: %{y:.1f}<extra></extra>"))
    fig.add_hline(y=threshold, line_dash="dot", line_color="#F59E0B",
                  annotation_text="THRESHOLD",
                  annotation_font=dict(size=10, color="#F59E0B", family="JetBrains Mono"),
                  annotation_position="top right")
    fig.add_vline(x=20, line_dash="dash", line_color="#7B61FF", opacity=0.5,
                  annotation_text="Both start accessing engineering_source_repos.csv",
                  annotation_font=dict(size=9, color="#7B61FF", family="JetBrains Mono"))
    layout = {**PLOTLY_LAYOUT, "height": 340}
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1)
    fig.update_layout(**layout)
    return fig

def make_gauge(score, threshold):
    level, color = get_threat_level(score, threshold)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number=dict(font=dict(size=36, family="JetBrains Mono", color=color)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#1E293B", tickfont=dict(size=10, color="#475569")),
            bar=dict(color=color, thickness=0.7), bgcolor="#111827",
            borderwidth=1, bordercolor="#1E293B",
            steps=[
                dict(range=[0, threshold * 0.5], color="#0A1F0D"),
                dict(range=[threshold * 0.5, threshold], color="#1E3A5F20"),
                dict(range=[threshold, threshold * 1.5], color="#78350F20"),
                dict(range=[threshold * 1.5, 100], color="#7F1D1D30"),
            ],
            threshold=dict(line=dict(color="#EF4444", width=2), thickness=0.8, value=threshold),
        ),
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#94A3B8"),
                       height=200, margin=dict(l=20, r=20, t=30, b=10))
    return fig


# ==========================================
# MAIN UI
# ==========================================
st.markdown("""
<div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-bottom: 24px;">
    <div class="pipeline-stage"><span class="dot"></span> Data Collector</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-stage"><span class="dot"></span> Baseline Builder</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-stage"><span class="dot"></span> RBAC + Drift Scoring</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-stage"><span class="dot"></span> Context Resolver</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-stage"><span class="dot"></span> SOC Output</div>
</div>
""", unsafe_allow_html=True)

# ── KPI row ──
total_violations_off = scored[~apply_context if False else scored["rbac_violation"]].shape[0]
alerts = daily[(daily.threat_score > alert_threshold) & (daily.day > 15)]
rbac_violations = scored[scored.rbac_violation]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Employees Monitored", f"{len(employees)}", f"{len(departments)} departments")
k2.metric("Access Events Logged", f"{len(access_logs)}", f"{DAYS}-day window")
k3.metric("RBAC Violations", f"{len(rbac_violations)}", "Context-aware" if apply_context else "Raw", delta_color="inverse" if not apply_context else "normal")
k4.metric("Active SOC Alerts", f"{len(alerts)}", f"threshold > {alert_threshold}", delta_color="inverse")

st.markdown("---")

# ── Org roster ──
st.markdown('<div class="section-header">🏢 Organization Roster</div>', unsafe_allow_html=True)
roster = employees.copy()
roster["department"] = roster.department_id.map(dept_name)
roster_display = roster[["employee_id", "name", "department", "role", "hire_date"]]
roster_display.columns = ["ID", "Name", "Department", "Role", "Hire Date"]
st.dataframe(roster_display, use_container_width=True, hide_index=True, height=180)

st.markdown("---")

# ── The money comparison chart ──
st.markdown('<div class="section-header">📊 Same-Day Behavior Shift, Different Outcome</div>', unsafe_allow_html=True)
st.caption("Both employees below start accessing `engineering_source_repos.csv` on Day 20. One has a logged role change justifying it — one doesn't.")
st.plotly_chart(make_comparison_chart(daily, alert_threshold), use_container_width=True)

# ── Per-user deep dive ──
st.markdown('<div class="section-header">🔍 Per-Employee Threat Analysis</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)

ananya_daily = daily[daily.employee_id == "E03"]
meera_daily = daily[daily.employee_id == "E05"]
ananya_peak = ananya_daily["threat_score"].max()
meera_peak = meera_daily["threat_score"].max()
ananya_level, _ = get_threat_level(ananya_peak, alert_threshold)
meera_level, _ = get_threat_level(meera_peak, alert_threshold)

with col_a:
    badge_class = {"CRITICAL": "threat-critical", "HIGH": "threat-high", "MEDIUM": "threat-medium", "LOW": "threat-low"}[ananya_level]
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
        <div style="width:10px; height:10px; border-radius:50%; background:#EF4444; box-shadow: 0 0 8px #EF4444;"></div>
        <span style="font-family:'JetBrains Mono'; font-size:0.9rem; color:#E2E8F0;">
            E03 · Ananya Iyer · Accountant
        </span>
        <span class="threat-badge {badge_class}">{ananya_level}</span>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(make_user_chart(ananya_daily, "#EF4444", "rgba(239,68,68,0.08)", alert_threshold), use_container_width=True)
    st.caption("No role change on file for this employee. Access to Engineering resources has no legitimate basis regardless of the Context Engine setting.")

with col_b:
    badge_class = {"CRITICAL": "threat-critical", "HIGH": "threat-high", "MEDIUM": "threat-medium", "LOW": "threat-low"}[meera_level]
    dot_color = "#22C55E" if apply_context else "#EF4444"
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
        <div style="width:10px; height:10px; border-radius:50%; background:{dot_color}; box-shadow: 0 0 8px {dot_color};"></div>
        <span style="font-family:'JetBrains Mono'; font-size:0.9rem; color:#E2E8F0;">
            E05 · Meera Pillai · HR Generalist
        </span>
        <span class="threat-badge {badge_class}">{meera_level}</span>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(make_user_chart(meera_daily, "#22C55E" if apply_context else "#EF4444",
                                     "rgba(34,197,94,0.08)" if apply_context else "rgba(239,68,68,0.08)",
                                     alert_threshold), use_container_width=True)
    if apply_context:
        st.caption("✅ Promoted to HR Business Partner - Engineering on Day 20 (logged in role_change_events.csv). Access recognized as authorized.")
    else:
        st.caption("⚠️ HR integration is OFF — the engine doesn't know about her promotion yet, so this reads identically to a violation.")

st.markdown("---")

# ── Gauge + Alert log ──
st.markdown('<div class="section-header">🚨 Threat Engine Output</div>', unsafe_allow_html=True)
gauge_col, log_col = st.columns([1, 2])

with gauge_col:
    st.markdown('<div style="text-align:center; font-family:\'JetBrains Mono\'; font-size:0.75rem; color:#64748B; margin-bottom:4px;">ANANYA IYER — PEAK THREAT</div>', unsafe_allow_html=True)
    st.plotly_chart(make_gauge(ananya_peak, alert_threshold), use_container_width=True)

    profile = builder.profiles["E03"]
    st.markdown(f"""
    <div style="background:#111827; border:1px solid #1E293B; border-radius:10px; padding:16px; margin-top:8px;">
        <div style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B; margin-bottom:10px; text-transform:uppercase; letter-spacing:0.08em;">
            Baseline Profile · E03
        </div>
        <div style="font-family:'JetBrains Mono'; font-size:0.8rem; color:#A0AEC0; line-height:1.8;">
            μ(Volume) = <span style="color:#E2E8F0;">{profile['mean_V']:.1f} MB</span><br/>
            σ(Volume) = <span style="color:#E2E8F0;">{profile['std_V']:.1f}</span><br/>
            μ(After-Hours) = <span style="color:#E2E8F0;">{profile['mean_T']:.2f}</span><br/>
            Window = <span style="color:#7B61FF;">15 days</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with log_col:
    if rbac_violations.empty:
        st.markdown("""
        <div class="alert-clear">
            <div class="alert-title" style="color:#22C55E;">✅ ALL CLEAR</div>
            <div class="alert-detail">No unauthorized access events detected across the organization.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-critical">
            <div class="alert-title" style="color:#FCA5A5;">⚠️ {len(rbac_violations)} RBAC VIOLATIONS DETECTED</div>
            <div class="alert-detail">Access events with no authorization under the current role mapping. SOC review recommended.</div>
        </div>
        """, unsafe_allow_html=True)

        if apply_context:
            legitimized = scored[(scored.employee_id == "E05") & (scored.day >= 20) & (~scored.rbac_violation)]
            if len(legitimized) > 0:
                st.markdown(f"""
                <div class="alert-suppressed">
                    <div class="alert-title" style="color:#A78BFA;">🏢 CONTEXT RESOLVER ACTIVE</div>
                    <div class="alert-detail">{len(legitimized)} events for Meera Pillai (E05) resolved as authorized — role change to "HR Business Partner - Engineering" recognized as of Day 20.</div>
                </div>
                """, unsafe_allow_html=True)

        display_violations = rbac_violations.copy()
        display_violations["employee"] = display_violations["employee_id"].map(emp_name)
        display_violations["resource"] = display_violations["resource_id"].map(resource_file)
        display_cols = display_violations[["day", "employee", "role_at_time", "resource", "action", "volume_mb", "threat_score"]]
        display_cols.columns = ["Day", "Employee", "Role at Time", "Resource", "Action", "Volume (MB)", "Threat Score"]

        st.dataframe(
            display_cols.style
                .background_gradient(subset=["Threat Score"], cmap="YlOrRd", vmin=0, vmax=100)
                .format({"Volume (MB)": "{:.1f}", "Threat Score": "{:.1f}"}),
            use_container_width=True, hide_index=True, height=320
        )

# ── Formula footer ──
st.markdown("---")
st.markdown(f"""
<div style="background:#111827; border:1px solid #1E293B; border-radius:10px; padding:20px 24px; margin-top:8px;">
    <div style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B; margin-bottom:10px; text-transform:uppercase; letter-spacing:0.1em;">
        Threat Scoring Logic
    </div>
    <div style="font-family:'JetBrains Mono'; font-size:0.95rem; color:#E2E8F0; line-height:1.6;">
        IF (role, resource) ∉ AccessControlMatrix: TS = {rbac_penalty} + drift<br/>
        ELSE: TS = ({w_volume} × σ<sub>volume</sub> + {w_temporal} × σ<sub>after-hours</sub>) × 10
    </div>
    <div style="font-family:'Inter'; font-size:0.78rem; color:#64748B; margin-top:8px;">
        Role is resolved per-event via the Context Resolver — checking role_change_events.csv when HR integration is enabled
        {"&nbsp; <span style='color:#A78BFA;'>[ CONTEXT ENGINE: ACTIVE ]</span>" if apply_context else "&nbsp; <span style='color:#475569;'>[ CONTEXT ENGINE: DISABLED ]</span>"}
    </div>
</div>
""", unsafe_allow_html=True)