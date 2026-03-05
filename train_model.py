"""
Train a hazard classification model on NASA NeoWs data.
Run this once to generate model.pkl, then integrate predictions into main.py.

Usage:
    pip install scikit-learn xgboost shap pandas requests
    python train_model.py
"""

import requests
import pandas as pd
import numpy as np
import pickle
import os
from datetime import date, timedelta

import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
import shap

NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
NASA_BROWSE_URL = "https://api.nasa.gov/neo/rest/v1/neo/browse"


# ──────────────────────────────────────────────
# 1. Fetch NEO data from NASA
# ──────────────────────────────────────────────

def fetch_neo_pages(max_pages: int = 20) -> list:
    """Fetch multiple pages of NEO data from NASA."""
    all_neos = []
    for page in range(max_pages):
        print(f"Fetching page {page + 1}/{max_pages}…")
        resp = requests.get(NASA_BROWSE_URL, params={
            "api_key": NASA_API_KEY, "page": page, "size": 20
        })
        resp.raise_for_status()
        data = resp.json()
        neos = data.get("near_earth_objects", [])
        if not neos:
            break
        all_neos.extend(neos)
    print(f"Fetched {len(all_neos)} NEOs total.")
    return all_neos


# ──────────────────────────────────────────────
# 2. Feature Engineering
# ──────────────────────────────────────────────

def extract_features(neo: dict) -> dict | None:
    """Extract ML features from a single NEO record."""
    try:
        diam_min = neo["estimated_diameter"]["kilometers"]["estimated_diameter_min"]
        diam_max = neo["estimated_diameter"]["kilometers"]["estimated_diameter_max"]
        diam_avg = (diam_min + diam_max) / 2

        approaches = neo.get("close_approach_data", [])
        if not approaches:
            return None

        # Use the most recent approach
        latest = approaches[-1]
        velocity_kms = float(latest["relative_velocity"]["kilometers_per_second"])
        miss_distance_km = float(latest["miss_distance"]["kilometers"])
        miss_distance_au = float(latest["miss_distance"]["astronomical"])

        # Kinetic energy proxy (mass estimate from diameter)
        radius_m = (diam_avg * 1000) / 2
        volume_m3 = (4 / 3) * np.pi * radius_m ** 3
        mass_kg = volume_m3 * 2000  # stony asteroid density
        velocity_ms = velocity_kms * 1000
        ke_joules = 0.5 * mass_kg * velocity_ms ** 2
        energy_mt = ke_joules * 2.1e-16

        orbital = neo.get("orbital_data", {})
        eccentricity = float(orbital.get("eccentricity", 0))
        inclination = float(orbital.get("inclination", 0))
        perihelion = float(orbital.get("perihelion_distance", 1))
        semi_major = float(orbital.get("semi_major_axis", 1))

        return {
            "diameter_km": diam_avg,
            "velocity_kms": velocity_kms,
            "miss_distance_km": miss_distance_km,
            "miss_distance_au": miss_distance_au,
            "energy_mt": energy_mt,
            "eccentricity": eccentricity,
            "inclination_deg": inclination,
            "perihelion_au": perihelion,
            "semi_major_axis_au": semi_major,
            "is_hazardous": int(neo["is_potentially_hazardous_asteroid"])
        }
    except (KeyError, ValueError, TypeError):
        return None


# ──────────────────────────────────────────────
# 3. Train Model
# ──────────────────────────────────────────────

def train(neos: list):
    records = [r for neo in neos if (r := extract_features(neo)) is not None]
    df = pd.DataFrame(records)

    print(f"\nDataset: {len(df)} samples, {df['is_hazardous'].sum()} hazardous ({df['is_hazardous'].mean():.1%})")

    FEATURES = [
        "diameter_km", "velocity_kms", "miss_distance_km",
        "energy_mt", "eccentricity", "inclination_deg",
        "perihelion_au", "semi_major_axis_au"
    ]
    X = df[FEATURES]
    y = df["is_hazardous"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = xgb.XGBClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=(y == 0).sum() / (y == 1).sum(),  # handle class imbalance
        eval_metric="logloss",
        random_state=42,
        verbosity=0
    )
    model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)

    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    print("\n── Classification Report ──")
    print(classification_report(y_test, y_pred, target_names=["Not Hazardous", "Hazardous"]))
    print(f"ROC-AUC: {roc_auc_score(y_test, y_prob):.4f}")

    # SHAP explainability
    print("\n── SHAP Feature Importance ──")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_test)
    importance = pd.DataFrame({
        "feature": FEATURES,
        "mean_abs_shap": np.abs(shap_values).mean(axis=0)
    }).sort_values("mean_abs_shap", ascending=False)
    print(importance.to_string(index=False))

    # Save model + feature list
    with open("model.pkl", "wb") as f:
        pickle.dump({"model": model, "features": FEATURES, "explainer": explainer}, f)
    print("\n✅ Model saved to model.pkl")
    print("   Next step: load model.pkl in main.py and replace estimate_hazard_probability()")

    return model, FEATURES, explainer


# ──────────────────────────────────────────────
# 4. Integration snippet (shows how to use in main.py)
# ──────────────────────────────────────────────

INTEGRATION_SNIPPET = '''
# Add this to main.py after training:

import pickle
import shap
import numpy as np

with open("model.pkl", "rb") as f:
    _pkg = pickle.load(f)
_model = _pkg["model"]
_features = _pkg["features"]
_explainer = _pkg["explainer"]

def ml_hazard_probability(diameter_km, velocity_kms, miss_distance_km,
                           energy_mt, eccentricity=0, inclination=0,
                           perihelion=1, semi_major=1) -> dict:
    """Return ML-based hazard probability + top SHAP features."""
    row = [[diameter_km or 0, velocity_kms, miss_distance_km or 1e8,
            energy_mt, eccentricity, inclination, perihelion, semi_major]]
    prob = float(_model.predict_proba(row)[0][1])
    shap_vals = _explainer.shap_values(row)[0]
    top_features = sorted(
        zip(_features, shap_vals), key=lambda x: abs(x[1]), reverse=True
    )[:3]
    return {
        "probability": round(prob, 4),
        "top_factors": [{"feature": f, "shap": round(s, 4)} for f, s in top_features]
    }
'''

if __name__ == "__main__":
    print("=" * 50)
    print("Asteroid Hazard Classification — Training Pipeline")
    print("=" * 50)
    neos = fetch_neo_pages(max_pages=15)
    model, features, explainer = train(neos)
    print("\n── Integration snippet for main.py ──")
    print(INTEGRATION_SNIPPET)
