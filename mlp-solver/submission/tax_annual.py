"""t7_tax_annual: per policy and calendar year the taxes Neuron withheld, accrued or reported.

The taxes of the payouts count in the year of the payout, the Swiss stamp duty on premiums in the year of its booking
(tax_premium_stamp), the Italian stamp duty on the value in the year of its effective date (tax_stamp). Reported
withholding tax (holders with status M) is added as rules.py T7_REPORTED_VST says (tax_reported).
"""
import rules
from guard import per_policy
from tax_payout import payout_details
from tax_times import policies
from tax_premium_stamp import stamp_duties
from tax_stamp import yearly
from tax_premium_stamp import reported_vst
from tax_annual_table import empty_table, put


def annual_taxes(folder):
    """{(policy, year): (ch_stp, ch_vst, it_sos, it_bol, de_kst, de_sol, de_kis)}."""
    table, details = empty_table(), payout_details(folder)
    for (pid, _), (payout, detail_country, _, amounts, _) in details.items():
        for kind in ('VST', 'SOS', 'KST', 'SOL', 'KIS'):
            put(table, pid, rules.T7_ANNUAL_YEAR(payout, detail_country), kind, amounts.get(kind, 0))
    duties = per_policy('t7_tax_annual', policies(folder).items(), lambda pid, head: {pid: {
        'STP': stamp_duties(folder, pid, head['PH_CCY']), 'BOL': yearly(folder, pid, head['PH_CCY'])}})
    for pid, kinds in duties.items():
        for kind, years in kinds.items():
            for year, amount in years.items():
                put(table, pid, year, kind, amount)
    found = {key: tuple(cells) for key, cells in table.items() if any(cells)}
    return rules.T7_REPORTED_VST(found, reported_vst(folder, details))
