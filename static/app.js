// The latest data from the Python server.
let state = null;
// Remembers which names have checkboxes, so we only rebuild them when needed.
let shownNames = "";

function byId(id) {
  return document.getElementById(id);
}

// Creates an element with some text. Using textContent (not innerHTML)
// means a name like "<b>Sam</b>" is shown as text instead of run as HTML.
function createElement(tag, text) {
  const element = document.createElement(tag);
  element.textContent = text;
  return element;
}

function createButton(text, onClick) {
  const button = createElement("button", text);
  button.type = "button";
  button.className = "secondary";
  button.addEventListener("click", onClick);
  return button;
}

// Sends a request to the server and redraws the page.
// Returns true if it worked.
async function sendRequest(path, data) {
  let options = {};
  if (data) {
    options = {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    };
  }

  try {
    const response = await fetch(path, options);
    const result = await response.json();
    if (!response.ok) {
      showError(result.error);
      return false;
    }
    state = result;
  } catch (error) {
    showError("Cannot reach the server. Is app.py still running?");
    return false;
  }

  showError("");
  render();
  return true;
}

function showError(message) {
  byId("error").textContent = message;
  byId("error").hidden = message === "";
}

function render() {
  renderMembers();
  renderTransfers();
  renderBalances();
  renderExpenses();
}

function renderMembers() {
  const names = state.members.map((member) => member.name);

  byId("members").replaceChildren();
  for (const name of names) {
    const item = createElement("li", name);
    item.append(createButton("×", () => sendRequest("/api/remove-member", { name })));
    byId("members").append(item);
  }

  byId("need-members").hidden = names.length >= 2;
  byId("expense-form").hidden = names.length < 2;

  if (JSON.stringify(names) !== shownNames) {
    shownNames = JSON.stringify(names);
    renderPayerList(names);
    renderParticipants(names);
  }
}

function renderPayerList(names) {
  byId("payer").replaceChildren();
  for (const name of names) {
    byId("payer").append(createElement("option", name));
  }
}

// One row per person: a checkbox, their name and a box for their value.
function renderParticipants(names) {
  byId("participants").replaceChildren();
  for (const name of names) {
    const row = document.createElement("div");
    row.className = "participant";
    row.dataset.name = name;

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = true;

    const label = document.createElement("label");
    label.append(checkbox, name);

    const valueInput = document.createElement("input");
    valueInput.className = "value";

    row.append(label, valueInput);
    byId("participants").append(row);
  }
  updateSplitInputs();
}

// The ticked people and what was typed next to each of them.
function getSelected() {
  const selected = [];
  for (const row of byId("participants").children) {
    if (row.querySelector("input[type=checkbox]").checked) {
      const value = row.querySelector(".value").value.trim();
      selected.push({ name: row.dataset.name, value });
    }
  }
  return selected;
}

// Shows or hides the value boxes and updates the hint under them.
function updateSplitInputs() {
  const method = byId("method").value;
  const placeholders = { equal: "", exact: "0.00", percent: "%", shares: "1" };

  for (const input of document.querySelectorAll(".value")) {
    input.hidden = method === "equal";
    input.placeholder = placeholders[method];
  }

  const selected = getSelected();
  const amount = Number(byId("amount").value);
  let sum = 0;
  for (const person of selected) {
    sum += Number(person.value);
  }

  let hint = "";
  if (method === "equal" && amount > 0 && selected.length > 0) {
    hint = `About ${(amount / selected.length).toFixed(2)} each`;
  } else if (method === "exact") {
    hint = `Assigned so far: ${sum.toFixed(2)}`;
  } else if (method === "percent") {
    hint = `Total so far: ${Number(sum.toFixed(2))}%`;
  } else if (method === "shares") {
    hint = "A blank box counts as 1 share";
  }
  byId("split-hint").textContent = hint;
}

function renderTransfers() {
  const count = state.transfers.length;
  let note;
  if (state.expenses.length === 0) {
    note = "Add an expense to see who pays whom.";
  } else if (count === 0) {
    note = "All settled. Nobody owes anything.";
  } else if (state.isMinimum) {
    note = `Payments needed: ${count} (the fewest possible)`;
  } else {
    note = `Payments needed: ${count} (large group, may not be the fewest)`;
  }
  byId("settle-note").textContent = note;

  byId("transfers").replaceChildren();
  for (const transfer of state.transfers) {
    const text = `${transfer.from} pays ${transfer.to} ${transfer.amount}`;
    const item = document.createElement("li");
    item.append(createElement("span", text));
    item.append(createButton("Mark paid", () => markPaid(transfer)));
    byId("transfers").append(item);
  }
}

// A payment is saved as an expense that only the receiver has to "pay back".
function markPaid(transfer) {
  sendRequest("/api/add-expense", {
    description: `Payment: ${transfer.from} to ${transfer.to}`,
    amount: transfer.amount,
    payer: transfer.from,
    method: "exact",
    values: { [transfer.to]: transfer.amount },
  });
}

function renderBalances() {
  byId("balances").replaceChildren();
  for (const member of state.members) {
    const balance = Number(member.balance);
    let text = "settled";
    let colour = "muted";
    if (balance > 0) {
      text = `gets back ${member.balance}`;
      colour = "positive";
    } else if (balance < 0) {
      text = `owes ${(-balance).toFixed(2)}`;
      colour = "negative";
    }

    const balanceCell = createElement("td", text);
    balanceCell.className = colour;

    const row = document.createElement("tr");
    row.append(
      createElement("td", member.name),
      createElement("td", member.paid),
      createElement("td", member.share),
      balanceCell
    );
    byId("balances").append(row);
  }
}

function renderExpenses() {
  byId("no-expenses").hidden = state.expenses.length > 0;
  byId("expenses").replaceChildren();

  for (const expense of state.expenses) {
    const shares = Object.entries(expense.shares)
      .map(([name, share]) => `${name} ${share}`)
      .join(", ");

    const details = document.createElement("span");
    details.append(
      createElement("strong", `${expense.description}: ${expense.amount}`),
      createElement("small", `Paid by ${expense.payer}. Split: ${shares}`)
    );

    const item = document.createElement("li");
    item.append(details);
    item.append(createButton("Delete", () => sendRequest("/api/remove-expense", { id: expense.id })));
    byId("expenses").prepend(item); // newest first
  }
}

byId("member-form").addEventListener("submit", async (event) => {
  event.preventDefault(); // stop the page from reloading
  const added = await sendRequest("/api/add-member", { name: byId("member-name").value });
  if (added) {
    byId("member-name").value = "";
  }
});

byId("expense-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const method = byId("method").value;

  const values = {};
  for (const person of getSelected()) {
    const blank = method === "shares" ? "1" : "0";
    values[person.name] = person.value || blank;
  }

  const added = await sendRequest("/api/add-expense", {
    description: byId("description").value,
    amount: byId("amount").value,
    payer: byId("payer").value,
    method,
    values,
  });

  if (added) {
    byId("description").value = "";
    byId("amount").value = "";
    renderParticipants(state.members.map((member) => member.name));
  }
});

byId("expense-form").addEventListener("input", updateSplitInputs);

// A number typed as a percentage means something else as an amount, so clear it.
byId("method").addEventListener("change", () => {
  for (const input of document.querySelectorAll(".value")) {
    input.value = "";
  }
  updateSplitInputs();
});

byId("reset").addEventListener("click", () => {
  if (confirm("Delete all people and expenses?")) {
    sendRequest("/api/reset", {});
  }
});

sendRequest("/api/state");
