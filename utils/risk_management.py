import logging
logger = logging.getLogger(__name__)

def get_risk_parameters(config):
    return {
        'risk_percent': config.get('risk_percent', 1.0),
        'max_position_size': config.get('max_position_size', 0.01)
    }

def manage_system_parameters(trade_history, df, sentiment, risk_agent):
    # Return unchanged risk percent for now
    return risk_agent.predict if hasattr(risk_agent, 'predict') else 1.0

def calculate_position_size(decision, current_price, trade_history, risk_params):
    try:
        risk_percent = float(risk_params.get('risk_percent', 1.0)) / 100.0
        # simple notional size using fixed portfolio assumption
        portfolio = 10000.0
        notional = portfolio * risk_percent
        amount = notional / float(current_price) if float(current_price) > 0 else 0
        max_size = risk_params.get('max_position_size', 0.01)
        return min(amount, max_size)
    except Exception as e:
        logger.error(f"Błąd kalkulacji rozmiaru pozycji: {e}")
        return 0
