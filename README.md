# pandas holiday calendars: NYSE, Federal Reserve, US federal, UK, Euro T2

Five pandas `AbstractHolidayCalendar` classes whose holiday dates are an **embedded, cross-checked list**, not rules computed at runtime. They plug into `CustomBusinessDay`, `pd.bdate_range(freq="C")`, `CBMonthEnd`, `numpy.busday_count` and `pandas.tseries.holiday.get_calendar`. Runtime dependency: pandas (>=1.5) only.

| Class | Calendar | Covered years |
|---|---|---|
| `NYSECalendar` | NYSE full-day closures, incl. one-offs (2001-09-11 to 14, 2004-06-11, 2007-01-02, 2012-10-29/30, 2018-12-05, 2025-01-09). Early closes are not included | 2000-2050 |
| `FederalReserveCalendar` | Federal Reserve Bank holidays (a holiday on a Saturday gives no weekday off) | 2000-2050 |
| `USFederalCalendar` | US federal holidays as observed (Saturday to Friday, Sunday to Monday, so 2021-12-31 is the observed New Year's Day 2022); Juneteenth from 2021 | 2000-2050 |
| `EnglandWalesCalendar` | England and Wales bank holidays, incl. substitute days | 2026-2028 |
| `EuroT2Calendar` | Euro T2 (TARGET2) closing days | 2026-2028 |

Only weekday closures are listed: a holiday that falls on a Saturday or Sunday and gives no weekday off is not in the data. `USFederalCalendar` excludes one-off executive-order closures (for example the 2018-12-05 and 2025-01-09 days of mourning, which are in `NYSECalendar`) and Inauguration Day (a holiday in the Washington DC area only).

## Install

```
pip install pandas-holiday-calendars
```

## Quick start

```python
import pandas as pd
from pandas_holiday_calendars import NYSECalendar, business_day

nyse = business_day(NYSECalendar)          # a pandas CustomBusinessDay; the class or its name "NYSECalendar" both work
pd.Timestamp("2026-07-02") + 1 * nyse      # Timestamp('2026-07-06'): 2026-07-03 is Independence Day (observed)
```

Helpers: `business_day(cal)` returns a `CustomBusinessDay`; `busdaycalendar(cal)` returns a `numpy.busdaycalendar`; `check_range(cal, start, end)` raises `ValueError` outside the covered years; `COVERAGE` maps each class name to `(first_year, last_year)`. `cal` is the class, an instance or its name string.

## Recipes

All snippets below are run as tests in `tests/test_readme.py`.

### Add N business days

```python
from pandas_holiday_calendars import NYSECalendar, business_day
nyse = business_day(NYSECalendar)
pd.Timestamp("2026-11-24") + 3 * nyse      # Timestamp('2026-11-30'): Thanksgiving is 2026-11-26
pd.Timestamp("2026-07-06") - 1 * nyse      # Timestamp('2026-07-02')
```

### Business days between two dates (numpy)

```python
import numpy as np
from pandas_holiday_calendars import busdaycalendar
bc = busdaycalendar("NYSECalendar")
np.busday_count("2026-12-01", "2027-01-01", busdaycal=bc)   # 22
np.is_busday("2026-12-25", busdaycal=bc)                    # False
np.busday_offset("2026-12-24", 1, busdaycal=bc)             # numpy.datetime64('2026-12-28')
```

`busday_count` counts the start date and excludes the end date.

### Business-day date range

```python
pd.bdate_range("2026-12-21", "2027-01-05", freq=nyse)
# 2026-12-21 22 23 24, 2026-12-28 29 30 31, 2027-01-04 05  (10 days)
```

### Last business day of the month

```python
from pandas.tseries.offsets import CBMonthEnd
pd.date_range("2026-01-01", "2026-12-31", freq=CBMonthEnd(calendar=NYSECalendar()))
# 2026-01-30, 02-27, 03-31, 04-30, 05-29, 06-30, 07-31, 08-31, 09-30, 10-30, 11-30, 12-31
```

### Holiday names

```python
NYSECalendar().holidays("2026-01-01", "2026-12-31", return_name=True)
# 2026-04-03    Good Friday
# 2026-07-03    Independence Day (observed)
# ... (10 closures in 2026)
NYSECalendar().holidays()          # no arguments: the whole covered range, 2000-2050 (490 dates)
```

### Look a calendar up by name

```python
from pandas.tseries.holiday import get_calendar
get_calendar("EuroT2Calendar")     # importing the package registers all five classes
```

### Combine two calendars (a settlement day open in both markets)

```python
from pandas.tseries.offsets import CustomBusinessDay
from pandas_holiday_calendars import EuroT2Calendar
span = ("2026-01-01", "2028-12-31")          # the range both calendars cover
both = NYSECalendar().holidays(*span).union(EuroT2Calendar().holidays(*span))   # 35 dates
cross = CustomBusinessDay(holidays=both)
pd.Timestamp("2026-04-02") + 1 * business_day(NYSECalendar)   # 2026-04-06 (NYSE closed Good Friday)
pd.Timestamp("2026-04-02") + 1 * cross                        # 2026-04-07 (T2 also closed Easter Monday)
pd.Timestamp("2026-04-30") + 1 * cross                        # 2026-05-04 (T2 closed 2026-05-01)
```

## Why not pandas' built-in `USFederalHolidayCalendar`?

pandas ships a rule-based `USFederalHolidayCalendar` only for US federal holidays; there is no NYSE, Federal Reserve, UK or T2 calendar in pandas. We compared `USFederalCalendar` with pandas' `USFederalHolidayCalendar` for 2000-2050: **0 differences, 539 identical dates**, checked with pandas 2.2.3 and 3.1.1. So for US federal holidays the choice is not about different dates. What this package adds: the same interface for the other four calendars, holiday names for every date, a fixed list that does not change when a pandas release changes its rules, and `check_range`.

## Warning: dates outside the covered years

pandas treats a year with no holiday data as a year **without holidays**. It does not warn. For example, Good Friday 2029-03-30 is a T2 closing day, but `EuroT2Calendar` stops at 2028:

```python
pd.Timestamp("2029-04-02") - 1 * business_day("EuroT2Calendar")   # Timestamp('2029-03-30'): wrong, that day is a T2 holiday
```

Guard your date range:

```python
from pandas_holiday_calendars import check_range
check_range("EuroT2Calendar", "2026-01-01", "2029-06-30")
# ValueError: EuroT2Calendar covers 2026-2028; 2026-01-01..2029-06-30 is outside
```

`check_range` returns `None` when the whole range is covered.

## Data sources and testing

The dates are generated by `scripts/generate.py` (in the GitHub repo, not shipped in the wheel) from the [`holidays`](https://github.com/vacanza/holidays) library (MIT), version 0.109, and stored in `_data.py`. The test suite (`python -m unittest discover -s tests -v`, run in CI on Python 3.12 with pandas 2.2.* and the latest pandas) checks:

- every list equals the `holidays` library output again for the same years (weekdays only);
- every weekday in the covered years against [QuantLib](https://www.quantlib.org/), an independent implementation: `UnitedStates(NYSE)` for NYSE, `UnitedStates(FederalReserve)` for the Federal Reserve, `UnitedStates(Settlement)` for US federal, `UnitedKingdom(Settlement)` for England and Wales, `TARGET()` for T2. NYSE, Federal Reserve, England and Wales and T2 agree on every weekday. US federal has one known difference, 2021-06-18: the data lists Juneteenth observed on that Friday and QuantLib's calendar does not have Juneteenth before 2022. The test requires exactly that one difference;
- NYSE closures 2000-2050 against the [exchange_calendars](https://github.com/gerrymanoim/exchange_calendars) `XNYS` sessions: identical;
- the pandas, numpy and `get_calendar` integration, and the recipes above.

| Class | Dates in data |
|---|---|
| `NYSECalendar` | 490 |
| `FederalReserveCalendar` | 506 |
| `USFederalCalendar` | 539 |
| `EnglandWalesCalendar` | 24 |
| `EuroT2Calendar` | 13 |

Holiday calendars are republished by authorities and can change. Check the official source for anything where a wrong date has a cost; this is not legal or financial advice.

## Free reference data and sibling packages

- Free business-day reference site: https://plainfoldhq.github.io/business-days/
- Free holiday lists for Excel and CSV: https://plainfoldhq.github.io/excel-holiday-lists/
- `usbizdays`, US business-day helpers: https://pypi.org/project/usbizdays/
- `exchange-trading-days`: https://pypi.org/project/exchange-trading-days/
- `fx-spot-dates`, FX settlement holidays and spot dates: https://pypi.org/project/fx-spot-dates/
- The same calendars in Go: https://github.com/plainfoldhq/go-holiday-calendars

## Need other years or countries?

These are paid products by Plainfold:

- World Public Holidays 2000-2050 (156 countries + 60 subdivisions): https://buy.polar.sh/polar_cl_GyNejNT1XIOvB0AyazglLeeinrcYHfdmPngZm1qqqg0?utm_source=readme&utm_medium=readme&utm_campaign=H&utm_content=pandas-holiday-calendars
- World Stock Exchange Holidays + Trading Hours 2000-2050 (24 exchanges): https://buy.polar.sh/polar_cl_8VwWMpQhsLCYXsPRdkmYGjbJzuzlHQB9Ul3GC3dlJW7?utm_source=readme&utm_medium=readme&utm_campaign=G&utm_content=pandas-holiday-calendars
- Currency Settlement Holidays + FX Spot Dates 2000-2050 (T2 and 5 more currencies): https://buy.polar.sh/polar_cl_9Rkaup8QpzW7cYaFe9nRx0AEiUSxVLMzYyU1K23uuVP?utm_source=readme&utm_medium=readme&utm_campaign=Q&utm_content=pandas-holiday-calendars

## License

Code: MIT (see LICENSE). Holiday data is derived from the `holidays` library (MIT) and checked against QuantLib. Source and issues: https://github.com/plainfoldhq/pandas-holiday-calendars. Contact: plainfoldhq@proton.me. Brand: Plainfold.
