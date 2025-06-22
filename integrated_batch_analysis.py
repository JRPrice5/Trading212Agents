import json
import pandas as pd
from datetime import datetime, timedelta
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.interface import get_YFin_data_window


class TradingLogger:
    def __init__(self, log_file='trading_decisions.json'):
        self.log_file = log_file
        self.trading_log = self.load_log()

    def load_log(self):
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_log(self):
        with open(self.log_file, 'w') as f:
            json.dump(self.trading_log, f, indent=2)

    def parse_decision(self, decision):
        # Parse the decision object to extract action and confidence
        # This needs to be customized based on your decision format
        return {
            'action': decision.get('action', 'HOLD'),
            'confidence': decision.get('confidence', 0.5),
            'reasoning': decision.get('reasoning', '')
        }

    def calculate_actual_return(self, trade_entry):
        # Get entry price data
        entry_data = get_YFin_data_window(
            trade_entry['ticker'],
            trade_entry['date'],
            1
        )

        # Extract price from the data string (you'll need to parse this)
        entry_price = self.extract_price_from_data(entry_data, trade_entry['date'])

        # Calculate exit date (e.g., next trading day)
        exit_date = self.calculate_exit_date(trade_entry['date'])

        # Get exit price data
        exit_data = get_YFin_data_window(
            trade_entry['ticker'],
            exit_date,
            1
        )
        exit_price = self.extract_price_from_data(exit_data, exit_date)

        # Calculate return based on decision
        parsed_decision = trade_entry['parsed_decision']
        if parsed_decision['action'] == 'BUY':
            return (exit_price - entry_price) / entry_price
        elif parsed_decision['action'] == 'SELL':
            return (entry_price - exit_price) / entry_price
        else:  # HOLD
            return 0.0

    def extract_price_from_data(self, data_string, date):
        # Parse the price data string to extract closing price
        # This is a simplified example - you'll need robust parsing
        lines = data_string.split('\n')
        for line in lines:
            if date in line and 'Close' in line:
                # Extract closing price from the line
                pass
        return 0.0  # Placeholder

    def calculate_exit_date(self, entry_date):
        # Simple next-day exit strategy
        date_obj = datetime.strptime(entry_date, "%Y-%m-%d")
        return (date_obj + timedelta(days=1)).strftime("%Y-%m-%d")


def run_batch_analysis_with_logging(tickers, analysis_date):
    logger = TradingLogger()
    ta = TradingAgentsGraph(debug=False, config=DEFAULT_CONFIG.copy())

    # Batch analysis phase
    print("Starting batch analysis...")
    for ticker in tickers:
        print(f"Analyzing {ticker}...")

        # Get trading decision
        _, decision = ta.propagate(ticker, analysis_date)

        # Parse and log decision
        parsed_decision = logger.parse_decision(decision)

        trade_entry = {
            'ticker': ticker,
            'date': analysis_date,
            'decision': decision,
            'parsed_decision': parsed_decision,
            'status': 'pending_return',
            'timestamp': datetime.now().isoformat()
        }

        logger.trading_log.append(trade_entry)
        print(f"Logged decision for {ticker}: {parsed_decision['action']}")

        # Process pending returns and reflect
    print("\nProcessing pending returns...")
    current_date = datetime.now().date()

    for entry in logger.trading_log:
        if entry['status'] == 'pending_return':
            try:
                # Calculate actual return
                actual_return = logger.calculate_actual_return(entry)
                entry['actual_return'] = actual_return
                entry['status'] = 'calculated'

                # Reflect and learn
                ta.reflect_and_remember(actual_return)
                entry['status'] = 'reflected'

                print(f"Reflected on {entry['ticker']}: {actual_return:.4f}")

            except Exception as e:
                print(f"Error processing {entry['ticker']}: {e}")
                entry['status'] = 'error'
                entry['error'] = str(e)

                # Save updated log
    logger.save_log()
    print(f"\nBatch analysis complete. Log saved to {logger.log_file}")

    return logger.trading_log


# Usage example
if __name__ == "__main__":
    tickers = ["NVDA", "AAPL", "MSFT"]
    analysis_date = "2024-05-10"

    results = run_batch_analysis_with_logging(tickers, analysis_date)

    # Print summary
    for result in results:
        if 'actual_return' in result:
            print(f"{result['ticker']}: {result['parsed_decision']['action']} -> {result['actual_return']:.4f}")