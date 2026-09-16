import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

st.set_page_config(page_title="Silent Shift SOC Dashboard", layout="wide")

# --- 1. DATA GENERATION (Cached for performance) ---
@st.cache_data
def load_data():
    np.random.seed(42)
    days = 30
    # User A: Normal behavior
    user_a = pd.DataFrame({'user_id': 'User_A', 'day': range(1, days + 1), 
                           'data_downloaded_mb': np.random.normal(50, 10, days), 
                           'lateral_moves': np.random.randint(0, 2, days)})
    # User B: Silent Shift (gradual drift + spike)
    user_b = pd.DataFrame({'user_id': 'User_B', 'day': range(1, days + 1), 
                           'data_downloaded_mb': np.random.normal(50, 10, days) + np.arange(days) * 3, 
                           'lateral_moves': np.random.randint(0, 2, days)})
    user_b.loc[25:, 'lateral_moves'] = 4 
    return pd.concat([user_a, user_b])

df = load_data()

# --- 2. ML SCORING ENGINE ---
features = ['data_downloaded_mb', 'lateral_moves']
baseline_data = df[df['day'] <= 15][features]
model = IsolationForest(contamination=0.1, random_state=42).fit(baseline_data)
df['raw_risk_score'] = -model.score_samples(df[features]) * 100 

# --- 3. UI: SIDEBAR & CONTEXT TOGGLE ---
st.sidebar.title("⚙️ Engine Controls")
st.sidebar.markdown("Simulate integrating Workday/HR logs to suppress false positives.")
apply_context = st.sidebar.checkbox("✅ Enable HR Context Integration (User_B promoted on Day 20)", value=False)
alert_threshold = st.sidebar.slider("Alert Threshold", 40, 90, 60)

# Apply Context Logic
hr_context = {'User_B': {'role_change_day': 20, 'risk_reduction': 40}}

def calculate_final_score(row):
    score = row['raw_risk_score']
    if apply_context and row['user_id'] in hr_context and row['day'] >= hr_context[row['user_id']]['role_change_day']:
        score -= hr_context[row['user_id']]['risk_reduction']
    return max(0, score)

df['final_risk_score'] = df.apply(calculate_final_score, axis=1)

# --- 4. UI: MAIN DASHBOARD ---
st.title("🛡️ Silent Shift: Insider Threat Analytics")
st.markdown("Monitoring continuous behavioral baselines. Context-awareness engine active.")

# Split view into two columns for the two users
col1, col2 = st.columns(2)

with col1:
    st.subheader("User A (Normal Employee)")
    st.line_chart(df[df['user_id'] == 'User_A'].set_index('day')['final_risk_score'])

with col2:
    st.subheader("User B (Potential Insider)")
    st.line_chart(df[df['user_id'] == 'User_B'].set_index('day')['final_risk_score'])

# Alerting Table
st.divider()
st.subheader("🚨 Priority SOC Alerts (Triggered by threshold)")
alerts = df[(df['final_risk_score'] > alert_threshold) & (df['day'] > 25)]
if alerts.empty:
    st.success("No critical alerts at this time.")
else:
    st.error(f"{len(alerts)} critical anomalies detected!")
    st.dataframe(alerts[['day', 'user_id', 'data_downloaded_mb', 'lateral_moves', 'final_risk_score']], use_container_width=True)