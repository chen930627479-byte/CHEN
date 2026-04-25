"""Unit tests for CatenaryAnalysis module."""

import math
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.catenary import TowWire, CatenaryAnalysis


@pytest.fixture
def standard_wire():
    return TowWire(
        diameter=0.064,
        mass_per_meter=25.0,
        breaking_load=2500.0,
        length=200.0,
    )


@pytest.fixture
def catenary(standard_wire):
    return CatenaryAnalysis(
        tow_wire=standard_wire,
        horizontal_force=500_000.0,   # 500 kN
        fairlead_depth=3.0,
        attachment_depth=0.5,
    )


def test_max_tension_exceeds_horizontal(catenary):
    assert catenary.max_tension() > catenary.horizontal_force


def test_departure_angle_positive(catenary):
    angle = catenary.departure_angle()
    assert 0 < angle < 90


def test_horizontal_span_less_than_wire_length(catenary):
    span = catenary.horizontal_span()
    assert span <= catenary.tow_wire.length


def test_catenary_geometry_length(catenary):
    points = catenary.catenary_geometry(n_points=10)
    assert len(points) == 11  # n_points + 1


def test_wire_utilization_range(standard_wire):
    util = standard_wire.utilization(500_000)  # 500 kN
    assert 0 < util <= 1.0


def test_submerged_weight_positive(standard_wire):
    assert standard_wire.submerged_weight_per_meter > 0


def test_check_wire_returns_bool_and_str(catenary):
    ok, msg = catenary.check_wire()
    assert isinstance(ok, bool)
    assert isinstance(msg, str)


def test_higher_force_higher_tension():
    wire = TowWire(diameter=0.064, mass_per_meter=25.0, breaking_load=2500.0, length=200.0)
    cat_low = CatenaryAnalysis(tow_wire=wire, horizontal_force=200_000, fairlead_depth=3.0, attachment_depth=0.5)
    cat_high = CatenaryAnalysis(tow_wire=wire, horizontal_force=800_000, fairlead_depth=3.0, attachment_depth=0.5)
    assert cat_high.max_tension() > cat_low.max_tension()


def test_results_dict_keys(catenary):
    r = catenary.results()
    assert "最大张力 Max Tension (kN)" in r
    assert "拖缆检查 Wire Check" in r
