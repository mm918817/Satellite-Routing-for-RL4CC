import src
from RL4CC.experiments.train_with_plots import TrainingExperimentWithPlots

exp = TrainingExperimentWithPlots(
    exp_config_file="exp_config.json"
)
exp.run()
