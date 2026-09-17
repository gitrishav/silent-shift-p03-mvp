import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="Silent Shift | SOC Threat Engine",
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

/* ── Base overrides ── */
.stApp {
    background-color: #0A0E1A;
    color: #C8CDD5;
}
header[data-testid="stHeader"] {
    background-color: #0A0E1A !important;
}
section[data-testid="stSidebar"] {
    background-color: #0D1224 !important;
    border-right: 1px solid #1A2040;
}
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stCheckbox label,
section[data-testid="stSidebar"] .stToggle label {
    color: #A0AEC0 !important;
}

/* ── Metric cards ── */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #111827 0%, #0D1224 100%);
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 20px 24px;
    transition: border-color 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    border-color: #7B61FF;
}
div[data-testid="stMetric"] label {
    color: #64748B !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.8rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
    color: #F1F5F9 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 700 !important;
    font-size: 2rem !important;
}

/* ── Header banner ── */
.hero-banner {
    background: linear-gradient(135deg, #0F172A 0%, #1E1B4B 50%, #0F172A 100%);
    border: 1px solid #2E1065;
    border-radius: 16px;
    padding: 32px 40px;
    margin-bottom: 24px;
    position: relative;
    overflow: hidden;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, #7B61FF, #A78BFA, #7B61FF, transparent);
}
.hero-banner h1 {
    font-family: 'Inter', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: #F1F5F9;
    margin: 0 0 4px 0;
}
.hero-banner p {
    font-family: 'Inter', sans-serif;
    color: #94A3B8;
    font-size: 0.95rem;
    margin: 0;
}
.hero-tag {
    display: inline-block;
    background: rgba(123, 97, 255, 0.15);
    color: #A78BFA;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    padding: 3px 10px;
    border-radius: 999px;
    border: 1px solid rgba(123, 97, 255, 0.3);
    margin-bottom: 12px;
    letter-spacing: 0.05em;
}

/* ── Section headers ── */
.section-header {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 1.1rem;
    color: #E2E8F0;
    padding-bottom: 8px;
    margin-top: 8px;
    margin-bottom: 16px;
    border-bottom: 1px solid #1E293B;
}

/* ── Alert cards ── */
.alert-critical {
    background: linear-gradient(135deg, #1C0A0A 0%, #2D0F0F 100%);
    border: 1px solid #7F1D1D;
    border-left: 4px solid #EF4444;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.alert-clear {
    background: linear-gradient(135deg, #052E16 0%, #0A1F0D 100%);
    border: 1px solid #14532D;
    border-left: 4px solid #22C55E;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.alert-suppressed {
    background: linear-gradient(135deg, #1A1523 0%, #1E1B2E 100%);
    border: 1px solid #3B2E6E;
    border-left: 4px solid #A78BFA;
    border-radius: 10px;
    padding: 16px 20px;
    margin-bottom: 8px;
}
.alert-title {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    font-size: 0.85rem;
    margin-bottom: 4px;
}
.alert-detail {
    font-family: 'Inter', sans-serif;
    font-size: 0.8rem;
    color: #94A3B8;
}

/* ── Pipeline indicator ── */
.pipeline-stage {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #111827;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 8px 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: #94A3B8;
}
.pipeline-stage .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #22C55E;
    box-shadow: 0 0 6px #22C55E;
}
.pipeline-arrow {
    color: #334155;
    font-size: 1.2rem;
    display: inline-flex;
    align-items: center;
    padding: 0 4px;
}

/* ── Threat level badge ── */
.threat-badge {
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    font-size: 0.7rem;
    padding: 3px 10px;
    border-radius: 6px;
    letter-spacing: 0.04em;
}
.threat-critical { background: #7F1D1D; color: #FCA5A5; }
.threat-high     { background: #78350F; color: #FCD34D; }
.threat-medium   { background: #1E3A5F; color: #7DD3FC; }
.threat-low      { background: #14532D; color: #86EFAC; }

/* ── Data table styling ── */
.stDataFrame { border-radius: 10px; overflow: hidden; }

/* ── Sidebar tweaks ── */
.sidebar-brand {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: #475569;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    padding: 4px 0 16px 0;
}
.sidebar-section {
    font-family: 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.85rem;
    color: #CBD5E1;
    margin-top: 16px;
    margin-bottom: 8px;
}

/* ── Dividers ── */
hr { border-color: #1E293B !important; }

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==========================================
# CORE ENGINE (unchanged logic)
# ==========================================
@st.cache_data
def generate_client_events():
    np.random.seed(42)
    days = 30
    events = []
    vol_a = np.random.normal(50, 10, days)
    move_a = np.random.randint(0, 2, days)
    temp_a = np.random.choice([0, 1], days, p=[0.85, 0.15])

    # User B: small baseline variance (days 1-15) so std isn't pinned at
    # the zero floor, a clean gap (days 16-19, still old role, no
    # anomalies), then a moderate elevated pattern starting exactly on
    # day 20 — the day HR reports the role change. This is what makes the
    # Context Resolver demo visible: the raw score crosses the alert
    # threshold after day 20, and toggling HR integration pulls every one
    # of those days back below it.
    vol_b = np.random.normal(50, 10, days)
    move_b = np.zeros(days)
    move_b[:15] = np.random.choice([0, 1], 15, p=[0.9, 0.1])
    move_b[19:] = np.random.choice([0, 1], days - 19, p=[0.3, 0.7])
    temp_b = np.zeros(days)
    temp_b[:15] = np.random.choice([0, 1], 15, p=[0.9, 0.1])
    temp_b[19:] = np.random.choice([0, 1], days - 19, p=[0.4, 0.6])

    role_change_idx = 19  # day 20 (0-indexed) — matches ContextResolver.hr_context
    vol_b[role_change_idx:] += 10  # modest volume bump from new role's data access

    base_date = datetime(2026, 8, 1)
    for d in range(days):
        ts = base_date + timedelta(days=d)
        events.append({
            "day": d + 1, "timestamp": ts, "user_id": "USR-4471 (A. Mercer)",
            "volume_mb": round(vol_a[d], 2), "spatial_moves": int(move_a[d]),
            "temporal_flag": int(temp_a[d])
        })
        events.append({
            "day": d + 1, "timestamp": ts, "user_id": "USR-8832 (R. Kaplan)",
            "volume_mb": round(vol_b[d], 2), "spatial_moves": int(move_b[d]),
            "temporal_flag": int(temp_b[d])
        })
    return pd.DataFrame(events)


class BaselineBuilder:
    def __init__(self, window=15):
        self.window = window
        self.profiles = {}

    def build_profiles(self, df):
        for user in df['user_id'].unique():
            bl = df[(df['user_id'] == user) & (df['day'] <= self.window)]
            self.profiles[user] = {
                "mean_V": bl['volume_mb'].mean(), "std_V": bl['volume_mb'].std() + 0.1,
                "mean_S": bl['spatial_moves'].mean(), "std_S": bl['spatial_moves'].std() + 0.1,
                "mean_T": bl['temporal_flag'].mean(), "std_T": bl['temporal_flag'].std() + 0.1,
            }


class ScoringEngine:
    def __init__(self, w_spatial, w_volume, w_temporal):
        self.w_S = w_spatial
        self.w_V = w_volume
        self.w_T = w_temporal

    def calculate_score(self, row, profile):
        sigma_S = max(0, (row['spatial_moves'] - profile['mean_S']) / profile['std_S'])
        sigma_V = max(0, (row['volume_mb'] - profile['mean_V']) / profile['std_V'])
        sigma_T = max(0, (row['temporal_flag'] - profile['mean_T']) / profile['std_T'])
        return ((self.w_S * sigma_S) + (self.w_V * sigma_V) + (self.w_T * sigma_T)) * 10


class ContextResolver:
    def __init__(self, active):
        self.active = active
        self.hr_context = {'USR-8832 (R. Kaplan)': {'role_change_day': 20, 'risk_reduction': 30}}

    def apply_context(self, user, day, score):
        if self.active and user in self.hr_context and day >= self.hr_context[user]['role_change_day']:
            return max(0, score - self.hr_context[user]['risk_reduction']), True
        return score, False


def get_threat_level(score, threshold):
    if score > threshold * 1.5:
        return "CRITICAL", "#EF4444"
    elif score > threshold:
        return "HIGH", "#F59E0B"
    elif score > threshold * 0.5:
        return "MEDIUM", "#3B82F6"
    return "LOW", "#22C55E"


# ==========================================
# PLOTLY CHART HELPERS
# ==========================================
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#94A3B8", size=12),
    margin=dict(l=0, r=0, t=30, b=0),
    xaxis=dict(
        gridcolor="#1E293B", zerolinecolor="#1E293B",
        tickfont=dict(size=10, color="#64748B")
    ),
    yaxis=dict(
        gridcolor="#1E293B", zerolinecolor="#1E293B",
        tickfont=dict(size=10, color="#64748B")
    ),
    legend=dict(
        font=dict(size=11, color="#94A3B8"),
        bgcolor="rgba(0,0,0,0)"
    ),
    hoverlabel=dict(
        bgcolor="#1E293B",
        font_size=12,
        font_family="JetBrains Mono, monospace",
        font_color="#E2E8F0",
        bordercolor="#334155"
    ),
)


def make_threat_chart(df_user, user_label, color_main, color_fill, threshold):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_user['day'], y=df_user['threat_score'],
        mode='lines', name='Threat Score',
        line=dict(color=color_main, width=2.5),
        fill='tozeroy', fillcolor=color_fill,
        hovertemplate="Day %{x}<br>Score: %{y:.1f}<extra></extra>"
    ))
    fig.add_hline(
        y=threshold, line_dash="dot", line_color="#EF4444",
        annotation_text="ALERT THRESHOLD",
        annotation_font=dict(size=10, color="#EF4444", family="JetBrains Mono"),
        annotation_position="top right"
    )
    # Mark the baseline window
    fig.add_vrect(x0=1, x1=15, fillcolor="rgba(123,97,255,0.05)",
                  line_width=0,
                  annotation_text="BASELINE WINDOW", annotation_position="top left",
                  annotation_font=dict(size=9, color="#7B61FF", family="JetBrains Mono"))
    fig.update_layout(
        **PLOTLY_LAYOUT,
        height=280,
        yaxis_title=None, xaxis_title=None,
        showlegend=False,
    )
    return fig


def make_comparison_chart(df, threshold):
    user_a = df[df['user_id'].str.contains("Mercer")]
    user_b = df[df['user_id'].str.contains("Kaplan")]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=user_a['day'], y=user_a['threat_score'],
        mode='lines', name='USR-4471 (A. Mercer)',
        line=dict(color="#22C55E", width=2),
        hovertemplate="Day %{x}<br>Score: %{y:.1f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=user_b['day'], y=user_b['threat_score'],
        mode='lines', name='USR-8832 (R. Kaplan)',
        line=dict(color="#EF4444", width=2.5),
        hovertemplate="Day %{x}<br>Score: %{y:.1f}<extra></extra>"
    ))
    fig.add_hline(y=threshold, line_dash="dot", line_color="#F59E0B",
                  annotation_text="THRESHOLD",
                  annotation_font=dict(size=10, color="#F59E0B", family="JetBrains Mono"),
                  annotation_position="top right")
    layout = {**PLOTLY_LAYOUT, "height": 320}
    layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    fig.update_layout(**layout)
    return fig


def make_gauge(score, threshold):
    level, color = get_threat_level(score, threshold)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(font=dict(size=36, family="JetBrains Mono", color=color)),
        gauge=dict(
            axis=dict(range=[0, 100], tickwidth=1, tickcolor="#1E293B",
                      tickfont=dict(size=10, color="#475569")),
            bar=dict(color=color, thickness=0.7),
            bgcolor="#111827",
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
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8"),
        height=200,
        margin=dict(l=20, r=20, t=30, b=10),
    )
    return fig


# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    st.markdown('<div class="sidebar-brand">SILENT SHIFT ENGINE v2.0</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">⚙️ Threat Model Weights</div>', unsafe_allow_html=True)
    w_spatial = st.slider("Spatial Risk (Lateral Movement)", 0.1, 1.0, 0.5, help="How heavily to weight unauthorized lateral network movement")
    w_volume = st.slider("Velocity Risk (Data Exfiltration)", 0.1, 1.0, 0.3, help="How heavily to weight abnormal data download volume")
    w_temporal = st.slider("Temporal Risk (After-Hours Access)", 0.1, 1.0, 0.2, help="How heavily to weight off-hours system access")

    st.divider()

    st.markdown('<div class="sidebar-section">🏢 Context Engine</div>', unsafe_allow_html=True)
    apply_context = st.toggle("Enable HR/Workday Integration", value=False)
    st.caption("Simulates Workday webhook: USR-8832 promoted to Data Science Lead on Day 20, suppressing expected behavioral drift.")

    st.divider()

    st.markdown('<div class="sidebar-section">🎯 Detection Tuning</div>', unsafe_allow_html=True)
    alert_threshold = st.slider("Alert Threshold (TS)", 20, 80, 40, help="Threat Score above which an event triggers a SOC alert")

    st.divider()
    st.markdown("""
    <div style="font-family: 'JetBrains Mono'; font-size: 0.65rem; color: #334155; padding-top: 8px;">
    TEAM P03 · MANIPAL HACKATHON 2026<br/>
    Engine: Z-Score + Context Pipeline<br/>
    Build: qualifier-v2.0
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# PIPELINE EXECUTION
# ==========================================
df_events = generate_client_events()
builder = BaselineBuilder()
builder.build_profiles(df_events)
scorer = ScoringEngine(w_spatial, w_volume, w_temporal)
resolver = ContextResolver(apply_context)

scores_list, ctx_list = [], []
for _, row in df_events.iterrows():
    user = row['user_id']
    raw = scorer.calculate_score(row, builder.profiles[user])
    final, flagged = resolver.apply_context(user, row['day'], raw)
    scores_list.append(round(final, 2))
    ctx_list.append(flagged)

df_events['threat_score'] = scores_list
df_events['context_applied'] = ctx_list

alerts = df_events[(df_events['threat_score'] > alert_threshold) & (df_events['day'] > 15)]
suppressed = df_events[df_events['context_applied'] == True]
max_score_b = df_events[df_events['user_id'].str.contains("Kaplan")]['threat_score'].max()
level_label, level_color = get_threat_level(max_score_b, alert_threshold)


# ==========================================
# MAIN UI
# ==========================================

# ── Hero banner ──
st.markdown(f"""
<div class="hero-banner">
    <span class="hero-tag">P03 · QUALIFIER ENGINE · MANIPAL HACKATHON 2026</span>
    <h1>🛡️ Silent Shift</h1>
    <p>Behavioral Threat Detection Engine — Continuous Z-score anomaly scoring with dynamic HR context resolution</p>
</div>
""", unsafe_allow_html=True)

# ── Pipeline status bar ──
st.markdown("""
<div style="display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-bottom: 24px;">
    <div class="pipeline-stage"><span class="dot"></span> Data Collector</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-stage"><span class="dot"></span> Baseline Builder</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-stage"><span class="dot"></span> Scoring Engine</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-stage"><span class="dot"></span> Context Resolver</div>
    <span class="pipeline-arrow">→</span>
    <div class="pipeline-stage"><span class="dot"></span> SOC Output</div>
</div>
""", unsafe_allow_html=True)

# ── KPI row ──
k1, k2, k3, k4 = st.columns(4)
k1.metric("Telemetry Events", f"{len(df_events)}", "30-day window")
if apply_context:
    k2.metric("SOC Alerts", f"{len(alerts)}", f"-{len(suppressed)} suppressed", delta_color="inverse")
    k3.metric("Context Interceptions", f"{len(suppressed)}", "HR integration active")
else:
    k2.metric("SOC Alerts", f"{len(alerts)}", "Unfiltered", delta_color="inverse")
    k3.metric("Context Interceptions", "0", "Integration offline", delta_color="off")
k4.metric("Peak Threat Score", f"{max_score_b:.1f}", level_label)

st.markdown("---")

# ── Threat comparison chart ──
st.markdown('<div class="section-header">📊 Behavioral Drift Comparison</div>', unsafe_allow_html=True)
st.plotly_chart(make_comparison_chart(df_events, alert_threshold), use_container_width=True)

# ── Per-user deep dive ──
st.markdown('<div class="section-header">🔍 Per-User Threat Analysis</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)

user_a_df = df_events[df_events['user_id'].str.contains("Mercer")]
user_b_df = df_events[df_events['user_id'].str.contains("Kaplan")]

with col_a:
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
        <div style="width:10px; height:10px; border-radius:50%; background:#22C55E; box-shadow: 0 0 8px #22C55E;"></div>
        <span style="font-family:'JetBrains Mono'; font-size:0.9rem; color:#E2E8F0;">
            USR-4471 · A. Mercer
        </span>
        <span class="threat-badge threat-low">LOW RISK</span>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(
        make_threat_chart(user_a_df, "User A", "#22C55E", "rgba(34,197,94,0.08)", alert_threshold),
        use_container_width=True
    )

with col_b:
    badge_class = "threat-critical" if level_label == "CRITICAL" else "threat-high" if level_label == "HIGH" else "threat-medium"
    st.markdown(f"""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
        <div style="width:10px; height:10px; border-radius:50%; background:#EF4444; box-shadow: 0 0 8px #EF4444;"></div>
        <span style="font-family:'JetBrains Mono'; font-size:0.9rem; color:#E2E8F0;">
            USR-8832 · R. Kaplan
        </span>
        <span class="threat-badge {badge_class}">{level_label}</span>
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(
        make_threat_chart(user_b_df, "User B", "#EF4444", "rgba(239,68,68,0.08)", alert_threshold),
        use_container_width=True
    )

# ── Threat gauge + alert log side by side ──
st.markdown("---")
st.markdown('<div class="section-header">🚨 Threat Engine Output</div>', unsafe_allow_html=True)

gauge_col, log_col = st.columns([1, 2])

with gauge_col:
    st.markdown("""
    <div style="text-align:center; font-family:'JetBrains Mono'; font-size:0.75rem; color:#64748B; margin-bottom:4px;">
        USR-8832 PEAK THREAT
    </div>
    """, unsafe_allow_html=True)
    st.plotly_chart(make_gauge(max_score_b, alert_threshold), use_container_width=True)

    # Baseline profile card
    profile_b = builder.profiles['USR-8832 (R. Kaplan)']
    st.markdown(f"""
    <div style="background:#111827; border:1px solid #1E293B; border-radius:10px; padding:16px; margin-top:8px;">
        <div style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B; margin-bottom:10px; text-transform:uppercase; letter-spacing:0.08em;">
            Baseline Profile · USR-8832
        </div>
        <div style="font-family:'JetBrains Mono'; font-size:0.8rem; color:#A0AEC0; line-height:1.8;">
            μ(Volume) = <span style="color:#E2E8F0;">{profile_b['mean_V']:.1f} MB</span><br/>
            σ(Volume) = <span style="color:#E2E8F0;">{profile_b['std_V']:.1f}</span><br/>
            μ(Spatial) = <span style="color:#E2E8F0;">{profile_b['mean_S']:.2f}</span><br/>
            σ(Spatial) = <span style="color:#E2E8F0;">{profile_b['std_S']:.2f}</span><br/>
            μ(Temporal) = <span style="color:#E2E8F0;">{profile_b['mean_T']:.2f}</span><br/>
            Window = <span style="color:#7B61FF;">15 days</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with log_col:
    if alerts.empty:
        st.markdown("""
        <div class="alert-clear">
            <div class="alert-title" style="color:#22C55E;">✅ ALL CLEAR</div>
            <div class="alert-detail">No anomalous baseline drift detected. All behavioral telemetry within expected deviation bounds.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="alert-critical">
            <div class="alert-title" style="color:#FCA5A5;">⚠️ {len(alerts)} HIGH-RISK EVENTS DETECTED</div>
            <div class="alert-detail">Behavioral drift exceeds configured threshold (TS &gt; {alert_threshold}). SOC review recommended.</div>
        </div>
        """, unsafe_allow_html=True)

        # Show suppression notice if context is active
        if apply_context and len(suppressed) > 0:
            st.markdown(f"""
            <div class="alert-suppressed">
                <div class="alert-title" style="color:#A78BFA;">🏢 CONTEXT RESOLVER ACTIVE</div>
                <div class="alert-detail">{len(suppressed)} events suppressed via HR integration. USR-8832 role change (→ Data Science Lead) on Day 20 recognized. Risk reduction factor applied: -30 TS.</div>
            </div>
            """, unsafe_allow_html=True)

        display_alerts = alerts[['day', 'user_id', 'volume_mb', 'spatial_moves', 'temporal_flag', 'threat_score', 'context_applied']].copy()
        display_alerts.columns = ['Day', 'User', 'Volume (MB)', 'Lateral Moves', 'After-Hours', 'Threat Score', 'Context Applied']
        display_alerts['Threat Score'] = display_alerts['Threat Score'].round(1)

        st.dataframe(
            display_alerts.style
                .background_gradient(subset=['Threat Score'], cmap='YlOrRd', vmin=0, vmax=100)
                .format({'Volume (MB)': '{:.1f}', 'Threat Score': '{:.1f}'}),
            use_container_width=True,
            hide_index=True,
            height=320
        )

# ── Equation footer ──
st.markdown("---")
st.markdown(f"""
<div style="background:#111827; border:1px solid #1E293B; border-radius:10px; padding:20px 24px; margin-top:8px;">
    <div style="font-family:'JetBrains Mono'; font-size:0.7rem; color:#64748B; margin-bottom:10px; text-transform:uppercase; letter-spacing:0.1em;">
        Threat Scoring Equation
    </div>
    <div style="font-family:'JetBrains Mono'; font-size:0.95rem; color:#E2E8F0; line-height:1.6;">
        TS = ({w_spatial} × σ<sub>spatial</sub> + {w_volume} × σ<sub>velocity</sub> + {w_temporal} × σ<sub>temporal</sub>) × 10 &nbsp;−&nbsp; C<sub>HR</sub>
    </div>
    <div style="font-family:'Inter'; font-size:0.78rem; color:#64748B; margin-top:8px;">
        Where σ<sub>i</sub> = max(0, (x − μ) / σ) per feature, and C<sub>HR</sub> = context suppression factor from Workday integration
        {"&nbsp; <span style='color:#A78BFA;'>[ C_HR = 30 — ACTIVE ]</span>" if apply_context else "&nbsp; <span style='color:#475569;'>[ C_HR = 0 — DISABLED ]</span>"}
    </div>
</div>
""", unsafe_allow_html=True)