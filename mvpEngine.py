import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

print("--- Initializing Silent Shift Detection Engine ---")

# 1. SIMULATE DATA: 30 days of baseline behavior for two users
np.random.seed(42)
days = 30

# User A: Normal employee (baseline: ~50MB data/day, 0-1 lateral moves)
user_a_data = pd.DataFrame({
    'user_id': ['User_A'] * days,
    'day': range(1, days + 1),
    'data_downloaded_mb': np.random.normal(50, 10, days),
    'lateral_moves': np.random.randint(0, 2, days)
})

# User B: The "Silent Shift" Insider (Starts normal, slowly escalates data hoarding)
user_b_data = pd.DataFrame({
    'user_id': ['User_B'] * days,
    'day': range(1, days + 1),
    'data_downloaded_mb': np.random.normal(50, 10, days) + np.arange(days) * 3, # Gradual drift
    'lateral_moves': np.random.randint(0, 2, days)
})
user_b_data.loc[25:, 'lateral_moves'] = 4 # Sudden spike in lateral movement

# Combine and shape the dataset
df = pd.concat([user_a_data, user_b_data])
features = ['data_downloaded_mb', 'lateral_moves']

# 2. TRAIN THE MODEL: Isolation Forest for unsupervised anomaly detection
# We train it on the first 15 days (assuming this is our "clean" baseline period)
baseline_data = df[df['day'] <= 15][features]
model = IsolationForest(contamination=0.1, random_state=42)
model.fit(baseline_data)

# Score all days (Output: 1 for normal, -1 for anomaly)
df['anomaly_prediction'] = model.predict(df[features])
# Convert isolation forest scores to a normalized Risk Score (higher = worse)
df['raw_risk_score'] = -model.score_samples(df[features]) * 100 

# 3. APPLY CONTEXT-AWARENESS (The Differentiator)
# Let's say User B's behavior is actually justified because on Day 20, 
# they were transferred to the Data Science team (requiring massive data access).
hr_context = {
    'User_B': {'role_change_day': 20, 'new_role': 'Data Scientist', 'risk_reduction': 40}
}

def apply_hr_context(row):
    score = row['raw_risk_score']
    user = row['user_id']
    day = row['day']
    
    if user in hr_context and day >= hr_context[user]['role_change_day']:
        # Suppress the alert due to legitimate HR role change
        score -= hr_context[user]['risk_reduction']
        
    return max(0, score) # Keep score above 0

df['contextual_risk_score'] = df.apply(apply_hr_context, axis=1)

# 4. OUTPUT RESULTS
print("\n[!] ALERTS GENERATED (Last 5 Days):")
recent_events = df[df['day'] > 25]
for index, row in recent_events.iterrows():
    if row['contextual_risk_score'] > 60: # Alert Threshold
        print(f"🚨 ALERT: {row['user_id']} on Day {row['day']} | Risk Score: {row['contextual_risk_score']:.2f} | Reason: Spike in Data/Lateral Moves")
    else:
        print(f"✅ CLEAR: {row['user_id']} on Day {row['day']} | Risk Score: {row['contextual_risk_score']:.2f}")