import http from "k6/http";

const TARGET = __ENV.TARGET;
const RATE = Number(__ENV.RATE || 5000);

export const options = {
  scenarios: {
    health: {
      executor: "constant-arrival-rate",
      rate: RATE,
      timeUnit: "1s",
      duration: __ENV.DURATION || "20s",
      preAllocatedVUs: Number(__ENV.VUS || 200),
      maxVUs: Number(__ENV.VUS || 200),
    },
  },
  summaryTrendStats: ["avg", "med", "p(95)", "p(99)", "max"],
};

export default function healthProbe() {
  http.get(`${TARGET}/health/live`);
}
