from __future__ import annotations

import html

from .models import ProofSpec


def blank_proof_table(spec: ProofSpec) -> str:
    rows = "".join(
        f"<tr><td>{index}</td><td>&nbsp;</td><td>&nbsp;</td></tr>"
        for index in range(1, len(spec.required_steps) + 1)
    )
    return (
        "<table class='proof-table'><thead><tr><th>#</th><th>Statement</th><th>Reason</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def completed_proof_table(spec: ProofSpec) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{index}</td><td>{html.escape(step.statement)}</td><td>{html.escape(step.reason)}</td>"
        "</tr>"
        for index, step in enumerate(spec.required_steps, start=1)
    )
    return (
        "<table class='proof-table'><thead><tr><th>#</th><th>Statement</th><th>Reason</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )
