"""t7, Germany: how church tax and the partial exemption change the capital gains tax (rare: no local amount shows it).

The law lowers the capital gains tax rate e to e / (1 + e * k) when church tax at rate k is withheld; Neuron may have
kept e. From 2018 a share of the gain is exempt (TFS); for a half-income payout (HEV) the law halves the exemption.
"""
from decimal import Decimal as D

ONE = D(1)


def lowered_by_church_tax(rate, church):
    """e / (1 + e * k), the law, when church tax is withheld: with k = 9 % the capital gains tax falls from 25 %
    to 24.45 %, so that it and the church tax together stay near the rate without church tax."""
    return rate / (ONE + rate * church) if church else rate


def not_lowered(rate, church):
    """e, whatever the church tax: the simpler rule an old system might have kept (29 payouts would change)."""
    return rate


def halved(exempt):
    """Half the exemption: the law for half-income payouts, which are taxed on half the gain already."""
    return exempt / 2


def full_exemption(exempt):
    """The whole exemption."""
    return exempt


def no_exemption(exempt):
    """No exemption on top of the half-income rule."""
    return D(0)


KST_CHURCH = {'lowered by the church tax': lowered_by_church_tax, 'not lowered': not_lowered}
TFS_WITH_HEV = {'halved': halved, 'the full exemption': full_exemption, 'none': no_exemption}
TFS = {'the full exemption': full_exemption, 'none': no_exemption}  # of a payout taxed in full
