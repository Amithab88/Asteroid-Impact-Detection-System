// Asteroid Impact Calculator - Pure JavaScript Calculations

function kineticEnergy(m, v) {
    return 0.5 * m * v * v;
}

function craterDiameterKm(m, v, targetMaterial = "rock") {
    const materialProps = {
        "water": { density: 1000, gravity: 9.81, k: 2.1, name: "Water/Ocean" },
        "rock": { density: 2500, gravity: 9.81, k: 1.8, name: "Rock/Solid Ground" },
        "ice": { density: 900, gravity: 9.81, k: 2.5, name: "Ice/Glacier" },
        "sand": { density: 1600, gravity: 9.81, k: 2.8, name: "Desert Sand" },
        "forest": { density: 1200, gravity: 9.81, k: 2.2, name: "Forest/Vegetation" }
    };
    
    const props = materialProps[targetMaterial] || materialProps["rock"];
    const ke = kineticEnergy(m, v);
    const diameterM = props.k * Math.pow(ke / (props.gravity * props.density), 0.25);
    return diameterM / 1000;
}

function airBlastRadiusKm(m, v) {
    const ke = kineticEnergy(m, v);
    // Adjusted to scale better with energy - uses E^(1/3) scaling
    return 0.0018 * Math.pow(ke, 1/3);
}

function shockWaveRadiusKm(m, v, k = 0.0015) {
    // Reduced coefficient to balance with other effects
    const ke = kineticEnergy(m, v);
    return k * Math.pow(ke, 1/3);
}

function thermalRadiationRadiusKm(m, v, thermalFraction = 0.2, fluenceThreshold = 150000) {
    // Reduced threshold to allow thermal effects to scale better
    const ke = kineticEnergy(m, v);
    const thermalEnergy = thermalFraction * ke;
    const radiusM = Math.sqrt(thermalEnergy / (4 * Math.PI * fluenceThreshold));
    return radiusM / 1000;
}

function generateInsights(metrics) {
    const insights = [];
    const energy = metrics.energy_megatons_tnt || 0;
    const massTons = metrics.mass_tons || 0;
    const velocityKms = metrics.velocity_kms || 0;
    const craterKm = metrics.crater_km || 0;
    const airKm = metrics.air_km || 0;
    const shockKm = metrics.shock_km || 0;
    const thermalKm = metrics.thermal_km || 0;

    // Core drivers
    insights.push(
        `Kinetic energy rises strongly with speed (E ∝ v²). At ${velocityKms} km/s, even modest mass (${massTons} t) can yield ${energy} Mt TNT.`
    );

    // Relative sizes
    const effects = [
        [airKm, "Air blast radius"],
        [shockKm, "Shock wave radius"],
        [thermalKm, "Thermal radiation radius"]
    ];
    const largest = effects.reduce((max, curr) => curr[0] > max[0] ? curr : max);
    insights.push(`${largest[1]} is the largest zone here. Atmospheric pressure waves travel farther than intense heat, so blast/shock often extend beyond thermal effects.`);

    if (shockKm >= thermalKm) {
        insights.push("Shock wave ≥ Thermal: Pressure waves attenuate more slowly with distance, while thermal radiation drops roughly with 1/r² and is absorbed by the atmosphere.");
    } else {
        insights.push("Thermal ≥ Shock: A large fraction of energy coupled into heat can drive a wider thermal zone in this scenario.");
    }

    if (airKm >= craterKm) {
        insights.push("Air blast ≫ Crater: Cratering is local to the impact point, but blast effects propagate through the atmosphere over much larger distances.");
    }

    insights.push("Scaling note: Crater size grows sub‑linearly with energy (~E^1/4), while blast/thermal radii grow a bit faster (~E^1/3), so radii can outpace crater size.");

    // Target material effects
    const targetMaterial = metrics.target_material || "Rock/Solid Ground";
    insights.push(`Target: ${targetMaterial}. Softer materials (water, ice) create larger craters, while dense rock produces smaller, deeper craters.`);

    // Severity
    insights.push(`Overall severity rated as '${metrics.severity}'. Reducing speed or mass reduces energy fastest (speed has the biggest effect).`);

    return insights;
}

function calculateAllMetrics(massTons, velocityKms, targetMaterial) {
    const mass = massTons * 1000; // tons to kg
    const velocity = velocityKms * 1000; // km/s to m/s

    const keJoules = kineticEnergy(mass, velocity);
    const energyMegatonsTnt = keJoules * 2.1e-16;
    const craterKm = craterDiameterKm(mass, velocity, targetMaterial);
    const airKm = airBlastRadiusKm(mass, velocity);
    const shockKm = shockWaveRadiusKm(mass, velocity);
    const thermalKm = thermalRadiationRadiusKm(mass, velocity);

    // Simple severity heuristic
    let severity;
    if (energyMegatonsTnt < 0.1) {
        severity = "Very Low";
    } else if (energyMegatonsTnt < 1) {
        severity = "Low";
    } else if (energyMegatonsTnt < 10) {
        severity = "Moderate";
    } else if (energyMegatonsTnt < 100) {
        severity = "High";
    } else {
        severity = "Extreme";
    }

    const materialProps = {
        "water": "Water/Ocean",
        "rock": "Rock/Solid Ground",
        "ice": "Ice/Glacier",
        "sand": "Desert Sand",
        "forest": "Forest/Vegetation"
    };

    return {
        mass_tons: Math.round(massTons * 1000) / 1000,
        velocity_kms: Math.round(velocityKms * 1000) / 1000,
        energy_megatons_tnt: Math.round(energyMegatonsTnt * 1000) / 1000,
        crater_km: Math.round(craterKm * 1000) / 1000,
        air_km: Math.round(airKm * 1000) / 1000,
        shock_km: Math.round(shockKm * 1000) / 1000,
        thermal_km: Math.round(thermalKm * 1000) / 1000,
        severity: severity,
        target_material: materialProps[targetMaterial] || "Rock/Solid Ground"
    };
}

