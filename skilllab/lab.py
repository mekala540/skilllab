"""lab.html: an animated replay of a batch. Skills sit on a revolving ring; each run
streams from its skill (or the centre, for baselines) to one of the agent lanes and
lands as pass or fail. Self-contained: one file, no network."""

from __future__ import annotations

import json
from typing import List, Optional

LANES = 12


def to_lab_html(summary: dict, records: List[dict], meta: dict, lines: Optional[int] = None) -> str:
    """lines: how many raw lines results.jsonl had, so live mode reads on from there."""
    verdicts = {s["id"]: s for s in summary["skills"]}
    skills = []
    for s in meta["skills"]:
        v = verdicts.get(s["id"])
        skills.append({
            "id": s["id"], "name": s["name"], "source": s["source"],
            "upfront": s["upfront_tokens"], "onuse": s["onuse_tokens"],
            "verdict": v["verdict"] if v else "untested",
            "trigger": v["trigger_rate"] if v else None,
            "tasks": v["tasks"] if v else [],
        })
    best = {}
    for p in summary["pairs"]:
        if p["with_rate"] is not None and p["with_rate"] >= best.get(p["task"], (-1, ""))[0]:
            best[p["task"]] = (p["with_rate"], p["skill"])
    tasks = [{
        "id": t["id"], "title": t["title"],
        "base": (summary["baseline"].get(t["id"]) or {}).get("rate"),
        "best": best.get(t["id"], (None, ""))[0], "best_skill": best.get(t["id"], (None, ""))[1],
    } for t in meta["tasks"]]
    runs = [{
        "s": r.get("skill"), "t": r.get("task"), "ok": bool(r.get("passed")),
        "err": bool(r.get("infra_error")), "trig": bool(r.get("skill_triggered")),
        "c": r.get("cost_usd") or 0, "rep": r.get("repeat", 0),
    } for r in records]
    gaps = {k: len(v or []) for k, v in summary["gaps"].items()}
    data = {
        "model": _model_label(meta.get("model", "")), "skills": skills, "tasks": tasks, "runs": runs,
        "gaps": gaps, "lanes": LANES, "lines": len(records) if lines is None else lines, "threshold": summary["threshold"],
        "gapItems": {k: [_label(k, i) for i in (v or [])[:6]] for k, v in summary["gaps"].items()},
    }
    payload = json.dumps(data).replace("</", "<\\/")
    return TEMPLATE.replace("__DATA__", payload)


def _model_label(model: str) -> str:
    if model.startswith("cmd:"):
        parts = model[4:].split()
        script = next((p for p in parts if p.endswith(".py")), parts[0] if parts else "")
        return "custom agent " + script.rsplit("/", 1)[-1]
    return model


def _label(key: str, item) -> str:
    if isinstance(item, str):
        return item
    if key == "lookalikes":
        return f"{item['a']} ≈ {item['b']}"
    return item.get("id", "")


TEMPLATE = r"""<!doctype html>
<html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Skill Lab Replay</title>
<style>
:root{--bg:#050505;--panel:#0d0d0d;--line:#262626;--fg:#e5e5e5;--dim:#737373;--faint:#404040;
--helps:#4ade80;--hurts:#f87171;--flag:#fbbf24;--none:#a3a3a3;--untested:#525252}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:12px/1.45 ui-monospace,SFMono-Regular,Menlo,monospace}
header{display:flex;flex-wrap:wrap;align-items:flex-end;gap:8px 28px;padding:14px 16px 10px;border-bottom:1px solid var(--line)}
h1{margin:0;font-size:15px;letter-spacing:.12em;font-weight:700}
.sub{color:var(--dim);font-size:10px;letter-spacing:.1em;text-transform:uppercase}
.stat{min-width:64px}.stat b{display:block;font-size:15px}.stat span{color:var(--dim);font-size:10px;letter-spacing:.1em;text-transform:uppercase}
.ctl{margin-left:auto;display:flex;gap:6px}
button{background:var(--panel);color:var(--fg);border:1px solid var(--line);font:inherit;padding:4px 10px;cursor:pointer;border-radius:3px}
button:hover{border-color:var(--dim)}
#stage{position:relative}
canvas{display:block;width:100%;height:min(68vh,660px);min-height:420px}
#tip{position:absolute;pointer-events:none;background:#000c;border:1px solid var(--line);padding:8px 10px;max-width:300px;display:none;z-index:2}
.grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;padding:8px 16px 16px}
@media (max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
html,body{overflow-x:hidden}
@media (max-width:560px){.grid{grid-template-columns:minmax(0,1fr)}.ctl{margin-left:0}}
.p{background:var(--panel);border:1px solid var(--line);padding:10px;min-height:170px;overflow:hidden}
.p h2{margin:0 0 8px;font-size:10px;letter-spacing:.14em;color:var(--dim);font-weight:600}
.feed div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--dim)}
.feed div:first-child{color:var(--fg)}
.ok{color:var(--helps)}.bad{color:var(--hurts)}.warn{color:var(--flag)}
.bar{display:grid;grid-template-columns:96px 1fr 68px;gap:6px;align-items:center;margin:5px 0}
.bar .n{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--dim)}
.track{position:relative;height:12px;background:#171717}
.track i{position:absolute;left:0;top:0;bottom:0;display:block}
.track .b{background:var(--faint);height:5px}.track .w{top:6px;height:6px;background:var(--helps)}
.v div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.g div{margin-bottom:3px}.g small{color:var(--dim)}
.legend{color:var(--dim);font-size:10px;padding:0 16px 14px}
.legend i{display:inline-block;width:8px;height:8px;margin:0 4px 0 12px;vertical-align:middle}
</style></head><body>
<header>
 <div><h1>SKILLLAB / LIFT LAB</h1><div class=sub id=model></div></div>
 <div class=stat><b id=sSkills></b><span>skills</span></div>
 <div class=stat><b id=sTasks></b><span>tasks</span></div>
 <div class=stat><b id=sRuns></b><span>runs</span></div>
 <div class=stat><b id=sPass></b><span>passed</span></div>
 <div class=stat><b id=sCost></b><span>spend</span></div>
 <div class=stat><b id=sHelps class=ok></b><span>helps</span></div>
 <div class=stat><b id=sGaps class=warn></b><span>gaps</span></div>
 <div class=ctl><button id=bPlay>pause</button><button id=bSpeed>1×</button><button id=bRestart>restart</button></div>
</header>
<div id=stage><canvas id=cv></canvas><div id=tip></div></div>
<div class=legend>ring: one tick per skill, length = tokens on use ·
 <i style="background:var(--helps)"></i>helps<i style="background:var(--hurts)"></i>hurts/mixed
 <i style="background:var(--flag)"></i>flagged<i style="background:var(--none)"></i>no lift<i style="background:var(--untested)"></i>untested ·
 centre = baseline (no skill) · lanes = agents</div>
<div class=grid>
 <div class=p><h2>RUN FEED</h2><div class=feed id=feed></div></div>
 <div class=p><h2>LIFT BY TASK · BEST SKILL vs BASELINE</h2><div id=lift></div></div>
 <div class=p><h2>VERDICTS</h2><div class=v id=verd></div></div>
 <div class=p><h2>GAPS</h2><div class=g id=gaps></div></div>
</div>
<script>
const D = __DATA__;
const css = getComputedStyle(document.documentElement);
const C = k => css.getPropertyValue(k).trim();
const VC = {helps:C('--helps'), hurts:C('--hurts'), mixed:C('--hurts'), flagged:C('--flag'), 'no lift':C('--none'), untested:C('--untested')};
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const pct = x => x == null ? '–' : Math.round(x * 100) + '%';

const skills = D.skills, N = skills.length, NL = D.lanes;
const idx = {}; skills.forEach((s, i) => idx[s.id] = i);
// Chords: skills that share a task, the "cross-references" web inside the ring.
const chords = [];
const byTask = {};
skills.forEach((s, i) => s.tasks.forEach(t => (byTask[t] = byTask[t] || []).push(i)));
Object.values(byTask).forEach(list => {
  for (let a = 0; a < list.length; a++) for (let b = a + 1; b < list.length; b++) if (chords.length < 900) chords.push([list[a], list[b]]);
});
// Texture chords so even a small batch has a web.
for (let i = 0; i < Math.min(160, N * 3); i++) chords.push([(i * 7) % Math.max(N, 1), (i * 13 + 5) % Math.max(N, 1)]);

$('model').textContent = 'model ' + D.model + ' · replay of ' + D.runs.length + ' runs';
$('sSkills').textContent = N; $('sTasks').textContent = D.tasks.length;
$('sHelps').textContent = skills.filter(s => s.verdict === 'helps').length;
$('sGaps').textContent = Object.values(D.gaps).reduce((a, b) => a + b, 0);

// Static panels
$('lift').innerHTML = D.tasks.map(t => `<div class=bar title="${esc(t.title)}${t.best_skill ? ' · best: ' + esc(t.best_skill) : ''}">
  <span class=n>${esc(t.id)}</span><span class=track><i class=b style="width:${(t.base || 0) * 100}%"></i><i class=w style="width:${(t.best || 0) * 100}%"></i></span>
  <span>${pct(t.base)}→${pct(t.best)}</span></div>`).join('') || '<span class=n>no tasks run</span>';
const order = ['helps', 'mixed', 'hurts', 'flagged', 'no lift', 'untested'];
$('verd').innerHTML = order.map(v => {
  const list = skills.filter(s => s.verdict === v);
  if (!list.length) return '';
  return `<div style="color:${VC[v]}">${v.toUpperCase()} · ${list.length}</div>` +
    list.slice(0, v === 'untested' ? 2 : 4).map(s => `<div>&nbsp; ${esc(s.id)}</div>`).join('');
}).join('');
const GT = {costly_no_lift:'costs context, no lift', never_triggered:'relevant, never used', hurts:'made agent worse',
  ceiling_tasks:'tasks too easy', unsolved_tasks:'nobody solves', untested_claims:'claims with no task', needs_person:'needs a person', lookalikes:'look-alike skills'};
$('gaps').innerHTML = Object.keys(GT).filter(k => D.gaps[k]).map(k =>
  `<div><span class=warn>${D.gaps[k]}</span> ${GT[k]}<br><small>${esc((D.gapItems[k] || []).slice(0, 2).join(', '))}</small></div>`).join('') || '<small>none found</small>';

// Canvas
const cv = $('cv'), g = cv.getContext('2d');
let W, H, cx, cy, R, wide, lanes = [];
function layout() {
  const dpr = window.devicePixelRatio || 1;
  W = cv.clientWidth; H = cv.clientHeight;
  cv.width = W * dpr; cv.height = H * dpr; g.setTransform(dpr, 0, 0, dpr, 0, 0);
  wide = W >= 720;
  if (wide) { cx = W * 0.36; cy = H * 0.5; R = Math.min(W * 0.27, H * 0.38); }
  else { cx = W * 0.5; cy = H * 0.4; R = Math.min(W * 0.36, H * 0.3); }
  lanes = [];
  for (let i = 0; i < NL; i++) {
    if (wide) { const y = H * 0.08 + i * (H * 0.84 / (NL - 1)); lanes.push({x: W * 0.74, y, w: W - 16 - W * 0.74}); }
    else { const x = 16 + i * ((W - 32) / (NL - 1)); lanes.push({x, y: H * 0.88, w: 0}); }
  }
}
window.addEventListener('resize', layout); layout();

const laneState = Array.from({length: NL}, () => ({label: '', col: C('--faint'), hist: [], busy: 0, prog: 0}));
let rot = 0, speed = 1, playing = true, last = performance.now(), clock = 0;
let next = 0, nextAt = 0.6, active = [], parts = [], done = 0, passed = 0, spent = 0, endAt = null;
const glow = new Float32Array(N);

function pos(i, r) { const a = (i / Math.max(N, 1)) * Math.PI * 2 + rot; return [cx + Math.cos(a) * r, cy + Math.sin(a) * r, a]; }
function laneTarget(l) { const L = lanes[l]; return wide ? [L.x, L.y] : [L.x, L.y - 8]; }

function startRun(k) {
  const r = D.runs[k], lane = k % NL;
  const si = r.s != null ? idx[r.s] : undefined;
  const [x0, y0] = si === undefined ? [cx, cy] : pos(si, R + 4);
  const [x1, y1] = laneTarget(lane);
  if (si !== undefined) glow[si] = 1;
  const col = r.s ? (VC[(skills[si] || {}).verdict] || C('--none')) : '#d4d4d4';
  const n = 80;
  for (let j = 0; j < n; j++) parts.push({k, x0, y0, x1, y1, t: -j * 0.022 - Math.random() * 0.02, w: (Math.random() - 0.5) * 70, col, si});
  laneState[lane].busy = 1; laneState[lane].prog = 0;
  laneState[lane].label = (r.t || '') + ' · ' + (r.s ? r.s.split('/').pop() : 'baseline');
  active.push({k, lane, t: 0});
}

function finishRun(a) {
  const r = D.runs[a.k], L = laneState[a.lane];
  L.busy = 0;
  const col = r.err ? C('--flag') : r.ok ? C('--helps') : C('--hurts');
  L.col = col; L.hist.push(col); if (L.hist.length > 24) L.hist.shift();
  done++; if (r.ok && !r.err) passed++; spent += r.c;
  const status = r.err ? '<span class=warn>ERROR</span>' : r.ok ? '<span class=ok>PASS</span>' : '<span class=bad>FAIL</span>';
  const who = r.s ? esc(r.s) + (r.trig ? '' : ' <span class=warn>(not triggered)</span>') : 'baseline';
  const feed = $('feed');
  feed.insertAdjacentHTML('afterbegin', `<div>#${String(done).padStart(3, '0')} ${esc(r.t)} · ${who} → ${status}</div>`);
  while (feed.children.length > 11) feed.lastChild.remove();
}

function reset() {
  next = 0; nextAt = clock + 0.6; active = []; parts = []; done = passed = 0; spent = 0; endAt = null;
  laneState.forEach(L => { L.label = ''; L.hist = []; L.busy = 0; L.col = C('--faint'); });
  $('feed').innerHTML = '';
}

function bez(p, t) {
  // Quadratic curve that bows away from the ring; w makes the stream a wave.
  const mx = (p.x0 + p.x1) / 2, my = (p.y0 + p.y1) / 2 - 60;
  const u = 1 - t;
  let x = u * u * p.x0 + 2 * u * t * mx + t * t * p.x1;
  let y = u * u * p.y0 + 2 * u * t * my + t * t * p.y1;
  const s = Math.sin(t * Math.PI) * p.w * Math.sin(clock * 2 + p.w);
  return [x + s * 0.3, y + s];
}

function draw(dt) {
  g.globalCompositeOperation = 'source-over';
  g.fillStyle = 'rgba(5,5,5,0.32)'; g.fillRect(0, 0, W, H);   // trails
  rot += dt * 0.05;

  // Web of chords
  g.lineWidth = 0.6;
  for (const [a, b] of chords) {
    const [x1, y1] = pos(a, R - 16), [x2, y2] = pos(b, R - 16);
    g.strokeStyle = 'rgba(220,220,220,0.05)';
    g.beginPath(); g.moveTo(x1, y1); g.quadraticCurveTo(cx + (x1 + x2 - 2 * cx) * 0.15, cy + (y1 + y2 - 2 * cy) * 0.15, x2, y2); g.stroke();
  }
  // Rings
  g.strokeStyle = 'rgba(255,255,255,0.35)'; g.lineWidth = 1.2;
  g.beginPath(); g.arc(cx, cy, R, 0, Math.PI * 2); g.stroke();
  g.setLineDash([2, 5]); g.strokeStyle = 'rgba(255,255,255,0.15)';
  g.beginPath(); g.arc(cx, cy, R - 12, rot * 2, rot * 2 + Math.PI * 2); g.stroke();
  g.beginPath(); g.arc(cx, cy, R + 70, -rot, -rot + Math.PI * 2); g.stroke(); g.setLineDash([]);

  // Skill ticks + labels
  g.font = '9px ui-monospace,Menlo,monospace';
  for (let i = 0; i < N; i++) {
    const s = skills[i], len = 8 + Math.min(46, s.onuse / 180);
    const [x0, y0, a] = pos(i, R + 2), [x1, y1] = pos(i, R + 2 + len);
    glow[i] = Math.max(0, glow[i] - dt * 0.6);
    g.strokeStyle = VC[s.verdict] || C('--none'); g.globalAlpha = 0.55 + glow[i] * 0.45; g.lineWidth = 1.5 + glow[i] * 2.5;
    g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke();
    if (N <= 90 && R > 150) {
      g.save(); g.translate(...pos(i, R + 2 + len + 5).slice(0, 2));
      const flip = Math.cos(a) < 0; g.rotate(flip ? a + Math.PI : a);
      g.textAlign = flip ? 'right' : 'left'; g.textBaseline = 'middle';
      g.fillStyle = glow[i] > 0.05 ? '#fff' : 'rgba(200,200,200,0.45)';
      g.fillText(s.name.slice(0, 26), 0, 0); g.restore();
    }
  }
  g.globalAlpha = 1;
  // Baseline core
  g.fillStyle = '#111'; g.strokeStyle = 'rgba(255,255,255,0.4)';
  g.beginPath(); g.arc(cx, cy, 22, 0, Math.PI * 2); g.fill(); g.stroke();
  g.fillStyle = '#bbb'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('BASELINE', cx, cy);

  // Particles
  g.globalCompositeOperation = 'lighter';
  const keep = [];
  for (const p of parts) {
    p.t += dt * 0.7;
    if (p.t < 0) { keep.push(p); continue; }
    if (p.t > 1) continue;
    const [x, y] = bez(p, p.t);
    g.fillStyle = p.col; g.globalAlpha = 0.25 + 0.6 * Math.sin(p.t * Math.PI);
    g.fillRect(x, y, 2, 2);
    keep.push(p);
  }
  parts = keep; g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';

  // Lanes
  g.textAlign = 'left'; g.textBaseline = 'middle';
  lanes.forEach((L, i) => {
    const S = laneState[i];
    if (wide) {
      g.fillStyle = '#737373'; g.fillText(String(i + 1).padStart(2, '0'), L.x, L.y);
      g.fillStyle = '#141414'; g.fillRect(L.x + 22, L.y - 5, L.w - 22, 10);
      if (S.busy) { g.fillStyle = 'rgba(255,255,255,0.5)'; g.fillRect(L.x + 22, L.y - 5, (L.w - 22) * S.prog, 10); }
      S.hist.forEach((c, j) => { g.fillStyle = c; g.fillRect(L.x + 22 + j * 7, L.y + 8, 5, 5); });
      g.fillStyle = S.busy ? '#fff' : '#a3a3a3'; g.fillText(S.label.slice(0, Math.floor((L.w - 30) / 5.6)), L.x + 26, L.y - 13);
    } else {
      g.fillStyle = S.busy ? '#fff' : S.col; g.beginPath(); g.arc(L.x, L.y, 5, 0, Math.PI * 2); g.fill();
      S.hist.slice(-6).forEach((c, j) => { g.fillStyle = c; g.fillRect(L.x - 2, L.y + 10 + j * 6, 4, 4); });
    }
  });
}

function step(dt) {
  clock += dt * speed;
  if (nextAt < clock - 1) nextAt = clock;  // new live runs start now, not in a burst
  while (next < D.runs.length && clock >= nextAt) { startRun(next++); nextAt += 0.42; }
  for (const a of active) { a.t += dt * speed; laneState[a.lane].prog = Math.min(1, Math.max(0, (a.t - 1.4) / 0.9)); }
  const fin = active.filter(a => a.t >= 2.4); fin.forEach(finishRun);
  active = active.filter(a => a.t < 2.4);
  if (!LIVE && next >= D.runs.length && !active.length) { if (endAt === null) endAt = clock; else if (clock - endAt > 5) reset(); }
  draw(dt * speed);
}

function stats() {
  $('sRuns').textContent = done + '/' + D.runs.length;
  $('sPass').textContent = passed;
  $('sCost').textContent = '$' + spent.toFixed(2);
}

function tick(now) {
  const dt = Math.min(0.05, (now - last) / 1000); last = now;
  if (playing) step(dt);
  stats();
  requestAnimationFrame(tick);
}
g.fillStyle = '#050505'; g.fillRect(0, 0, W, H);
if (!D.runs.length) $('feed').innerHTML = '<div>no runs in this batch yet</div>';
// Live mode (lab.html?live, served by `skilllab watch`): pull new runs as they finish.
const LIVE = new URLSearchParams(location.search).has('live');
function toRun(r) {
  return {s: r.skill, t: r.task, ok: !!r.passed, err: !!r.infra_error, trig: !!r.skill_triggered,
          c: r.cost_usd || 0, rep: r.repeat || 0};
}
async function poll() {
  try {
    const text = await (await fetch('results.jsonl?' + Date.now(), {cache: 'no-store'})).text();
    const lines = text.split('\n').filter(l => l.trim());
    for (; D.lines < lines.length; D.lines++) {
      try { D.runs.push(toRun(JSON.parse(lines[D.lines]))); } catch (e) {}
    }
    $('model').textContent = 'model ' + D.model + ' · LIVE · ' + D.runs.length + ' runs so far';
  } catch (e) {}
}
if (LIVE) { poll(); setInterval(poll, 3000); }
// lab.html#t=12 starts the replay 12 seconds in.
const ff = parseFloat((location.hash.match(/t=([\d.]+)/) || [])[1]);
if (ff > 0) { for (let i = 0; i < ff * 30; i++) step(1 / 30); stats(); }
requestAnimationFrame(tick);

$('bPlay').onclick = e => { playing = !playing; e.target.textContent = playing ? 'pause' : 'play'; last = performance.now(); };
$('bSpeed').onclick = e => { speed = speed >= 4 ? 1 : speed * 2; e.target.textContent = speed + '×'; };
$('bRestart').onclick = () => { g.fillStyle = '#050505'; g.fillRect(0, 0, W, H); reset(); };

// Hover a tick for details
const tip = $('tip');
cv.addEventListener('mousemove', e => {
  const b = cv.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top;
  const d = Math.hypot(x - cx, y - cy);
  if (!N || d < R - 10 || d > R + 60) { tip.style.display = 'none'; return; }
  let a = Math.atan2(y - cy, x - cx) - rot; a = ((a % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
  const s = skills[Math.round(a / (2 * Math.PI) * N) % N];
  tip.innerHTML = `<b>${esc(s.id)}</b><br><span style="color:${VC[s.verdict]}">${s.verdict}</span>` +
    (s.tasks.length ? ` on ${esc(s.tasks.join(', '))}<br>${s.trigger === null ? 'started by the user' : 'triggered ' + pct(s.trigger)}` : '') +
    `<br>≈${s.upfront} tokens up front · ≈${s.onuse} on use`;
  tip.style.display = 'block';
  tip.style.left = Math.min(x + 14, W - 300) + 'px'; tip.style.top = (y + 14) + 'px';
});
cv.addEventListener('mouseleave', () => tip.style.display = 'none');
</script></body></html>
"""
