"""
Generate a SYNTHETIC loan dataset for working-age adults in Klerksdorp, North West, South Africa.

Design (fixed counts, so results are reproducible and exact):
  - 600 adults aged 18-64: 360 employed, 240 unemployed
  - Loans: 144/360 employed (40.0%) vs 79/240 unemployed (32.9%)
  - Seed is fixed -> identical output on every run

Outputs: data/klerksdorp_loans.csv and sql/insert_data.sql
"""
import csv, os, random

SEED = 2026
random.seed(SEED)

N_EMP, N_UNEMP = 360, 240
LOANS_EMP, LOANS_UNEMP = 144, 79

RACES = ["Black African", "White", "Coloured", "Indian/Asian"]
RACE_W = [84, 11, 3, 2]
GENDERS = ["Female", "Male"]
GENDER_W = [51, 49]

# (occupation, sector, weight, monthly income range ZAR)
JOBS = [
    ("Teacher", "Public", 8, (16000, 38000)),
    ("Nurse", "Public", 6, (14000, 32000)),
    ("Police Officer", "Public", 5, (15000, 30000)),
    ("Municipal Clerk", "Public", 5, (9000, 22000)),
    ("Government Admin Officer", "Public", 4, (10000, 25000)),
    ("Mine Worker", "Private", 16, (12000, 35000)),
    ("Retail Assistant", "Private", 14, (4500, 9500)),
    ("Construction Worker", "Private", 8, (5000, 14000)),
    ("Security Officer", "Private", 9, (4500, 8500)),
    ("Driver / Transport", "Private", 7, (6000, 15000)),
    ("Farm Worker", "Private", 5, (4000, 7500)),
    ("Technician / IT", "Private", 4, (12000, 38000)),
    ("Bank / Office Clerk", "Private", 5, (9000, 24000)),
    ("Hospitality / Food Service", "Private", 4, (4000, 8000)),
]

# (loan type, weight, amount range ZAR, term range months)
LOANS_EMPLOYED = [
    ("Personal Loan", 35, (5000, 80000), (12, 60)),
    ("Vehicle Finance", 18, (80000, 350000), (48, 72)),
    ("Home Loan", 7, (350000, 1200000), (180, 240)),
    ("Store Credit", 20, (1000, 12000), (6, 24)),
    ("Microloan", 20, (500, 8000), (1, 6)),
]
LOANS_UNEMPLOYED = [
    ("Microloan", 55, (300, 4000), (1, 6)),
    ("Store Credit", 30, (500, 6000), (6, 18)),
    ("Personal Loan", 15, (2000, 15000), (6, 24)),
]

def pick(items, weights):
    return random.choices(items, weights=weights, k=1)[0]

def pick_loan(table):
    t = pick(table, [x[1] for x in table])
    amount = round(random.uniform(*t[2]) / 100) * 100
    term = random.randint(*t[3])
    return t[0], amount, term

def make_person(employed):
    gender = pick(GENDERS, GENDER_W)
    race = pick(RACES, RACE_W)
    if employed:
        age = int(round(random.triangular(21, 64, 37)))
        job = pick(JOBS, [j[2] for j in JOBS])
        occupation, sector = job[0], job[1]
        income = round(random.uniform(*job[3]) / 100) * 100
        status = "Employed"
    else:
        age = int(round(random.triangular(18, 62, 24)))
        occupation, sector, income, status = "Not Applicable", "Not Applicable", 0, "Unemployed"
    return dict(age=age, gender=gender, race=race, employment_status=status,
                sector=sector, occupation=occupation, monthly_income_zar=income)

people = [make_person(True) for _ in range(N_EMP)] + [make_person(False) for _ in range(N_UNEMP)]
random.shuffle(people)

# Assign exact numbers of loan holders per group
emp_idx = [i for i, p in enumerate(people) if p["employment_status"] == "Employed"]
unemp_idx = [i for i, p in enumerate(people) if p["employment_status"] == "Unemployed"]
has_loan = set(random.sample(emp_idx, LOANS_EMP)) | set(random.sample(unemp_idx, LOANS_UNEMP))

rows = []
for i, p in enumerate(people):
    p["person_id"] = f"KLK-{i+1:04d}"
    if i in has_loan:
        table = LOANS_EMPLOYED if p["employment_status"] == "Employed" else LOANS_UNEMPLOYED
        lt, amt, term = pick_loan(table)
        p.update(has_loan=1, loan_type=lt, loan_amount_zar=amt, loan_term_months=term)
    else:
        p.update(has_loan=0, loan_type="None", loan_amount_zar=0, loan_term_months=0)
    rows.append(p)

COLS = ["person_id", "age", "gender", "race", "employment_status", "sector", "occupation",
        "monthly_income_zar", "has_loan", "loan_type", "loan_amount_zar", "loan_term_months"]

# ---- Validation: the dataset must be 100% clean ----
ids = set()
for r in rows:
    assert r["person_id"] not in ids; ids.add(r["person_id"])
    assert all(r[c] not in ("", None) for c in COLS), r
    assert 18 <= r["age"] <= 64, r
    assert r["gender"] in GENDERS and r["race"] in RACES
    if r["employment_status"] == "Employed":
        assert r["sector"] in ("Public", "Private") and r["monthly_income_zar"] > 0
    else:
        assert r["sector"] == r["occupation"] == "Not Applicable" and r["monthly_income_zar"] == 0
    if r["has_loan"]:
        assert r["loan_amount_zar"] > 0 and r["loan_term_months"] > 0 and r["loan_type"] != "None"
    else:
        assert r["loan_amount_zar"] == 0 and r["loan_term_months"] == 0 and r["loan_type"] == "None"
assert len(rows) == N_EMP + N_UNEMP

root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
with open(os.path.join(root, "data", "klerksdorp_loans.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)

def sql_val(v):
    return str(v) if isinstance(v, int) else "'" + str(v).replace("'", "''") + "'"

with open(os.path.join(root, "sql", "insert_data.sql"), "w", encoding="utf-8") as f:
    f.write("-- SYNTHETIC DATA. Generated by python/generate_dataset.py (seed 2026)\n")
    f.write(f"INSERT INTO loans ({', '.join(COLS)}) VALUES\n")
    f.write(",\n".join("(" + ", ".join(sql_val(r[c]) for c in COLS) + ")" for r in rows))
    f.write(";\n")

print(f"Wrote {len(rows)} rows. Validation passed.")
