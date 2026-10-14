import time


class TokenBucket:
    """Token-bucket rate limiter.

    - capacity and rate must be > 0, otherwise ValueError
    - the bucket starts full, with `capacity` tokens
    - tokens refill continuously at `rate` per second and never exceed `capacity`
    - allow(cost=1): if at least `cost` tokens are available, take them and return True;
      otherwise take nothing and return False
    - wait_time(cost=1): seconds until allow(cost) would succeed; 0.0 if it would now
    - for both, cost must be > 0 and <= capacity, otherwise ValueError
    - time comes from `clock()` (seconds). If the clock goes backwards, no tokens are
      added or removed, and refilling resumes only once the clock passes the latest
      time already seen
    """

    def __init__(self, capacity, rate, clock=time.monotonic):
        if capacity <= 0:
            raise ValueError("capacity must be > 0")
        if rate <= 0:
            raise ValueError("rate must be > 0")
        self.capacity = capacity
        self.rate = rate
        self.clock = clock
        self.tokens = float(capacity)
        self.last = clock()

    def _check_cost(self, cost):
        if cost <= 0:
            raise ValueError("cost must be > 0")
        if cost > self.capacity:
            raise ValueError("cost must be <= capacity")

    def _refill(self):
        now = self.clock()
        elapsed = now - self.last
        if elapsed > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last = max(self.last, now)

    def allow(self, cost=1):
        self._check_cost(cost)
        self._refill()
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False

    def wait_time(self, cost=1):
        self._check_cost(cost)
        self._refill()
        deficit = cost - self.tokens
        if deficit <= 0:
            return 0.0
        return deficit / self.rate
