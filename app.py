"""Who Owes Whom? A small web app that runs on your own computer.

Start it with:  python app.py
"""

import json
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from group import Group
from settlement import settle

PORT = 8000
FOLDER = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(FOLDER, "data.json")

PAGES = {
    "/": ("index.html", "text/html"),
    "/app.js": ("app.js", "text/javascript"),
    "/style.css": ("style.css", "text/css"),
}

group = Group()
lock = threading.Lock()  # stops two requests changing the data at once


def money(cents):
    return f"{cents / 100:.2f}"


def get_state():
    """Collect everything the web page needs to display."""
    totals = group.totals()
    balances = {name: person["balance"] for name, person in totals.items()}
    payments, is_minimum = settle(balances)

    members = []
    for name, person in totals.items():
        members.append({
            "name": name,
            "paid": money(person["paid"]),
            "share": money(person["share"]),
            "balance": money(person["balance"]),
        })

    expenses = []
    for expense in group.expenses:
        shares = {name: money(cents) for name, cents in expense["shares"].items()}
        expenses.append({**expense, "amount": money(expense["amount"]), "shares": shares})

    transfers = []
    for debtor, creditor, amount in payments:
        transfers.append({"from": debtor, "to": creditor, "amount": money(amount)})

    return {
        "members": members,
        "expenses": expenses,
        "transfers": transfers,
        "isMinimum": is_minimum,
    }


def make_change(path, data):
    """Apply one change from the web page. Returns False for an unknown path."""
    if path == "/api/add-member":
        group.add_member(data.get("name"))
    elif path == "/api/remove-member":
        group.remove_member(data.get("name"))
    elif path == "/api/add-expense":
        group.add_expense(
            data.get("description"),
            data.get("amount"),
            data.get("payer"),
            data.get("method"),
            data.get("values"),
        )
    elif path == "/api/remove-expense":
        group.remove_expense(data.get("id"))
    elif path == "/api/reset":
        group.__init__()
    else:
        return False
    return True


class Handler(BaseHTTPRequestHandler):
    def send(self, status, content, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, status, data):
        self.send(status, json.dumps(data).encode(), "application/json")

    def is_local_request(self):
        """Only answer requests addressed to this computer."""
        host = self.headers.get("Host", "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def do_GET(self):
        if not self.is_local_request():
            self.send_json(403, {"error": "Forbidden"})
        elif self.path == "/api/state":
            with lock:
                self.send_json(200, get_state())
        elif self.path in PAGES:
            filename, content_type = PAGES[self.path]
            with open(os.path.join(FOLDER, "static", filename), "rb") as file:
                self.send(200, file.read(), content_type)
        else:
            self.send_json(404, {"error": "Not found"})

    def do_POST(self):
        # Requiring JSON stops other websites from changing your data.
        is_json = self.headers.get("Content-Type") == "application/json"
        if not self.is_local_request() or not is_json:
            self.send_json(403, {"error": "Forbidden"})
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length))
            if not isinstance(data, dict):
                raise ValueError("Invalid request")

            with lock:
                if make_change(self.path, data):
                    group.save(DATA_FILE)
                    self.send_json(200, get_state())
                else:
                    self.send_json(404, {"error": "Not found"})
        except ValueError as error:
            self.send_json(400, {"error": str(error)})


def main():
    group.load(DATA_FILE)
    # 127.0.0.1 means other computers cannot connect.
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"Running at {url} (press Ctrl+C to stop)")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
