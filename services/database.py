import sqlite3
import os


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
# DATABASE CONNECTION
# =========================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False
    )

    return connection


# =========================================================
# CREATE TABLE
# =========================================================

def initialize_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS decisions (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            date_time TEXT,

            crop TEXT,

            growth_stage TEXT,

            latitude REAL,

            longitude REAL,

            soil_moisture REAL,

            rain_probability REAL,

            pest_risk TEXT,

            conflict TEXT,

            conflict_type TEXT,

            recommended_action TEXT,

            priority TEXT,

            confidence REAL
        )
        """
    )

    connection.commit()
    connection.close()


# =========================================================
# SAVE DECISION
# =========================================================

def save_decision(decision_record):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO decisions (

            date_time,
            crop,
            growth_stage,
            latitude,
            longitude,
            soil_moisture,
            rain_probability,
            pest_risk,
            conflict,
            conflict_type,
            recommended_action,
            priority,
            confidence

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            decision_record.get(
                "Date & Time",
                ""
            ),

            decision_record.get(
                "Crop",
                ""
            ),

            decision_record.get(
                "Growth Stage",
                ""
            ),

            decision_record.get(
                "Latitude",
                0
            ),

            decision_record.get(
                "Longitude",
                0
            ),

            decision_record.get(
                "Soil Moisture (%)",
                0
            ),

            decision_record.get(
                "Rain Probability (%)",
                0
            ),

            decision_record.get(
                "Pest Risk",
                "Low"
            ),

            decision_record.get(
                "Conflict",
                "No"
            ),

            decision_record.get(
                "Conflict Type",
                "No major conflict"
            ),

            decision_record.get(
                "Recommended Action",
                "N/A"
            ),

            decision_record.get(
                "Priority",
                "N/A"
            ),

            decision_record.get(
                "Confidence (%)",
                0
            )
        )
    )

    connection.commit()

    connection.close()


# =========================================================
# GET ALL DECISIONS
# =========================================================

def get_all_decisions():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            date_time,
            crop,
            growth_stage,
            latitude,
            longitude,
            soil_moisture,
            rain_probability,
            pest_risk,
            conflict,
            conflict_type,
            recommended_action,
            priority,
            confidence

        FROM decisions

        ORDER BY id DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    history = []

    for row in rows:

        history.append(
            {
                "Date & Time": row[0],
                "Crop": row[1],
                "Growth Stage": row[2],
                "Latitude": row[3],
                "Longitude": row[4],
                "Soil Moisture (%)": row[5],
                "Rain Probability (%)": row[6],
                "Pest Risk": row[7],
                "Conflict": row[8],
                "Conflict Type": row[9],
                "Recommended Action": row[10],
                "Priority": row[11],
                "Confidence (%)": row[12]
            }
        )

    return history


# =========================================================
# CLEAR DECISIONS
# =========================================================

def clear_all_decisions():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        "DELETE FROM decisions"
    )

    connection.commit()

    connection.close()
    # =========================================================
# GET USER COUNT
# =========================================================

def get_user_count():

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        count = 0

    connection.close()

    return count
