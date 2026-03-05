"""
Asteroid Impact Detection System - FastAPI Backend
Integrates NASA NeoWs API, physics calculations, ML hazard classification, and Torino/Palermo scale scoring.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import httpx
import math
import os
import json
from datetime import date, timedelta

app = FastAPI(
    title="Asteroid Impact Detection API",
    description="Real-time asteroid hazard detection using NASA NeoWs data, physics models, and ML classification.",
    version="2.0.0"
)

# Allow GitHub Pages frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict to your GitHub Pages URL in production
    allow_methods=["*"],
    allow_headers=["*"],
)

NASA_API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")  # Set via environment variable
NASA_BASE_URL = "https://api.nasa.gov/neo/rest/v1"

# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────

class ImpactRequest(BaseModel):
    mass_tons: float = Field(..., gt=0, description="Asteroid mass in metric tons")
    velocity_kms: float = Field(..., gt=0, description="Impact velocity in km/s")
    target_material: str = Field("rock", description="Surface material at impact site")
    diameter_km: Optional[float] = Field(None, description="Asteroid diameter in km (for risk scoring)")
    miss_distance_km: Optional[float] = Field(None, description="Closest approach distance in km")

class ImpactMetrics(BaseModel):
    mass_tons: float
    velocity_kms: float
    energy_megatons_tnt: float
    crater_km: float
    air_km: float
    shock_km: float
    thermal_km: float
    severity: str
    target_material: str
    torino_scale: int
    torino_label: str
    torino_color: str
    palermo_scale: Optional[float]
    hazard_probability: float
    insights: list[str]

# ──────────────────────────────────────────────
# Physics Calculations (ported from calculations.js)
# ──────────────────────────────────────────────

MATERIAL_PROPS = {
    "water":  {"density": 1000, "gravity": 9.81, "k": 2.1, "name": "Water/Ocean"},
    "rock":   {"density": 2500, "gravity": 9.81, "k": 1.8, "name": "Rock/Solid Ground"},
    "ice":    {"density": 900,  "gravity": 9.81, "k": 2.5, "name": "Ice/Glacier"},
    "sand":   {"density": 1600, "gravity": 9.81, "k": 2.8, "name": "Desert Sand"},
    "forest": {"density": 1200, "gravity": 9.81, "k": 2.2, "name": "Forest/Vegetation"},
}

def kinetic_energy_joules(mass_kg: float, velocity_ms: float) -> float:
    return 0.5 * mass_kg * velocity_ms ** 2

def crater_diameter_km(mass_kg: float, velocity_ms: float, material: str = "rock") -> float:
    props = MATERIAL_PROPS.get(material, MATERIAL_PROPS["rock"])
    ke = kinetic_energy_joules(mass_kg, velocity_ms)
    diameter_m = props["k"] * (ke / (props["gravity"] * props["density"])) ** 0.25
    return diameter_m / 1000

def air_blast_radius_km(mass_kg: float, velocity_ms: float) -> float:
    ke = kinetic_energy_joules(mass_kg, velocity_ms)
    return 0.0018 * ke ** (1 / 3)

def shock_wave_radius_km(mass_kg: float, velocity_ms: float, k: float = 0.0015) -> float:
    ke = kinetic_energy_joules(mass_kg, velocity_ms)
    return k * ke ** (1 / 3)

def thermal_radiation_radius_km(mass_kg: float, velocity_ms: float,
                                 thermal_fraction: float = 0.2,
                                 fluence_threshold: float = 150_000) -> float:
    ke = kinetic_energy_joules(mass_kg, velocity_ms)
    thermal_energy = thermal_fraction * ke
    radius_m = math.sqrt(thermal_energy / (4 * math.pi * fluence_threshold))
    return radius_m / 1000

# ──────────────────────────────────────────────
# Torino Scale Classifier
# ──────────────────────────────────────────────

def torino_scale(energy_mt: float, impact_probability: float = 0.0) -> dict:
    """
    Simplified Torino Scale (0–10) based on energy and probability.
    Real Torino Scale uses a 2D lookup table (probability × energy).
    """
    if impact_probability < 1e-4 or energy_mt < 0.001:
        return {"level": 0, "label": "No Hazard", "color": "white"}
    if energy_mt < 1:
        return {"level": 1, "label": "Normal", "color": "green"}
    if energy_mt < 10:
        level = 2 if impact_probability < 0.01 else 3
        return {"level": level, "label": "Meriting Attention", "color": "yellow"}
    if energy_mt < 100:
        level = 4 if impact_probability < 0.05 else 5
        return {"level": level, "label": "Threatening", "color": "orange"}
    if energy_mt < 1_000_000:
        level = 6 if impact_probability < 0.5 else 8
        return {"level": level, "label": "Certain Collision", "color": "red"}
    return {"level": 10, "label": "Global Catastrophe", "color": "red"}

# ──────────────────────────────────────────────
# Palermo Scale
# ──────────────────────────────────────────────

def palermo_scale(impact_probability: float, energy_mt: float, years_to_impact: float = 10) -> Optional[float]:
    """
    Palermo Technical Impact Hazard Scale.
    PS = log10(Pi / (fp * T))
    where fp = background annual impact frequency for energy E.
    """
    if impact_probability <= 0:
        return None
    # Background frequency for energy E (Shoemaker 1983 approximation)
    # fp ≈ 0.03 * E^(-0.78) per year for E in megatons
    if energy_mt <= 0:
        return None
    fp = 0.03 * energy_mt ** (-0.78)
    ps = math.log10(impact_probability / (fp * years_to_impact))
    return round(ps, 3)

# ──────────────────────────────────────────────
# Hazard Probability Estimate (rule-based, pre-ML)
# ──────────────────────────────────────────────

def estimate_hazard_probability(energy_mt: float, diameter_km: Optional[float],
                                  miss_distance_km: Optional[float]) -> float:
    """
    Rule-based hazard probability proxy.
    Replace with trained ML model output in Phase 2.
    """
    score = 0.0
    # Energy contribution
    if energy_mt > 1000:
        score += 0.4
    elif energy_mt > 10:
        score += 0.2
    elif energy_mt > 1:
        score += 0.05
    # Size contribution
    if diameter_km:
        if diameter_km > 1:
            score += 0.3
        elif diameter_km > 0.1:
            score += 0.1
    # Miss distance contribution
    if miss_distance_km:
        earth_radius_km = 6371
        if miss_distance_km < 3 * earth_radius_km:
            score += 0.3
        elif miss_distance_km < 10 * earth_radius_km:
            score += 0.1
    return min(round(score, 4), 1.0)

# ──────────────────────────────────────────────
# Insights Generator
# ──────────────────────────────────────────────

def generate_insights(metrics: dict) -> list[str]:
    insights = []
    energy = metrics["energy_megatons_tnt"]
    velocity = metrics["velocity_kms"]
    mass = metrics["mass_tons"]
    crater = metrics["crater_km"]
    air = metrics["air_km"]
    shock = metrics["shock_km"]
    thermal = metrics["thermal_km"]
    material = metrics["target_material"]
    torino = metrics["torino_scale"]

    insights.append(
        f"Kinetic energy scales with v² — at {velocity} km/s, this impact releases "
        f"{energy} megatons of TNT equivalent."
    )
    effects = {"Air Blast": air, "Shock Wave": shock, "Thermal Radiation": thermal}
    largest = max(effects, key=effects.get)
    insights.append(
        f"{largest} is the widest effect zone ({effects[largest]:.2f} km). "
        f"Atmospheric pressure waves typically propagate further than intense thermal radiation."
    )
    if crater < air:
        insights.append(
            f"Crater ({crater:.2f} km) is smaller than blast radius ({air:.2f} km) — "
            f"craters scale as E^1/4, slower than blast/thermal effects (E^1/3)."
        )
    insights.append(
        f"Target: {material}. Softer materials like sand or ice produce wider craters "
        f"than dense rock due to lower compressive strength."
    )
    if torino >= 5:
        insights.append(
            "⚠️ Torino Scale ≥5: This scenario warrants urgent attention. "
            "Real events at this scale trigger international planetary defense protocols."
        )
    elif torino >= 2:
        insights.append(
            "Torino Scale 2–4: This warrants monitoring. Astronomers would refine orbital "
            "data with follow-up observations before issuing public alerts."
        )
    else:
        insights.append(
            "Torino Scale 0–1: Most known near-Earth objects fall in this range. "
            "Continued observation typically reduces uncertainty further."
        )
    return insights

# ──────────────────────────────────────────────
# Core Calculation Endpoint
# ──────────────────────────────────────────────

@app.post("/calculate", response_model=ImpactMetrics, tags=["Calculations"])
async def calculate_impact(req: ImpactRequest):
    """
    Calculate all impact effects for given asteroid parameters.
    Optionally accepts diameter and miss distance for enhanced risk scoring.
    """
    mass_kg = req.mass_tons * 1000
    velocity_ms = req.velocity_kms * 1000

    ke_joules = kinetic_energy_joules(mass_kg, velocity_ms)
    energy_mt = ke_joules * 2.1e-16

    crater = crater_diameter_km(mass_kg, velocity_ms, req.target_material)
    air = air_blast_radius_km(mass_kg, velocity_ms)
    shock = shock_wave_radius_km(mass_kg, velocity_ms)
    thermal = thermal_radiation_radius_km(mass_kg, velocity_ms)

    prob = estimate_hazard_probability(energy_mt, req.diameter_km, req.miss_distance_km)
    torino = torino_scale(energy_mt, prob)
    palermo = palermo_scale(prob, energy_mt)

    if energy_mt < 0.1:
        severity = "Very Low"
    elif energy_mt < 1:
        severity = "Low"
    elif energy_mt < 10:
        severity = "Moderate"
    elif energy_mt < 100:
        severity = "High"
    else:
        severity = "Extreme"

    material_name = MATERIAL_PROPS.get(req.target_material, MATERIAL_PROPS["rock"])["name"]

    base_metrics = {
        "mass_tons": round(req.mass_tons, 3),
        "velocity_kms": round(req.velocity_kms, 3),
        "energy_megatons_tnt": round(energy_mt, 4),
        "crater_km": round(crater, 3),
        "air_km": round(air, 3),
        "shock_km": round(shock, 3),
        "thermal_km": round(thermal, 3),
        "severity": severity,
        "target_material": material_name,
        "torino_scale": torino["level"],
        "torino_label": torino["label"],
        "torino_color": torino["color"],
        "palermo_scale": palermo,
        "hazard_probability": prob,
        "insights": [],
    }
    base_metrics["insights"] = generate_insights(base_metrics)
    return base_metrics


# ──────────────────────────────────────────────
# NASA NeoWs Integration
# ──────────────────────────────────────────────

@app.get("/nasa/today", tags=["NASA Data"])
async def get_todays_asteroids():
    """
    Fetch today's near-Earth asteroids from NASA NeoWs API.
    Returns top 10 closest approaches sorted by miss distance.
    """
    today = date.today().isoformat()
    url = f"{NASA_BASE_URL}/feed"
    params = {"start_date": today, "end_date": today, "api_key": NASA_API_KEY}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"NASA API error: {str(e)}")

    data = response.json()
    neo_list = data.get("near_earth_objects", {}).get(today, [])

    results = []
    for neo in neo_list:
        approach = neo["close_approach_data"][0] if neo["close_approach_data"] else {}
        diameter_avg = (
            neo["estimated_diameter"]["kilometers"]["estimated_diameter_min"] +
            neo["estimated_diameter"]["kilometers"]["estimated_diameter_max"]
        ) / 2
        results.append({
            "id": neo["id"],
            "name": neo["name"],
            "diameter_km": round(diameter_avg, 4),
            "is_potentially_hazardous": neo["is_potentially_hazardous_asteroid"],
            "velocity_kms": round(float(approach.get("relative_velocity", {}).get("kilometers_per_second", 0)), 3),
            "miss_distance_km": round(float(approach.get("miss_distance", {}).get("kilometers", 0)), 0),
            "close_approach_date": approach.get("close_approach_date", today),
            "nasa_url": neo.get("nasa_jpl_url", ""),
        })

    results.sort(key=lambda x: x["miss_distance_km"])
    return {"date": today, "count": len(results), "asteroids": results[:10]}


@app.get("/nasa/asteroid/{asteroid_id}", tags=["NASA Data"])
async def get_asteroid_by_id(asteroid_id: str):
    """
    Fetch full details for a specific asteroid by NASA ID.
    Auto-populates mass estimate and velocity for the calculator.
    """
    url = f"{NASA_BASE_URL}/neo/{asteroid_id}"
    params = {"api_key": NASA_API_KEY}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError:
            raise HTTPException(status_code=404, detail=f"Asteroid {asteroid_id} not found.")
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"NASA API error: {str(e)}")

    neo = response.json()
    diameter_avg = (
        neo["estimated_diameter"]["kilometers"]["estimated_diameter_min"] +
        neo["estimated_diameter"]["kilometers"]["estimated_diameter_max"]
    ) / 2

    # Estimate mass from diameter (assumes spherical, density ~2000 kg/m³ for stony asteroid)
    radius_m = (diameter_avg * 1000) / 2
    volume_m3 = (4 / 3) * math.pi * radius_m ** 3
    density_kg_m3 = 2000  # stony asteroid average
    mass_kg = volume_m3 * density_kg_m3
    mass_tons = mass_kg / 1000

    # Latest close approach
    approaches = neo.get("close_approach_data", [])
    latest = approaches[-1] if approaches else {}
    velocity_kms = float(latest.get("relative_velocity", {}).get("kilometers_per_second", 20))
    miss_distance_km = float(latest.get("miss_distance", {}).get("kilometers", 0))

    return {
        "id": neo["id"],
        "name": neo["name"],
        "diameter_km": round(diameter_avg, 4),
        "estimated_mass_tons": round(mass_tons, 2),
        "velocity_kms": round(velocity_kms, 3),
        "miss_distance_km": round(miss_distance_km, 0),
        "is_potentially_hazardous": neo["is_potentially_hazardous_asteroid"],
        "orbital_period_days": neo.get("orbital_data", {}).get("orbital_period"),
        "nasa_url": neo.get("nasa_jpl_url", ""),
    }


@app.get("/nasa/search", tags=["NASA Data"])
async def search_asteroid(name: str = Query(..., description="Partial or full asteroid name")):
    """
    Search for asteroids by name using the NASA browse endpoint.
    """
    url = f"{NASA_BASE_URL}/neo/browse"
    params = {"api_key": NASA_API_KEY, "page": 0, "size": 20}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=503, detail=f"NASA API error: {str(e)}")

    data = response.json()
    all_neos = data.get("near_earth_objects", [])
    matches = [n for n in all_neos if name.lower() in n["name"].lower()]

    return {
        "query": name,
        "results": [
            {
                "id": n["id"],
                "name": n["name"],
                "is_potentially_hazardous": n["is_potentially_hazardous_asteroid"],
                "diameter_km_min": round(n["estimated_diameter"]["kilometers"]["estimated_diameter_min"], 4),
                "diameter_km_max": round(n["estimated_diameter"]["kilometers"]["estimated_diameter_max"], 4),
            }
            for n in matches[:10]
        ]
    }


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────

@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok", "version": "2.0.0", "nasa_key_set": NASA_API_KEY != "DEMO_KEY"}
