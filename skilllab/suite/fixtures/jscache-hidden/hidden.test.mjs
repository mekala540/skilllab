import { test } from "node:test";
import assert from "node:assert/strict";
import { TtlLru } from "./src/cache.mjs";

function make(max = 2, ttlMs = 1000) {
  const clock = { t: 0 };
  return [new TtlLru({ max, ttlMs, now: () => clock.t }), clock];
}

test("get refreshes recency", () => {
  const [c] = make();
  c.set("a", 1).set("b", 2);
  c.get("a");
  c.set("c", 3);
  assert.equal(c.get("a"), 1);
  assert.equal(c.get("b"), undefined);
});

test("re-setting a key refreshes recency", () => {
  const [c] = make();
  c.set("a", 1).set("b", 2);
  c.set("a", 10);
  c.set("c", 3);
  assert.equal(c.get("a"), 10);
  assert.equal(c.get("b"), undefined);
  assert.equal(c.get("c"), 3);
});

test("expires exactly at insert time + ttl", () => {
  const [c, clock] = make(2, 100);
  c.set("a", 1);
  clock.t = 99;
  assert.equal(c.get("a"), 1);
  clock.t = 100;
  assert.equal(c.get("a"), undefined);
});

test("per-entry ttl", () => {
  const [c, clock] = make(3, 100);
  c.set("short", 1, 10).set("long", 2);
  clock.t = 50;
  assert.equal(c.get("short"), undefined);
  assert.equal(c.get("long"), 2);
});

test("size counts only live entries", () => {
  const [c, clock] = make(3, 100);
  c.set("a", 1).set("b", 2, 10);
  clock.t = 20;
  assert.equal(c.size, 1);
});

test("expired entries are dropped before evicting live ones", () => {
  const [c, clock] = make(2, 100);
  c.set("live", 1);
  c.set("dying", 2, 10);
  clock.t = 50;
  c.set("new", 3);
  assert.equal(c.get("live"), 1);
  assert.equal(c.get("new"), 3);
});

test("validates options", () => {
  assert.throws(() => new TtlLru({ max: 0, ttlMs: 1 }), RangeError);
  assert.throws(() => new TtlLru({ max: 1, ttlMs: 0 }), RangeError);
});
