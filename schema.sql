-- Works in PostgreSQL and SQLite. SYNTHETIC data, see README.
DROP TABLE IF EXISTS loans;
CREATE TABLE loans (
    person_id          VARCHAR(8)  PRIMARY KEY,
    age                INTEGER     NOT NULL CHECK (age BETWEEN 18 AND 64),
    gender             VARCHAR(10) NOT NULL CHECK (gender IN ('Female','Male')),
    race               VARCHAR(20) NOT NULL CHECK (race IN ('Black African','White','Coloured','Indian/Asian')),
    employment_status  VARCHAR(12) NOT NULL CHECK (employment_status IN ('Employed','Unemployed')),
    sector             VARCHAR(16) NOT NULL CHECK (sector IN ('Public','Private','Not Applicable')),
    occupation         VARCHAR(30) NOT NULL,
    monthly_income_zar INTEGER     NOT NULL CHECK (monthly_income_zar >= 0),
    has_loan           INTEGER     NOT NULL CHECK (has_loan IN (0,1)),
    loan_type          VARCHAR(20) NOT NULL,
    loan_amount_zar    INTEGER     NOT NULL CHECK (loan_amount_zar >= 0),
    loan_term_months   INTEGER     NOT NULL CHECK (loan_term_months >= 0),
    CHECK ((employment_status = 'Employed'   AND sector <> 'Not Applicable')
        OR (employment_status = 'Unemployed' AND sector =  'Not Applicable')),
    CHECK ((has_loan = 1 AND loan_amount_zar > 0) OR (has_loan = 0 AND loan_amount_zar = 0))
);
