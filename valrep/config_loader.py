import json
import os
import sys

def load_config(path):
    """
    Load configuration file in various supported formats.

    :param path: Path to config file
    :return: Parsed configuration as dict
    :raises ValueError: Unsupported or invalid config format
    """
    ext = os.path.splitext(path)[1].lower()

    # JSON config
    if ext == ".json":
        with open(path, "r") as f:
            return json.load(f)

    # YAML config
    elif ext in [".yaml", ".yml"]:
        import yaml
        with open(path, "r") as f:
            return yaml.safe_load(f)

    # TOML config (Python 3.11+)
    elif ext == ".toml":
        import tomllib
        with open(path, "rb") as f:
            return tomllib.load(f)

    # INI config
    elif ext == ".ini":
        import configparser
        config = configparser.ConfigParser()
        config.read(path)
        return {section: dict(config[section]) for section in config.sections()}

    # Python file containing a `config` dict
    elif ext == ".py":
        config_dict = {}
        sys.path.insert(0, os.path.dirname(path))
        module_name = os.path.basename(path).replace(".py", "")
        mod = __import__(module_name)
        if hasattr(mod, "config"):
            return mod.config
        raise ValueError("Python config must define variable `config`")

    # Unsupported formats
    else:
        raise ValueError(f"Unsupported config format: {ext}")
