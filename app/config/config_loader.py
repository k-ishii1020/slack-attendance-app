import yaml


def load_config():
    with open("config.yaml", "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


config = load_config()
