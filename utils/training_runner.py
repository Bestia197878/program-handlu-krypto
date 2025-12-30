"""Small runner to train the pure-Python agent and produce a model file."""
from .ai_models import train_simple_agent

def run_quick_train():
    print("Starting quick training (this is a lightweight simulation)...")
    save_path = '/workspaces/program-handlu-krypto/models/trading_agent.zip'
    agent = train_simple_agent(episodes=20, steps_per_episode=30, save_path=save_path)
    print(f"Training finished — model saved to {save_path}")

if __name__ == '__main__':
    run_quick_train()
