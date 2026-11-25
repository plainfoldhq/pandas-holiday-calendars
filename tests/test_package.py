"""pandas integration of the package."""
import os
import sys
import unittest

import numpy as np
import pandas as pd
from pandas.tseries.holiday import get_calendar
from pandas.tseries.offsets import CustomBusinessDay

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import pandas_holiday_calendars as phc  # noqa: E402
from pandas_holiday_calendars import (COVERAGE, EnglandWalesCalendar, EuroT2Calendar, NYSECalendar,  # noqa: E402
                                      business_day, busdaycalendar, check_range)
from pandas_holiday_calendars._data import DATES  # noqa: E402


class Pandas(unittest.TestCase):
    def test_default_range_is_coverage(self):
        for name, (first, last) in COVERAGE.items():
            h = getattr(phc, name)().holidays()
            self.assertEqual(len(h), len(DATES[name]), name)
            self.assertEqual(h[0].year >= first and h[-1].year <= last, True, name)
            self.assertEqual([d.strftime("%Y-%m-%d") for d in h], [d for d, _ in DATES[name]], name)

    def test_add_business_days(self):
        nyse = business_day(NYSECalendar)
        self.assertIsInstance(nyse, CustomBusinessDay)
        self.assertEqual(pd.Timestamp("2026-07-02") + 1 * nyse, pd.Timestamp("2026-07-06"))
        self.assertEqual(pd.Timestamp("2026-07-06") - 1 * nyse, pd.Timestamp("2026-07-02"))
        self.assertEqual(pd.Timestamp("2026-11-24") + 3 * nyse, pd.Timestamp("2026-11-30"))
        self.assertEqual(pd.Timestamp("2021-12-30") + 1 * business_day("USFederalCalendar"), pd.Timestamp("2022-01-03"))

    def test_bdate_range_equals_busday_count(self):
        for name, (first, last) in COVERAGE.items():
            bd, bc = business_day(name), busdaycalendar(name)
            start, end = "%d-01-01" % first, "%d-12-31" % last
            rng = pd.bdate_range(start, end, freq=bd)
            self.assertEqual(len(rng), np.busday_count(start, "%d-01-01" % (last + 1), busdaycal=bc), name)
            self.assertFalse(set(rng) & set(getattr(phc, name)().holidays()), name)

    def test_get_calendar_by_name(self):
        for name in COVERAGE:
            self.assertIsInstance(get_calendar(name), getattr(phc, name))

    def test_return_name(self):
        s = NYSECalendar().holidays("2026-01-01", "2026-12-31", return_name=True)
        self.assertEqual(s[pd.Timestamp("2026-04-03")], "Good Friday")
        self.assertEqual(s[pd.Timestamp("2026-07-03")], "Independence Day (observed)")
        self.assertEqual(len(s), 10)
        s = NYSECalendar().holidays("2001-09-10", "2001-09-15", return_name=True)
        self.assertEqual(list(s.index.strftime("%Y-%m-%d")), ["2001-09-11", "2001-09-12", "2001-09-13", "2001-09-14"])

    def test_calendar_instances_and_names(self):
        a, b, c = business_day("EuroT2Calendar"), business_day(EuroT2Calendar), business_day(EuroT2Calendar())
        self.assertEqual(a, b)
        self.assertEqual(b, c)
        with self.assertRaises(ValueError):
            business_day("NoSuchCalendar")

    def test_check_range(self):
        check_range("NYSECalendar", "2000-01-01", "2050-12-31")
        check_range(EnglandWalesCalendar, "2026-01-01", "2028-12-31")
        for bad in [("1999-12-31", "2001-01-01"), ("2020-01-01", "2051-01-01")]:
            with self.assertRaises(ValueError):
                check_range("NYSECalendar", *bad)
        with self.assertRaises(ValueError):
            check_range("EuroT2Calendar", "2026-01-01", "2029-06-30")

    def test_out_of_coverage_is_silent_in_pandas(self):
        # why check_range exists: Good Friday 2029-03-30 is simply treated as a business day
        self.assertEqual(pd.Timestamp("2029-04-02") - 1 * business_day("EuroT2Calendar"), pd.Timestamp("2029-03-30"))

    def test_speed(self):
        import time
        t = time.time()
        pd.bdate_range("2026-01-01", periods=1000, freq=business_day(NYSECalendar))
        self.assertLess(time.time() - t, 1.0)


if __name__ == "__main__":
    unittest.main()
