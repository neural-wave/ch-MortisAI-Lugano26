"""Neuron migration: one entry point per task. Everything is calculated from the files in legacy_dir."""
from commission import commissions
from schedule import due_dates
from projection import projections
from accounts import surrender_values, statements
from ledger import EXTRACT_DATE
from outliers import outliers
from tax_payout import payout_taxes
from tax_annual import annual_taxes
from eras import adopt


def t0_commission(legacy_dir):
    """{(policy, due nr): commission}"""
    adopt(legacy_dir)
    return commissions(legacy_dir)


def t1_next_due_dates(legacy_dir, extract_date):
    """{(policy, n): (due date, collection date)} of the year after the extract date"""
    adopt(legacy_dir)
    return due_dates(legacy_dir, extract_date)


def t2_projected_maturity_value(legacy_dir):
    """{policy: projected maturity value of the offer}"""
    adopt(legacy_dir)
    return projections(legacy_dir)[0]


def t3_surrender_value(legacy_dir, valuation_dates):
    """{(policy, valuation date): surrender value}"""
    adopt(legacy_dir)
    return surrender_values(legacy_dir, valuation_dates)


def t4_annual_statement(legacy_dir):
    """{(policy, year): (premiums, entry, admin, management, risk, total charges)}"""
    adopt(legacy_dir)
    return statements(legacy_dir)


def t5_outlier_detection(legacy_dir, targets_dir):
    """{(task, key)} of the values that were changed by hand"""
    adopt(legacy_dir)
    tasks = {'t0_commission': t0_commission, 't1_next_due_dates': t1_next_due_dates,
             't2_projected_maturity_value': t2_projected_maturity_value,
             't3_surrender_value': t3_surrender_value, 't4_annual_statement': t4_annual_statement}
    return outliers(tasks, legacy_dir, targets_dir, EXTRACT_DATE)


def t7_tax_payout(legacy_dir):
    """{(policy, event): (country, taxable base, withholding, surcharges, stamp duty, remittance date)}"""
    adopt(legacy_dir)
    return payout_taxes(legacy_dir)


def t7_tax_annual(legacy_dir):
    """{(policy, year): (ch_stp, ch_vst, it_sos, it_bol, de_kst, de_sol, de_kis)}, years with an amount only"""
    adopt(legacy_dir)
    return annual_taxes(legacy_dir)
