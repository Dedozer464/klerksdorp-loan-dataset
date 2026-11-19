// Chi-square test of independence: employment status vs. having a loan. No dependencies.
const fs = require("fs");
const path = require("path");

const text = fs.readFileSync(path.join(__dirname, "..", "data", "klerksdorp_loans.csv"), "utf8").trim();
const [header, ...lines] = text.split(/\r?\n/);
const cols = header.split(",");
// No field in this dataset contains a comma, so a plain split is safe.
const rows = lines.map((l) => Object.fromEntries(l.split(",").map((v, i) => [cols[i], v])));

const count = (status, loan) =>
  rows.filter((r) => r.employment_status === status && Number(r.has_loan) === loan).length;

const a = count("Employed", 1), b = count("Employed", 0);
const c = count("Unemployed", 1), d = count("Unemployed", 0);
const n = a + b + c + d;

// Complementary error function (Numerical Recipes erfcc, ~1e-7 accuracy)
function erfc(x) {
  const z = Math.abs(x);
  const t = 1 / (1 + 0.5 * z);
  const r = t * Math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 +
    t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 +
    t * (-0.82215223 + t * 0.17087277)))))))));
  return x >= 0 ? r : 2 - r;
}

const chi2 = (n * (a * d - b * c) ** 2) / ((a + b) * (c + d) * (a + c) * (b + d));
const p = erfc(Math.sqrt(chi2 / 2));
const odds = (a * d) / (b * c);
const se = Math.sqrt(1 / a + 1 / b + 1 / c + 1 / d);

console.log(`Employed:   ${a}/${a + b} with a loan (${((100 * a) / (a + b)).toFixed(1)}%)`);
console.log(`Unemployed: ${c}/${c + d} with a loan (${((100 * c) / (c + d)).toFixed(1)}%)`);
console.log(`Pearson chi-square (df=1, no continuity correction) = ${chi2.toFixed(3)}`);
console.log(`p-value = ${p.toFixed(4)} (alpha = 0.05 -> ${p < 0.05 ? "significant" : "NOT significant"})`);
console.log(`Odds ratio = ${odds.toFixed(2)}, 95% CI [${Math.exp(Math.log(odds) - 1.96 * se).toFixed(2)}, ${Math.exp(Math.log(odds) + 1.96 * se).toFixed(2)}]`);
