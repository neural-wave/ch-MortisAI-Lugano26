"""The fund accounting of one policy: premiums buy units, charges cancel units, customer orders move units.

The rates valid on a date are in ledger_rates.py, the pot and fund shares of a premium in ledger_terms.py,
the investment of premiums in ledger_premium.py, the conversion of amounts to units in ledger_units.py,
the valuation in ledger_value.py, the calendar in ledger_dates.py, the day-by-day replay in ledger_run.py
and the monthly charges in charges.py.
"""
from collections import defaultdict
from decimal import Decimal as D
from tables import grouped, day
from eras import birth_date, entry_age, by_era, ERA_AGE, ERA_DATE
from tariff import parameters
from market import market
from conventions_fx_dates import agreed
from ledger_cancel import cancel_units
from ledger_value import fund_values, policy_value
from ledger_dates import EXTRACT_DATE, last_year  # EXTRACT_DATE is imported from here by submission.py
from ledger_run import replay


def zero_totals():
    """Yearly totals: premiums, entry charges, admin fees, management charges, risk charges."""
    return [D(0), D(0), D(0), D(0), D(0)]


class Ledger:
    """Units per (fund, pot) and the yearly totals of premiums and charges of one policy.

    The start, maturity and currency come from the original policy version (lowest PH_VRSNR);
    the state and the broker are read from the version valid on each date, as they can change.
    The tariff key RK_TARKEY (NRRISK) selects the charges (NRCHRG) and the risk parameters.
    """

    def __init__(self, folder, pid, rule):
        self.folder, self.rule = folder, rule  # rule: the rules module, or a trial of choices in the search
        self.history = grouped(folder, 'NRPOLH', 'PH_POLNR')[pid]
        original = min(self.history, key=lambda r: int(r['PH_VRSNR']))
        self.start, self.end, self.ccy = day(original['PH_BEGDT']), day(original['PH_ENDDT']), original['PH_CCY']
        # Only the main risk (RK_RSKNR 1) of NRRISK is charged; brokers map to their commission tier,
        # which sets the entry rate, and mortality holds the qx of NRMORT by table, sex and age.
        risks, persons, self.brokers, self.mortality = parameters(folder)
        self.risk, self.tariff = risks[pid], risks[pid]['RK_TARKEY']
        self.person = persons[self.risk['RK_PERNR']]
        # The entry age follows the system that wrote the offer: the one live on ERA_DATE (the application date).
        self.applied, self.birth = day(original['PH_APPDT']), birth_date(self.person['PS_BIRTH'])
        offer = ERA_DATE(original)
        self.age, self.age_rule = entry_age(self.birth, self.start, offer), by_era(ERA_AGE, offer)
        self.product = grouped(folder, 'NRPROD', 'PD_PRDCD')[original['PH_PRDCD']][0]
        self.market = market(folder)
        self.allocations = grouped(folder, 'NRALLO', 'AL_POLNR')[pid]
        self.agreements = grouped(folder, 'NRAGRE', 'AG_POLNR')[pid]
        # Units per (fund, pot); every booking adds or removes units rounded to 6 decimals, so the
        # holdings need no further rounding (t3_holding.csv shows them on the valuation dates).
        self.units = defaultdict(lambda: D(0))
        self.annual = defaultdict(zero_totals)

    def era(self, pair, which, date, money=None):
        """The rule of `pair` (COBOL, Neuron NG) for the system live on the day `which` of the calculation on
        `date` names (a *_ERA_DATE of rules.py, conventions_era_date)."""
        return pair[1] if which(date, self, money) >= self.rule.ERA_CUTOFF else pair[0]

    # The methods are module functions bound directly, without a wrapper: the charges call slots,
    # cancel and agreed several times in every policy month, and a second call layer shows in t3's run time.
    agreed = agreed  # agreed(kind, date, default): an ENT or AMC agreement in force replaces the tariff rate
    slots = fund_values  # slots(date): {(fund, pot): value in policy currency}, the base of every charge
    cancel = cancel_units  # cancel(date, kind, amounts): pay a charge by cancelling units of each slot
    value = policy_value  # value(date): the surrender value before penalty, 0 once surrendered or claimed
    last_year = last_year  # last_year(): the last statement year (t4), the year of closing or 2025
    run = replay  # run(premiums, orders, dates): replay the policy, {valuation date: policy value}
