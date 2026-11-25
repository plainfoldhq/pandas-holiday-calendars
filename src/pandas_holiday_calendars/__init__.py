"""pandas holiday calendars (NYSE, Federal Reserve, US federal, England and Wales, Euro T2) with embedded dates."""
import numpy as np
from pandas import Timestamp
from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday
from pandas.tseries.offsets import CustomBusinessDay

from ._data import COVERAGE, DATES

__version__ = "0.1.0"
__all__ = ["NYSECalendar", "FederalReserveCalendar", "USFederalCalendar", "EnglandWalesCalendar",
           "EuroT2Calendar", "COVERAGE", "business_day", "busdaycalendar", "check_range"]


def _rules(name):
    out = []
    for iso, label in DATES[name]:
        y, m, d = int(iso[:4]), int(iso[5:7]), int(iso[8:])
        out.append(Holiday(label, year=y, month=m, day=d))
    return out


def _make(name, doc):
    first, last = COVERAGE[name]
    return type(name, (AbstractHolidayCalendar,), {
        "__doc__": doc, "__module__": __name__, "rules": _rules(name),
        "start_date": Timestamp(first, 1, 1), "end_date": Timestamp(last, 12, 31)})


NYSECalendar = _make("NYSECalendar", "NYSE full-day closures 2000-2050 (early closes are not included).")
FederalReserveCalendar = _make("FederalReserveCalendar", "Federal Reserve Bank holidays 2000-2050 (weekdays only).")
USFederalCalendar = _make("USFederalCalendar", "US federal holidays as observed by OPM, 2000-2050 (no one-off executive-order closures).")
EnglandWalesCalendar = _make("EnglandWalesCalendar", "England and Wales bank holidays 2026-2028 (incl. substitute days).")
EuroT2Calendar = _make("EuroT2Calendar", "Euro T2 (TARGET2) closing days 2026-2028.")
_CALENDARS = {c.__name__: c for c in (NYSECalendar, FederalReserveCalendar, USFederalCalendar,
                                      EnglandWalesCalendar, EuroT2Calendar)}


def _cal(calendar):
    """Return a calendar instance from a class, an instance or a class name."""
    if isinstance(calendar, str):
        try:
            calendar = _CALENDARS[calendar]
        except KeyError:
            raise ValueError("unknown calendar %r, choose from %s" % (calendar, sorted(_CALENDARS))) from None
    return calendar() if isinstance(calendar, type) else calendar


def business_day(calendar):
    """A pandas CustomBusinessDay (Monday-Friday) skipping the calendar's holidays."""
    return CustomBusinessDay(calendar=_cal(calendar))


def busdaycalendar(calendar):
    """A numpy.busdaycalendar (Monday-Friday) for np.busday_count, np.is_busday, np.busday_offset."""
    hol = _cal(calendar).holidays()
    return np.busdaycalendar(holidays=hol.values.astype("datetime64[D]"))


def check_range(calendar, start, end):
    """Raise ValueError if start..end is not fully inside the calendar's covered years.

    pandas treats years without data as having no holidays, so out-of-range results are silently wrong.
    """
    cal = _cal(calendar)
    first, last = COVERAGE[type(cal).__name__]
    s, e = Timestamp(start), Timestamp(end)
    if s > e:
        s, e = e, s
    if s < Timestamp(first, 1, 1) or e > Timestamp(last, 12, 31):
        raise ValueError("%s covers %d-%d; %s..%s is outside" % (type(cal).__name__, first, last,
                                                               s.date(), e.date()))
