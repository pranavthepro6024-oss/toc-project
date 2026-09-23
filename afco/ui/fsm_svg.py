"""Pure-Python high-contrast SVG generator for the AFCO 18-State Canonical Session DFA.

Zero system Graphviz dependencies; produces fully responsive, crisp, interactive
automata diagrams with active state glow, edge routing, and label callouts.
"""

from __future__ import annotations
import math
from typing import Optional, Tuple, Dict, List

# 4-tier topological layout optimized for 1160x520 canvas
STATE_COORDS: Dict[str, Tuple[float, float]] = {
    # Tier 1: Connection & Authentication (Left to Right)
    "IDLE": (90.0, 80.0),
    "RESERVED": (270.0, 80.0),
    "AUTH_PENDING": (450.0, 80.0),
    "AUTHORIZED": (630.0, 80.0),
    "CABLE_DETECTED": (810.0, 80.0),
    "EV_CONNECTED": (990.0, 80.0),

    # Tier 2: Power Transfer & Dispatch (Right to Left)
    "PRECHARGE": (990.0, 210.0),
    "CHARGING": (790.0, 210.0),
    "PAUSED_DISPATCH": (590.0, 210.0),
    "SUSPENDED_EV": (390.0, 210.0),
    "SUSPENDED_EVSE": (190.0, 210.0),

    # Tier 3: Ramp Down & Physical Separation (Right to Left)
    "RAMP_DOWN": (790.0, 340.0),
    "ISOLATING": (590.0, 340.0),
    "UNLOCKED": (390.0, 340.0),
    "UNPLUGGED": (190.0, 340.0),

    # Tier 4: Financial Settlement & Terminal States
    "BILLING_PENDING": (190.0, 460.0),
    "COMPLETED": (480.0, 460.0),
    "FAULT_TERMINAL": (880.0, 460.0),
}

# (Source, Target, Symbol Label, CurveOffset)
MAJOR_TRANSITIONS = [
    # Tier 1 flows
    ("IDLE", "RESERVED", "reserve_req", 0),
    ("IDLE", "AUTH_PENDING", "auth_req", 25),
    ("RESERVED", "AUTH_PENDING", "auth_req", 0),
    ("AUTH_PENDING", "AUTHORIZED", "auth_ok", 0),
    ("AUTHORIZED", "CABLE_DETECTED", "plug_in", 0),
    ("CABLE_DETECTED", "EV_CONNECTED", "lock_ok", 0),

    # Tier 1 to Tier 2
    ("EV_CONNECTED", "PRECHARGE", "ev_ready", 0),
    ("PRECHARGE", "CHARGING", "power_start", 0),

    # Tier 2 power controls
    ("CHARGING", "PAUSED_DISPATCH", "grid_curtail", -18),
    ("PAUSED_DISPATCH", "CHARGING", "power_start", -18),
    ("CHARGING", "SUSPENDED_EV", "ev_stop", 24),
    ("SUSPENDED_EV", "CHARGING", "ev_ready", 24),
    ("PAUSED_DISPATCH", "SUSPENDED_EVSE", "grid_curtail", 0),

    # Tier 2 to Tier 3 ramp down
    ("CHARGING", "RAMP_DOWN", "power_ramp_down", 0),
    ("RAMP_DOWN", "ISOLATING", "power_stop", 0),
    ("ISOLATING", "UNLOCKED", "contactors_open", 0),
    ("ISOLATING", "UNPLUGGED", "unplug", 15),
    ("UNLOCKED", "UNPLUGGED", "unplug", 0),

    # Tier 3 to Tier 4 settlement
    ("UNPLUGGED", "BILLING_PENDING", "meter_final", 0),
    ("BILLING_PENDING", "COMPLETED", "pay_ok", 0),
    ("UNPLUGGED", "COMPLETED", "pay_ok", -25),

    # Reset
    ("COMPLETED", "IDLE", "reset_cmd", -45),

    # Safety Traps to FAULT_TERMINAL
    ("CHARGING", "FAULT_TERMINAL", "e_stop", 20),
    ("PRECHARGE", "FAULT_TERMINAL", "fault", 0),
    ("CABLE_DETECTED", "FAULT_TERMINAL", "lock_fail", 30),
    ("RAMP_DOWN", "FAULT_TERMINAL", "overcurrent", 0),
]


def _circle_boundary(x1: float, y1: float, x2: float, y2: float, r: float) -> Tuple[float, float]:
    """Calculate point on boundary of circle (x1, y1) with radius r directed toward (x2, y2)."""
    dx = x2 - x1
    dy = y2 - y1
    dist = math.hypot(dx, dy)
    if dist < 1e-4:
        return x1, y1
    return x1 + (dx / dist) * r, y1 + (dy / dist) * r


def generate_fsm_svg(active_state: Optional[str] = None) -> str:
    """Render the canonical 18-state FSM as high-contrast vector SVG."""
    w, h = 1140, 520
    node_r = 32.0

    svg: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" height="100%" '
        'style="background: #090b10; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; user-select: none;">',
        '<defs>',
        '  <linearGradient id="activeGrad" x1="0%" y1="0%" x2="100%" y2="100%">',
        '    <stop offset="0%" stop-color="#0284c7" />',
        '    <stop offset="100%" stop-color="#0369a1" />',
        '  </linearGradient>',
        '  <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#64748b" />',
        '  </marker>',
        '  <marker id="arrow-active" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        '    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#38bdf8" />',
        '  </marker>',
        '  <marker id="arrow-start" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">',
        '    <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#10b981" />',
        '  </marker>',
        '  <filter id="glow" x="-30%" y="-30%" width="160%" height="160%">',
        '    <feGaussianBlur stdDeviation="5" result="blur" />',
        '    <feComposite in="SourceGraphic" in2="blur" operator="over" />',
        '  </filter>',
        '</defs>',
    ]

    # Start arrow into IDLE
    start_x, start_y = STATE_COORDS["IDLE"]
    svg.append(f'<path d="M 20 {start_y} L {start_x - node_r - 4} {start_y}" fill="none" stroke="#10b981" stroke-width="2.5" marker-end="url(#arrow-start)" />')
    svg.append(f'<text x="22" y="{start_y - 8}" font-size="10" font-weight="700" fill="#10b981">START</text>')

    # Draw transition edges
    for src, dst, label, curve_offset in MAJOR_TRANSITIONS:
        if src not in STATE_COORDS or dst not in STATE_COORDS:
            continue
        x1, y1 = STATE_COORDS[src]
        x2, y2 = STATE_COORDS[dst]
        is_active_edge = (src == active_state)

        stroke = "#38bdf8" if is_active_edge else "#475569"
        stroke_width = "2.8" if is_active_edge else "1.5"
        marker = "url(#arrow-active)" if is_active_edge else "url(#arrow)"
        opacity = "1.0" if is_active_edge else "0.75"

        # Calculate exact boundary points
        if curve_offset != 0:
            mid_x = (x1 + x2) / 2.0
            mid_y = (y1 + y2) / 2.0
            # Perpendicular vector
            dx = x2 - x1
            dy = y2 - y1
            length = max(1e-4, math.hypot(dx, dy))
            nx = -dy / length
            ny = dx / length
            cx = mid_x + nx * curve_offset
            cy = mid_y + ny * curve_offset

            # Start and end boundaries facing control point
            p1_x, p1_y = _circle_boundary(x1, y1, cx, cy, node_r)
            p2_x, p2_y = _circle_boundary(x2, y2, cx, cy, node_r)

            d_str = f"M {p1_x:.1f} {p1_y:.1f} Q {cx:.1f} {cy:.1f} {p2_x:.1f} {p2_y:.1f}"
            lbl_x = (p1_x + 2 * cx + p2_x) / 4.0
            lbl_y = (p1_y + 2 * cy + p2_y) / 4.0
        else:
            p1_x, p1_y = _circle_boundary(x1, y1, x2, y2, node_r)
            p2_x, p2_y = _circle_boundary(x2, y2, x1, y1, node_r)
            d_str = f"M {p1_x:.1f} {p1_y:.1f} L {p2_x:.1f} {p2_y:.1f}"
            lbl_x = (p1_x + p2_x) / 2.0
            lbl_y = (p1_y + p2_y) / 2.0 - 5.0

        dash_attr = 'stroke-dasharray="4,3"' if is_active_edge else ''
        svg.append(f'<path d="{d_str}" fill="none" stroke="{stroke}" stroke-width="{stroke_width}" marker-end="{marker}" opacity="{opacity}" {dash_attr} />')

        # Clean readable label badge
        if label:
            label_len = len(label)
            rect_w = max(40, label_len * 5.8 + 10)
            rect_h = 14
            badge_bg = "#0f172a" if not is_active_edge else "#082f49"
            badge_border = "#334155" if not is_active_edge else "#0284c7"
            badge_text = "#94a3b8" if not is_active_edge else "#7dd3fc"

            svg.append(
                f'<g transform="translate({lbl_x:.1f}, {lbl_y:.1f})">'
                f'  <rect x="{-rect_w / 2:.1f}" y="{-rect_h / 2:.1f}" width="{rect_w:.1f}" height="{rect_h}" rx="3" '
                f'fill="{badge_bg}" stroke="{badge_border}" stroke-width="0.8" opacity="0.92" />'
                f'  <text x="0" y="3.5" font-size="8" font-family="monospace" font-weight="600" fill="{badge_text}" text-anchor="middle">{label}</text>'
                f'</g>'
            )

    # Draw state nodes
    for name, (x, y) in STATE_COORDS.items():
        is_active = (name == active_state)
        is_accepting = (name == "COMPLETED")
        is_trap = (name == "FAULT_TERMINAL")

        if is_active:
            fill = "url(#activeGrad)"
            stroke = "#38bdf8"
            stroke_width = 3.5
            text_color = "#ffffff"
            r = node_r + 2
            filter_attr = 'filter="url(#glow)"'
        elif is_accepting:
            fill = "#064e3b"
            stroke = "#10b981"
            stroke_width = 2.5
            text_color = "#a7f3d0"
            r = node_r
            filter_attr = ""
        elif is_trap:
            fill = "#450a0a"
            stroke = "#ef4444"
            stroke_width = 2.5
            text_color = "#fecaca"
            r = node_r
            filter_attr = ""
        else:
            fill = "#131b2e"
            stroke = "#475569"
            stroke_width = 1.8
            text_color = "#f1f5f9"
            r = node_r
            filter_attr = ""

        svg.append(f'<g class="fsm-node" data-state="{name}" style="cursor: pointer;">')

        # Double circle for accepting state
        if is_accepting:
            svg.append(f'<circle cx="{x}" cy="{y}" r="{r + 5}" fill="none" stroke="#10b981" stroke-width="1.8" stroke-dasharray="4,2" />')

        # Pulsing halo for active state
        if is_active:
            svg.append(
                f'<circle cx="{x}" cy="{y}" r="{r + 7}" fill="none" stroke="#38bdf8" stroke-width="2.5" opacity="0.8">'
                '  <animate attributeName="r" values="39;47;39" dur="2s" repeatCount="indefinite" />'
                '  <animate attributeName="opacity" values="0.8;0.15;0.8" dur="2s" repeatCount="indefinite" />'
                '</circle>'
            )

        # Main node circle
        svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" {filter_attr} />')

        # Split state text cleanly into up to 2 readable lines
        clean_name = name.replace("_", " ")
        words = clean_name.split(" ")
        if len(words) >= 2:
            mid = len(words) // 2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
            svg.append(f'<text x="{x}" y="{y - 3.5}" font-size="9" font-weight="{700 if is_active else 600}" fill="{text_color}" text-anchor="middle">{line1}</text>')
            svg.append(f'<text x="{x}" y="{y + 9.5}" font-size="9" font-weight="{700 if is_active else 600}" fill="{text_color}" text-anchor="middle">{line2}</text>')
        else:
            svg.append(f'<text x="{x}" y="{y + 3.5}" font-size="9.5" font-weight="{700 if is_active else 600}" fill="{text_color}" text-anchor="middle">{clean_name}</text>')

        # Active tag pill
        if is_active:
            svg.append(
                f'<rect x="{x - 24}" y="{y + r + 3}" width="48" height="15" rx="7.5" fill="#38bdf8" />'
                f'<text x="{x}" y="{y + r + 14}" font-size="8" font-weight="800" fill="#090d16" text-anchor="middle">ACTIVE</text>'
            )

        svg.append('</g>')

    svg.append('</svg>')
    return "".join(svg)
