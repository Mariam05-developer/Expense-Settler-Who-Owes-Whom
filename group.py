"""The Group class stores the people and their expenses."""

import json
import os

from splitting import split_expense, to_cents


class Group:
    def __init__(self):
        self.members = []
        self.expenses = []
        self.next_id = 1

    def add_member(self, name):
        name = str(name or "").strip()
        if not name:
            raise ValueError("Name is required")
        if name.lower() in [member.lower() for member in self.members]:
            raise ValueError(f"{name} is already in the group")
        self.members.append(name)

    def remove_member(self, name):
        if name not in self.members:
            raise ValueError("No such person")
        for expense in self.expenses:
            if name == expense["payer"] or name in expense["shares"]:
                raise ValueError(f"Delete {name}'s expenses first")
        self.members.remove(name)

    def add_expense(self, description, amount, payer, method, values):
        description = str(description or "").strip()
        if not description:
            raise ValueError("Description is required")

        cents = to_cents(amount)
        if cents == 0:
            raise ValueError("Amount must be more than 0")
        if payer not in self.members:
            raise ValueError("Choose who paid")
        if not isinstance(values, dict):
            raise ValueError("Select at least one person")
        for name in values:
            if name not in self.members:
                raise ValueError(f"{name} is not in the group")

        self.expenses.append({
            "id": self.next_id,
            "description": description,
            "amount": cents,
            "payer": payer,
            "method": method,
            "shares": split_expense(cents, method, values),
        })
        self.next_id += 1

    def remove_expense(self, expense_id):
        self.expenses = [e for e in self.expenses if e["id"] != expense_id]

    def totals(self):
        """For each person: what they paid, their share and their balance."""
        totals = {}
        for name in self.members:
            totals[name] = {"paid": 0, "share": 0, "balance": 0}

        for expense in self.expenses:
            totals[expense["payer"]]["paid"] += expense["amount"]
            for name, share in expense["shares"].items():
                totals[name]["share"] += share

        for person in totals.values():
            person["balance"] = person["paid"] - person["share"]

        return totals

    def save(self, filename):
        data = {
            "members": self.members,
            "expenses": self.expenses,
            "next_id": self.next_id,
        }
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)

    def load(self, filename):
        if not os.path.exists(filename):
            return  # first run, nothing saved yet
        with open(filename, encoding="utf-8") as file:
            data = json.load(file)
        self.members = data["members"]
        self.expenses = data["expenses"]
        self.next_id = data["next_id"]
