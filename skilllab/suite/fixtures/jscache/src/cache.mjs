/**
 * LRU cache with per-entry time-to-live.
 *
 * - `new TtlLru({ max, ttlMs, now })`: holds at most `max` live entries. `now()` returns
 *   milliseconds (defaults to Date.now) so tests can control time.
 * - `set(key, value, ttlMs = default)`: insert or replace; the entry becomes most recently used.
 * - `get(key)`: the value, or undefined if missing or expired. A hit makes the entry most
 *   recently used. Expired entries are removed when seen.
 * - `size`: number of live (unexpired) entries.
 * - When a `set` would exceed `max` live entries, expired entries are dropped first, then the
 *   least recently used live entry is evicted.
 * - An entry expires exactly when now() >= its insert time + ttl.
 */
export class TtlLru {
  constructor({ max, ttlMs, now = Date.now }) {
    if (!(max > 0)) throw new RangeError("max must be > 0");
    if (!(ttlMs > 0)) throw new RangeError("ttlMs must be > 0");
    this.max = max;
    this.ttlMs = ttlMs;
    this.now = now;
    this.map = new Map(); // key -> { value, expires }; Map keeps insertion order
  }

  #expired(entry) {
    return this.now() > entry.expires;
  }

  get(key) {
    const entry = this.map.get(key);
    if (!entry) return undefined;
    if (this.#expired(entry)) {
      this.map.delete(key);
      return undefined;
    }
    return entry.value;
  }

  set(key, value, ttlMs = this.ttlMs) {
    this.map.set(key, { value, expires: this.now() + ttlMs });
    if (this.map.size > this.max) {
      const oldest = this.map.keys().next().value;
      this.map.delete(oldest);
    }
    return this;
  }

  get size() {
    return this.map.size;
  }
}
