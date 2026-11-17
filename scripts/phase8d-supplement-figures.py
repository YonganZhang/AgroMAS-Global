"""Render the four-gap quantitative supplement from frozen outputs."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name("phase8d-plot-gaps.py")),run_name="__main__")
