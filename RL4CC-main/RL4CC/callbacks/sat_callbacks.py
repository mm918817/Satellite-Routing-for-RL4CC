from RL4CC.callbacks import BaseCallbacks

class SatCallbacks(BaseCallbacks):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.RELEVANT_KEYS = [
      "current_time",
      "reward",
      "current_sat"
    ]