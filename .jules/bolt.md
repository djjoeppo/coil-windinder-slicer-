# Bolt's Performance Journal - Speaker Coil Winder

## 2025-02-15 - Smart G-code Compression & Reversal Performance
**Learning:** Dense G-code with dozens of points per rotation creates significant USB serial bandwidth bottlenecks on microcontrollers like ESP32, which can cause motor stutter. Compressing middle segments of a winding layer to single G1 movements dramatically reduces G-code file size and serial traffic (up to 95% reduction), while maintaining precise motion control. At the same time, applying physical limits and dedicated transition behavior (deceleration, dwell, and Y-retract) during layer reversals avoids physical speaker coil winding failures without bloating the G-code.
**Action:** Implement an analytical G-code compression logic in `GCodeEngine` and provide real-world tuning options (M0 wait, smart reversal parameters) in the PySide6 UI.
