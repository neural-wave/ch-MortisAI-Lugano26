"""Easter Sunday, the anchor of the movable holidays in conventions_holidays."""
import datetime as dt


def easter(year):
    """Easter Sunday of `year` (Gregorian computus, Gauss's form), valid for 1900-2199.

    Easter is the first Sunday strictly after (never on) the Paschal full moon, `epact` days after
    21 March (Gauss's century correction M is 24 throughout 1900-2199). An epact of 29, or of
    28 with golden number > 10, is taken a day earlier so Easter stays on or before 25 April.
    Agrees with the Meeus/Jones/Butcher formula for every year 1900-2199.
    """
    if not 1900 <= year <= 2199:
        raise ValueError(f"easter() is only valid for 1900-2199, got {year}")
    golden = year % 19
    epact = (19 * golden + 24) % 30
    epact -= epact == 29 or (epact == 28 and golden > 10)
    full_moon = dt.date(year, 3, 21) + dt.timedelta(days=epact)
    return full_moon + dt.timedelta(days=7 - (full_moon.weekday() + 1) % 7)
