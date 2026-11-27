# Who Owes Whom?

A split-bill app. Add people, record who paid for what, and see the payments
needed to clear every debt.

Built with Python (standard library only) and plain HTML, CSS and JavaScript.

## How to run

```
python app.py
```

Then open <http://127.0.0.1:8000> (it should open by itself). Press Ctrl+C to
stop. Your data is saved in `data.json`.

## Features

- Split expenses evenly, by exact amounts, by percentages or by shares
- See what each person paid, their share and their balance
- See who should pay whom, and mark payments as paid

## How settling up works

Each person's balance is what they paid minus their share, so all the balances
add up to zero.

A group of `k` people whose balances add up to zero needs at most `k - 1`
payments. So the more zero-sum groups we can find, the fewer payments we need.

1. `find_groups` uses recursion to try the possible zero-sum groups and keeps the
   split with the most groups.
2. Inside each group, the biggest debtor pays the biggest creditor until everyone
   is at zero.

Example: balances `+9, +8, -5, -4, -7, -1`. Only using step 2 takes 5 payments.
Splitting into `{+9, -5, -4}` and `{+8, -7, -1}` first takes 4.

Trying every grouping takes exponential time, so step 1 is only used when 12 or
fewer people have a non-zero balance. Larger groups use step 2 alone, which still
settles everything but may not use the fewest payments.

## Files

| File | What it does |
|---|---|
| `app.py` | Web server |
| `group.py` | Stores people and expenses |
| `splitting.py` | The four ways to split |
| `settlement.py` | Works out who pays whom |
| `static/` | The web page |
| `test_app.py` | Tests |

## Tests

```
python -m unittest
```

## Possible improvements

- Edit an existing expense
- Support more than one group
- Use a database instead of a JSON file
