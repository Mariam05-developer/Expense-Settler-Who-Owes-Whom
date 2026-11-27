"""Functions for splitting an expense between people.

Money is stored as a whole number of cents (1250 means 12.50) because
floating point numbers can cause rounding errors.
"""


def to_cents(value):
    """Turn input such as "12.50" into 1250."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{value}' is not a number")

    # This also rejects "nan" and "inf".
    if not 0 <= number <= 1_000_000_000:
        raise ValueError("Numbers must be between 0 and 1,000,000,000")

    cents = round(number * 100)
    if abs(number * 100 - cents) > 0.001:
        raise ValueError("Use at most 2 decimal places")
    return cents


def split_by_weight(total, weights):
    """Split total cents in proportion to each person's weight."""
    total_weight = sum(weights.values())
    if total_weight == 0:
        raise ValueError("At least one person needs a value above 0")

    # Give everyone their share, rounded down.
    result = {}
    for name, weight in weights.items():
        result[name] = total * weight // total_weight

    # Rounding down can leave a few cents over. Hand them out one at a time.
    leftover = total - sum(result.values())
    for name, weight in weights.items():
        if leftover > 0 and weight > 0:
            result[name] += 1
            leftover -= 1

    return result


def split_expense(total, method, values):
    """Work out how many cents each person owes for one expense.

    values is a dictionary of name -> what the user typed. What it means
    depends on the method: an amount, a percentage or a number of shares.
    It is ignored for an even split.
    """
    if not values:
        raise ValueError("Select at least one person")

    if method == "equal":
        return split_by_weight(total, {name: 1 for name in values})

    # Percentages and shares are also read with 2 decimal places,
    # so 33.33% becomes the whole number 3333.
    numbers = {name: to_cents(value) for name, value in values.items()}

    if method == "exact":
        if sum(numbers.values()) != total:
            assigned = sum(numbers.values()) / 100
            raise ValueError(
                f"Amounts add up to {assigned:.2f}, not {total / 100:.2f}"
            )
        return numbers

    if method == "percent":
        if sum(numbers.values()) != 100 * 100:
            percent = sum(numbers.values()) / 100
            raise ValueError(f"Percentages add up to {percent:g}, not 100")
        return split_by_weight(total, numbers)

    if method == "shares":
        return split_by_weight(total, numbers)

    raise ValueError("Unknown split method")
