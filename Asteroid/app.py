from flask import Flask, render_template, request, redirect, url_for

import math

app = Flask(__name__)

def kinetic_energy(m, v):
    return 0.5 * m * v**2

def crater_diameter_km(m, v, target_material="rock"):
    material_props = {
        "water": {"density": 1000, "gravity": 9.81, "k": 2.1, "name": "Water/Ocean"},
        "rock": {"density": 2500, "gravity": 9.81, "k": 1.8, "name": "Rock/Solid Ground"},
        "ice": {"density": 900, "gravity": 9.81, "k": 2.5, "name": "Ice/Glacier"},
        "sand": {"density": 1600, "gravity": 9.81, "k": 2.8, "name": "Desert Sand"},
        "forest": {"density": 1200, "gravity": 9.81, "k": 2.2, "name": "Forest/Vegetation"}
    }
    
    props = material_props.get(target_material, material_props["rock"])
    ke = kinetic_energy(m, v)
    diameter_m = props["k"] * (ke / (props["gravity"] * props["density"]))**0.25
    return diameter_m / 1000

def air_blast_radius_km(m, v):
    ke = kinetic_energy(m, v)
    return 0.28 * (ke / 1e12)**(1/3)

def shock_wave_radius_km(m, v, k=0.005):
    ke = kinetic_energy(m, v)
    return k * ke**(1/3)

def thermal_radiation_radius_km(m, v, thermal_fraction=0.2, fluence_threshold=350_000):
    ke = kinetic_energy(m, v)
    thermal_energy = thermal_fraction * ke
    radius_m = math.sqrt(thermal_energy / (4 * math.pi * fluence_threshold))
    return radius_m / 1000

def generate_insights(metrics: dict) -> list[str]:
    insights: list[str] = []
    energy = metrics.get("energy_megatons_tnt", 0)
    mass_tons = metrics.get("mass_tons", 0)
    velocity_kms = metrics.get("velocity_kms", 0)
    crater_km = metrics.get("crater_km", 0)
    air_km = metrics.get("air_km", 0)
    shock_km = metrics.get("shock_km", 0)
    thermal_km = metrics.get("thermal_km", 0)

    # Core drivers
    insights.append(
        f"Kinetic energy rises strongly with speed (E ∝ v²). At {velocity_kms} km/s, even modest mass ({mass_tons} t) can yield {energy} Mt TNT."
    )

    # Relative sizes
    largest = max([(air_km, "Air blast radius"), (shock_km, "Shock wave radius"), (thermal_km, "Thermal radiation radius")], key=lambda x: x[0])
    insights.append(f"{largest[1]} is the largest zone here. Atmospheric pressure waves travel farther than intense heat, so blast/shock often extend beyond thermal effects.")

    if shock_km >= thermal_km:
        insights.append("Shock wave ≥ Thermal: Pressure waves attenuate more slowly with distance, while thermal radiation drops roughly with 1/r² and is absorbed by the atmosphere.")
    else:
        insights.append("Thermal ≥ Shock: A large fraction of energy coupled into heat can drive a wider thermal zone in this scenario.")

    if air_km >= crater_km:
        insights.append("Air blast ≫ Crater: Cratering is local to the impact point, but blast effects propagate through the atmosphere over much larger distances.")

    insights.append("Scaling note: Crater size grows sub‑linearly with energy (~E^1/4), while blast/thermal radii grow a bit faster (~E^1/3), so radii can outpace crater size.")

    # Target material effects
    target_material = metrics.get("target_material", "Rock/Solid Ground")
    insights.append(f"Target: {target_material}. Softer materials (water, ice) create larger craters, while dense rock produces smaller, deeper craters.")

    # Severity
    insights.append(f"Overall severity rated as '{metrics.get('severity')}'. Reducing speed or mass reduces energy fastest (speed has the biggest effect).")

    return insights

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/result", methods=["GET", "POST"])
def result():
    # If accessed directly, send user back to the form
    if request.method == "GET":
        return redirect(url_for("index"))

    print("Result route was accessed")
    option = int(request.form["option"]) if request.form.get("option") else 1
    mass_tons_str = request.form.get("mass", "0").strip()
    velocity_kms_str = request.form.get("velocity", "0").strip()
    target_material = request.form.get("target_material", "rock")

    # Basic validation
    try:
        mass_tons = float(mass_tons_str)
        velocity_kms = float(velocity_kms_str)
    except ValueError:
        output = "Error: Please enter valid numeric values for Mass and Velocity."
        return render_template("result.html", result=output, metrics=None)

    mass = mass_tons * 1000  # tons to kg
    velocity = velocity_kms * 1000  # km/s to m/s

    # Check for negative inputs
    if mass < 0 or velocity < 0:
        output = "Error: Mass and Velocity must be non-negative values."
        return render_template("result.html", result=output, metrics=None)

    # Compute all metrics for visualization/education
    ke_joules = kinetic_energy(mass, velocity)
    energy_megatons_tnt = ke_joules * 2.1e-16
    crater_km = crater_diameter_km(mass, velocity, target_material)
    air_km = air_blast_radius_km(mass, velocity)
    shock_km = shock_wave_radius_km(mass, velocity)
    thermal_km = thermal_radiation_radius_km(mass, velocity)

    # Simple severity heuristic
    if energy_megatons_tnt < 0.1:
        severity = "Very Low"
    elif energy_megatons_tnt < 1:
        severity = "Low"
    elif energy_megatons_tnt < 10:
        severity = "Moderate"
    elif energy_megatons_tnt < 100:
        severity = "High"
    else:
        severity = "Extreme"

    # Get material name for display
    material_props = {
        "water": "Water/Ocean",
        "rock": "Rock/Solid Ground", 
        "ice": "Ice/Glacier",
        "sand": "Desert Sand",
        "forest": "Forest/Vegetation"
    }
    
    metrics = {
        "mass_tons": round(mass_tons, 3),
        "velocity_kms": round(velocity_kms, 3),
        "energy_megatons_tnt": round(energy_megatons_tnt, 3),
        "crater_km": round(crater_km, 3),
        "air_km": round(air_km, 3),
        "shock_km": round(shock_km, 3),
        "thermal_km": round(thermal_km, 3),
        "severity": severity,
        "target_material": material_props.get(target_material, "Rock/Solid Ground"),
    }

    if option == 1:
        output = f"Kinetic Energy: {metrics['energy_megatons_tnt']} Megatons of TNT"
    elif option == 2:
        output = f"Crater Diameter: {metrics['crater_km']} km"
    elif option == 3:
        output = f"Air Blast Radius: {metrics['air_km']} km"
    elif option == 4:
        output = f"Shock Wave Radius: {metrics['shock_km']} km"
    elif option == 5:
        output = f"Thermal Radiation Radius: {metrics['thermal_km']} km"
    else:
        output = "Invalid Option Selected"

    insights = generate_insights(metrics)

    return render_template("result.html", result=output, metrics=metrics, insights=insights)

if __name__ == "__main__":
    app.run(debug=True)