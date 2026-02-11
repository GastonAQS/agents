import pytest
from backend import create_account, deposit_funds, withdraw_funds, buy_asset, sell_asset, get_portfolio_value, get_profit_loss, get_holdings, list_transactions, accounts

@pytest.fixture(scope="function", autouse=True)
def setup():
    # Reset accounts before each test
    accounts.clear()

def test_create_account():
    user_id = "user123"
    create_account(user_id)
    assert "user123" in accounts

def test_deposit_funds():
    user_id = "user123"
    create_account(user_id)
    deposit_funds(user_id, 100.00)
    assert accounts[user_id].balance == 100.00
    assert "Deposited 100.00" in accounts[user_id].transactions

def test_withdraw_funds_exceeding_balance():
    user_id = "user123"
    create_account(user_id)
    deposit_funds(user_id, 50.00)
    with pytest.raises(ValueError, match="Insufficient funds for withdrawal."):
        withdraw_funds(user_id, 150.00)

def test_deposit_negative_amount():
    user_id = "user123"
    create_account(user_id)
    with pytest.raises(ValueError, match="Deposit amount must be positive."):
        deposit_funds(user_id, -50.00)

def test_buy_asset_insufficient_balance():
    user_id = "user123"
    create_account(user_id)
    deposit_funds(user_id, 50.00)
    with pytest.raises(ValueError, match="Insufficient funds to buy asset."):
        buy_asset(user_id, "AAPL", 10, lambda x: 10.00)

def test_sell_asset():
    user_id = "user123"
    create_account(user_id)
    deposit_funds(user_id, 100.00)
    buy_asset(user_id, "AAPL", 5, lambda x: 10.00)
    sell_asset(user_id, "AAPL", 5, lambda x: 15.00)
    assert accounts[user_id].balance == 100.00 - (5 * 10.00) + (5 * 15.00)
    assert "Sold 5 of AAPL at 15.00" in accounts[user_id].transactions

def test_get_portfolio_value():
    user_id = "user123"
    create_account(user_id)
    deposit_funds(user_id, 100.00)
    buy_asset(user_id, "AAPL", 5, lambda x: 10.00)
    value = get_portfolio_value(user_id, lambda x: 15.00)
    assert value == 100.00 - (5 * 10.00) + (5 * 15.00)

def test_list_transactions():
    user_id = "user123"
    create_account(user_id)
    deposit_funds(user_id, 100.00)
    buy_asset(user_id, "AAPL", 5, lambda x: 10.00)
    transactions = list_transactions(user_id)
    assert len(transactions) == 2
    assert "Deposited 100.00" in transactions
    assert "Bought 5 of AAPL at 10.00" in transactions

def test_edge_case_withdraw_funds_negative():
    user_id = "user123"
    create_account(user_id)
    with pytest.raises(ValueError, match="Withdrawal amount must be positive."):
        withdraw_funds(user_id, -50.00)

def test_get_profit_loss():
    user_id = "user123"
    create_account(user_id)
    deposit_funds(user_id, 100.00)
    buy_asset(user_id, "AAPL", 5, lambda x: 10.00)
    profit_loss = get_profit_loss(user_id, lambda x: 15.00)
    assert profit_loss == (5 * 15.00 - (5 * 10.00)) + 100.00 - 100.00

def test_buy_asset_before_deposit():
    user_id = "user123"
    create_account(user_id)
    with pytest.raises(ValueError, match="Insufficient funds to buy asset."):
        buy_asset(user_id, "AAPL", 1, lambda x: 10.00)