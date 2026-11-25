"""Check the embedded dates against the `holidays` library (the source) and against independent
implementations (QuantLib, exchange_calendars). Each test skips if its library is not installed.

    pip install holidays==0.109 QuantLib exchange_calendars
    python -m unittest discover -s tests -v
"""
import os
import sys
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pandas_holiday_calendars._data import COVERAGE, DATES  # noqa: E402

try:
    import holidays
except ImportError:  # pragma: no cover
    holidays = None
try:
    import QuantLib as ql
except ImportError:  # pragma: no cover
    ql = None
try:
    import exchange_calendars
except ImportError:  # pragma: no cover
    exchange_calendars = None

NAMES = sorted(DATES)

# QuantLib differences we know about, with the reason. The test requires exactly these, no more, no fewer.
KNOWN_QL_DIFFS = {
    # US federal: QuantLib's Settlement calendar has Juneteenth only from 2022. OPM observed it on Friday
    # 2021-06-18 (the holiday was signed into law on 2021-06-17), so the data lists it and QuantLib does not.
    "USFederalCalendar": {"2021-06-18"},
}


def weekdays(first, last):
    d = date(first, 1, 1)
    while d.year <= last:
        if d.weekday() < 5:
            yield d
        d += timedelta(days=1)


def source(name):
    """The `holidays` library's view of the same calendar, weekdays inside coverage."""
    first, last = COVERAGE[name]
    years = range(first - 1, last + 2)
    lib = {
        "NYSECalendar": lambda: holidays.financial_holidays("XNYS", years=years),
        "FederalReserveCalendar": lambda: holidays.financial_holidays("XFED", years=years),
        "USFederalCalendar": lambda: holidays.country_holidays("US", years=years),
        "EnglandWalesCalendar": lambda: holidays.country_holidays("GB", subdiv="ENG", years=years),
        "EuroT2Calendar": lambda: holidays.financial_holidays("XECB", years=years),
    }[name]()
    return {d.isoformat() for d in lib if d.weekday() < 5 and first <= d.year <= last}


def ql_calendar(name):
    us = ql.UnitedStates
    return {
        "NYSECalendar": us(us.NYSE),
        "FederalReserveCalendar": us(us.FederalReserve),
        "USFederalCalendar": us(us.Settlement),
        "EnglandWalesCalendar": ql.UnitedKingdom(ql.UnitedKingdom.Settlement),
        "EuroT2Calendar": ql.TARGET(),
    }[name]


class Structure(unittest.TestCase):
    def test_sorted_unique_weekdays_in_coverage(self):
        for name in NAMES:
            iso = [d for d, _ in DATES[name]]
            self.assertEqual(iso, sorted(set(iso)), name)
            first, last = COVERAGE[name]
            for s in iso:
                d = date.fromisoformat(s)
                self.assertLess(d.weekday(), 5, (name, s))
                self.assertTrue(first <= d.year <= last, (name, s))

    def test_counts(self):
        self.assertEqual({n: len(DATES[n]) for n in NAMES}, {
            "NYSECalendar": 490, "FederalReserveCalendar": 506, "USFederalCalendar": 539,
            "EnglandWalesCalendar": 24, "EuroT2Calendar": 13})

    def test_known_dates(self):
        nyse = {d for d, _ in DATES["NYSECalendar"]}
        for d in ["2001-09-11", "2001-09-12", "2001-09-13", "2001-09-14", "2004-06-11", "2007-01-02",
                  "2012-10-29", "2012-10-30", "2018-12-05", "2025-01-09"]:
            self.assertIn(d, nyse)
        fed = {d for d, _ in DATES["USFederalCalendar"]}
        self.assertIn("2021-12-31", fed)
        self.assertIn("2027-12-31", fed)
        self.assertNotIn("2020-06-19", fed)  # Juneteenth is a federal holiday from 2021
        self.assertIn("2021-06-18", fed)
        self.assertFalse(any("Inauguration" in n for _, n in DATES["USFederalCalendar"]))


@unittest.skipIf(holidays is None, "holidays not installed")
class AgainstHolidaysLibrary(unittest.TestCase):
    def test_equal_to_source(self):
        for name in NAMES:
            self.assertEqual({d for d, _ in DATES[name]}, source(name), name)


@unittest.skipIf(ql is None, "QuantLib not installed")
class AgainstQuantLib(unittest.TestCase):
    def test_weekdays_agree_except_documented(self):
        for name in NAMES:
            cal = ql_calendar(name)
            ours = {d for d, _ in DATES[name]}
            diffs = set()
            for d in weekdays(*COVERAGE[name]):
                is_hol_ql = not cal.isBusinessDay(ql.Date(d.day, d.month, d.year))
                if (d.isoformat() in ours) != is_hol_ql:
                    diffs.add(d.isoformat())
            self.assertEqual(diffs, KNOWN_QL_DIFFS.get(name, set()), name)


@unittest.skipIf(exchange_calendars is None, "exchange_calendars not installed")
class AgainstExchangeCalendars(unittest.TestCase):
    def test_nyse_sessions(self):
        # 2000-01-01 and 2000-01-02 are a weekend, so the calendar's first session (2000-01-03) is no loss
        xnys = exchange_calendars.get_calendar("XNYS", start="2000-01-01", end="2050-12-31")
        sessions = {s.date().isoformat() for s in xnys.sessions}
        self.assertEqual(min(sessions), "2000-01-03")
        self.assertGreaterEqual(max(sessions), "2050-12-30")
        closed = {d.isoformat() for d in weekdays(2000, 2050)} - sessions
        self.assertEqual(closed, {d for d, _ in DATES["NYSECalendar"]})


if __name__ == "__main__":
    unittest.main()
