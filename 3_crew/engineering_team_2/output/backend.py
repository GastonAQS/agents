import json
import os
from typing import Any, Callable, Dict, List

DATA_FILE = "data.json"


def _load_state() -> Dict[str, Any]:
    if not os.path.exists(DATA_FILE):
        return {"accounts": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        data = {}
    data.setdefault("accounts", {})
    return data


def _save_state(state: Dict[str, Any]) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _get_account(state: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    accounts = state["accounts"]
    if user_id not in accounts:
        raise ValueError(f"Account '{user_id}' does not exist.")
    return accounts[user_id]


def create_account(user_id: str) -> None:
    state = _load_state()
    accounts = state["accounts"]
    if user_id in accounts:
        raise ValueError(f"Account '{user_id}' already exists.")
    accounts[user_id] = {"cash": 0.0, "positions": {}, "transactions": [], "cost_basis": 0.0}
    _save_state(state)


def deposit_funds(user_id: str, amount: float) -> None:
    if amount <= 0:
        raise ValueError("Deposit amount must be greater than 0.")
    state = _load_state()
    account = _get_account(state, user_id)
    account["cash"] += float(amount)
    account["transactions"].append({"type": "deposit", "amount": float(amount)})
    _save_state(state)


def withdraw_funds(user_id: str, amount: float) -> None:
    if amount <= 0:
        raise ValueError("Withdraw amount must be greater than 0.")
    state = _load_state()
    account = _get_account(state, user_id)
    if account["cash"] < float(amount):
        raise ValueError("Insufficient funds.")
    account["cash"] -= float(amount)
    account["transactions"].append({"type": "withdraw", "amount": float(amount)})
    _save_state(state)


def buy_asset(
    user_id: str, asset_symbol: str, quantity: float, price_fn: Callable[[str], float]
) -> None:
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")
    price = float(price_fn(asset_symbol))
    state = _load_state()
    account = _get_account(state, user_id)
    cost = price * float(quantity)
    if account["cash"] < cost:
        raise ValueError("Insufficient funds.")

    account["cash"] -= cost
    positions = account["positions"]
    positions[asset_symbol] = float(positions.get(asset_symbol, 0.0)) + float(quantity)
    account["cost_basis"] += cost
    account["transactions"].append(
        {"type": "buy", "symbol": asset_symbol, "quantity": float(quantity), "price": price}
    )
    _save_state(state)


def sell_asset(
    user_id: str, asset_symbol: str, quantity: float, price_fn: Callable[[str], float]
) -> None:
    if quantity <= 0:
        raise ValueError("Quantity must be greater than 0.")
    state = _load_state()
    account = _get_account(state, user_id)
    positions = account["positions"]
    held = float(positions.get(asset_symbol, 0.0))
    if held < float(quantity):
        raise ValueError(f"Not enough {asset_symbol} to sell.")

    price = float(price_fn(asset_symbol))
    proceeds = price * float(quantity)
    account["cash"] += proceeds
    new_qty = held - float(quantity)
    if new_qty == 0:
        positions.pop(asset_symbol, None)
    else:
        positions[asset_symbol] = new_qty
    account["transactions"].append(
        {"type": "sell", "symbol": asset_symbol, "quantity": float(quantity), "price": price}
    )
    _save_state(state)


def get_portfolio_value(user_id: str, price_fn: Callable[[str], float]) -> float:
    state = _load_state()
    account = _get_account(state, user_id)
    value = float(account["cash"])
    for symbol, qty in account["positions"].items():
        value += float(qty) * float(price_fn(symbol))
    return value


def get_profit_loss(user_id: str, price_fn: Callable[[str], float]) -> float:
    state = _load_state()
    account = _get_account(state, user_id)
    return get_portfolio_value(user_id, price_fn) - float(account["cost_basis"])


def get_holdings(user_id: str) -> Dict[str, float]:
    state = _load_state()
    account = _get_account(state, user_id)
    return dict(account["positions"])


def list_transactions(user_id: str) -> List[Dict[str, Any]]:
    state = _load_state()
    account = _get_account(state, user_id)
    return list(account["transactions"])
