from RL4CC.callbacks.base_callbacks import BaseCallbacks

class SatCallbacks(BaseCallbacks):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
#    self.epsilon_reset_done = False # Flag del reset di epsilon
    self.RELEVANT_KEYS = [
      "current_time",
      "step_reward",
      "hole_counter",
      "current_sat",
      "total_distance",
      "dest_reached",
      "dijkstra_dist",
      "dijkstra_hop"
    ]
