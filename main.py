"""
海上管道拖运分析主程序
Offshore Pipeline Towing Analysis - Main Script

Usage / 使用方法:
    python main.py

Covers three towing methods / 涵盖三种拖运方式:
    1. Surface Tow      水面拖运
    2. Off-Bottom Tow   离底拖运
    3. Bottom Tow       海底拖运
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.pipeline import Pipeline
from src.environment import MarineEnvironment
from src.towing import TowingAnalysis, TowingMethod
from src.catenary import TowWire, CatenaryAnalysis


def print_section(title: str):
    width = 60
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_dict(d: dict):
    for k, v in d.items():
        print(f"  {k:<45} {v}")


def run_surface_tow_example():
    print_section("案例1：水面拖运 / Case 1: Surface Tow")

    pipeline = Pipeline(
        outer_diameter=0.508,           # 20" 管道
        wall_thickness=0.0127,          # 12.7mm 壁厚
        coating_thickness=0.004,        # 4mm 防腐涂层
        coating_density=900.0,
        concrete_coating_thickness=0.0, # 无混凝土配重层（水面拖运需正浮力）
        content_density=1.2,            # 空气
        length=500.0,                   # 500m 长
    )

    env = MarineEnvironment(
        water_depth=50.0,
        current_speed=0.5,
        current_direction=15.0,  # 15°斜向海流
        wave_height=1.5,
        wave_period=7.0,
        wind_speed=8.0,
    )

    tow = TowingAnalysis(
        pipeline=pipeline,
        environment=env,
        method=TowingMethod.SURFACE,
        towing_speed=1.0,
        safety_factor=1.5,
    )

    print("\n-- 管道参数 Pipeline Properties --")
    print_dict(pipeline.summary())
    print("\n-- 环境条件 Environmental Conditions --")
    print_dict(env.summary())
    print("\n-- 拖运分析 Towing Analysis --")
    print_dict(tow.results())

    # 拖缆分析
    wire = TowWire(
        diameter=0.064,         # 64mm 拖缆
        mass_per_meter=25.0,    # kg/m
        breaking_load=2500.0,   # kN
        length=200.0,           # 200m 拖缆
    )
    cat = CatenaryAnalysis(
        tow_wire=wire,
        horizontal_force=tow.towing_resistance(),
        fairlead_depth=3.0,
        attachment_depth=0.5,
    )
    print("\n-- 拖缆悬链线分析 Tow Wire Catenary Analysis --")
    print_dict(cat.results())


def run_off_bottom_tow_example():
    print_section("案例2：离底拖运 / Case 2: Off-Bottom Tow")

    pipeline = Pipeline(
        outer_diameter=0.324,           # 12.75" 管道
        wall_thickness=0.0127,
        coating_thickness=0.004,
        coating_density=900.0,
        concrete_coating_thickness=0.040,  # 40mm 混凝土配重层
        concrete_density=3000.0,
        content_density=1.2,
        length=1000.0,
    )

    env = MarineEnvironment(
        water_depth=80.0,
        current_speed=0.8,
        current_direction=0.0,
        wave_height=2.0,
        wave_period=9.0,
        wind_speed=12.0,
    )

    tow = TowingAnalysis(
        pipeline=pipeline,
        environment=env,
        method=TowingMethod.OFF_BOTTOM,
        towing_speed=0.8,
        off_bottom_clearance=5.0,
        safety_factor=1.5,
    )

    print("\n-- 管道参数 Pipeline Properties --")
    print_dict(pipeline.summary())
    print("\n-- 环境条件 Environmental Conditions --")
    print_dict(env.summary())
    print("\n-- 拖运分析 Towing Analysis --")
    print_dict(tow.results())

    wire = TowWire(
        diameter=0.076,
        mass_per_meter=35.0,
        breaking_load=3500.0,
        length=500.0,
    )
    cat = CatenaryAnalysis(
        tow_wire=wire,
        horizontal_force=tow.towing_resistance(),
        fairlead_depth=4.0,
        attachment_depth=75.0,
    )
    print("\n-- 拖缆悬链线分析 Tow Wire Catenary Analysis --")
    print_dict(cat.results())


def run_bottom_tow_example():
    print_section("案例3：海底拖运 / Case 3: Bottom Tow")

    pipeline = Pipeline(
        outer_diameter=0.610,           # 24" 大口径管道
        wall_thickness=0.0159,
        coating_thickness=0.005,
        coating_density=900.0,
        concrete_coating_thickness=0.060,  # 60mm 配重层
        concrete_density=3100.0,
        content_density=1.2,
        length=800.0,
    )

    env = MarineEnvironment(
        water_depth=30.0,
        current_speed=0.4,
        current_direction=0.0,
        wave_height=1.0,
        wave_period=6.0,
        wind_speed=6.0,
    )

    tow = TowingAnalysis(
        pipeline=pipeline,
        environment=env,
        method=TowingMethod.BOTTOM,
        towing_speed=0.5,
        seabed_friction_coeff=0.3,
        safety_factor=1.5,
    )

    print("\n-- 管道参数 Pipeline Properties --")
    print_dict(pipeline.summary())
    print("\n-- 环境条件 Environmental Conditions --")
    print_dict(env.summary())
    print("\n-- 拖运分析 Towing Analysis --")
    print_dict(tow.results())

    wire = TowWire(
        diameter=0.089,
        mass_per_meter=48.0,
        breaking_load=5000.0,
        length=300.0,
    )
    cat = CatenaryAnalysis(
        tow_wire=wire,
        horizontal_force=tow.towing_resistance(),
        fairlead_depth=4.5,
        attachment_depth=29.5,
    )
    print("\n-- 拖缆悬链线分析 Tow Wire Catenary Analysis --")
    print_dict(cat.results())


def run_sensitivity_analysis():
    print_section("灵敏度分析：拖运速度 vs 所需拖力 / Sensitivity: Speed vs Bollard Pull")

    pipeline = Pipeline(
        outer_diameter=0.508,
        wall_thickness=0.0127,
        coating_thickness=0.004,
        coating_density=900.0,
        concrete_coating_thickness=0.0,
        length=500.0,
    )
    env = MarineEnvironment(
        water_depth=50.0,
        current_speed=0.5,
        current_direction=0.0,
        wave_height=1.5,
        wave_period=7.0,
    )

    print(f"\n  {'拖速 (kn)':<15} {'拖速 (m/s)':<15} {'拖力 (kN)':<15}")
    print("  " + "-" * 45)
    for v_knots in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        v_ms = v_knots * 0.5144
        tow = TowingAnalysis(
            pipeline=pipeline,
            environment=env,
            method=TowingMethod.SURFACE,
            towing_speed=v_ms,
            safety_factor=1.5,
        )
        bp = tow.required_bollard_pull()
        print(f"  {v_knots:<15.1f} {v_ms:<15.3f} {bp:<15.1f}")


if __name__ == "__main__":
    print("\n" + "*" * 60)
    print("  海上管道拖运分析系统")
    print("  Offshore Pipeline Towing Analysis System")
    print("  Version 1.0.0")
    print("*" * 60)

    run_surface_tow_example()
    run_off_bottom_tow_example()
    run_bottom_tow_example()
    run_sensitivity_analysis()

    print("\n" + "=" * 60)
    print("  分析完成 / Analysis Complete")
    print("=" * 60 + "\n")
