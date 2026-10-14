import { test } from "node:test";
import assert from "node:assert/strict";
import { TtlLru } from "../src/cache.mjs";

test("a recently read entry survives eviction", () => {
  let t = 0;
  const c = new TtlLru({ max: 2, ttlMs: 1000, now: () => t });
  c.set("a", 1);
  c.set("b", 2);
  assert.equal(c.get("a"), 1);
  c.set("c", 3);
  assert.equal(c.get("a"), 1);
  assert.equal(c.get("b"), undefined);
});
