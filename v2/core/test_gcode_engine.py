import numpy as np
from core.gcode_engine import GCodeEngine
from core.coil_math import CoilMathEngine

def test_gcode_generation_with_smart_reversal_and_m0():
    # Simulate basic path parameters
    # wire_d=0.5, layers=2, inner_d=35, width=50, p_res=32
    pts_list, length_m, angles_list = CoilMathEngine.calculate_path(0.5, 2, 35, 50, 32)

    engine = GCodeEngine()
    gcode = engine.generate(
        pts_list=pts_list,
        angles_list=angles_list,
        nozzle_y_offset=0.0,
        wire_offset=0.0,
        spool_offset=0.0,
        z_force=0.5,
        feedrate=500,
        units="mm",
        max_x=200.0,
        m0_enable=True,
        compress_gcode=True,
        smart_reversal=True,
        reversal_speed_pct=50.0,
        reversal_y_retract=1.0,
        reversal_dwell_ms=250.0
    )

    # 1. Assert we got G-code back
    assert len(gcode) > 0

    # 2. Assert M0 is present after home sequence/first move
    assert "M0 ;" in gcode

    # 3. Assert Compressed Mid-Zone comments are present
    assert "Compressed Mid-Zone" in gcode

    # 4. Assert dwell and reversal comments are present
    assert "G4 F250" in gcode
    assert "Reversal Exit" in gcode or "Reversal Entry" in gcode

def test_gcode_generation_without_compression():
    pts_list, length_m, angles_list = CoilMathEngine.calculate_path(0.5, 2, 35, 50, 32)

    engine = GCodeEngine()
    gcode = engine.generate(
        pts_list=pts_list,
        angles_list=angles_list,
        compress_gcode=False,
        smart_reversal=True
    )

    assert len(gcode) > 0
    assert "Compressed Mid-Zone" not in gcode
