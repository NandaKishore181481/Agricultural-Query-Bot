import os
import json
import sqlite3
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if DATABASE_URL:
        # Use PostgreSQL on Render
        return psycopg2.connect(DATABASE_URL)
    else:
        # Use SQLite locally
        return sqlite3.connect("whatsapp_users.db")

def get_placeholder():
    return "%s" if DATABASE_URL else "?"

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    if DATABASE_URL:
        # PostgreSQL syntax
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users
                    (id SERIAL PRIMARY KEY,
                    wa_no TEXT NOT NULL UNIQUE,
                    wa_name TEXT,
                    preferences TEXT,
                    image BYTEA)"""
        )
        # Create threads table for OpenAI history
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS threads
                    (wa_id TEXT PRIMARY KEY,
                    messages TEXT NOT NULL)"""
        )
    else:
        # SQLite syntax
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS users
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wa_no TEXT NOT NULL UNIQUE,
                    wa_name TEXT,
                    preferences TEXT,
                    image BLOB)"""
        )
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS threads
                    (wa_id TEXT PRIMARY KEY,
                    messages TEXT NOT NULL)"""
        )

    conn.commit()
    conn.close()

def add_user(wa_no, wa_name, preferences=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    p = get_placeholder()

    try:
        # Check if user already exists
        cursor.execute(f"SELECT wa_no FROM users WHERE wa_no = {p}", (wa_no,))
        if cursor.fetchone():
            return False
        
        # Insert a new user
        cursor.execute(
            f"INSERT INTO users (wa_no, wa_name, preferences) VALUES ({p}, {p}, {p})",
            (wa_no, wa_name, json.dumps(preferences) if preferences else None),
        )
        conn.commit()
        return True
    finally:
        conn.close()

def get_user(wa_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    p = get_placeholder()

    try:
        cursor.execute(f"SELECT preferences FROM users WHERE wa_no = {p}", (wa_no,))
        user = cursor.fetchone()
        if user:
            return (json.loads(user[0]) if user[0] else None,)
        return None
    finally:
        conn.close()

def update_preferences(wa_no, preferences):
    conn = get_db_connection()
    cursor = conn.cursor()
    p = get_placeholder()

    try:
        cursor.execute(
            f"UPDATE users SET preferences = {p} WHERE wa_no = {p}",
            (json.dumps(preferences), wa_no),
        )
        conn.commit()
    finally:
        conn.close()

def update_image(wa_no, image_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    p = get_placeholder()

    try:
        cursor.execute(
            f"UPDATE users SET image = {p} WHERE wa_no = {p}",
            (image_data, wa_no),
        )
        conn.commit()
    finally:
        conn.close()

# --- New Thread Management Functions ---

def get_thread(wa_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    p = get_placeholder()

    try:
        cursor.execute(f"SELECT messages FROM threads WHERE wa_id = {p}", (wa_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None
    finally:
        conn.close()

def save_thread(wa_id, messages):
    conn = get_db_connection()
    cursor = conn.cursor()
    p = get_placeholder()

    try:
        # Use UPSERT (Update or Insert)
        if DATABASE_URL:
            # Postgres UPSERT
            cursor.execute(
                f"""INSERT INTO threads (wa_id, messages) VALUES ({p}, {p})
                   ON CONFLICT (wa_id) DO UPDATE SET messages = EXCLUDED.messages""",
                (wa_id, json.dumps(messages))
            )
        else:
            # SQLite UPSERT
            cursor.execute(
                f"INSERT OR REPLACE INTO threads (wa_id, messages) VALUES ({p}, {p})",
                (wa_id, json.dumps(messages))
            )
        conn.commit()
    finally:
        conn.close()
