"""
Marine environmental conditions for towing analysis.
拖运分析海洋环境条件模块
"""

import math
from dataclasses import dataclass


@dataclass
class MarineEnvironment:
    """
    Environmental conditions during towing operation.
    拖运作业期间的环境条件。
    """

    water_depth: float          # m, 水深
    current_speed: float        # m/s, 海流速度
    current_direction: float = 0.0  # deg, 海流方向（相对拖运方向，0°为顺流）
    wave_height: float = 2.0    # m, 有效波高 Hs
    wave_period: float = 8.0    # s, 波浪周期
    wind_speed: float = 10.0    # m/s, 风速（10m高度处）
    wind_direction: float = 0.0 # deg, 风向（相对拖运方向）
    seawater_density: float = 1025.0  # kg/m³
    air_density: float = 1.225  # kg/m³
    kinematic_viscosity: float = 1.07e-6  # m²/s, 海水运动粘度（15°C）

    @property
    def current_velocity_x(self) -> float:
        """m/s, 顺拖运方向海流分量"""
        return self.current_speed * math.cos(math.radians(self.current_direction))

    @property
    def current_velocity_y(self) -> float:
        """m/s, 横拖运方向海流分量"""
        return self.current_speed * math.sin(math.radians(self.current_direction))

    @property
    def wave_length(self) -> float:
        """m, 深水波长（线性波浪理论）"""
        g = 9.81
        return g * self.wave_period**2 / (2 * math.pi)

    @property
    def wave_celerity(self) -> float:
        """m/s, 波速"""
        return self.wave_length / self.wave_period

    def reynolds_number(self, diameter: float, velocity: float) -> float:
        """计算雷诺数"""
        return velocity * diameter / self.kinematic_viscosity

    def drag_coefficient_cylinder(self, diameter: float, velocity: float) -> float:
        """
        Estimate drag coefficient for a cylinder based on Reynolds number.
        基于雷诺数估算圆柱体阻力系数。
        """
        if velocity < 1e-6:
            return 1.2
        re = self.reynolds_number(diameter, velocity)
        if re < 1e5:
            return 1.2
        elif re < 5e5:
            # 超临界过渡区
            return 1.2 - 0.7 * (re - 1e5) / (4e5)
        else:
            return 0.3

    def summary(self) -> dict:
        return {
            "水深 Water Depth (m)": self.water_depth,
            "海流速度 Current Speed (m/s)": self.current_speed,
            "海流方向 Current Direction (deg)": self.current_direction,
            "有效波高 Hs (m)": self.wave_height,
            "波浪周期 Tp (s)": self.wave_period,
            "风速 Wind Speed (m/s)": self.wind_speed,
            "波长 Wave Length (m)": round(self.wave_length, 1),
        }
