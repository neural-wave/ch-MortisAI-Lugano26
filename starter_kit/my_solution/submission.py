"""Submission stub of the Neuron migration challenge.

Each function gets the folder `legacy_dir` with the NR*.csv files and returns the calculated values.
Dates are `datetime.date`, amounts are `decimal.Decimal`. A missing function scores 0 for its task.
Your code must calculate every value from `legacy_dir`: do not read the target files and do not embed values.

Check your solution locally against the train targets with `python check.py`.
"""
import csv
import datetime as dt
import functools
import pathlib
from decimal import ROUND_HALF_UP, Decimal


@functools.cache
def table(legacy_dir, name):
    """All rows of a legacy table as dicts (`;`-separated, see SCHEMA.md)."""
    with open(pathlib.Path(legacy_dir) / f"{name}.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))


def day(n):
    """Legacy date CYYMMDD (`1250131` = 2025-01-31, `970630` = 1997-06-30)."""
    n = int(n)
    return dt.date(1900 + n // 10000, n // 100 % 100, n % 100)


def scale(value, decimals):
    """Legacy integer with implied decimals -> Decimal (`N(2)`: 18500 -> 185.00)."""
    return Decimal(int(value)).scaleb(-decimals)


def valid_on(rows, d, start, end):
    """Rows whose validity period [start, end] contains the legacy date `d`; the caller picks among them."""
    return [r for r in rows if int(r[start]) <= d <= int(r[end])]


@functools.cache
def by_key(legacy_dir, name, key):
    """Rows of a table grouped by the (trimmed) value of column `key`."""
    groups = {}
    for row in table(legacy_dir, name):
        groups.setdefault(row[key].strip(), []).append(row)
    return groups


def broker_tier(legacy_dir, policy, d):
    """Tier of the broker who held the policy on legacy date `d` (highest valid version wins)."""
    versions = valid_on(by_key(legacy_dir, "NRPOLH", "PH_POLNR")[policy], d, "PH_VLDFR", "PH_VLDTO")
    broker = max(versions, key=lambda r: int(r["PH_VRSNR"]))["PH_BRKNR"]
    return by_key(legacy_dir, "NRBROK", "BR_BRKNR")[broker.strip()][0]["BR_TIER"]


def t0_commission(legacy_dir) -> dict[tuple[str, int], Decimal]:
    """{(policy_id, due_nr): commission}

    Rule: every paid item (state P) earns `amount received * rate`. The rate comes from NRCOMR by the tier of the
    broker on the money date and by the premium type (6th char of the tariff key: L regular, E single).
    """
    rates = by_key(legacy_dir, "NRCOMR", "CR_TIER")
    result = {}
    for item in table(legacy_dir, "NRPREM"):
        if item["PR_STATE"] != "P":
            continue
        policy, received = item["PR_POLNR"].strip(), int(item["PR_RCVDT"])
        premium_type = by_key(legacy_dir, "NRRISK", "RK_POLNR")[policy][0]["RK_TARKEY"][5]
        tier = broker_tier(legacy_dir, policy, received)
        rate = next(r for r in valid_on(rates[tier], received, "CR_VLDFR", "CR_VLDTO") if r["CR_PAYTP"] == premium_type)
        amount = scale(item["PR_AMTRC"], 2) * scale(rate["CR_RATE"], 6)
        result[(policy, int(item["PR_DUENR"]))] = amount.quantize(Decimal("0.01"), ROUND_HALF_UP)
    return result


def t1_next_due_dates(legacy_dir, extract_date: dt.date) -> dict[tuple[str, int], tuple[dt.date, dt.date]]:
    """{(policy_id, n): (due_date, collection_date)} for the due dates after `extract_date`, n = 1, 2, ..."""
    return {}


def t2_projected_maturity_value(legacy_dir) -> dict[str, Decimal]:
    """{policy_id: maturity_value}"""
    return {}


def t3_surrender_value(legacy_dir, valuation_dates: list[dt.date]) -> dict[tuple[str, dt.date], Decimal]:
    """{(policy_id, valuation_date): surrender_value}"""
    return {}


def t4_annual_statement(legacy_dir) -> dict[tuple[str, int], tuple[Decimal, ...]]:
    """{(policy_id, year): (premiums, entry_charges, admin_fees, management_fees, risk_charges, total_charges)}"""
    return {}


def t5_outlier_detection(legacy_dir, targets_dir) -> set[tuple[str, object]]:
    """{(task, key)} of the values that were changed by hand.

    `targets_dir` holds the target files (t0 to t4) of the policies to check, in the format of `targets/`. This is
    the only function that may read target files. Example keys: ("t2_projected_maturity_value", "BL10000042"),
    ("t4_annual_statement", ("BL10000042", 2021)).
    """
    return set()
