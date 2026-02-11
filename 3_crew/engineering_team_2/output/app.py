import gradio as gr
from backend import create_account, deposit_funds, withdraw_funds, buy_asset, sell_asset, get_portfolio_value, get_profit_loss, get_holdings, list_transactions
from main import get_share_price, get_crypto_price

def create_account_ui(user_id):
    try:
        create_account(user_id)
        return f"Account for {user_id} created successfully."
    except Exception as e:
        return str(e)

def deposit_funds_ui(user_id, amount):
    try:
        deposit_funds(user_id, amount)
        return f"Deposited ${amount:.2f} into account {user_id}."
    except Exception as e:
        return str(e)

def withdraw_funds_ui(user_id, amount):
    try:
        withdraw_funds(user_id, amount)
        return f"Withdrew ${amount:.2f} from account {user_id}."
    except Exception as e:
        return str(e)

def buy_asset_ui(user_id, asset_symbol, quantity):
    try:
        buy_asset(user_id, asset_symbol, quantity, get_share_price)
        return f"Bought {quantity} of {asset_symbol} for account {user_id}."
    except Exception as e:
        return str(e)

def sell_asset_ui(user_id, asset_symbol, quantity):
    try:
        sell_asset(user_id, asset_symbol, quantity, get_share_price)
        return f"Sold {quantity} of {asset_symbol} from account {user_id}."
    except Exception as e:
        return str(e)

def get_portfolio_value_ui(user_id):
    try:
        value = get_portfolio_value(user_id, get_share_price)
        return f"Portfolio value for {user_id}: ${value:.2f}."
    except Exception as e:
        return str(e)

def get_profit_loss_ui(user_id):
    try:
        profit_loss = get_profit_loss(user_id, get_share_price)
        return f"Profit/Loss for {user_id}: ${profit_loss:.2f}."
    except Exception as e:
        return str(e)

def get_holdings_ui(user_id):
    try:
        holdings = get_holdings(user_id)
        return holdings
    except Exception as e:
        return str(e)

def list_transactions_ui(user_id):
    try:
        transactions = list_transactions(user_id)
        return transactions
    except Exception as e:
        return str(e)

def main():
    with gr.Blocks() as demo:
        user_input = gr.Textbox(label="User ID")
        create_btn = gr.Button("Create Account")
        create_output = gr.Textbox(label="Output", interactive=False)
        
        # Create account
        create_btn.click(create_account_ui, inputs=user_input, outputs=create_output)

        # Deposit Interface
        deposit_amount = gr.Number(label="Deposit Amount")
        deposit_btn = gr.Button("Deposit Funds")
        deposit_output = gr.Textbox(label="Output", interactive=False)
        deposit_btn.click(deposit_funds_ui, inputs=[user_input, deposit_amount], outputs=deposit_output)

        # Withdraw Interface
        withdraw_amount = gr.Number(label="Withdraw Amount")
        withdraw_btn = gr.Button("Withdraw Funds")
        withdraw_output = gr.Textbox(label="Output", interactive=False)
        withdraw_btn.click(withdraw_funds_ui, inputs=[user_input, withdraw_amount], outputs=withdraw_output)

        # Buy Asset Interface
        asset_symbol_buy = gr.Textbox(label="Asset Symbol to Buy")
        quantity_buy = gr.Number(label="Quantity to Buy")
        buy_btn = gr.Button("Buy Asset")
        buy_output = gr.Textbox(label="Output", interactive=False)
        buy_btn.click(buy_asset_ui, inputs=[user_input, asset_symbol_buy, quantity_buy], outputs=buy_output)

        # Sell Asset Interface
        asset_symbol_sell = gr.Textbox(label="Asset Symbol to Sell")
        quantity_sell = gr.Number(label="Quantity to Sell")
        sell_btn = gr.Button("Sell Asset")
        sell_output = gr.Textbox(label="Output", interactive=False)
        sell_btn.click(sell_asset_ui, inputs=[user_input, asset_symbol_sell, quantity_sell], outputs=sell_output)

        # Get Portfolio Value Interface
        portfolio_btn = gr.Button("Get Portfolio Value")
        portfolio_output = gr.Textbox(label="Output", interactive=False)
        portfolio_btn.click(get_portfolio_value_ui, inputs=user_input, outputs=portfolio_output)

        # Get Profit/Loss Interface
        profit_loss_btn = gr.Button("Get Profit/Loss")
        profit_loss_output = gr.Textbox(label="Output", interactive=False)
        profit_loss_btn.click(get_profit_loss_ui, inputs=user_input, outputs=profit_loss_output)

        # Get Holdings Interface
        holdings_btn = gr.Button("Get Holdings")
        holdings_output = gr.Textbox(label="Output", interactive=False)
        holdings_btn.click(get_holdings_ui, inputs=user_input, outputs=holdings_output)

        # List Transactions Interface
        transactions_btn = gr.Button("List Transactions")
        transactions_output = gr.Textbox(label="Output", interactive=False)
        transactions_btn.click(list_transactions_ui, inputs=user_input, outputs=transactions_output)

    demo.launch()

if __name__ == "__main__":
    main()