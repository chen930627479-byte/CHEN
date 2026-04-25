"""Unit tests for TowingAnalysis module."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pipeline import Pipeline
from src.environment import MarineEnvironment
from src.towing import TowingAnalysis, TowingMethod


@pytest.fixture
def light_pipeline():
    return Pipeline(
        outer_diameter=0.508,
        wall_thickness=0.0080,
        coating_thickness=0.005,
        coating_density=700.0,
        content_density=1.2,
        length=500.0,
    )


@pytest.fixture
def heavy_pipeline():
    return Pipeline(
        outer_diameter=0.508,
        wall_thickness=0.0127,
        concrete_coating_thickness=0.050,
        concrete_density=3000.0,
        length=500.0,
    )


@pytest.fixture
def calm_env():
    return MarineEnvironment(
        water_depth=50.0,
        current_speed=0.3,
        current_direction=0.0,
        wave_height=1.0,
        wave_period=7.0,
    )


def test_surface_tow_resistance_positive(light_pipeline, calm_env):
    tow = TowingAnalysis(
        pipeline=light_pipeline,
        environment=calm_env,
        method=TowingMethod.SURFACE,
        towing_speed=1.0,
    )
    assert tow.towing_resistance() > 0


def test_bollard_pull_includes_safety_factor(light_pipeline, calm_env):
    tow_sf1 = TowingAnalysis(
        pipeline=light_pipeline,
        environment=calm_env,
        method=TowingMethod.SURFACE,
        towing_speed=1.0,
        safety_factor=1.0,
    )
    tow_sf2 = TowingAnalysis(
        pipeline=light_pipeline,
        environment=calm_env,
        method=TowingMethod.SURFACE,
        towing_speed=1.0,
        safety_factor=2.0,
    )
    assert tow_sf2.required_bollard_pull() > tow_sf1.required_bollard_pull()


def test_higher_speed_higher_resistance(light_pipeline, calm_env):
    tow_slow = TowingAnalysis(
        pipeline=light_pipeline,
        environment=calm_env,
        method=TowingMethod.SURFACE,
        towing_speed=0.5,
    )
    tow_fast = TowingAnalysis(
        pipeline=light_pipeline,
        environment=calm_env,
        method=TowingMethod.SURFACE,
        towing_speed=2.0,
    )
    assert tow_fast.towing_resistance() > tow_slow.towing_resistance()


def test_bottom_tow_includes_friction(heavy_pipeline, calm_env):
    tow_bottom = TowingAnalysis(
        pipeline=heavy_pipeline,
        environment=calm_env,
        method=TowingMethod.BOTTOM,
        towing_speed=0.5,
        seabed_friction_coeff=0.5,
    )
    tow_no_friction = TowingAnalysis(
        pipeline=heavy_pipeline,
        environment=calm_env,
        method=TowingMethod.BOTTOM,
        towing_speed=0.5,
        seabed_friction_coeff=0.0,
    )
    assert tow_bottom.towing_resistance() > tow_no_friction.towing_resistance()


def test_stability_check_surface_heavy_pipeline(heavy_pipeline, calm_env):
    tow = TowingAnalysis(
        pipeline=heavy_pipeline,
        environment=calm_env,
        method=TowingMethod.SURFACE,
    )
    stable, msg = tow.check_stability()
    assert not stable


def test_stability_check_bottom_heavy(heavy_pipeline, calm_env):
    tow = TowingAnalysis(
        pipeline=heavy_pipeline,
        environment=calm_env,
        method=TowingMethod.BOTTOM,
    )
    stable, msg = tow.check_stability()
    assert stable


def test_towing_power_positive(light_pipeline, calm_env):
    tow = TowingAnalysis(
        pipeline=light_pipeline,
        environment=calm_env,
        method=TowingMethod.SURFACE,
        towing_speed=1.0,
    )
    assert tow.towing_power() > 0


def test_results_dict_keys(light_pipeline, calm_env):
    tow = TowingAnalysis(
        pipeline=light_pipeline,
        environment=calm_env,
        method=TowingMethod.SURFACE,
    )
    results = tow.results()
    assert "所需拖轮拖力 Required Bollard Pull (kN)" in results
    assert "纵向拖运阻力 Axial Resistance (kN)" in results
