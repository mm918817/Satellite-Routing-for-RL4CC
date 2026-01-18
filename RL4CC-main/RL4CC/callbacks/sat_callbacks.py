from RL4CC.callbacks.base_callbacks_for_plots import BaseCallbacksForPlots

class SatCallbacks(BaseCallbacksForPlots):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.RELEVANT_KEYS = [
      "current_time",
      "reward",
      "current_sat"
    ]