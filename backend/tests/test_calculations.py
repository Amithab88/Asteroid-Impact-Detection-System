"""
Unit tests for Asteroid Impact Detection System backend.
Run with: pytest tests/ -v
"""
import pytest
from main import (
    kinetic_energy_joules,
    crater_diameter_km,
    air_blast_radius_km,
    shock_wave_radius_km,
    thermal_radiation_radius_km,
    torino_scale,
    palermo_scale,
    estimate_hazard_probability,
    generate_insights,
)


# ─── Physics Tests ───────────────────────────────────────

class TestKineticEnergy:
    def test_zero_velocity(self):
        assert kinetic_energy_joules(1000, 0) == 0

    def test_scales_with_velocity_squared(self):
        ke1 = kinetic_energy_joules(1000, 10)
        ke2 = kinetic_energy_joules(1000, 20)
        assert abs(ke2 / ke1 - 4.0) < 0.001  # doubling v → 4x energy

    def test_positive_values(self):
        assert kinetic_energy_joules(5000, 20_000) > 0


class TestCraterDiameter:
    def test_returns_positive(self):
        assert crater_diameter_km(1_000_000, 20_000, "rock") > 0

    def test_softer_material_larger_crater(self):
        rock_crater = crater_diameter_km(1_000_000, 20_000, "rock")
        sand_crater = crater_diameter_km(1_000_000, 20_000, "sand")
        assert sand_crater > rock_crater

    def test_faster_impact_larger_crater(self):
        slow = crater_diameter_km(1_000_000, 10_000, "rock")
        fast = crater_diameter_km(1_000_000, 30_000, "rock")
        assert fast > slow


class TestBlastRadii:
    def test_air_blast_positive(self):
        assert air_blast_radius_km(1_000_000, 20_000) > 0

    def test_shock_positive(self):
        assert shock_wave_radius_km(1_000_000, 20_000) > 0

    def test_thermal_positive(self):
        assert thermal_radiation_radius_km(1_000_000, 20_000) > 0

    def test_air_blast_scales_with_energy(self):
        r1 = air_blast_radius_km(1_000_000, 10_000)
        r2 = air_blast_radius_km(8_000_000, 10_000)  # 8x mass → 8x energy → 2x radius (E^1/3)
        assert abs(r2 / r1 - 2.0) < 0.1


# ─── Risk Scoring Tests ──────────────────────────────────

class TestTorinoScale:
    def test_zero_probability_returns_level_0(self):
        result = torino_scale(100, 0.0)
        assert result["level"] == 0

    def test_low_energy_returns_level_1(self):
        result = torino_scale(0.5, 0.001)
        assert result["level"] == 1

    def test_high_energy_high_prob_returns_high_level(self):
        result = torino_scale(1_000_000, 0.9)
        assert result["level"] >= 8

    def test_color_returned(self):
        result = torino_scale(10, 0.01)
        assert "color" in result
        assert result["color"] in ["white", "green", "yellow", "orange", "red"]


class TestPalmernoScale:
    def test_zero_probability_returns_none(self):
        assert palermo_scale(0, 10) is None

    def test_returns_float(self):
        result = palermo_scale(0.001, 100, 10)
        assert isinstance(result, float)

    def test_higher_prob_higher_palermo(self):
        ps_low = palermo_scale(0.001, 100, 10)
        ps_high = palermo_scale(0.1, 100, 10)
        assert ps_high > ps_low


class TestHazardProbability:
    def test_zero_energy_low_probability(self):
        result = estimate_hazard_probability(0.0001, None, None)
        assert result == 0.0

    def test_high_energy_raises_probability(self):
        low = estimate_hazard_probability(1, None, None)
        high = estimate_hazard_probability(10000, None, None)
        assert high > low

    def test_close_miss_raises_probability(self):
        far = estimate_hazard_probability(10, 0.5, 1_000_000)
        close = estimate_hazard_probability(10, 0.5, 10_000)
        assert close > far

    def test_capped_at_1(self):
        result = estimate_hazard_probability(1e12, 10, 100)
        assert result <= 1.0


# ─── Insights Tests ──────────────────────────────────────

class TestGenerateInsights:
    def test_returns_list(self):
        metrics = {
            "energy_megatons_tnt": 100,
            "velocity_kms": 20,
            "mass_tons": 5000,
            "crater_km": 2.0,
            "air_km": 5.0,
            "shock_km": 4.0,
            "thermal_km": 3.0,
            "target_material": "Rock/Solid Ground",
            "torino_scale": 3,
        }
        result = generate_insights(metrics)
        assert isinstance(result, list)
        assert len(result) >= 3

    def test_high_torino_triggers_warning(self):
        metrics = {
            "energy_megatons_tnt": 500_000,
            "velocity_kms": 30,
            "mass_tons": 1e9,
            "crater_km": 100,
            "air_km": 200,
            "shock_km": 180,
            "thermal_km": 150,
            "target_material": "Rock/Solid Ground",
            "torino_scale": 7,
        }
        result = generate_insights(metrics)
        warning_found = any("Torino Scale ≥5" in insight for insight in result)
        assert warning_found
