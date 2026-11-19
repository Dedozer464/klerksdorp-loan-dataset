"""
Logistic regression (IRLS / Newton-Raphson), standard library only.

Why two models? In this dataset every unemployed person has income = 0 and sector = 'Not Applicable',
so employment_status is perfectly determined by income and sector. Putting all of them in one model
makes the design matrix singular (perfect collinearity). So:

  Model A (everyone, n=600):   has_loan ~ employed + age
  Model B (employed, n=360):   has_loan ~ age + income + public_sector
"""
import csv, math, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "klerksdorp_loans.csv")
with open(path, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

def invert(m):
    n = len(m)
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(a[r][i]))
        if abs(a[p][i]) < 1e-12:
            raise ValueError("Singular matrix: perfectly collinear predictors")
        a[i], a[p] = a[p], a[i]
        piv = a[i][i]
        a[i] = [v / piv for v in a[i]]
        for r in range(n):
            if r != i:
                f = a[r][i]
                a[r] = [rv - f * iv for rv, iv in zip(a[r], a[i])]
    return [row[n:] for row in a]

def logit(X, y, names, iters=50):
    k = len(X[0])
    beta = [0.0] * k
    for _ in range(iters):
        eta = [sum(b * x for b, x in zip(beta, row)) for row in X]
        mu = [1 / (1 + math.exp(-e)) for e in eta]
        w = [m * (1 - m) for m in mu]
        xtwx = [[sum(w[i] * X[i][a] * X[i][b] for i in range(len(X))) for b in range(k)] for a in range(k)]
        grad = [sum(X[i][a] * (y[i] - mu[i]) for i in range(len(X))) for a in range(k)]
        cov = invert(xtwx)
        step = [sum(cov[a][b] * grad[b] for b in range(k)) for a in range(k)]
        beta = [b + s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-10:
            break
    eta = [sum(b * x for b, x in zip(beta, row)) for row in X]
    ll = sum(yi * e - math.log(1 + math.exp(e)) for yi, e in zip(y, eta))
    p0 = sum(y) / len(y)
    ll0 = len(y) * (p0 * math.log(p0) + (1 - p0) * math.log(1 - p0))
    out = []
    for j, name in enumerate(names):
        se = math.sqrt(cov[j][j])
        z = beta[j] / se
        out.append((name, beta[j], se, math.erfc(abs(z) / math.sqrt(2)),
                    math.exp(beta[j]), math.exp(beta[j] - 1.96 * se), math.exp(beta[j] + 1.96 * se)))
    return out, ll, ll0

def report(title, out, ll, ll0, n):
    print(f"\n{title}  (n={n}, McFadden pseudo-R2 = {1 - ll/ll0:.4f})")
    print(f"{'term':<24}{'coef':>8}{'SE':>8}{'p':>8}{'OR':>7}   95% CI")
    for name, b, se, p, o, lo, hi in out:
        print(f"{name:<24}{b:>8.3f}{se:>8.3f}{p:>8.3f}{o:>7.2f}   [{lo:.2f}, {hi:.2f}]")

# ---- Model A: everyone ----
XA = [[1.0, 1.0 if r["employment_status"] == "Employed" else 0.0, (int(r["age"]) - 35) / 10] for r in rows]
y = [float(r["has_loan"]) for r in rows]
report("Model A: has_loan ~ employed + age (per 10 yrs)",
       *logit(XA, y, ["intercept", "employed (vs unemployed)", "age (per 10 yrs)"]), len(rows))

# ---- Model B: employed only ----
emp = [r for r in rows if r["employment_status"] == "Employed"]
XB = [[1.0, (int(r["age"]) - 35) / 10, int(r["monthly_income_zar"]) / 10000,
       1.0 if r["sector"] == "Public" else 0.0] for r in emp]
yB = [float(r["has_loan"]) for r in emp]
report("Model B (employed only): has_loan ~ age + income + sector",
       *logit(XB, yB, ["intercept", "age (per 10 yrs)", "income (per R10,000)", "public (vs private)"]), len(emp))

# ---- Demonstrate why a single full model is impossible ----
print("\nAttempting has_loan ~ employed + age + income + sector on all 600 rows:")
XC = [[1.0, 1.0 if r["employment_status"] == "Employed" else 0.0, (int(r["age"]) - 35) / 10,
       int(r["monthly_income_zar"]) / 10000, 1.0 if r["sector"] == "Public" else 0.0] for r in rows]
try:
    # With 'employed' + 'public' + 'income', unemployed rows are fully identified by all-zero covariates
    # apart from age, so 'employed' = (income > 0) exactly. Check that directly:
    assert all((x[1] == 1.0) == (x[3] > 0) for x in XC)
    print("  employed == (income > 0) for every row -> 'employed' is redundant with income; model is not identifiable.")
except AssertionError:
    print("  not perfectly collinear")
