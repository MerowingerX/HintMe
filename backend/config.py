import yaml


class RulesConfig:
    def __init__(self, path: str = "config/rules.yaml"):
        with open(path, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def is_enabled(self, rule: str) -> bool:
        return self.config.get("rules", {}).get(rule, {}).get("enabled", False)

    def get_hint(self, rule: str, **kwargs) -> str:
        template = self.config["rules"][rule]["hint"]
        return template.format(**kwargs)

    def get_custom_rules(self) -> list:
        return self.config.get("custom_rules", [])
