"""The README recipes, run as tests. Keep them in sync with README.md."""
import os
import sys
import unittest

import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CBMonthEnd, CustomBusinessDay

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from pandas_holiday_calendars import (EuroT2Calendar, NYSECalendar, USFederalCalendar,  # noqa: E402
                                      business_day, busdaycalendar, check_range)


class Readme(unittest.TestCase):
    def test_add_business_days(self):
        nyse = business_day(NYSECalendar)
        self.assertEqual(pd.Timestamp("2026-07-02") + 1 * nyse, pd.Timestamp("2026-07-06"))
        self.assertEqual(pd.Timestamp("2026-11-24") + 3 * nyse, pd.Timestamp("2026-11-30"))

    def test_count_between(self):
        bc = busdaycalendar("NYSECalendar")
        self.assertEqual(np.busday_count("2026-12-01", "2027-01-01", busdaycal=bc), 22)
        self.assertFalse(np.is_busday("2026-12-25", busdaycal=bc))
        self.assertEqual(str(np.busday_offset("2026-12-24", 1, busdaycal=bc)), "2026-12-28")

    def test_date_range(self):
        r = pd.bdate_range("2026-12-21", "2027-01-05", freq=business_day(NYSECalendar))
        self.assertEqual(list(r.strftime("%Y-%m-%d")), [
            "2026-12-21", "2026-12-22", "2026-12-23", "2026-12-24", "2026-12-28",
            "2026-12-29", "2026-12-30", "2026-12-31", "2027-01-04", "2027-01-05"])

    def test_month_end(self):
        me = pd.date_range("2026-01-01", "2026-12-31", freq=CBMonthEnd(calendar=NYSECalendar()))
        self.assertEqual(me.strftime("%Y-%m-%d").tolist(), [
            "2026-01-30", "2026-02-27", "2026-03-31", "2026-04-30", "2026-05-29", "2026-06-30",
            "2026-07-31", "2026-08-31", "2026-09-30", "2026-10-30", "2026-11-30", "2026-12-31"])

    def test_union(self):
        span = ("2026-01-01", "2028-12-31")
        both = NYSECalendar().holidays(*span).union(EuroT2Calendar().holidays(*span))
        self.assertEqual(len(both), 35)
        x, nyse = CustomBusinessDay(holidays=both), business_day(NYSECalendar)
        self.assertEqual(pd.Timestamp("2026-04-02") + 1 * nyse, pd.Timestamp("2026-04-06"))
        self.assertEqual(pd.Timestamp("2026-04-02") + 1 * x, pd.Timestamp("2026-04-07"))
        self.assertEqual(pd.Timestamp("2026-04-30") + 1 * nyse, pd.Timestamp("2026-05-01"))
        self.assertEqual(pd.Timestamp("2026-04-30") + 1 * x, pd.Timestamp("2026-05-04"))

    def test_pandas_builtin_us_federal(self):
        ours = USFederalCalendar().holidays("2000-01-01", "2050-12-31")
        theirs = USFederalHolidayCalendar().holidays("2000-01-01", "2050-12-31")
        # verified with pandas 2.2.3 and 3.1.1: same 539 dates
        self.assertEqual(len(ours), 539)
        self.assertEqual(len(theirs.symmetric_difference(ours)), 0)

    def test_coverage_warning(self):
        t2 = business_day("EuroT2Calendar")
        self.assertEqual(pd.Timestamp("2029-04-02") - 1 * t2, pd.Timestamp("2029-03-30"))
        with self.assertRaises(ValueError) as cm:
            check_range("EuroT2Calendar", "2026-01-01", "2029-06-30")
        self.assertEqual(str(cm.exception), "EuroT2Calendar covers 2026-2028; 2026-01-01..2029-06-30 is outside")


if __name__ == "__main__":
    unittest.main()
