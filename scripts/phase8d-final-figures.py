"""Render each Phase8D quantitative figure from immutable source data."""
from pathlib import Path
import runpy
for name in ["g1","p1","p2","stress","closure"]:
    runpy.run_path(str(Path(__file__).with_name("phase8d-plot-"+name+".py")),run_name="__main__")
