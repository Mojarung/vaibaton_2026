import http from "k6/http";
import { check } from "k6";
import { SharedArray } from "k6/data";
import { Counter } from "k6/metrics";

const TARGET = __ENV.TARGET;
const RATE = Number(__ENV.RATE || 1000);
const DURATION = __ENV.DURATION || "60s";
const RAMP = __ENV.RAMP || "20s";
const VUS = Number(__ENV.VUS || 200);

const texts = new SharedArray("texts", () => {
  const out = [];
  for (const file of ["/datasets/blind.jsonl", "/datasets/generated.jsonl"]) {
    let raw = "";
    try { raw = open(file); } catch (e) { continue; }
    for (const line of raw.split("\n")) {
      if (line.trim()) out.push(JSON.parse(line).text);
    }
  }
  return out;
});

const roundtripErrors = new Counter("roundtrip_errors");

export const options = {
  discardResponseBodies: false,
  scenarios: {
    process: {
      executor: "ramping-arrival-rate",
      startRate: Math.max(1, Math.floor(RATE / 20)),
      timeUnit: "1s",
      preAllocatedVUs: VUS,
      maxVUs: VUS,
      stages: [
        { target: Math.floor(RATE / 2), duration: RAMP },
        { target: Math.floor(RATE / 2), duration: DURATION },
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<500", "p(99)<1000"],
    http_req_failed: ["rate<0.01"],
    checks: ["rate>0.99"],
  },
  summaryTrendStats: ["avg", "min", "med", "p(90)", "p(95)", "p(99)", "max"],
};

let seed = 0;

function nextUnit() {
  if (seed === 0) seed = (__VU * 2654435761) >>> 0 || 1;
  seed ^= seed << 13;
  seed ^= seed >>> 17;
  seed ^= seed << 5;
  seed >>>= 0;
  return seed / 4294967296;
}

function pieceCount(r) {
  if (r < 0.85) return 1;
  if (r < 0.98) return 8;
  return 60;
}

function pickText() {
  const n = pieceCount(nextUnit());
  const parts = [];
  for (let i = 0; i < n; i++) parts.push(texts[Math.floor(nextUnit() * texts.length)]);
  return parts.join("\n");
}

const params = { headers: { "Content-Type": "application/json" }, timeout: "10s" };

export default function maskRoundtrip() {
  const text = pickText();
  const id = `k6-${__VU}-${__ITER}-${Date.now()}`;
  const masked = http.post(`${TARGET}/process`, JSON.stringify({ payload: text, payload_id: id }), params);
  const okMask = check(masked, { "mask 200": (r) => r.status === 200 });
  if (!okMask) return;
  const maskedText = masked.json("result");
  const back = http.post(`${TARGET}/process`, JSON.stringify({ payload: maskedText, payload_id: id }), params);
  const exact = back.status === 200 && back.json("result") === text;
  if (!exact) roundtripErrors.add(1);
  check(back, { "unmask 200": (r) => r.status === 200, "roundtrip exact": () => exact });
}
