"""
Catenary and tow wire analysis for offshore pipeline towing.
海上管道拖运拖缆悬链线分析模块

Analyzes the geometry and tension distribution of tow wire/chain
under combined effects of weight, buoyancy, and drag.
分析拖缆在重力、浮力和阻力共同作用下的几何形态和张力分布。
"""

import math
from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class TowWire:
    """
    Tow wire / tow chain properties.
    拖缆/拖链物理属性。
    """
    diameter: float         # m, 缆绳直径
    mass_per_meter: float   # kg/m, 单位长度质量（空气中）
    breaking_load: float    # kN, 破断负荷
    length: float           # m, 拖缆长度
    wire_density: float = 7850.0  # kg/m³
    seawater_density: float = 1025.0  # kg/m³

    @property
    def displaced_volume_per_meter(self) -> float:
        return math.pi / 4 * self.diameter**2

    @property
    def buoyancy_per_meter(self) -> float:
        """N/m"""
        return self.displaced_volume_per_meter * self.seawater_density * 9.81

    @property
    def submerged_weight_per_meter(self) -> float:
        """N/m, 水中单位长度重量"""
        return self.mass_per_meter * 9.81 - self.buoyancy_per_meter

    @property
    def axial_stiffness(self) -> float:
        """N, 轴向刚度 EA"""
        E_steel = 200e9  # Pa
        A = math.pi / 4 * self.diameter**2
        return E_steel * A

    def utilization(self, tension: float) -> float:
        """拖缆张力利用率（张力/破断负荷）"""
        return tension / (self.breaking_load * 1000)


@dataclass
class CatenaryAnalysis:
    """
    Catenary analysis of tow wire under load.
    拖缆悬链线受力分析。

    Uses catenary equations to determine:
    - Wire geometry (shape, maximum depth)
    - Tension distribution along wire
    - Horizontal and vertical force components

    使用悬链线方程确定：
    - 拖缆几何形态（形状、最大水深）
    - 沿拖缆张力分布
    - 水平和垂直力分量
    """

    tow_wire: TowWire
    horizontal_force: float   # N, 水平拖力（等于管道拖运阻力）
    fairlead_depth: float     # m, 导缆孔水深（拖轮吃水）
    attachment_depth: float   # m, 管道端拖缆连接点水深

    @property
    def net_weight_per_meter(self) -> float:
        """N/m, 拖缆单位长度净水中重量"""
        return self.tow_wire.submerged_weight_per_meter

    @property
    def catenary_parameter(self) -> float:
        """
        Catenary parameter a = H / w
        H = horizontal tension component (N)
        w = net weight per unit length (N/m)
        """
        w = self.net_weight_per_meter
        if abs(w) < 1e-6:
            return 1e9  # 接近中性浮力，参数趋于无穷
        return self.horizontal_force / w

    def tension_at_point(self, arc_length_from_bottom: float) -> float:
        """
        N, 距悬链线最低点弧长s处的张力
        T(s) = sqrt(H² + (w*s)²)
        """
        H = self.horizontal_force
        w = self.net_weight_per_meter
        return math.sqrt(H**2 + (w * arc_length_from_bottom)**2)

    def max_tension(self) -> float:
        """N, 拖缆最大张力（在拖轮导缆孔处）"""
        H = self.horizontal_force
        w = self.net_weight_per_meter
        L = self.tow_wire.length
        return math.sqrt(H**2 + (w * L)**2)

    def departure_angle(self) -> float:
        """deg, 拖缆在拖轮端的离水角度"""
        H = self.horizontal_force
        w = self.net_weight_per_meter
        L = self.tow_wire.length
        vertical = w * L
        return math.degrees(math.atan2(vertical, H))

    def catenary_geometry(self, n_points: int = 20) -> List[Tuple[float, float]]:
        """
        Calculate catenary shape points (x, z) along wire.
        计算拖缆悬链线形态点列 (水平距离, 深度)。
        Returns list of (horizontal_distance, depth) tuples.
        """
        a = self.catenary_parameter
        L = self.tow_wire.length
        points = []

        for i in range(n_points + 1):
            s = L * i / n_points
            if abs(a) > 1e6:  # 近似直线
                x = s
                z = self.fairlead_depth
            else:
                x = a * math.asinh(s / a) if a > 0 else s
                z = self.fairlead_depth + a * (math.cosh(s / a) - 1) if a > 0 else self.fairlead_depth
            points.append((round(x, 2), round(z, 2)))

        return points

    def horizontal_span(self) -> float:
        """m, 拖缆水平投影长度"""
        a = self.catenary_parameter
        L = self.tow_wire.length
        if abs(a) > 1e6:
            return L
        return a * math.asinh(L / a) if a > 0 else L

    def check_wire(self) -> Tuple[bool, str]:
        """
        Check tow wire adequacy.
        检查拖缆是否满足要求。
        """
        max_t = self.max_tension()
        util = self.tow_wire.utilization(max_t)
        safe_util = 1.0 / 3.0  # 安全工作负荷 = 破断负荷 / 3

        status = util <= safe_util
        msg = (
            f"最大张力 {max_t/1000:.1f} kN，"
            f"利用率 {util*100:.1f}%，"
            f"{'满足要求 OK' if status else '超出安全工作负荷 FAIL'}"
            f"（安全工作负荷 = {self.tow_wire.breaking_load/3:.1f} kN）"
        )
        return status, msg

    def results(self) -> dict:
        ok, wire_check = self.check_wire()
        return {
            "拖缆长度 Wire Length (m)": self.tow_wire.length,
            "拖缆直径 Wire Diameter (mm)": self.tow_wire.diameter * 1000,
            "拖缆破断负荷 Breaking Load (kN)": self.tow_wire.breaking_load,
            "悬链线参数 Catenary Parameter a (m)": round(self.catenary_parameter, 1),
            "水平跨距 Horizontal Span (m)": round(self.horizontal_span(), 1),
            "最大张力 Max Tension (kN)": round(self.max_tension() / 1000, 2),
            "拖轮端离水角 Departure Angle (deg)": round(self.departure_angle(), 1),
            "拖缆检查 Wire Check": wire_check,
        }
