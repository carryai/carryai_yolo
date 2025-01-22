import json
from pathlib import Path

def load_config(config_path):
    config_path = Path(config_path)
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise Exception(f"Config file not found at {config_path}")
    except json.JSONDecodeError:
        raise Exception("Invalid JSON format in config file")
