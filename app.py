import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Silent Shift | Core Engine", layout="wide")

# ==========================================
# CORE ENGINE MODULES
# ==========================================
@st.cache_data
def generate_client_events():
    """Module 1 & 2: Data Collector & Feature Extractor"""
    np.random.seed(42)
    days = 30
    events = []
    
    # User A: Normal Baseline
    vol_a = np.random.normal(50, 10, days)
    move_a = np.random.randint(0, 2, days)
    
    # User B: The "Silent Shift"
    vol_b = np.random.normal(50, 10, days) + np.arange(days) * 2.5
    move_b = np.zeros(days)
    move_b[25:] = 3 # Sudden spike on Day 25
    
    for d in range(days):
        events.append({"day": d+1, "user_id": "User_A", "volume_mb": vol_a[d], "spatial_moves": move_a[d]})
        events.append({"day": d+1, "user_id": "User_B", "volume_mb": vol_b[d], "spatial_moves": move_b[d]})
        
    return pd.DataFrame(events)

class BaselineBuilder:
    """Module 3: Baseline Builder"""
    def __init__(self, window=15):
        self.window = window
        self.profiles = {}

    def build_profiles(self, df):
        for user in df['user_id'].unique():
            baseline = df[(df['user_id'] == user) & (df['day'] <= self.window)]
            self.profiles[user] = {
                "mean_V": baseline['volume_mb'].mean(),
                "std_V": baseline['volume_mb'].std() + 0.1,
                "mean_S": baseline['spatial_moves'].mean(),
                "std_S": baseline['spatial_moves'].std() + 0.1
            }

class ScoringEngine:
    """Module 4: Scoring Engine (Z-Score Math Model)"""
    def __init__(self, w_spatial, w_volume):
        self.w_S = w_spatial
        self.w_V = w_volume

    def calculate_score(self, row, profile):
        sigma_S = max(0, (row['spatial_moves'] - profile['mean_S']) / profile['std_S'])
        sigma_V = max(0, (row['volume_mb'] - profile['mean_V']) / profile['std_V'])
        return ((self.w_S * sigma_S) + (self.w_V * sigma_V)) * 10

class ContextResolver:
    """Module 5: Context Resolver"""
    def __init__(self, active):
        self.active = active
        self.hr_context = {'User_B': {'role_change_day': 20, 'risk_reduction': 30}}

    def apply_context(self, user, day, score):
        if self.active and user in self.hr_context and day >= self.hr_context[user]['role_change_day']:
            return max(0, score - self.hr_context[user]['risk_reduction'])
        return score

# ==========================================
# UI FRONTEND & PIPELINE EXECUTION
# ==========================================
st.sidebar.title("⚙️ Threat Model Weights")
st.sidebar.markdown("Adjust the mathematical weights of the scoring engine.")
w_spatial = st.sidebar.slider("Spatial Weight (Lateral Moves)", 0.1, 1.0, 0.6)
w_volume = st.sidebar.slider("Velocity Weight (Data Volume)", 0.1, 1.0, 0.4)

st.sidebar.divider()
st.sidebar.title("🏢 Business Logic")
apply_context = st.sidebar.checkbox("✅ Enable HR Context Integration (User_B promoted on Day 20)", value=False)
alert_threshold = st.sidebar.slider("Alert Threshold", 20, 80, 40)

# Initialize and run pipeline
df_events = generate_client_events()
builder = BaselineBuilder()
builder.build_profiles(df_events)

scorer = ScoringEngine(w_spatial, w_volume)
resolver = ContextResolver(apply_context)

# Process scores
final_scores = []
for _, row in df_events.iterrows():
    user = row['user_id']
    raw_score = scorer.calculate_score(row, builder.profiles[user])
    final_scores.append(resolver.apply_context(user, row['day'], raw_score))
df_events['threat_score'] = final_scores

# Render Dashboard
st.title("🛡️ Silent Shift: Threat Engine Architecture")
st.markdown("Demonstrating a decoupled ingestion, baseline, scoring, and context resolution pipeline.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("User A (Normal Employee)")
    st.line_chart(df_events[df_events['user_id'] == 'User_A'].set_index('day')['threat_score'])

with col2:
    st.subheader("User B (Potential Insider)")
    st.line_chart(df_events[df_events['user_id'] == 'User_B'].set_index('day')['threat_score'])

st.divider()
st.subheader("🚨 Threat Engine Alerts")
alerts = df_events[(df_events['threat_score'] > alert_threshold) & (df_events['day'] > 20)]
if alerts.empty:
    st.success("No active threats detected. Context rules suppressing false positives.")
else:
    st.error(f"{len(alerts)} anomalies breached the threat threshold!")
    st.dataframe(alerts[['day', 'user_id', 'volume_mb', 'spatial_moves', 'threat_score']], use_container_width=True)