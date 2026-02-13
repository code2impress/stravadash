"""
SQLite database for multi-user token storage with Google + Strava auth
"""
import sqlite3
from flask import current_app, g


def get_db_path():
    """Get the database file path from app config."""
    return current_app.config.get("DATABASE", "strava_users.db")


def get_db():
    """Get a database connection for the current request."""
    if "db" not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    """Close the database connection at end of request."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


NEW_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    google_id     TEXT UNIQUE,
    email         TEXT UNIQUE,
    athlete_id    INTEGER UNIQUE,
    access_token  TEXT,
    refresh_token TEXT,
    expires_at    INTEGER,
    firstname     TEXT,
    lastname      TEXT,
    profile_pic   TEXT,
    auth_provider TEXT NOT NULL DEFAULT 'strava',
    is_admin      INTEGER NOT NULL DEFAULT 0,
    is_disabled   INTEGER NOT NULL DEFAULT 0,
    last_login    TIMESTAMP,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def init_db():
    """Create the users table if it doesn't exist, and run migration if needed."""
    db = get_db()

    # Check if table exists at all
    table_exists = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()

    if not table_exists:
        db.execute(NEW_SCHEMA)
        db.commit()
        return

    # Check if migration is needed (old schema has athlete_id as PK, no 'id' column)
    columns = [row[1] for row in db.execute("PRAGMA table_info(users)").fetchall()]

    if "google_id" not in columns:
        _migrate_db(db)


def _migrate_db(db):
    """Migrate from old schema (athlete_id PK) to new schema (id AUTOINCREMENT)."""
    current_app.logger.info("Migrating database to new multi-user schema...")

    db.execute("ALTER TABLE users RENAME TO users_old")

    db.execute(NEW_SCHEMA.replace("IF NOT EXISTS ", ""))

    db.execute("""
        INSERT INTO users (athlete_id, access_token, refresh_token, expires_at,
                          firstname, lastname, profile_pic, auth_provider,
                          is_admin, created_at, updated_at, last_login)
        SELECT athlete_id, access_token, refresh_token, expires_at,
               firstname, lastname, profile_pic, 'strava',
               1, created_at, updated_at, CURRENT_TIMESTAMP
        FROM users_old
    """)

    db.execute("DROP TABLE users_old")
    db.commit()
    current_app.logger.info("Database migration complete. Existing users preserved as admins.")


# --- Query functions ---

def get_user(user_id):
    """Get user by internal id."""
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def get_user_by_athlete_id(athlete_id):
    """Get user by Strava athlete_id."""
    db = get_db()
    return db.execute("SELECT * FROM users WHERE athlete_id = ?", (athlete_id,)).fetchone()


def get_user_by_google_id(google_id):
    """Get user by Google sub ID."""
    db = get_db()
    return db.execute("SELECT * FROM users WHERE google_id = ?", (google_id,)).fetchone()


def get_user_by_email(email):
    """Get user by email address."""
    db = get_db()
    return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_all_users():
    """Get all users for admin view."""
    db = get_db()
    return db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()


def create_strava_user(athlete_id, access_token, refresh_token, expires_at,
                       firstname=None, lastname=None, profile_pic=None):
    """Create a new user via Strava login. Returns user id."""
    db = get_db()
    db.execute("""
        INSERT INTO users (athlete_id, access_token, refresh_token, expires_at,
                          firstname, lastname, profile_pic, auth_provider, last_login)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'strava', CURRENT_TIMESTAMP)
    """, (athlete_id, access_token, refresh_token, expires_at,
          firstname, lastname, profile_pic))
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_strava_tokens(user_id, access_token, refresh_token, expires_at,
                         firstname=None, lastname=None, profile_pic=None):
    """Update Strava tokens for an existing user."""
    db = get_db()
    db.execute("""
        UPDATE users SET access_token=?, refresh_token=?, expires_at=?,
            firstname=COALESCE(?, firstname), lastname=COALESCE(?, lastname),
            profile_pic=COALESCE(?, profile_pic),
            last_login=CURRENT_TIMESTAMP, updated_at=CURRENT_TIMESTAMP
        WHERE id=?
    """, (access_token, refresh_token, expires_at,
          firstname, lastname, profile_pic, user_id))
    db.commit()


def create_google_user(google_id, email, firstname=None, lastname=None, profile_pic=None):
    """Create a new user via Google login. Returns user id."""
    db = get_db()
    db.execute("""
        INSERT INTO users (google_id, email, firstname, lastname, profile_pic,
                          auth_provider, last_login)
        VALUES (?, ?, ?, ?, ?, 'google', CURRENT_TIMESTAMP)
    """, (google_id, email, firstname, lastname, profile_pic))
    db.commit()
    return db.execute("SELECT last_insert_rowid()").fetchone()[0]


def update_google_info(user_id, google_id, email, firstname=None, lastname=None, profile_pic=None):
    """Update Google info for an existing user."""
    db = get_db()
    db.execute("""
        UPDATE users SET
            google_id = COALESCE(google_id, ?),
            email = COALESCE(email, ?),
            firstname = COALESCE(firstname, ?),
            lastname = COALESCE(lastname, ?),
            profile_pic = COALESCE(profile_pic, ?),
            auth_provider = CASE
                WHEN athlete_id IS NOT NULL THEN 'both'
                ELSE 'google'
            END,
            last_login = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (google_id, email, firstname, lastname, profile_pic, user_id))
    db.commit()


def link_strava_to_user(user_id, athlete_id, access_token, refresh_token, expires_at,
                        firstname=None, lastname=None, profile_pic=None):
    """Link a Strava account to an existing user (Google user linking Strava)."""
    db = get_db()
    db.execute("""
        UPDATE users SET
            athlete_id = ?, access_token = ?, refresh_token = ?,
            expires_at = ?, firstname = COALESCE(?, firstname),
            lastname = COALESCE(?, lastname),
            profile_pic = COALESCE(?, profile_pic),
            auth_provider = 'both', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (athlete_id, access_token, refresh_token, expires_at,
          firstname, lastname, profile_pic, user_id))
    db.commit()


def update_user_field(user_id, field, value):
    """Update a single field for a user. Field must be whitelisted."""
    allowed = {'is_disabled', 'is_admin', 'last_login'}
    if field not in allowed:
        raise ValueError(f"Field '{field}' not allowed")
    db = get_db()
    db.execute(
        f"UPDATE users SET {field} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (value, user_id)
    )
    db.commit()


def delete_user(user_id):
    """Delete a user by internal id."""
    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()


def get_admin_stats():
    """Get usage statistics for admin dashboard."""
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active_7d = db.execute(
        "SELECT COUNT(*) FROM users WHERE last_login > datetime('now', '-7 days')"
    ).fetchone()[0]
    disabled = db.execute(
        "SELECT COUNT(*) FROM users WHERE is_disabled = 1"
    ).fetchone()[0]
    strava_linked = db.execute(
        "SELECT COUNT(*) FROM users WHERE athlete_id IS NOT NULL"
    ).fetchone()[0]
    google_linked = db.execute(
        "SELECT COUNT(*) FROM users WHERE google_id IS NOT NULL"
    ).fetchone()[0]
    return {
        'total_users': total,
        'active_7d': active_7d,
        'disabled': disabled,
        'strava_linked': strava_linked,
        'google_linked': google_linked
    }


def check_make_admin(user_id):
    """Make first user or ADMIN_EMAIL user an admin."""
    db = get_db()
    admin_exists = db.execute("SELECT COUNT(*) FROM users WHERE is_admin = 1").fetchone()[0]

    if not admin_exists:
        db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
        db.commit()
        return

    admin_email = current_app.config.get("ADMIN_EMAIL", "")
    if admin_email:
        user = get_user(user_id)
        if user and user["email"] and user["email"].lower() == admin_email.lower():
            db.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
            db.commit()
