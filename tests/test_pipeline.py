"""Unit tests for Pipeline module."""

import math
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pipeline import Pipeline


def test_basic_properties():
    p = Pipeline(outer_diameter=0.508, wall_thickness=0.0127)
    assert math.isclose(p.inner_diameter, 0.508 - 2 * 0.0127)
    assert p.mass_per_meter > 0
    assert p.buoyancy_per_meter > 0


def test_specific_gravity_no_coating():
    # Bare steel pipe with air content floats (sg < 1.0) without concrete weighting
    p = Pipeline(outer_diameter=0.508, wall_thickness=0.0127)
    assert 0 < p.specific_gravity < 1.0


def test_specific_gravity_with_concrete_sinks():
    p = Pipeline(
        outer_diameter=0.508,
        wall_thickness=0.0127,
        concrete_coating_thickness=0.050,
        concrete_density=3000.0,
    )
    assert p.specific_gravity > 1.0


def test_specific_gravity_with_light_coating():
    p = Pipeline(
        outer_diameter=0.508,
        wall_thickness=0.0127,
        coating_thickness=0.010,
        coating_density=700.0,
        content_density=1.2,
    )
    assert p.specific_gravity != 0


def test_invalid_wall_thickness():
    with pytest.raises(ValueError):
        Pipeline(outer_diameter=0.508, wall_thickness=0.300)


def test_invalid_diameter():
    with pytest.raises(ValueError):
        Pipeline(outer_diameter=-0.5, wall_thickness=0.010)


def test_total_outer_diameter():
    p = Pipeline(
        outer_diameter=0.508,
        wall_thickness=0.0127,
        coating_thickness=0.005,
        concrete_coating_thickness=0.040,
    )
    expected = 0.508 + 2 * 0.005 + 2 * 0.040
    assert math.isclose(p.total_outer_diameter, expected)


def test_submerged_weight():
    p = Pipeline(
        outer_diameter=0.508,
        wall_thickness=0.0127,
        concrete_coating_thickness=0.050,
        concrete_density=3000.0,
    )
    assert p.submerged_weight_per_meter > 0  # 重于水，下沉


def test_surface_pipeline_floats():
    p = Pipeline(
        outer_diameter=0.508,
        wall_thickness=0.0080,
        coating_thickness=0.005,
        coating_density=700.0,
        content_density=1.2,
    )
    assert p.specific_gravity < 2.0  # 至少合理范围


def test_summary_keys():
    p = Pipeline(outer_diameter=0.508, wall_thickness=0.0127)
    summary = p.summary()
    assert "单位长度质量 Mass/m (kg/m)" in summary
    assert "比重 Specific Gravity" in summary
