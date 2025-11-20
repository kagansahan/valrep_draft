from itertools import product
from typing import Dict, Any

# ============================================================
# Helper functions
# ============================================================

def format_float_to_str(value: float) -> str:
    """
    Convert a float into the project's compact `XpY` format (e.g. 125.5 → 125p5).

    Rules:
    * Replace '.' with 'p'
    * Strip trailing zeros in decimals
    * Use 'p0' if no decimals remain
    """
    s = f"{value:.10g}"
    if "." in s:
        integer, decimal = s.split(".")
        decimal = decimal.rstrip("0") or "0"
        return f"{integer}p{decimal}"
    return f"{s}p0"


def evaluate_formula(value, param_space):
    """
    Evaluate a string formula (e.g. 'MSQUARK/4') using values from param_space.
    Returns the original string if evaluation fails.
    """
    if isinstance(value, (int, float)):
        return value

    if isinstance(value, str):
        local_vars = {k: float(v["value"]) for k, v in param_space.items()}
        try:
            return float(eval(value, {"__builtins__": {}}, local_vars))
        except Exception:
            return value

    return None


# ============================================================
# Parameter-space expansion & job-name generation
# ============================================================

class ParameterSpaceModifier:
    """
    Expand the parameter space by generating all combinations defined
    via fixed `value` or `min/max/step` ranges.
    """

    def generate(self, **config):
        """Yield new configs for each point in the Cartesian product."""
        param_space = config.get("parameter_space", {})
        keys = list(param_space.keys())

        ranges = []
        for k in keys:
            p = param_space[k]
            if "min" in p and "max" in p and "step" in p:
                ranges.append(range(p["min"], p["max"] + 1, p["step"]))
            elif "value" in p:
                ranges.append([p["value"]])
            else:
                raise ValueError(
                    f"For parameter {k}, either min/max/step or value must be defined."
                )

        for values in product(*ranges):
            combo = {k: {"value": v} for k, v in zip(keys, values)}
            new_cfg = config.copy()
            new_cfg["parameter_space"] = combo
            yield new_cfg


class JobNameModifier:
    """
    Build a compact job name encoding topology, parameters, and energy.
    Example:  SS_direct.100p0_50p0.13p0
    """

    def modify(self, **config):
        """Attach a generated `job_name` field to the config."""
        topology = config.get("topology", "unknown")
        energy = config.get("energy")
        combo = config.get("parameter_space", {})

        param_values_list = [
            format_float_to_str(float(p["value"])) for p in combo.values()
        ]

        param_values = "_".join(param_values_list)
        job_name = f"{topology}.{param_values}.{format_float_to_str(float(energy))}"

        new_cfg = config.copy()
        new_cfg["job_name"] = job_name
        return new_cfg
