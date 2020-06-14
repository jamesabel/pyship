import time


class RestartMonitor:
    """
    Monitor application restarts and detect issues or anomalies
    """
    def __init__(self):
        self.restarts = []
        self.max_samples = 4
        self.quick = 60.0  # this time or less (in seconds) is considered a quick restart

    def add(self):
        self.restarts.append(time.time())
        if len(self.restarts) > self.max_samples:
            self.restarts.pop(0)

    def excessive(self):
        """
        Determine if there has been excessive frequency of restarts.  Return True if the time between all the most recent restarts are less than the "quick" time.
        :return: True if restarts have been excessive
        """
        if len(self.restarts) < self.max_samples:
            excessive = False
        else:
            excessive = all([j - i <= self.quick for i, j in zip(self.restarts[:-1], self.restarts[1:])])
        return excessive
