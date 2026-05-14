from pathlib import Path

import yaml
from jinja2 import Template

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name, **vars):
    data = yaml.safe_load((PROMPTS_DIR / f"{name}.yaml").read_text())
    result = []
    for role in ("system", "user"):
        if role in data:
            result.append({"role": role, "text": Template(data[role]).render(**vars)})
    return result
