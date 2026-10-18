"""Figure for the report: exact matches of the plain Neuron NG rule per application year (t2).

    python3 vocabulary/figures/change_point.py vocabulary/results/t2_offer_plain_change_point.json out.png

The input is written by run.py (case t2_offer_plain); the figure needs matplotlib.
"""
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

curve = json.load(open(sys.argv[1]))
years, share = [int(y) for y in curve], [100 * v for v in curve.values()]
ink, muted, bar, accent = '#1d2420', '#5d6a62', '#2a7f6c', '#b3261e'
fig, ax = plt.subplots(figsize=(9, 3.6), dpi=200)
ax.bar(years, share, width=0.7, color=bar)
ax.axvline(2007 + 222 / 365, color=accent, lw=1.5)
ax.annotate('conversion COBOL → Neuron NG,\nfound by the search: 2007-08-11', xy=(2007.6, 60), xytext=(1996, 60),
            color=ink, fontsize=9, va='center', arrowprops=dict(arrowstyle='->', color=muted, lw=1))
ax.set_ylabel('exact matches, %', color=muted, fontsize=9)
ax.set_title('t2 offers: "half up, nearest age" explains every offer from August 2007 on, almost none before',
             color=ink, fontsize=10, loc='left')
ax.set_ylim(0, 105)
ax.grid(axis='y', color='#d9ded8', lw=0.6)
ax.set_axisbelow(True)
for s in ('top', 'right', 'left'):
    ax.spines[s].set_visible(False)
ax.tick_params(colors=muted, labelsize=8)
fig.tight_layout()
fig.savefig(sys.argv[2])
