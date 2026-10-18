# t7 findings (Sat 17 Oct, 21:20)

What the research on t7 had found by then; the choices made since, and their evidence, are in `my_solution/README.md`
(t7), `logs/t7_evidence.json` and `logs/t7_leaderboard.md`. Every number is an aggregate count from the code run on
the legacy data.

**Status:** upload **#41** reaches payout **11/20**, annual **15/20**, and 90.00 % overall (t0–t4 at 100 %). It was at
1/20 before. That jump came from writing the remittance date as `""` instead of `None` when nothing was withheld; the
server's scorer had dropped every untaxed row as malformed. #41 also set the Swiss untaxed base back to the payout in
CHF. According to #41's `rules.py`, the leaderboard has used **the same 20 sample rows** for the last evaluations, and
about 14 of the 20 are untaxed. So: about 10 of 14 untaxed rows pass now, and about 5 of 6 taxed rows still fail.

---

## A. Confirmed by local evidence

### A1. Neuron taxed the amount actually paid out, after the surrender penalty (high confidence)
- **What:** for withdrawals (400) and surrenders (410), the payout is `sum(BK_AMTPC) × (1 − penalty rate)`.
  - The rate comes from NRSURR via `PD_SRPSCL` of the product and the completed policy years since `PH_BEGDT`, measured at
    `EV_EFFDT`.
  - It is 0 inside an NRWAIV waiver period and for death claims (500).
  - Every upload so far, #41 included, uses the gross `sum(BK_AMTPC)`, which is the value of the units sold **before**
    the penalty.
- **Why we believe it:** NRTAXB records whether Neuron booked a tax, though not the amount, so we can test whether a rule
  predicts the bookings that exist. Counts only:

  | Rule | Gross amount (current) | Net of penalty |
  |---|---|---|
  | CH VST (status E, payout > CHF 5000) | 2 disagreements | **0** (386 of 386 agree) |
  | IT SOS (gain > 0, not death) | 5 | **0** (393 of 393) |
  | DE KST (gain > 0, regime 'full') | 6 | **3** (the rest are DE regime issues) |

  The "Neuron mistakes" in the team's code comments (257/259, 153/158, 86/92) are mostly this penalty. The net rule
  creates no new contradiction. The 2006 DE example from the PDF had no penalty, so it agrees either way.
- **Impact:** 750 of 2,493 payouts carry a penalty: 397 withdrawals, 334 surrenders and 19 deaths (no penalty is
  applied to deaths). Under #41 the switch changes about 555 payout rows:
  - CH untaxed: 450
  - CH taxed: 44
  - IT taxed: 44
  - DE: 14

  The base, withholding, stamp duty and threshold decisions all change.
- **Change:** a new `rules.py` choice `T7_PAYOUT_AMOUNT = after_penalty`. In `tax_payouts.payouts` (bundled), set
  `amount = rounded(paid × (1 − rate), day)` for kinds 400 and 410. Use the **same expression as
  `accounts_surrender.surrender_value`**, which is proven on t3. The two rounding forms, `round(v×(1−r))` and
  `v − round(v×r)`, differ on 175 payouts. Verify by re-running the presence test; it must give CH 0, IT 0, DE 3.

### A2. 97 Italian payout rows have a base with fractions of a cent, so they can never match (high confidence)
- **What:** in `tax_gain.gains`, a withdrawal's share of the premium basis (`still_open × share`) is never rounded and is
  carried into later payouts. `tax_italy` returns `max(profit, 0)` without rounding it.
- **Evidence:** a check of the answer format (counts only) reported `taxable_base_not_cents: 97`. All 97 are Italian:
  78 withdrawals, plus 19 surrenders that follow an earlier withdrawal. That is about 60 % of the Italian rows with a
  positive base. CH, DE and LU have none.
- **Change:** round the basis share to the cent at each withdrawal, carry the rounded value, and round the final base.
  The choice between "round the basis" and "round the gain once" changes only about 10 rows. Use the first.
  `tests/test_t7.py` checks it now (no amount with a fraction of a cent).

### A3. Conventions now backed by data: keep them, and don't spend uploads on them
- The payout converts at the rate of `EV_EFFDT`, the last rate on or before that day, weekends included.
- Each premium converts at its own money-date rate and is rounded on its own.
- The gain for IT and DE is computed in EUR.
- Premiums are the received amounts, and premiums paid back by earlier payouts are carried forward.
- Gross is the sum of the booked amounts per booking.

These rest on the DE example (only 8 of 3,456 variants hit 5628.16, and all of them share these choices), on the ledger
(3,675 of 3,675 FX rates reproduced) and on the presence test.

Also immaterial for payouts:
- **Rounding day:** `EV_CHGTS` always falls on the `EV_EFFDT` day.
- **Residence "known today" vs "known at processing":** changes 4 rows.
- **The set of payout keys:** all 2,493 are emitted, none is missing.
- **Country:** agrees with the country implied by the bookings on 668 of 680 taxed payouts. The 12 exceptions are stamp
  duty collected (BOC) from holders who left Italy, which the code already explains.

---

## B. Strong hypotheses: test them with uploads (each probe touches only its own rows)

### B1. Italian stamp duty base = the surrender value at 31.12, not the policy value (medium, annual)
- **Why:** Italian law taxes the redemption value, and A1 shows Neuron's tax module already applies the penalty.
- **Arithmetic:** switching changes 1,517 of 6,381 annual rows (23.8 %, all in `it_bol`). If everything else were right,
  annual would be 76.2 %, close to the observed 75 % (15/20). The rival explanation is that all payout-year, STP and
  TAXFIX19 rows are wrong; it fits about as well, so this needs a probe.
- **Probe:** flip only `T7_BOL_VALUE = the_surrender_value`. Annual going up toward 19 or 20 confirms it; going down
  toward about 11 refutes it. It also changes 163 payout BOC rows.

### B2. Remittance date of taxed rows (medium, the main suspect for the about 5 failing taxed rows)
- Only DE's "10th of the next month" has evidence (the PDF example falls on a Thursday, so it doesn't settle a weekend
  rule). CH "30 days after month end" and IT "16th of next month" are legal guesses.
- **The bookings contain nothing about remittance.** All 1,000 payout tax bookings have `TB_EFFDT = EV_EFFDT` and the
  payout's `EV_CHGTS`. The idea that remittance follows a later payment date (`PD_PAYDAY`) gets no support from the
  bookings.
- **Candidates:**
  - one Neuron batch rule for all countries, the 10th of the next month (changes 590 rows: CH 255, IT 321, ...)
  - a weekend shift to the next Ticino business day (208 rows) or the next weekday (201)
  - CH = payout day + 30 days
- **Probe:** change it only in the taxed CH and IT rows. It can ride with an untaxed-row change in the same upload.

### B3. Rows where only Italian stamp duty was collected should get "no remittance" (low)
- The PDF says "None if nothing was **withheld**". BOC is collected, not withheld. The code currently gives these rows a
  remittance date.
- Switching changes 182 rows, 168 of them Italian BOC-only.
- It overlaps the IT remittance probe, so don't run both in one upload.

### B4. Base of untaxed rows outside Switzerland = the signed gain (low to medium)
- **What:** for LU, and for IT and DE rows with a loss, use the gain without the floor at zero (in EUR; for DE multiply
  by the taxable share). The code gives 0 today, and LU always gets 0.
- **Impact:** changes 577 non-Swiss rows.
- **Probe:** apply it only to non-Swiss untaxed rows, so a jump can be attributed. The Swiss untaxed base (payout in CHF)
  works in #41, so keep it, now net of penalty per A1.

### B5. Death claims (low, 75 rows)
- The DTH booking is the unit value. Whether the tax module used that or the guaranteed benefit (RK_SUMIN, option
  A/B/C) is untested; they differ for 52 of 75. Probe only if a death claim is among the sampled rows.

### B6. Smaller open items, to try only if a sampled failing row is of that type
- **Premium amount:** `PR_AMTRC` vs `PR_AMTDU`. Changes cents on 854 events; flips 1 sign.
- **Rounding era of a COBOL-era premium inside an NG-era payout:** the payout's era vs the premium's. About 73 IT/DE rows
  with a gain.
- **Pre-1999 premiums converted to EUR:** at the first EUR rate. About 66 IT/DE rows with a gain.
- **DE partial exemption (TFS) by fund asset class:** `NRFUND.FD_ASSCL`. At most 35 DE rows from 2018.
- **BOC on a withdrawal:** the withdrawn share vs everything. 167 rows.
