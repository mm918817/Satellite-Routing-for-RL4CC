import src
from RL4CC.experiments.train import TrainingExperiment
from RL4CC.experiments.tune import TuningExperiment # Per fare Tuning degli Hyperparameters, usando TuningExperiment

exp = TrainingExperiment(
    exp_config_file="exp_config.json"
)
#exp = TuningExperiment(exp_config_file="exp_config.json") # Per fare Tuning

exp.run()
