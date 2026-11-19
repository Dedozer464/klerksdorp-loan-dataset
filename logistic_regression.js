// Logistic regression (IRLS / Newton-Raphson), no dependencies. Mirrors python/logistic_regression.py.
//
// Model A (everyone, n=600):   has_loan ~ employed + age
// Model B (employed, n=360):   has_loan ~ age + income + public_sector
// A single model with employed + income + sector is not identifiable: every unemployed person has
// income = 0 and sector = 'Not Applicable', so 'employed' is exactly (income > 0).
const fs = require("fs");
const path = require("path");

const text = fs.readFileSync(path.join(__dirname, "..", "data", "klerksdorp_loans.csv"), "utf8").trim();
const [header, ...lines] = text.split(/\r?\n/);
const cols = header.split(",");
// No field in this dataset contains a comma, so a plain split is safe.
const rows = lines.map((l) => Object.fromEntries(l.split(",").map((v, i) => [cols[i], v])));

function invert(m) {
  const n = m.length;
  const a = m.map((row, i) => [...row, ...Array.from({ length: n }, (_, j) => (i === j ? 1 : 0))]);
  for (let i = 0; i < n; i++) {
    let p = i;
    for (let r = i + 1; r < n; r++) if (Math.abs(a[r][i]) > Math.abs(a[p][i])) p = r;
    if (Math.abs(a[p][i]) < 1e-12) throw new Error("Singular matrix: perfectly collinear predictors");
    [a[i], a[p]] = [a[p], a[i]];
    const piv = a[i][i];
    a[i] = a[i].map((v) => v / piv);
    for (let r = 0; r < n; r++) {
      if (r !== i) {
        const f = a[r][i];
        a[r] = a[r].map((v, c) => v - f * a[i][c]);
      }
    }
  }
  return a.map((row) => row.slice(n));
}

// Complementary error function (Numerical Recipes erfcc, ~1e-7 accuracy)
function erfc(x) {
  const z = Math.abs(x);
  const t = 1 / (1 + 0.5 * z);
  const r = t * Math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 +
    t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 +
    t * (-0.82215223 + t * 0.17087277)))))))));
  return x >= 0 ? r : 2 - r;
}

function logit(X, y, names, iters = 50) {
  const n = X.length, k = X[0].length;
  let beta = new Array(k).fill(0);
  let cov;
  for (let it = 0; it < iters; it++) {
    const mu = X.map((row) => 1 / (1 + Math.exp(-row.reduce((s, x, j) => s + x * beta[j], 0))));
    const w = mu.map((m) => m * (1 - m));
    const xtwx = Array.from({ length: k }, (_, a) =>
      Array.from({ length: k }, (_, b) => X.reduce((s, row, i) => s + w[i] * row[a] * row[b], 0)));
    const grad = Array.from({ length: k }, (_, a) => X.reduce((s, row, i) => s + row[a] * (y[i] - mu[i]), 0));
    cov = invert(xtwx);
    const step = cov.map((row) => row.reduce((s, c, b) => s + c * grad[b], 0));
    beta = beta.map((b, j) => b + step[j]);
    if (Math.max(...step.map(Math.abs)) < 1e-10) break;
  }
  const eta = X.map((row) => row.reduce((s, x, j) => s + x * beta[j], 0));
  const ll = y.reduce((s, yi, i) => s + yi * eta[i] - Math.log(1 + Math.exp(eta[i])), 0);
  const p0 = y.reduce((s, v) => s + v, 0) / n;
  const ll0 = n * (p0 * Math.log(p0) + (1 - p0) * Math.log(1 - p0));
  const out = names.map((name, j) => {
    const se = Math.sqrt(cov[j][j]);
    return {
      name, b: beta[j], se,
      p: erfc(Math.abs(beta[j] / se) / Math.SQRT2),
      or: Math.exp(beta[j]),
      lo: Math.exp(beta[j] - 1.96 * se),
      hi: Math.exp(beta[j] + 1.96 * se),
    };
  });
  return { out, ll, ll0, n };
}

function report(title, { out, ll, ll0, n }) {
  console.log(`\n${title}  (n=${n}, McFadden pseudo-R2 = ${(1 - ll / ll0).toFixed(4)})`);
  console.log("term".padEnd(24) + "coef".padStart(8) + "SE".padStart(8) + "p".padStart(8) + "OR".padStart(7) + "   95% CI");
  for (const r of out) {
    console.log(r.name.padEnd(24) + r.b.toFixed(3).padStart(8) + r.se.toFixed(3).padStart(8) +
      r.p.toFixed(3).padStart(8) + r.or.toFixed(2).padStart(7) + `   [${r.lo.toFixed(2)}, ${r.hi.toFixed(2)}]`);
  }
}

// ---- Model A: everyone ----
const XA = rows.map((r) => [1, r.employment_status === "Employed" ? 1 : 0, (Number(r.age) - 35) / 10]);
const yA = rows.map((r) => Number(r.has_loan));
report("Model A: has_loan ~ employed + age (per 10 yrs)",
  logit(XA, yA, ["intercept", "employed (vs unemployed)", "age (per 10 yrs)"]));

// ---- Model B: employed only ----
const emp = rows.filter((r) => r.employment_status === "Employed");
const XB = emp.map((r) => [1, (Number(r.age) - 35) / 10, Number(r.monthly_income_zar) / 10000, r.sector === "Public" ? 1 : 0]);
const yB = emp.map((r) => Number(r.has_loan));
report("Model B (employed only): has_loan ~ age + income + sector",
  logit(XB, yB, ["intercept", "age (per 10 yrs)", "income (per R10,000)", "public (vs private)"]));

// ---- Why a single full model is impossible ----
console.log("\nAttempting has_loan ~ employed + age + income + sector on all 600 rows:");
const redundant = rows.every((r) => (r.employment_status === "Employed") === (Number(r.monthly_income_zar) > 0));
console.log(redundant
  ? "  employed == (income > 0) for every row -> 'employed' is redundant with income; model is not identifiable."
  : "  not perfectly collinear");
