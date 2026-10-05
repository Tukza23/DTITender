import sqlite3
import hashlib
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tender_intelligence.db"


def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120000
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password, stored_value):
    try:
        salt, stored_hash = stored_value.split("$", 1)

        check_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            120000
        ).hex()

        return secrets.compare_digest(
            check_hash,
            stored_hash
        )
    except Exception:
        return False


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_number TEXT UNIQUE NOT NULL,
            business_name TEXT NOT NULL,
            registration_number TEXT,
            email TEXT,
            cellphone TEXT,
            province TEXT,
            industry TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            cellphone TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'USER',
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS super_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER UNIQUE NOT NULL,
            plan TEXT DEFAULT 'TRIAL',
            monthly_fee REAL DEFAULT 0,
            status TEXT DEFAULT 'TRIAL',
            start_date DATE,
            end_date DATE,
            next_billing_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS company_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER UNIQUE NOT NULL,
            trading_name TEXT,
            company_description TEXT,
            bbbee_level TEXT,
            csd_number TEXT,
            cidb_grading TEXT,
            vat_number TEXT,
            years_in_business INTEGER,
            employee_count INTEGER,
            turnover_band TEXT,
            provinces TEXT,
            services TEXT,
            certifications TEXT,
            licences TEXT,
            minimum_contract_value REAL,
            maximum_contract_value REAL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(org_id) REFERENCES organizations(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tenders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            tender_number TEXT,
            title TEXT NOT NULL,
            description TEXT,
            organisation TEXT,
            province TEXT,
            category TEXT,
            published_date DATE,
            closing_date DATETIME,
            tender_url TEXT,
            estimated_value REAL,
            raw_requirements TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tender_matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id INTEGER NOT NULL,
            tender_id INTEGER NOT NULL,
            eligibility_status TEXT,
            match_score REAL,
            mandatory_pass INTEGER,
            reasons TEXT,
            missing_requirements TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(org_id, tender_id),
            FOREIGN KEY(org_id) REFERENCES organizations(id),
            FOREIGN KEY(tender_id) REFERENCES tenders(id)
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


def ensure_super_admin():
    conn = get_connection()
    cur = conn.cursor()

    admin_email = "admin@tender.local"

    cur.execute("""
        SELECT id
        FROM super_users
        WHERE LOWER(email)=LOWER(?)
    """, (admin_email,))

    existing = cur.fetchone()

    if not existing:
        cur.execute("""
            INSERT INTO super_users (
                full_name,
                email,
                password_hash
            )
            VALUES (?,?,?)
        """, (
            "Platform Administrator",
            admin_email,
            hash_password("Admin123!")
        ))
        conn.commit()

    cur.close()
    conn.close()


def generate_business_number():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COALESCE(MAX(id), 0) + 1
        FROM organizations
    """)

    number = cur.fetchone()[0]

    cur.close()
    conn.close()

    return f"TND-{number:05d}"


def register_business(
    business_name,
    registration_number,
    business_email,
    cellphone,
    province,
    industry,
    full_name,
    user_email,
    password
):
    conn = get_connection()

    try:
        cur = conn.cursor()

        business_number = generate_business_number()

        cur.execute("""
            INSERT INTO organizations (
                business_number,
                business_name,
                registration_number,
                email,
                cellphone,
                province,
                industry,
                status
            )
            VALUES (?,?,?,?,?,?,?,'PENDING')
        """, (
            business_number,
            business_name,
            registration_number,
            business_email,
            cellphone,
            province,
            industry
        ))

        org_id = cur.lastrowid

        cur.execute("""
            INSERT INTO users (
                org_id,
                full_name,
                email,
                cellphone,
                password_hash,
                role
            )
            VALUES (?,?,?,?,?,'ADMIN')
        """, (
            org_id,
            full_name,
            user_email.lower().strip(),
            cellphone,
            hash_password(password)
        ))

        cur.execute("""
            INSERT INTO subscriptions (
                org_id,
                plan,
                monthly_fee,
                status,
                start_date,
                end_date
            )
            VALUES (
                ?,
                'TRIAL',
                0,
                'TRIAL',
                DATE('now'),
                DATE('now', '+14 day')
            )
        """, (org_id,))

        cur.execute("""
            INSERT INTO company_profiles (
                org_id
            )
            VALUES (?)
        """, (org_id,))

        conn.commit()
        return True, business_number

    except Exception as e:
        conn.rollback()
        return False, str(e)

    finally:
        conn.close()


def authenticate_user(email, password):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            u.*,
            o.business_name,
            o.business_number,
            o.status AS organization_status
        FROM users u
        JOIN organizations o
            ON o.id = u.org_id
        WHERE LOWER(u.email) = LOWER(?)
          AND u.is_active = 1
    """, (email.strip(),))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    user = dict(row)

    if not verify_password(
        password,
        user["password_hash"]
    ):
        return None

    return user


def authenticate_super_admin(
    email,
    password
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM super_users
        WHERE LOWER(email)=LOWER(?)
          AND is_active=1
    """, (email.strip(),))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return None

    user = dict(row)

    if not verify_password(
        password,
        user["password_hash"]
    ):
        return None

    return user


def platform_metrics():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM organizations
    """)
    organizations = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM organizations
        WHERE status='ACTIVE'
    """)
    active = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM subscriptions
        WHERE status='TRIAL'
    """)
    trials = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM organizations
        WHERE status='SUSPENDED'
    """)
    suspended = cur.fetchone()[0]

    cur.execute("""
        SELECT COALESCE(SUM(monthly_fee), 0)
        FROM subscriptions
        WHERE status='ACTIVE'
    """)
    revenue = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM tenders
    """)
    tenders = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM tender_matches
    """)
    matches = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "organizations": organizations,
        "active": active,
        "trials": trials,
        "suspended": suspended,
        "monthly_revenue": revenue,
        "tenders": tenders,
        "matches": matches
    }


def list_businesses():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            o.id,
            o.business_number,
            o.business_name,
            o.registration_number,
            o.email,
            o.cellphone,
            o.province,
            o.industry,
            o.status,
            o.created_at,
            s.plan,
            s.monthly_fee,
            s.status AS subscription_status,
            s.next_billing_date
        FROM organizations o
        LEFT JOIN subscriptions s
            ON s.org_id = o.id
        ORDER BY o.created_at DESC
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [dict(row) for row in rows]


def update_business_status(
    org_id,
    status
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE organizations
        SET status=?
        WHERE id=?
    """, (
        status,
        org_id
    ))

    conn.commit()

    cur.close()
    conn.close()


def update_subscription(
    org_id,
    plan,
    monthly_fee,
    status
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE subscriptions
        SET
            plan=?,
            monthly_fee=?,
            status=?,
            start_date=DATE('now'),
            next_billing_date=DATE('now', '+1 month')
        WHERE org_id=?
    """, (
        plan,
        monthly_fee,
        status,
        org_id
    ))

    conn.commit()

    cur.close()
    conn.close()


def get_company_profile(org_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM company_profiles
        WHERE org_id=?
    """, (org_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    return dict(row) if row else {}


def save_company_profile(
    org_id,
    trading_name,
    company_description,
    bbbee_level,
    csd_number,
    cidb_grading,
    vat_number,
    years_in_business,
    employee_count,
    turnover_band,
    provinces,
    services,
    certifications,
    licences,
    minimum_contract_value,
    maximum_contract_value
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE company_profiles
        SET
            trading_name=?,
            company_description=?,
            bbbee_level=?,
            csd_number=?,
            cidb_grading=?,
            vat_number=?,
            years_in_business=?,
            employee_count=?,
            turnover_band=?,
            provinces=?,
            services=?,
            certifications=?,
            licences=?,
            minimum_contract_value=?,
            maximum_contract_value=?,
            updated_at=CURRENT_TIMESTAMP
        WHERE org_id=?
    """, (
        trading_name,
        company_description,
        bbbee_level,
        csd_number,
        cidb_grading,
        vat_number,
        years_in_business,
        employee_count,
        turnover_band,
        provinces,
        services,
        certifications,
        licences,
        minimum_contract_value,
        maximum_contract_value,
        org_id
    ))

    conn.commit()

    cur.close()
    conn.close()


def business_dashboard_metrics(org_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM tender_matches
        WHERE org_id=?
    """, (org_id,))
    total = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM tender_matches
        WHERE org_id=?
          AND eligibility_status='STRONG MATCH'
    """, (org_id,))
    strong = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM tender_matches
        WHERE org_id=?
          AND eligibility_status='ALMOST QUALIFIED'
    """, (org_id,))
    almost = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM tender_matches
        WHERE org_id=?
          AND eligibility_status='NOT ELIGIBLE'
    """, (org_id,))
    not_eligible = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        "total_matches": total,
        "strong_matches": strong,
        "almost": almost,
        "not_eligible": not_eligible
    }