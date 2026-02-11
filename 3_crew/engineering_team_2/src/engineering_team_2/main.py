#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from engineering_team_2.crew import EngineeringTeam2

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information


def run():
    """
    Run the crew.
    """
    inputs = {
        "requirements": (
            """
            A simple account management system for a trading simulation platform.
            The system should allow users to create an account, deposit funds, and withdraw funds.
            The system should allow users to record that they have bought or sold shares, providing a quantity.
            The system should calculate the total value of the user's portfolio, and the profit or loss from the initial deposit.
            The system should be able to report the holdings of the user at any point in time.
            The system should be able to report the profit or loss of the user at any point in time.
            The system should be able to list the transactions that the user has made over time.
            The system should prevent the user from withdrawing funds that would leave them with a negative balance, or
            from buying more shares than they can afford, or selling shares that they don't have.
            The system has access to a function get_share_price(symbol) which returns the current price of a share, and includes a test implementation that returns fixed prices for AAPL, TSLA, GOOGL.
            The system also supports cryptocurrency trading, and has access to a function get_crypto_price(symbol) which returns the current price of a cryptocurrency, and includes a test implementation that returns fixed prices for BTC, ETH, XRP.
            The system would be integrated with Binance API for trading, do only a mock integration for now.
            """
        ),
        "module_name": "backend.py",
        "current_year": str(datetime.now().year),
    }

    try:
        EngineeringTeam2().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "requirements": (
            "Build a simple task manager app with create/list/complete task operations, "
            "a minimal UI, and clear separation between backend logic and UI integration."
        ),
        "module_name": "backend.py",
        "current_year": str(datetime.now().year),
    }
    try:
        EngineeringTeam2().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        EngineeringTeam2().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "requirements": (
            "Build a simple task manager app with create/list/complete task operations, "
            "a minimal UI, and clear separation between backend logic and UI integration."
        ),
        "module_name": "backend.py",
        "current_year": str(datetime.now().year),
    }

    try:
        EngineeringTeam2().crew().test(
            n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


def run_with_trigger():
    """
    Run the crew with trigger payload.
    """
    import json

    if len(sys.argv) < 2:
        raise Exception(
            "No trigger payload provided. Please provide JSON payload as argument."
        )

    try:
        trigger_payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload provided as argument")

    inputs = {
        "crewai_trigger_payload": trigger_payload,
        "requirements": "",
        "module_name": "backend.py",
        "current_year": "",
    }

    try:
        result = EngineeringTeam2().crew().kickoff(inputs=inputs)
        return result
    except Exception as e:
        raise Exception(f"An error occurred while running the crew with trigger: {e}")
