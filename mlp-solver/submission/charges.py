"""The monthly charges on every monthly anniversary (t3, t4): admin fee, management charge and risk charge.

Each charge is split over the funds and pots by their value and paid by cancelling units. Every convention
is a choice of ledger.rule (T3_*), found on the ADM, AMC and RSK bookings of t3_booking.csv: the NRCHRG row
of the charge date, the admin fee at most the value, the management charge on the values before the charges,
the risk charge on those values less the two charges, the rounding rest to the largest slot but never below
zero, every amount rounded by its era. The management charge is in charges_management, the risk charge in
charges_risk.
"""
from tables import scaled
from tariff import charge_parameters
from conventions_day_count import management_charges
from charges_risk import risk_charge

ADMIN, MANAGEMENT = 2, 3  # positions in the yearly totals (t4 admin_fees, management_fees)


def monthly_charges(ledger, date, previous):
    """The three charges of the anniversary `date`; `previous` is the anniversary before it."""
    rule, values = ledger.rule, ledger.slots(date)
    if not values or rule.T3_CLOSED(ledger, date):
        return
    params = charge_parameters(ledger.folder, ledger.tariff, rule.T3_TARIFF_DAY(ledger, date))
    fee = rule.T3_ADMIN_CAP(scaled(params['CG_ADMFEE'], 2), sum(values.values()))
    admin = rule.T3_SPLIT_REST(fee, values, ledger.era(rule.T3_PIECE_ROUNDING, rule.T3_CHARGES_ERA_DATE, date), date)
    management = management_charges(ledger, date, rule.T3_MANAGEMENT_BASE(values, admin, {}, ledger, date), params,
                                     previous)
    ledger.cancel(date, ADMIN, admin)
    ledger.cancel(date, MANAGEMENT, management)
    risk_charge(ledger, date, params, rule.T3_RISK_BASE(values, admin, management, ledger, date))
