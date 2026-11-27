"""Run with:  python -m unittest"""

import os
import tempfile
import unittest

from group import Group
from settlement import settle
from splitting import split_expense, to_cents


class SplittingTests(unittest.TestCase):
    def test_to_cents(self):
        self.assertEqual(to_cents("12.50"), 1250)
        self.assertEqual(to_cents("999999999.99"), 99999999999)

    def test_to_cents_rejects_bad_input(self):
        for bad in ["", "abc", "-1", "1.005", "nan", "inf", None]:
            with self.assertRaises(ValueError):
                to_cents(bad)

    def test_equal_split_keeps_every_cent(self):
        result = split_expense(1000, "equal", {"A": 0, "B": 0, "C": 0})
        self.assertEqual(result, {"A": 334, "B": 333, "C": 333})

    def test_exact_split(self):
        result = split_expense(1000, "exact", {"A": "7.50", "B": "2.50"})
        self.assertEqual(result, {"A": 750, "B": 250})

    def test_exact_split_must_match_total(self):
        with self.assertRaises(ValueError):
            split_expense(1000, "exact", {"A": "7", "B": "2"})

    def test_percent_split(self):
        result = split_expense(1001, "percent", {"A": "50", "B": "30", "C": "20"})
        self.assertEqual(result, {"A": 501, "B": 300, "C": 200})

    def test_percent_must_total_100(self):
        with self.assertRaises(ValueError):
            split_expense(1000, "percent", {"A": "50", "B": "40"})

    def test_shares_split(self):
        result = split_expense(101, "shares", {"A": "0", "B": "2", "C": "1"})
        self.assertEqual(result, {"A": 0, "B": 68, "C": 33})


class SettlementTests(unittest.TestCase):
    def check_all_paid(self, balances, payments):
        remaining = dict(balances)
        for debtor, creditor, amount in payments:
            self.assertGreater(amount, 0)
            remaining[debtor] += amount
            remaining[creditor] -= amount
        for balance in remaining.values():
            self.assertEqual(balance, 0)

    def test_nothing_to_settle(self):
        self.assertEqual(settle({"A": 0, "B": 0}), ([], True))

    def test_finds_fewest_payments(self):
        # Greedy alone needs 5 payments. Two zero-sum groups only need 4.
        balances = {"A": 900, "B": 800, "C": -500, "D": -400, "E": -700, "F": -100}
        payments, is_minimum = settle(balances)
        self.assertTrue(is_minimum)
        self.assertEqual(len(payments), 4)
        self.check_all_paid(balances, payments)

    def test_large_group(self):
        balances = {f"P{i}": 100 for i in range(10)}
        balances.update({f"Q{i}": -50 for i in range(20)})
        payments, is_minimum = settle(balances)
        self.assertFalse(is_minimum)
        self.check_all_paid(balances, payments)


class GroupTests(unittest.TestCase):
    def setUp(self):
        self.group = Group()
        self.group.add_member("Ana")
        self.group.add_member("Ben")

    def test_balances(self):
        self.group.add_expense("Taxi", "10", "Ana", "equal", {"Ana": 0, "Ben": 0})
        self.assertEqual(self.group.totals()["Ana"]["balance"], 500)
        self.assertEqual(self.group.totals()["Ben"]["balance"], -500)

    def test_duplicate_name(self):
        with self.assertRaises(ValueError):
            self.group.add_member("ana")

    def test_cannot_remove_person_with_expenses(self):
        self.group.add_expense("Taxi", "10", "Ana", "equal", {"Ben": 0})
        with self.assertRaises(ValueError):
            self.group.remove_member("Ben")
        self.group.remove_expense(1)
        self.group.remove_member("Ben")
        self.assertEqual(self.group.members, ["Ana"])

    def test_save_and_load(self):
        self.group.add_expense("Taxi", "10", "Ana", "equal", {"Ben": 0})
        with tempfile.TemporaryDirectory() as folder:
            filename = os.path.join(folder, "data.json")
            self.group.save(filename)
            loaded = Group()
            loaded.load(filename)
        self.assertEqual(loaded.members, self.group.members)
        self.assertEqual(loaded.expenses, self.group.expenses)


if __name__ == "__main__":
    unittest.main()
