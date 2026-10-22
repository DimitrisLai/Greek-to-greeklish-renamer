"""Spreadsheet-safe output for informational CSV exports only.

Undo logs must keep literal paths: modifying them would make restore unreliable.
For human-facing preview/results CSVs, prepend a literal apostrophe to cells
Excel/LibreOffice could otherwise interpret as executable formulas.
"""
from __future__ import annotations


def spreadsheet_cell(value: object) -> str:
    cell = str(value)
    if cell.lstrip(' \t\r\n\ufeff').startswith(('=', '+', '-', '@')) or cell.startswith(('\t', '\r', '\n')):
        return "'" + cell
    return cell
