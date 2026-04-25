"""
Towing force calculation for offshore pipeline towing operations.
海上管道拖运力计算模块

Supports three towing methods:
支持三种拖运方式：
  1. Surface Tow (水面拖运)
  2. Off-Bottom Tow (离底拖运)
  3. Bottom Tow (海底拖运)
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Tuple

from .pipeline import Pipeline
from .environment import MarineEnvironment


class TowingMethod(Enum):
    SURFACE = "surface"        # 水面拖运
    OFF_BOTTOM = "off_bottom"  # 离底拖运
    BOTTOM = "bottom"          # 海底拖运


@dataclass
class TowingAnalysis:
    """
    Calculates towing forces for offshore pipeline towing.
    计算海上管道拖运力。
    """

    pipeline: Pipeline
    environment: MarineEnvironment
    method: TowingMethod = TowingMethod.SURFACE
    towing_speed: float = 1.0          # m/s, 拖运速度
    off_bottom_clearance: float = 3.0  # m, 离底高度（离底拖运时）
    cd_axial: float = 0.01             # 轴向阻力系数
    cd_lateral: float = 1.2            # 横向阻力系数（垂直于管道轴线）
    cm_inertia: float = 2.0            # 附加质量系数（Morison方程）
    seabed_friction_coeff: float = 0.3 # 海底摩擦系数（底部拖运时）
    safety_factor: float = 1.5         # 安全系数

    @property
    def relative_velocity(self) -> float:
        """m/s, 相对流速（拖运速度 + 海流影响）"""
        vt = self.towing_speed
        vc_x = self.environment.current_velocity_x
        return vt + vc_x

    @property
    def lateral_current_velocity(self) -> float:
        """m/s, 横向海流速度"""
        return abs(self.environment.current_velocity_y)

    def _axial_drag_force(self) -> float:
        """N, 轴向拖曳力（沿管道轴线方向）"""
        rho = self.environment.seawater_density
        d = self.pipeline.total_outer_diameter
        L = self.pipeline.length
        v = self.relative_velocity
        # 轴向阻力面积为管道端面积（较小）
        area_axial = math.pi / 4 * d**2
        return 0.5 * rho * self.cd_axial * area_axial * abs(v) * v * L / d

    def _lateral_drag_force(self) -> float:
        """N, 横向拖曳力（垂直于管道轴线方向）"""
        rho = self.environment.seawater_density
        d = self.pipeline.total_outer_diameter
        L = self.pipeline.length
        v = self.lateral_current_velocity
        cd = self.environment.drag_coefficient_cylinder(d, v)
        # 横向阻力：作用在管道侧面投影面积上
        return 0.5 * rho * cd * d * L * v**2

    def _surface_tow_drag(self) -> float:
        """
        N, 水面拖运阻力
        包含：水动力阻力 + 波浪阻力（简化为增大系数）
        """
        rho = self.environment.seawater_density
        d = self.pipeline.total_outer_diameter
        L = self.pipeline.length
        v = self.relative_velocity

        cd = self.environment.drag_coefficient_cylinder(d, v)
        # 水面效应修正系数（近自由面时阻力增加约20-30%）
        surface_factor = 1.25
        hydro_drag = 0.5 * rho * cd * d * L * v**2 * surface_factor

        # 波浪漂流力（简化估算）
        wave_drift = self._wave_drift_force()

        return hydro_drag + wave_drift

    def _wave_drift_force(self) -> float:
        """
        N, 波浪漂移力（二阶波浪力）
        使用简化公式估算
        """
        rho = self.environment.seawater_density
        g = 9.81
        hs = self.environment.wave_height
        d = self.pipeline.total_outer_diameter
        L = self.pipeline.length
        # 简化：波浪漂移力 ≈ 0.5 * ρ * g * Hs² * D * L / wave_length
        wave_length = self.environment.wave_length
        if wave_length < 1e-3:
            return 0.0
        return 0.5 * rho * g * hs**2 * d * L / wave_length * 0.1

    def _off_bottom_tow_drag(self) -> float:
        """
        N, 离底拖运阻力
        管道悬浮于海底以上，受海流和拖速影响
        """
        rho = self.environment.seawater_density
        d = self.pipeline.total_outer_diameter
        L = self.pipeline.length
        v = self.relative_velocity
        cd = self.environment.drag_coefficient_cylinder(d, v)
        # 近底效应修正（距离底部 < 1D 时阻力增加）
        h = self.off_bottom_clearance
        if h < d:
            bottom_factor = 1.0 + 0.5 * (1.0 - h / d)
        else:
            bottom_factor = 1.0
        return 0.5 * rho * cd * d * L * v**2 * bottom_factor

    def _bottom_tow_drag(self) -> float:
        """
        N, 海底拖运阻力
        包含：水动力拖曳力 + 海底摩擦力
        """
        rho = self.environment.seawater_density
        d = self.pipeline.total_outer_diameter
        L = self.pipeline.length
        v = self.relative_velocity
        cd = self.environment.drag_coefficient_cylinder(d, v)

        # 水动力拖曳（仅上半部分暴露在水流中）
        hydro_drag = 0.5 * rho * cd * d * L * v**2 * 0.7

        # 海底摩擦力
        submerged_weight = abs(self.pipeline.total_submerged_weight)
        friction = self.seabed_friction_coeff * submerged_weight

        return hydro_drag + friction

    def towing_resistance(self) -> float:
        """N, 拖运阻力（不含安全系数）"""
        if self.method == TowingMethod.SURFACE:
            return self._surface_tow_drag()
        elif self.method == TowingMethod.OFF_BOTTOM:
            return self._off_bottom_tow_drag()
        else:
            return self._bottom_tow_drag()

    def required_bollard_pull(self) -> float:
        """kN, 所需拖轮拖力（含安全系数）"""
        resistance = self.towing_resistance()
        lateral = self._lateral_drag_force()
        total = math.sqrt(resistance**2 + lateral**2)
        return total * self.safety_factor / 1000

    def towing_power(self) -> float:
        """kW, 拖运所需功率"""
        f = self.towing_resistance()
        return f * self.towing_speed / 1000

    def check_stability(self) -> Tuple[bool, str]:
        """
        Check if pipeline is stable for the selected towing method.
        检查管道对于所选拖运方式的稳定性。
        """
        sg = self.pipeline.specific_gravity
        method = self.method

        if method == TowingMethod.SURFACE:
            if sg >= 1.0:
                return False, f"比重 {sg:.3f} ≥ 1.0，管道将下沉，不能进行水面拖运"
            return True, f"比重 {sg:.3f} < 1.0，可进行水面拖运"

        elif method == TowingMethod.OFF_BOTTOM:
            if sg < 1.0:
                return False, f"比重 {sg:.3f} < 1.0，管道上浮，需增加配重"
            return True, f"比重 {sg:.3f} > 1.0，可进行离底拖运"

        else:  # BOTTOM
            if sg < 1.02:
                return False, f"比重 {sg:.3f} < 1.02，管道水中重量不足以保持海底稳定"
            return True, f"比重 {sg:.3f} ≥ 1.02，可进行海底拖运"

    def results(self) -> dict:
        stable, stability_msg = self.check_stability()
        resistance = self.towing_resistance()
        lateral = self._lateral_drag_force()
        bollard_pull = self.required_bollard_pull()

        return {
            "拖运方式 Method": self.method.value,
            "拖运速度 Towing Speed (m/s)": self.towing_speed,
            "相对流速 Relative Velocity (m/s)": round(self.relative_velocity, 3),
            "稳定性 Stability": stability_msg,
            "纵向拖运阻力 Axial Resistance (kN)": round(resistance / 1000, 2),
            "横向流体力 Lateral Force (kN)": round(lateral / 1000, 2),
            "所需拖轮拖力 Required Bollard Pull (kN)": round(bollard_pull, 2),
            "拖运功率 Towing Power (kW)": round(self.towing_power(), 2),
            "安全系数 Safety Factor": self.safety_factor,
        }
