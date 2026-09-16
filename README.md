# 🛡️ Silent Shift: Threat Engine Architecture (P03)

An MVP core security engine for the Manipal Hackathon 2026. This project demonstrates a decoupled, mathematically explicit anomaly detection pipeline designed to catch gradual insider threats ("Silent Shifts") while suppressing false positives via business context integration.

## 🧠 Core Engine Architecture

Instead of relying on brittle static rules or opaque "black-box" machine learning, we built a transparent pipeline consisting of four independent modules:

1. **Data Collector & Extractor:** Ingests raw client telemetry (e.g., data download volume, lateral network movement).
2. **Baseline Builder:** Calculates and freezes a rolling statistical profile (Mean and Standard Deviation) for each user based on a 15-day clean baseline.
3. **Scoring Engine (Threat Model):** Calculates the Z-score deviation for incoming events and applies dynamic weights (Spatial vs. Velocity risk) to generate a raw Threat Score.
4. **Context Resolver:** An interception layer that integrates with HR/IT APIs. If a user's role changes (e.g., a promotion), this module dynamically suppresses the resulting behavioral spike, preventing SOC alert fatigue.

## 🚀 How to Run the Demo

1. Clone the repository:
   `git clone [your-repo-link]`
2. Install dependencies:
   `pip install -r requirements.txt`
3. Launch the SOC Dashboard:
   `streamlit run app.py`

## 🛠️ Tech Stack
* **Engine Logic:** Python, Pandas, NumPy (Custom Z-Score Pipeline)
* **Interactive UI:** Streamlit (Features real-time Threat Model weight adjustments)
