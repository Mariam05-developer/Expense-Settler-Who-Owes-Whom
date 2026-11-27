"""Work out who should pay whom, using as few payments as possible.

Key idea: a group of k people whose balances add up to zero can settle up in
at most k - 1 payments. So if we can cut everyone into more zero-sum groups,
we need fewer payments overall.
"""

from itertools import combinations

# Trying every grouping takes exponential time, so we only do it for small cases.
MAX_EXACT_PEOPLE = 12


def find_groups(people):
    """Split people into as many zero-sum groups as possible (recursive).

    people is a list of (name, balance) pairs whose balances add up to zero.
    """
    if not people:
        return []

    first = people[0]
    others = people[1:]
    best = [people]  # worst case: everyone is in one big group

    # Try every smaller zero-sum group that contains the first person.
    for size in range(1, len(others)):
        for chosen in combinations(others, size):
            group = [first, *chosen]
            if sum(balance for name, balance in group) == 0:
                remaining = [person for person in others if person not in chosen]
                groups = [group] + find_groups(remaining)
                if len(groups) > len(best):
                    best = groups

    return best


def settle_group(people):
    """Repeatedly have the biggest debtor pay the biggest creditor."""
    balances = dict(people)
    payments = []

    while any(balances.values()):
        debtor = min(balances, key=balances.get)
        creditor = max(balances, key=balances.get)
        amount = min(-balances[debtor], balances[creditor])

        payments.append((debtor, creditor, amount))
        balances[debtor] += amount
        balances[creditor] -= amount

    return payments


def settle(balances):
    """Return (payments, is_minimum) for a dictionary of name -> cents.

    A positive balance means the person is owed money. Each payment is a
    (debtor, creditor, amount) tuple.
    """
    if sum(balances.values()) != 0:
        raise ValueError("Balances must add up to zero")

    people = [(name, balance) for name, balance in balances.items() if balance != 0]

    is_minimum = len(people) <= MAX_EXACT_PEOPLE
    if is_minimum:
        groups = find_groups(people)
    else:
        groups = [people]  # too many to search, so just use the greedy method

    payments = []
    for group in groups:
        payments += settle_group(group)

    return payments, is_minimum
