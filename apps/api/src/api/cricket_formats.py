"""Known cricket formats plus room for a club to name its own.

HT does not assume an over count. T20 is 20 overs. Premier League is 40.
A code outside this catalog is a configurable format and needs a display name.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from fastapi import HTTPException

_CODE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


@dataclass(frozen=True, slots=True)
class FormatSpec:
    code: str
    name: str
    overs: int | None


BUILTIN_FORMATS: tuple[FormatSpec, ...] = (
    FormatSpec("ht", "HT", None),
    FormatSpec("t20", "T20", 20),
    FormatSpec("premier_40", "Premier League", 40),
)

_BY_CODE = {spec.code: spec for spec in BUILTIN_FORMATS}


def resolve_format(
    code: str,
    name: str | None,
    overs: int | None,
) -> tuple[str, str, int | None]:
    normalized = code.strip().lower()
    if not _CODE.fullmatch(normalized):
        raise HTTPException(status_code=422, detail="Invalid format code")
    spec = _BY_CODE.get(normalized)
    if spec is not None:
        display = (name or spec.name).strip()
        if not display:
            display = spec.name
        chosen = spec.overs if overs is None else overs
        return normalized, display, chosen
    display = (name or "").strip()
    if not display:
        raise HTTPException(
            status_code=422,
            detail="A configurable format needs format_name",
        )
    return normalized, display, overs
