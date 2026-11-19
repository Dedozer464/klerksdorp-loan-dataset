-- 1. Loan rate by employment status
SELECT employment_status,
       COUNT(*)                                   AS people,
       SUM(has_loan)                              AS with_loan,
       ROUND(100.0 * SUM(has_loan) / COUNT(*), 1) AS loan_rate_pct
FROM loans GROUP BY employment_status;

-- 2. Employed only: public vs private sector
SELECT sector, COUNT(*) AS people, ROUND(100.0 * SUM(has_loan) / COUNT(*), 1) AS loan_rate_pct
FROM loans WHERE employment_status = 'Employed' GROUP BY sector;

-- 3. Loan rate by gender and by race
SELECT gender, ROUND(100.0 * SUM(has_loan) / COUNT(*), 1) AS loan_rate_pct FROM loans GROUP BY gender;
SELECT race, COUNT(*) AS people, ROUND(100.0 * SUM(has_loan) / COUNT(*), 1) AS loan_rate_pct FROM loans GROUP BY race;

-- 4. Average loan size by employment status (borrowers only)
SELECT employment_status, ROUND(AVG(loan_amount_zar), 0) AS avg_loan_zar
FROM loans WHERE has_loan = 1 GROUP BY employment_status;

-- 5. Pearson chi-square statistic in pure SQL (critical value 3.841 at p = 0.05, df = 1)
WITH t AS (
  SELECT SUM(CASE WHEN employment_status='Employed'   AND has_loan=1 THEN 1.0 ELSE 0 END) AS a,
         SUM(CASE WHEN employment_status='Employed'   AND has_loan=0 THEN 1.0 ELSE 0 END) AS b,
         SUM(CASE WHEN employment_status='Unemployed' AND has_loan=1 THEN 1.0 ELSE 0 END) AS c,
         SUM(CASE WHEN employment_status='Unemployed' AND has_loan=0 THEN 1.0 ELSE 0 END) AS d
  FROM loans)
SELECT ROUND((a+b+c+d) * (a*d - b*c) * (a*d - b*c) / ((a+b)*(c+d)*(a+c)*(b+d)), 3) AS chi_square FROM t;
