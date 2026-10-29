import yaml
from dotenv import load_dotenv

from .openai_compatible import OpenAICompatibleProvider


def get_provider(config_path="config.yaml"):
    """Create the model provider chosen in config.yaml."""
    load_dotenv()
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    p = cfg["providers"][cfg["provider"]]
    return OpenAICompatibleProvider(p["base_url"], p["api_key_env"], cfg["model"])