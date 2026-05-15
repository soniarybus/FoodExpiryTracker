import sqlite3
from models import FoodItem, Recipe


def create_connection():
    # Opens food_tracker.db if it exists, or creates it if it doesn't
    conn = sqlite3.connect("food_tracker.db")
    return conn


def create_table(conn):
    # Creates the food_items and recipes tables if they don't already exist
    cursor = conn.cursor() #reads from the database

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            expiry_date TEXT NOT NULL
        )
    """)
    # expiry_date is stored as TEXT in DD/MM/YYYY format

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            ingredients TEXT,
            match_count INTEGER,
            is_cached INTEGER
        )
    """)

    conn.commit()


def insert_item(conn, item):
    # Inserts a FoodItem object into food_items and returns the new row id
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO food_items (name, quantity, expiry_date) VALUES (?, ?, ?)", #prevents SQL injection
        (item.name, item.quantity, item.expiry_date)
    )
    conn.commit()
    return cursor.lastrowid #id that SQL automatically gave the new row


def fetch_all_items(conn):
    # Queries all rows from food_items and returns them as a list of FoodItem objects
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, quantity, expiry_date FROM food_items")
    rows = cursor.fetchall() # selects all rows and returns as a list
    return [FoodItem(id=row[0], name=row[1], quantity=row[2], expiry_date=row[3]) for row in rows]
#matches to FoodItem objects

def delete_item(conn, item_id):
    # Deletes the food_items row matching the given primary key id
    cursor = conn.cursor()
    cursor.execute("DELETE FROM food_items WHERE id = ?", (item_id,))
    conn.commit()


def insert_recipe(conn, recipe):
    # Inserts a Recipe object into the recipes table and returns the new row id
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO recipes (title, ingredients, match_count, is_cached) VALUES (?, ?, ?, ?)",
        (recipe.title, recipe.ingredients, recipe.match_count, int(recipe.is_cached))
    )
    conn.commit()
    return cursor.lastrowid


def fetch_saved_recipes(conn):
    # Queries all rows from recipes and returns them as a list of Recipe objects
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, ingredients, match_count, is_cached FROM recipes")
    rows = cursor.fetchall()
    return [
        Recipe(
            id=row[0],
            title=row[1],
            ingredients=row[2],
            match_count=row[3],
            is_cached=bool(row[4])
        )
        for row in rows
    ]
