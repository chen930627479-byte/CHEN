"""
Pipeline physical properties and buoyancy calculations.
管道物理属性及浮力计算模块
"""

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Pipeline:
    """
    Represents a marine pipeline with its physical properties.
    表示具有物理属性的海洋管道。
    """

    outer_diameter: float        # m, 外径
    wall_thickness: float        # m, 壁厚
    steel_density: float = 7850.0  # kg/m³, 钢材密度
    coating_thickness: float = 0.0  # m, 涂层厚度
    coating_density: float = 900.0  # kg/m³, 涂层密度（混凝土加重层约3000）
    concrete_coating_thickness: float = 0.0  # m, 混凝土配重层厚度
    concrete_density: float = 3000.0  # kg/m³, 混凝土密度
    content_density: float = 0.0    # kg/m³, 管内介质密度（拖运时通常为空气）
    length: float = 1000.0          # m, 管道总长度
    seawater_density: float = 1025.0  # kg/m³, 海水密度

    def __post_init__(self):
        if self.wall_thickness >= self.outer_diameter / 2:
            raise ValueError("壁厚不得超过外径的一半 / Wall thickness must be less than outer radius")
        if self.outer_diameter <= 0 or self.wall_thickness <= 0:
            raise ValueError("外径和壁厚必须为正值 / Diameter and thickness must be positive")

    @property
    def inner_diameter(self) -> float:
        return self.outer_diameter - 2 * self.wall_thickness

    @property
    def total_outer_diameter(self) -> float:
        return (self.outer_diameter
                + 2 * self.coating_thickness
                + 2 * self.concrete_coating_thickness)

    @property
    def steel_cross_section_area(self) -> float:
        return math.pi / 4 * (self.outer_diameter**2 - self.inner_diameter**2)

    @property
    def inner_cross_section_area(self) -> float:
        return math.pi / 4 * self.inner_diameter**2

    @property
    def coating_cross_section_area(self) -> float:
        d_with_coating = self.outer_diameter + 2 * self.coating_thickness
        return math.pi / 4 * (d_with_coating**2 - self.outer_diameter**2)

    @property
    def concrete_cross_section_area(self) -> float:
        d_outer = self.total_outer_diameter
        d_inner = self.outer_diameter + 2 * self.coating_thickness
        return math.pi / 4 * (d_outer**2 - d_inner**2)

    @property
    def displaced_cross_section_area(self) -> float:
        return math.pi / 4 * self.total_outer_diameter**2

    @property
    def mass_per_meter(self) -> float:
        """kg/m, 单位长度管道质量"""
        steel_mass = self.steel_cross_section_area * self.steel_density
        coating_mass = self.coating_cross_section_area * self.coating_density
        concrete_mass = self.concrete_cross_section_area * self.concrete_density
        content_mass = self.inner_cross_section_area * self.content_density
        return steel_mass + coating_mass + concrete_mass + content_mass

    @property
    def total_mass(self) -> float:
        """kg, 管道总质量"""
        return self.mass_per_meter * self.length

    @property
    def displaced_volume_per_meter(self) -> float:
        """m³/m, 单位长度排水体积"""
        return self.displaced_cross_section_area

    @property
    def buoyancy_per_meter(self) -> float:
        """N/m, 单位长度浮力"""
        return self.displaced_volume_per_meter * self.seawater_density * 9.81

    @property
    def weight_in_air_per_meter(self) -> float:
        """N/m, 单位长度空气中重量"""
        return self.mass_per_meter * 9.81

    @property
    def submerged_weight_per_meter(self) -> float:
        """N/m, 单位长度水中重量（正值=下沉，负值=上浮）"""
        return self.weight_in_air_per_meter - self.buoyancy_per_meter

    @property
    def total_submerged_weight(self) -> float:
        """N, 总水中重量"""
        return self.submerged_weight_per_meter * self.length

    @property
    def specific_gravity(self) -> float:
        """管道比重（相对于海水）"""
        return self.mass_per_meter / (self.displaced_volume_per_meter * self.seawater_density)

    def summary(self) -> dict:
        return {
            "外径 OD (mm)": self.outer_diameter * 1000,
            "壁厚 WT (mm)": self.wall_thickness * 1000,
            "总外径 Total OD (mm)": self.total_outer_diameter * 1000,
            "单位长度质量 Mass/m (kg/m)": round(self.mass_per_meter, 2),
            "单位长度浮力 Buoyancy/m (N/m)": round(self.buoyancy_per_meter, 2),
            "单位长度水中重量 Submerged Weight/m (N/m)": round(self.submerged_weight_per_meter, 2),
            "比重 Specific Gravity": round(self.specific_gravity, 3),
            "管道总长度 Length (m)": self.length,
            "总水中重量 Total Submerged Weight (kN)": round(self.total_submerged_weight / 1000, 2),
        }
