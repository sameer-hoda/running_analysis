#!/usr/bin/env node
/* Voice-coach canonical tour contract (REBUILD-18, durable, zero-dep).
 * Extracts the generator from site/report_template.html and proves per
 * fixture: exact spoken intro (no name — Kabeer is display-only), foot-first
 * order, hip second when suitable, hard cap (default <=18 s, demo 18-25 s
 * ending on the upload ask), whole-thought beats from this photo's data,
 * unclear skipped silently. Across fixtures: distinct.
 * Run: node site/demo_script_test.js site/report_template.html <a.json> <b.json> <c.json>
 */
const fs = require("fs");

const FUNCS = ["estSecs", "clause", "demoBeatText", "footBeatText",
  "buildCappedStory", "buildDemoStory", "buildDefaultStory", "coachStyleForZone",
  "zoneSuitable", "suitableFindings", "zoneEntry", "zoneTitle", "zoneFocus", "isUnclear"];
const VARS = ["INTRO_TEXT", "CTA_TEXT", "DEMO_CTA", "DEMO_BUDGET_S", "DEMO_WINDOW_S",
  "DEMO_START_S", "DEMO_GAP_MS", "DEMO_PACE", "COACH_STYLE", "COACH_INTRO_STYLE", "ZONE_KB"];
const INTRO = "Hi, I am the running coach. Let us deep dive into the model. Here is what your running form is hiding.";
const HEDGE = ["three", "can't assess", "cannot assess", "can't judge",
  "another angle", "another view", "another photo", "unclear"];
const FOOT_REWRITE = ["ahead of your body", "needs a side view"];

function extract(src, name) {
  const m = src.match(new RegExp("(?:function\\s+" + name + "\\s*\\(|var\\s+" + name + "\\s*=)"));
  if (!m) throw new Error("not found: " + name);
  const isFunc = /^function/.test(m[0]);
  let i = m.index + m[0].length;
  if (!isFunc) {
    while (i < src.length && /\s/.test(src[i])) i++;
    if (src[i] !== "{" && src[i] !== "[") {
      const e = src.indexOf(";", i);
      if (e < 0) throw new Error("no end: " + name);
      return src.slice(m.index, e + 1);
    }
  }
  const open = isFunc ? "{" : src[i];
  i = src.indexOf(open, isFunc ? m.index : i);
  if (i < 0) throw new Error("no body: " + name);
  const stack = [];
  let str = null, line = false, block = false;
  for (let j = i; j < src.length; j++) {
    const c = src[j], nx = src[j + 1];
    if (str) {
      if (c === "\\") { j++; continue; }
      if (c === str) str = null;
      continue;
    }
    if (line) { if (c === "\n") line = false; continue; }
    if (block) { if (c === "*" && nx === "/") { block = false; j++; } continue; }
    if (c === "/" && nx === "/") { line = true; j++; continue; }
    if (c === "/" && nx === "*") { block = true; j++; continue; }
    if (c === "'" || c === '"' || c === "`") { str = c; continue; }
    if (c === "{" || c === "[") stack.push(c);
    if (c === "}" || c === "]") {
      const o = stack.pop();
      if ((c === "}" && o !== "{") || (c === "]" && o !== "[")) throw new Error("mismatch: " + name);
      if (stack.length === 0) return src.slice(m.index, j + 1);
    }
  }
  throw new Error("unbalanced: " + name);
}

function loadBundle(templatePath, fixturePath) {
  const src = fs.readFileSync(templatePath, "utf8");
  const parts = FUNCS.concat(VARS).map((n) => extract(src, n));
  const analysis = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
  const stub = "var ANALYSIS=" + JSON.stringify(analysis) + ";\n" +
    "var SHOWCASE=false;\n" +
    "var __store={};\n" +
    "var localStorage={getItem:(k)=>__store[k]||null,setItem:(k,v)=>{__store[k]=String(v);}};\n";
  const vm = require("vm");
  const ctx = vm.createContext({ console });
  vm.runInContext(stub + parts.join("\n"), ctx, { filename: "bundle.js" });
  return ctx;
}

function estTotal(ctx, steps) {
  let t = ctx.DEMO_START_S;
  for (const s of steps) t += ctx.estSecs(s.text);
  t += (ctx.DEMO_GAP_MS / 1000) * Math.max(0, steps.length - 1);
  return t;
}

function check(cond, msg) {
  console.log((cond ? "ok - " : "FAIL - ") + msg);
  if (!cond) { check.failed = true; }
}
check.failed = false;

function auditSteps(ctx, a, tag, steps, isDemo) {
  const texts = steps.map((s) => s.text);
  const cap = isDemo ? ctx.DEMO_WINDOW_S : ctx.DEMO_BUDGET_S;
  check(steps.length >= 2, `${tag}: intro + beats (${steps.length} steps)`);
  check(texts[0] === INTRO, `${tag}: exact spoken intro (no name)`);
  check(!/kabeer|darmani/i.test(texts.join(" ")), `${tag}: spoken script never names the coach`);
  const beats = steps.filter((s) => s.kind === "focus");
  check(beats.length >= 1 && beats[0].zone === "feet_strike", `${tag}: footstrike first`);
  check(beats.every((s) => s.zone && s.view === "zone"), `${tag}: every beat carries its zone (move sync)`);
  const total = estTotal(ctx, steps);
  check(total <= cap + 1e-9, `${tag}: est ${total.toFixed(2)}s <= ${cap}s ${isDemo ? "(demo 18-25s window)" : "(default 18s cap)"}`);
  // hip second when suitable, third never foot/hip
  const hipBeat = beats.find((s) => s.zone === "hips_pelvis");
  if (hipBeat) check(beats[1] && beats[1].zone === "hips_pelvis", `${tag}: hip second`);
  const rest = beats.slice(hipBeat ? 2 : 1);
  check(rest.every((s) => s.zone !== "feet_strike" && s.zone !== "hips_pelvis"),
    `${tag}: third finding is neither foot nor hip`);
  check(beats.every((s) => ctx.zoneSuitable(s.zone) ||
    (s.zone === "feet_strike" && /needs a side view/.test(s.text))), `${tag}: suitable-only (silently skipped)`);
  // DEMO-CTA: the homepage cut ends on the upload ask; a user's own report
  // keeps the free-play close (when it fits).
  const last = steps[steps.length - 1];
  if (isDemo) {
    check(last && last.kind === "free" && last.text === ctx.DEMO_CTA, `${tag}: demo ends on the upload ask`);
  } else if (last && last.kind === "free") {
    check(last.text === ctx.CTA_TEXT, `${tag}: canonical CTA`);
  }
  const low = texts.join(" ").toLowerCase();
  check(!HEDGE.some((h) => low.includes(h)), `${tag}: no counts/hedges`);
  // ORDINAL-FIX: ordinals derive from final spoken order — the spoken beats
  // must number clean First, Second, Third with no gap, even when the
  // suitability skip drops a beat.
  const ords = beats.map((s) => (s.text.match(/^(First|Second|Third), /) || [])[1]);
  check(beats.length <= 3, `${tag}: at most 3 spoken finding beats`);
  check(JSON.stringify(ords) === JSON.stringify(["First", "Second", "Third"].slice(0, beats.length)),
    `${tag}: ordinals recount over spoken beats only (${ords.join(",") || "none"})`);
  // Whole-thought: hip/third beats are verbatim source clauses; foot may use
  // the overstride rewrite or the fixed retake ask.
  const src = JSON.stringify(a.findings || []);
  for (const s of beats) {
    const body = s.text.replace(/^(First|Second|Third), /, "").replace(/\.$/, "");
    if (s.zone === "feet_strike") {
      const footOk = FOOT_REWRITE.some((w) => s.text.includes(w)) ||
        (src.includes(body.slice(0, 20)) && s.text.length > 20);
      check(footOk, `${tag}: foot beat (overstride style / data / retake)`);
      continue;
    }
    check(body.length > 8 && src.toLowerCase().includes(body.toLowerCase()),
      `${tag}: beat verbatim from analysis`);
  }
  return texts.join("\n");
}

function main() {
  const [tpl, ...fixtures] = process.argv.slice(2);
  if (!tpl || fixtures.length < 3) {
    console.error("usage: node site/demo_script_test.js <template> <a.json> <b.json> <c.json>");
    process.exit(2);
  }
  const sigs = [];
  for (const f of fixtures) {
    const ctx = loadBundle(tpl, f);
    const tag = f.split("/").slice(-2, -1)[0] || f;
    for (const [bname, build] of [["demo", "buildDemoStory"], ["default", "buildDefaultStory"]]) {
      const sig = auditSteps(ctx, JSON.parse(fs.readFileSync(f, "utf8")), `${tag}:${bname}`, ctx[build](), bname === "demo");
      check(ctx[build]().map((s) => s.text).join("\n") === sig, `${tag}:${bname} deterministic per photo`);
      sigs.push(tag + ":" + bname + "::" + sig);
    }
    if (tag === "419d46c0abbf") {
      const all = sigs.filter((s) => s.startsWith(tag)).join(" ").toLowerCase();
      check(!/pelvis|pelvic|hip drop|belt line/.test(all), "419d: no pelvic language without contact");
      check(!/overstride|braking/.test(all), "419d: no braking/overstride claims in flight");
    }
    if (tag === "aeb979a86e8b") {
      const all = sigs.filter((s) => s.startsWith(tag)).join(" ");
      check(/ahead of your body/.test(all), "aeb9: overstride-style foot beat");
      const zones = ctx.buildDemoStory().filter((s) => s.kind === "focus").map((s) => s.zone);
      check(!zones.includes("hips_pelvis"), "aeb9: hips skipped (insufficient side view)");
      check(JSON.stringify(zones) === JSON.stringify(["feet_strike", "trunk_lean"]),
        `aeb9: foot,hip-skipped,then worst suitable (${zones.join(",")})`);
    }
  }
  const demoSigs = sigs.filter((s, i) => i % 2 === 0);
  check(new Set(demoSigs).size === demoSigs.length, "3 photos give 3 different scripts");
  process.exit(check.failed ? 1 : 0);
}
main();
