"""Hard cap on Claude spending, shared by brain/ and owner/.

Before every Claude call: budget.check()        -> raises BudgetExceeded once the cap is reached
After every Claude call:  budget.record(model, response.usage)

Spend is added up in spend.json (next to this file) from the token counts the API returns.
Images are billed as input tokens, so usage.input_tokens already includes them.
Cap: $20 by default, or set DOG_BUDGET_USD in owner/.env or the environment.
Reset: delete spend.json (e.g. after topping up the account).
"""
import json
import os
from pathlib import Path

LEDGER = Path(__file__).parent / "spend.json"
RESERVE = 0.05  # stop a little early so the last call can't push us over

# US dollars per million tokens (input, output). Anthropic list prices, 2026.
PRICES = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5": (2.00, 10.00),
}


class BudgetExceeded(RuntimeError):
    pass


def cap():
    return float(os.environ.get("DOG_BUDGET_USD", "20"))


def spent():
    if not LEDGER.exists():
        return 0.0
    return json.loads(LEDGER.read_text())["spent_usd"]


def check():
    if spent() + RESERVE >= cap():
        raise BudgetExceeded(f"Claude budget used up: ${spent():.2f} of ${cap():.2f}. "
                             f"Delete {LEDGER.name} to reset.")


def record(model, usage):
    price_in, price_out = next(p for name, p in PRICES.items() if model.startswith(name))
    cost = (usage.input_tokens * price_in + usage.output_tokens * price_out) / 1_000_000
    data = json.loads(LEDGER.read_text()) if LEDGER.exists() else {"spent_usd": 0.0, "calls": 0}
    data["spent_usd"] = round(data["spent_usd"] + cost, 6)
    data["calls"] += 1
    LEDGER.write_text(json.dumps(data, indent=2))
    return cost


if __name__ == "__main__":
    data = json.loads(LEDGER.read_text()) if LEDGER.exists() else {"spent_usd": 0.0, "calls": 0}
    print(f"Spent ${data['spent_usd']:.4f} of ${cap():.2f} over {data['calls']} Claude calls")
