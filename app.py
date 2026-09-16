import streamlit as st
import pandas as pd
import numpy as np
import time

# Must be the first command
st.set_page_config(page_title="Silent Shift | Threat Engine", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

# --- Custom CSS for a slight Hacker/Cyber aesthetic ---
st.markdown("""
    <style>
    .stMetric { background-color: #1E1E2E; padding: 15px; border-radius: 8px; border-left: 4px solid #7B61FF; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# CORE ENGINE MODULES (Same math, better UI)
# ==========================================
@st.cache_data
def generate_client_events():
    np.random.seed(42)
    days = 30
    events = []
    vol_a = np.random.normal(50, 10, days)
    move_a = np.random.randint(0, 2, days)
    vol_b = np.random.normal(50, 10, days) + np.arange(days) * 2.5
    move_b = np.zeros(days)
    move_b[25:] = 3 
    for d in range(days):
        events.append({"day": d+1, "user_id": "User_A", "volume_mb": vol_a[d], "spatial_moves": move_a[d]})
        events.append({"day": d+1, "user_id": "User_B", "volume_mb": vol_b[d], "spatial_moves": move_b[d]})
    return pd.DataFrame(events)

class BaselineBuilder:
    def __init__(self, window=15):
        self.window = window
        self.profiles = {}
    def build_profiles(self, df):
        for user in df['user_id'].unique():
            baseline = df[(df['user_id'] == user) & (df['day'] <= self.window)]
            self.profiles[user] = {
                "mean_V": baseline['volume_mb'].mean(), "std_V": baseline['volume_mb'].std() + 0.1,
                "mean_S": baseline['spatial_moves'].mean(), "std_S": baseline['spatial_moves'].std() + 0.1
            }

class ScoringEngine:
    def __init__(self, w_spatial, w_volume):
        self.w_S, self.w_V = w_spatial, w_volume
    def calculate_score(self, row, profile):
        sigma_S = max(0, (row['spatial_moves'] - profile['mean_S']) / profile['std_S'])
        sigma_V = max(0, (row['volume_mb'] - profile['mean_V']) / profile['std_V'])
        return ((self.w_S * sigma_S) + (self.w_V * sigma_V)) * 10

class ContextResolver:
    def __init__(self, active):
        self.active = active
        self.hr_context = {'User_B': {'role_change_day': 20, 'risk_reduction': 30}}
    def apply_context(self, user, day, score):
        if self.active and user in self.hr_context and day >= self.hr_context[user]['role_change_day']:
            return max(0, score - self.hr_context[user]['risk_reduction']), True
        return score, False

# ==========================================
# SIDEBAR CONTROLS
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/GitHub_Invertocat_Logo.svg/1200px-GitHub_Invertocat_Logo.svg.png", width=50) # Placeholder logo
    st.title("Engine Controls")
    
    st.subheader("⚙️ Threat Model Weights")
    w_spatial = st.slider("Spatial Risk (Lateral Moves)", 0.1, 1.0, 0.7, help="Weight given to accessing unusual network locations.")
    w_volume = st.slider("Velocity Risk (Data Volume)", 0.1, 1.0, 0.3, help="Weight given to massive data downloads.")
    
    st.divider()
    
    st.subheader("🏢 Context Engine (HR)")
    apply_context = st.toggle("Enable Workday/HR Integration", value=False)
    st.caption("Simulates an API webhook notifying the engine that User_B was promoted to Data Science on Day 20.")
    
    alert_threshold = st.slider("Alert Threshold", 20, 80, 40)

# ==========================================
# MAIN DASHBOARD
# ==========================================
st.title("🛡️ Silent Shift: Behavioral Threat Core")
st.markdown("Real-time behavioral telemetry monitoring with dynamic HR context resolution.")

# Execute Pipeline
df_events = generate_client_events()
builder = BaselineBuilder()
builder.build_profiles(df_events)
scorer = ScoringEngine(w_spatial, w_volume)
resolver = ContextResolver(apply_context)

final_scores, context_flags = [], []
for _, row in df_events.iterrows():
    user = row['user_id']
    raw_score = scorer.calculate_score(row, builder.profiles[user])
    score, flagged = resolver.apply_context(user, row['day'], raw_score)
    final_scores.append(score)
    context_flags.append(flagged)

df_events['threat_score'] = final_scores
df_events['context_applied'] = context_flags

# KPI Metrics Row
alerts = df_events[(df_events['threat_score'] > alert_threshold) & (df_events['day'] > 20)]
suppressed_count = len(df_events[df_events['context_applied'] == True])

col1, col2, col3 = st.columns(3)
col1.metric(label="Total Telemetry Events", value="60", delta="Live")
if apply_context:
    col2.metric(label="Critical SOC Alerts", value=len(alerts), delta="-10 False Positives", delta_color="inverse")
    col3.metric(label="Context Interceptions", value=suppressed_count, delta="Active Integration", delta_color="normal")
else:
    col2.metric(label="Critical SOC Alerts", value=len(alerts), delta="Action Required", delta_color="inverse")
    col3.metric(label="Context Interceptions", value="0", delta="Integration Offline", delta_color="off")

st.divider()

# The "Wow Factor" Button
if st.button("🚀 Run Behavioral Analysis Matrix", use_container_width=True):
    with st.spinner("Correlating spatial and velocity matrices..."):
        time.sleep(1.5) # Fake loading time for dramatic effect during demo
    
    # Charts Row
    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("🟢 User A (Normal Employee)")
        st.area_chart(df_events[df_events['user_id'] == 'User_A'].set_index('day')['threat_score'], color="#2E8B57")

    with chart_col2:
        st.subheader("🔴 User B (Silent Shift Insider)")
        st.area_chart(df_events[df_events['user_id'] == 'User_B'].set_index('day')['threat_score'], color="#FF4B4B")

    # Alerts Table Row
    st.subheader("🚨 Threat Engine Alert Log")
    if alerts.empty:
        st.success("✅ Engine cleared. No anomalous baseline drift detected.")
    else:
        st.error(f"⚠️ {len(alerts)} High-Risk Events Detected! Initiating SOC workflow.")
        # Make the table look nicer
        st.dataframe(
            alerts[['day', 'user_id', 'volume_mb', 'spatial_moves', 'threat_score']].style.highlight_max(axis=0, color="#4b0000"),
            use_container_width=True,
            hide_index=True
        )