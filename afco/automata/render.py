"""Graphviz DOT generator and diagram renderer for DFAs.

Produces professional state transition diagrams with double circles
for accepting states, invisible start node, and active-state highlighting.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from afco.automata.dfa import DFA


def dfa_to_dot(
    dfa: DFA,
    active_state: Optional[Any] = None,
    graph_name: str = "DFA",
    rankdir: str = "LR"
) -> str:
    """Generate Graphviz DOT source string for a DFA."""
    lines: List[str] = [
        f"digraph {graph_name} {{",
        f'  rankdir="{rankdir}";',
        '  node [fontname="Helvetica", fontsize=11];',
        '  edge [fontname="Helvetica", fontsize=10];',
        "",
        "  // Start indicator",
        '  __start__ [shape=none, label="", width=0, height=0];',
        f'  __start__ -> "{dfa.start_state}";',
        "",
        "  // States",
    ]

    for state in sorted(list(dfa.states), key=str):
        attrs: List[str] = []
        is_accepting = state in dfa.accepting_states
        attrs.append(f'shape="{"doublecircle" if is_accepting else "circle"}"')

        if state == active_state:
            attrs.append('style="filled,bold"')
            attrs.append('fillcolor="#C6F6D5"')  # Mint green highlight
            attrs.append('color="#22543D"')
            attrs.append('penwidth=2.5')
        elif is_accepting:
            attrs.append('style="filled"')
            attrs.append('fillcolor="#EBF8FF"')  # Soft blue for accepting
            attrs.append('color="#2B6CB0"')
        else:
            attrs.append('style="filled"')
            attrs.append('fillcolor="#EDF2F7"')  # Neutral light grey
            attrs.append('color="#4A5568"')

        attrs_str = ", ".join(attrs)
        lines.append(f'  "{state}" [{attrs_str}];')

    lines.append("")
    lines.append("  // Transitions")

    # Group transitions between same source and target to combine labels (e.g. "a, b")
    edge_labels: Dict[Tuple[Any, Any], List[str]] = defaultdict(list)
    for (src, sym), tgt in dfa.transitions.items():
        edge_labels[(src, tgt)].append(str(sym))

    for (src, tgt), syms in sorted(edge_labels.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))):
        label = ", ".join(sorted(syms))
        lines.append(f'  "{src}" -> "{tgt}" [label="{label}"];')

    lines.append("}")
    return "\n".join(lines)


def render_dfa_svg(
    dfa: DFA,
    output_path: str,
    active_state: Optional[Any] = None,
    graph_name: str = "DFA"
) -> str:
    """Render a DFA to an SVG file using graphviz.

    Returns the path to the written file.
    """
    dot_source = dfa_to_dot(dfa, active_state=active_state, graph_name=graph_name)
    try:
        import graphviz
        src = graphviz.Source(dot_source)
        src.render(filename=output_path, format="svg", cleanup=True)
        return f"{output_path}.svg"
    except Exception:
        # Fallback: write raw dot file if graphviz binary is not on system path
        dot_file = f"{output_path}.dot"
        with open(dot_file, "w", encoding="utf-8") as f:
            f.write(dot_source)
        return dot_file
