import sqlite3
import os
import hashlib


# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_PATH = os.path.join(
    DATA_DIR,
    "agriresolve.db"
)


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password):

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_auth_connection():

    return sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )


# =========================================================
# CREATE USERS TABLE
# =========================================================

def initialize_users():

    connection = get_auth_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL,

            created_at TEXT
        )
        """
    )

    connection.commit()
    connection.close()


# =========================================================
# CREATE USER
# =========================================================

def create_user(
    name,
    email,
    password,
    role
):

    connection = get_auth_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO users (
                name,
                email,
                password,
                role,
                created_at
            )

            VALUES (?, ?, ?, ?, datetime('now'))
            """,
            (
                name,
                email.lower().strip(),
                hash_password(password),
                role
            )
        )

        connection.commit()

        return True, "Account created successfully."

    except sqlite3.IntegrityError:

        return False, "An account with this email already exists."

    finally:

        connection.close()


# =========================================================
# LOGIN USER
# =========================================================

def login_user(
    email,
    password
):

    connection = get_auth_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            name,
            email,
            role
        FROM users
        WHERE email = ?
        AND password = ?
        """,
        (
            email.lower().strip(),
            hash_password(password)
        )
    )

    user = cursor.fetchone()

    connection.close()

    if user:

        return {
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "role": user[3]
        }

    return None