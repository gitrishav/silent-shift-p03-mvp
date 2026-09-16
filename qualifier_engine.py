import pandas as pd
import numpy as np

print("--- Initializing Silent Shift Core Engine (Qualifier Build) ---")

# ==========================================
# MODULE 1 & 2: Data Collector & Feature Extractor
# ==========================================
def generate_client_events():
    """Simulates 30 days of raw client JSON events for 'User_B'."""
    np.random.seed(42)
    days = 30
    
    # Simulating a user who slowly increases data downloads and suddenly accesses new servers
    data_volume = np.random.normal(50, 10, days) + np.arange(days) * 2.5 # Gradual drift
    lateral_moves = np.zeros(days)
    lateral_moves[25:] = 3 # Sudden spike on day 25
    after_hours_logins = np.random.randint(0, 2, days)
    
    events = []
    for day in range(days):
        events.append({
            "day": day + 1,
            "user_id": "User_B",
            "volume_mb": data_volume[day],
            "spatial_moves": lateral_moves[day],
            "temporal_flags": after_hours_logins[day]
        })
    return pd.DataFrame(events)

# ==========================================
# MODULE 3: Baseline Builder
# ==========================================
class BaselineBuilder:
    def __init__(self, baseline_window=15):
        self.window = baseline_window
        self.profiles = {}

    def build_profile(self, df):
        """Calculates the historical mean and standard deviation for the user."""
        baseline_data = df[df['day'] <= self.window]
        
        self.profiles["User_B"] = {
            "mean_V": baseline_data['volume_mb'].mean(),
            "std_V": baseline_data['volume_mb'].std(),
            "mean_S": baseline_data['spatial_moves'].mean(),
            "std_S": baseline_data['spatial_moves'].std() + 0.1, # Add 0.1 to prevent division by zero
            "mean_T": baseline_data['temporal_flags'].mean(),
            "std_T": baseline_data['temporal_flags'].std() + 0.1
        }
        print(f"[*] Baseline Profile Built for User_B: {self.profiles['User_B']}")

# ==========================================
# MODULE 4: Scoring Engine (The Math Model)
# ==========================================
class ScoringEngine:
    def __init__(self, w1, w2, w3):
        self.w1 = w1 # Weight for Spatial (Lateral Movement)
        self.w2 = w2 # Weight for Velocity (Data Volume)
        self.w3 = w3 # Weight for Temporal (After-hours)

    def calculate_raw_score(self, row, profile):
        """Calculates Z-scores and weights them according to our threat model."""
        # Calculate standard deviations (Z-scores): (value - mean) / std
        sigma_S = (row['spatial_moves'] - profile['mean_S']) / profile['std_S']
        sigma_V = (row['volume_mb'] - profile['mean_V']) / profile['std_V']
        sigma_T = (row['temporal_flags'] - profile['mean_T']) / profile['std_T']
        
        # Only count positive deviations (we don't care if they download *less* than usual)
        sigma_S, sigma_V, sigma_T = max(0, sigma_S), max(0, sigma_V), max(0, sigma_T)

        # Apply the TS equation (before context)
        raw_score = (self.w1 * sigma_S) + (self.w2 * sigma_V) + (self.w3 * sigma_T)
        return raw_score * 10 # Scale for readability

# ==========================================
# MODULE 5: Context Resolver
# ==========================================
class ContextResolver:
    def __init__(self):
        # Simulated HR API Response
        self.hr_context = {'User_B': {'role_change_day': 20, 'risk_reduction_factor': 30}}

    def apply_context(self, user_id, day, raw_score):
        """Subtracts the C_HR factor if a legitimate business context exists."""
        if user_id in self.hr_context and day >= self.hr_context[user_id]['role_change_day']:
            return max(0, raw_score - self.hr_context[user_id]['risk_reduction_factor'])
        return raw_score

# ==========================================
# EXECUTE THE PIPELINE
# ==========================================
df_events = generate_client_events()

builder = BaselineBuilder()
builder.build_profile(df_events)

# Prioritize Spatial anomalies (w1=0.5) over Volume (w2=0.3) and Temporal (w3=0.2)
scorer = ScoringEngine(w1=0.5, w2=0.3, w3=0.2)
resolver = ContextResolver()

print("\n--- Pipeline Execution Results (Last 10 Days) ---")
for index, row in df_events[df_events['day'] > 20].iterrows():
    user = row['user_id']
    profile = builder.profiles[user]
    
    # 1. Score the anomaly
    raw_score = scorer.calculate_raw_score(row, profile)
    
    # 2. Resolve with Context
    final_score = resolver.apply_context(user, row['day'], raw_score)
    
    alert = "🚨 CRITICAL ALERT" if final_score > 40 else "✅ Normal"
    print(f"Day {int(row['day']):02d} | Raw TS: {raw_score:.1f} | Final TS: {final_score:.1f} | Status: {alert}")