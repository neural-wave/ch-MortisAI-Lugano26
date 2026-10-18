"""Helpers shared by the cases: reading target files."""
import csv
import datetime as dt
from decimal import Decimal as D
from pathlib import Path


def read(targets, name):
    """Rows of a target file as dicts of text."""
    with open(Path(targets) / f'{name}.csv', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def iso(text):
    """'2026-06-30' -> date."""
    return dt.date.fromisoformat(text)


def money(text):
    """'1234.50' -> Decimal, exact."""
    return D(text)
