"""Execute examples/business_days_in_pandas.ipynb and check its numbers against an independent count.
Skipped if nbclient / nbformat / holidays / numpy are not installed (pip install -r examples/requirements.txt)."""
import os
import re
import unittest

try:
    import nbformat
    from nbclient import NotebookClient
except ImportError:  # pragma: no cover
    nbformat = None
try:
    import holidays
except ImportError:  # pragma: no cover
    holidays = None
import numpy as np

NB = os.path.join(os.path.dirname(__file__), "..", "examples", "business_days_in_pandas.ipynb")


@unittest.skipIf(nbformat is None, "nbclient/nbformat not installed")
@unittest.skipIf(holidays is None, "holidays not installed")
class Notebook(unittest.TestCase):
    def test_notebook_runs_and_count_matches_numpy(self):
        nb = nbformat.read(NB, as_version=4)
        NotebookClient(nb, timeout=120, kernel_name="python3").execute()
        text = ""
        for cell in nb.cells:
            if cell.cell_type != "code":
                continue
            for out in cell.get("outputs", []):
                self.assertNotEqual(out.output_type, "error", out)
                if out.output_type == "stream":
                    text += out.text
        m = re.search(r"NYSE trading days in 2027: (\d+)", text)
        self.assertIsNotNone(m, text)
        hol = [np.datetime64(d) for d in holidays.financial_holidays("XNYS", years=2027)
               if d.weekday() < 5]
        expected = int(np.busday_count("2027-01-01", "2028-01-01", holidays=hol))
        self.assertEqual(int(m.group(1)), expected)
        m2 = re.search(r"Total: (\d+)", text)
        self.assertEqual(int(m2.group(1)), expected)
        self.assertIn("ValueError", text)
        self.assertIn("2051", text)


if __name__ == "__main__":
    unittest.main()
