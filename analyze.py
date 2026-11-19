"""Chi-square test of independence: employment status vs. having a loan. Standard library only."""
import csv, math, os

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "klerksdorp_loans.csv")
with open(path, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

def count(status, loan):
    return sum(1 for r in rows if r["employment_status"] == status and int(r["has_loan"]) == loan)

a, b = count("Employed", 1), count("Employed", 0)       # employed: loan / no loan
c, d = count("Unemployed", 1), count("Unemployed", 0)   # unemployed: loan / no loan
n = a + b + c + d

chi2 = n * (a * d - b * c) ** 2 / ((a + b) * (c + d) * (a + c) * (b + d))
p = math.erfc(math.sqrt(chi2 / 2))            # exact for 1 degree of freedom
odds = (a * d) / (b * c)
se = math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
lo, hi = math.exp(math.log(odds) - 1.96 * se), math.exp(math.log(odds) + 1.96 * se)

print(f"Employed:   {a}/{a+b} with a loan ({a/(a+b):.1%})")
print(f"Unemployed: {c}/{c+d} with a loan ({c/(c+d):.1%})")
print(f"Pearson chi-square (df=1, no continuity correction) = {chi2:.3f}")
print(f"p-value = {p:.4f}  (alpha = 0.05 -> {'significant' if p < 0.05 else 'NOT significant'})")
print(f"Odds ratio (employed vs unemployed) = {odds:.2f}, 95% CI [{lo:.2f}, {hi:.2f}]")
