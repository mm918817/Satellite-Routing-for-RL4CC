from .sat_environment import SatEnvironment

from ray.tune.registry import register_env

register_env("SatEnvironment", lambda config: SatEnvironment(config))