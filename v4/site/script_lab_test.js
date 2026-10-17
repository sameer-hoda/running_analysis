#!/usr/bin/env node
/* Script-lab narration contract (quality-voice, durable, zero-dep).
 * Extracts the REWRITE builder from site/script-lab.html and proves per
 * fixture: exact canonical intro, est <= budget, every focus beat quotes its
 * zone's analysis (specific flaw + fix, never generic), retakes at most one
 * per script and never leading, ordinals recount cleanly. 961e6b5de398 must
 * name the head-turn + ankle-lean with 2+ take-home fixes.
 * Run: node site/script_lab_test.js site/script-lab.html <a.json> [<b.json> ...]
 */
const fs = require("fs");

const FUNCS = ["curClause", "curZoneEntry", "curZoneSuitable", "labLower",
  "labZoneEntry", "labZoneSuitable", "labFixSecond", "labQuoteFields",
  "labQuotes", "labFlaw", "labFix", "labBeatBody", "labPraise", "labRetakeText",
  "labEstSecs", "buildLabStory"];
const VARS = ["LAB_BUDGET_S", "LAB_FLAW_MAX", "LAB_FIX_MAX", "LAB_START_S",
  "LAB_GAP_MS", "LAB_INTRO_TEXT", "LAB_CTA_TEXT"];
const INTRO = "Hi, I am the running coach. Let us deep dive into the model. Here is what your running form is hiding.";

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

function loadBundle(labPath, fixturePath) {
  const src = fs.readFileSync(labPath, "utf8");
  const parts = FUNCS.concat(VARS).map((n) => extract(src, n));
  const analysis = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
  const stub = "var ANALYSIS=" + JSON.stringify(analysis) + ";\n";
  const vm = require("vm");
  const ctx = vm.createContext({ console });
  vm.runInContext(stub + parts.join("\n"), ctx, { filename: "lab-bundle.js" });
  return { ctx, analysis };
}

function estTotal(ctx, steps) {
  let t = ctx.LAB_START_S;
  for (const s of steps) t += ctx.labEstSecs(s.text);
  t += (ctx.LAB_GAP_MS / 1000) * Math.max(0, steps.length - 1);
  return t;
}

function check(cond, msg) {
  console.log((cond ? "ok - " : "FAIL - ") + msg);
  if (!cond) { check.failed = true; }
}
check.failed = false;

function auditSteps(ctx, tag, steps) {
  const texts = steps.map((s) => s.text);
  check(steps.length >= 2, `${tag}: intro + beats (${steps.length} steps)`);
  check(texts[0] === INTRO, `${tag}: exact canonical intro`);
  const beats = steps.filter((s) => s.kind === "focus");
  const retakes = steps.filter((s) => s.kind === "retake");
  check(beats.length >= 1, `${tag}: at least one flaw+fix beat`);
  check(beats.every((s) => s.zone), `${tag}: every beat carries its zone`);
  // Specificity: each focus beat must quote its zone's analysis text.
  for (const s of beats) {
    const q = ctx.labQuotes(s.text, s.zone);
    check(!!q, `${tag}: beat quotes analysis [${s.zone}]: ${q || s.text}`);
    check(/—/.test(s.text), `${tag}: beat joins flaw + fix [${s.zone}]`);
  }
  // Retake rule: max one per script, never the lead beat.
  check(retakes.length <= 1, `${tag}: at most one retake (${retakes.length})`);
  if (retakes.length) {
    check(steps[1].kind !== "retake", `${tag}: retake never leads`);
    check(!!ctx.labQuotes(retakes[0].text, retakes[0].zone),
      `${tag}: retake names what is needed`);
  }
  if (beats.length) check(steps[1].kind === "focus", `${tag}: lead beat is a flaw+fix`);
  const total = estTotal(ctx, steps);
  check(total <= ctx.LAB_BUDGET_S + 1e-9, `${tag}: est ${total.toFixed(2)}s <= ${ctx.LAB_BUDGET_S}s`);
  // Ordinals recount over spoken flaw beats only.
  const ords = beats.map((s) => (s.text.match(/^(First|Second|Third), /) || [])[1]);
  check(JSON.stringify(ords) === JSON.stringify(["First", "Second", "Third"].slice(0, beats.length)),
    `${tag}: ordinals clean (${ords.join(",") || "none"})`);
  check(ctx.buildLabStory().map((s) => s.text).join("\n") === texts.join("\n"),
    `${tag}: deterministic per photo`);
  return texts.join("\n");
}

function loadBundleObj(labPath, analysis) {
  const src = fs.readFileSync(labPath, "utf8");
  const parts = FUNCS.concat(VARS).map((n) => extract(src, n));
  const stub = "var ANALYSIS=" + JSON.stringify(analysis) + ";\n";
  const vm = require("vm");
  const ctx = vm.createContext({ console });
  vm.runInContext(stub + parts.join("\n"), ctx, { filename: "lab-bundle.js" });
  return { ctx, analysis };
}

function auditSynth(lab) {
  // Retake fits: one short flaw beat + one unscorable zone.
  const a = { camera_angle: "side", gait_phase: "stance", foot_contact: "yes",
    overall_score: 70, overall_label: "Fair", findings: [
      { zone: "head_neck", title: "Head", status: "fair", zone_score: 60,
        tldr: "Head tilted left.", observation: "Head tilted left.",
        signs: ["Head tilt"], action: ["Look straight ahead"] },
      { zone: "hips_pelvis", title: "Hips", status: "fair", zone_score: 65,
        tldr: "Hips look uneven.", observation: "Hips look uneven.",
        signs: ["Uneven hips"], action: ["Level the hips"] },
    ],
    insufficient: [{ zone: "feet_strike", title: "Foot strike",
      why: "No contact visible.", needed_view: "side view at contact" }] };
  const { ctx } = loadBundleObj(lab, a);
  const steps = ctx.buildLabStory();
  const kinds = steps.map((s) => s.kind);
  check(steps.length >= 3, `synth: intro + flaw + retake (${kinds.join(",")})`);
  check(steps[1].kind === "focus", "synth: flaw beat leads, never the retake");
  const rt = steps.filter((s) => s.kind === "retake");
  check(rt.length === 1, `synth: exactly one retake (${rt.length})`);
  if (rt.length) check(/side view at contact/.test(rt[0].text), "synth: retake names needed view");
  check(estTotal(ctx, steps) <= ctx.LAB_BUDGET_S + 1e-9, "synth: retake script within budget");
  // No suitable findings: retake must NOT appear alone as the lead.
  const b = { camera_angle: "side", gait_phase: "swing", foot_contact: "no",
    overall_score: 70, overall_label: "Fair",
    findings: [{ zone: "hips_pelvis", title: "Hips", status: "fair",
      zone_score: 65, tldr: "Hips look uneven.", observation: "Hips look uneven.",
      signs: ["Uneven hips"], action: ["Level the hips"] }],
    insufficient: [{ zone: "feet_strike", title: "Foot strike",
      why: "No contact visible.", needed_view: "side view at contact" }] };
  const c2 = loadBundleObj(lab, b).ctx;
  const s2 = c2.buildLabStory();
  check(s2.filter((s) => s.kind === "retake").length === 0, "synth: no orphan retake without a flaw beat");
  check(s2[0].text === INTRO, "synth: intro still leads");
}

function main() {
  const [lab, ...fixtures] = process.argv.slice(2);
  if (!lab || fixtures.length < 1) {
    console.error("usage: node site/script_lab_test.js <script-lab.html> <a.json> [...]");
    process.exit(2);
  }
  auditSynth(lab);
  const sigs = [];
  for (const f of fixtures) {
    const { ctx } = loadBundle(lab, f);
    const tag = f.split("/").slice(-2, -1)[0] || f;
    sigs.push(tag + "::" + auditSteps(ctx, tag, ctx.buildLabStory()));
    if (/961e6b5de398/.test(f)) {
      const all = sigs[sigs.length - 1].toLowerCase();
      check(/spectator/.test(all), "961e: names the head-turn (spectator)");
      check(/ankle/.test(all), "961e: names the missing ankle-lean");
      const nFix = ctx.buildLabStory().filter((s) => s.kind === "focus").length;
      check(nFix >= 2, `961e: 2+ take-home fixes (${nFix})`);
    }
  }
  check(new Set(sigs).size === sigs.length, `${fixtures.length} photos give distinct lab scripts`);
  process.exit(check.failed ? 1 : 0);
}
main();
