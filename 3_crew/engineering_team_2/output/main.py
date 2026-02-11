def get_share_price(symbol: str) -> float:
    """Simple deterministic price service consumed by app.py."""
    prices = {
        "AAPL": 190.0,
        "MSFT": 420.0,
        "GOOGL": 170.0,
        "TSLA": 210.0,
        "AMZN": 185.0,
    }
    return float(prices.get(symbol.upper(), 100.0))


def get_crypto_price(symbol: str) -> float:
    prices = {
        "BTC": 98000.0,
        "ETH": 3300.0,
        "SOL": 210.0,
    }
    return float(prices.get(symbol.upper(), 1.0))
