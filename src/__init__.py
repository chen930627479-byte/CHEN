"""
海上管道拖运分析工具包
Offshore Pipeline Towing Analysis Toolkit
"""

from .pipeline import Pipeline
from .towing import TowingAnalysis
from .catenary import CatenaryAnalysis
from .environment import MarineEnvironment

__all__ = ["Pipeline", "TowingAnalysis", "CatenaryAnalysis", "MarineEnvironment"]
__version__ = "1.0.0"
