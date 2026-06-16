import os
import sqlite3
import json
from models import FoodItem, Recipe

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "food_tracker.db")


def create_connection():
    # Opens food_tracker.db if it exists, or creates it if it doesn't
    conn = sqlite3.connect(DB_PATH)
    return conn


def create_table(conn):
    # Creates the food_items and recipes tables if they don't already exist
    cursor = conn.cursor()

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
        "INSERT INTO food_items (name, quantity, expiry_date) VALUES (?, ?, ?)",  # prevents SQL injection


        (item.name, item.quantity, item.expiry_date_str())  # expiry_date_str() gives DD/MM/YYYY text
    )
    conn.commit()
    return cursor.lastrowid  # id that SQLite automatically assigned to the new row


def fetch_all_items(conn):
    # Queries all rows from food_items and returns them as a list of FoodItem objects
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, quantity, expiry_date FROM food_items")
    rows = cursor.fetchall()  # returns every row as a tuple
    return [FoodItem(item_id=row[0], name=row[1], quantity=row[2], expiry_date=row[3]) for row in rows]


def delete_item(conn, item_id):
    # Deletes the food_items row matching the given primary key id
    cursor = conn.cursor()
    cursor.execute("DELETE FROM food_items WHERE id = ?", (item_id,))
    conn.commit()


def update_item(conn, item_id, name, quantity, expiry_date):
    # Overwrites name, quantity and expiry_date for the food_items row matching item_id
    # expiry_date is expected as DD/MM/YYYY text, same format used when inserting
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE food_items SET name = ?, quantity = ?, expiry_date = ? WHERE id = ?",  # prevents SQL injection
        (name, quantity, expiry_date, item_id)
    )
    conn.commit()


def insert_recipe(conn, recipe):
    # Inserts a Recipe object into the recipes table and returns the new row id
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO recipes (title, ingredients, match_count, is_cached) VALUES (?, ?, ?, ?)",
        (recipe.title, json.dumps(recipe.ingredients), recipe.match_count, int(recipe.is_cached))
        # ingredients list is serialised to a JSON string for TEXT storage
    )
    conn.commit()
    return cursor.lastrowid


def fetch_saved_recipes(conn):
    # Queries all rows from recipes and returns them as a list of Recipe objects
    cursor = conn.cursor()
    cursor.execute("SELECT title, ingredients, match_count, is_cached FROM recipes")
    rows = cursor.fetchall()
    return [
        Recipe(
            title=row[0],
            ingredients=json.loads(row[1]) if row[1] else [],  # deserialise JSON string back to list
            match_count=row[2],
            is_cached=bool(row[3])
        )
        for row in rows
    ]



if __name__ == "__main__":
    conn = create_connection()
    create_table(conn)

    dummy = FoodItem(item_id=None, name="Test Apple", quantity=3, expiry_date="31/12/2026")
    new_id = insert_item(conn, dummy)
    print(f"Inserted dummy item with id={new_id}")


    items = fetch_all_items(conn)
    print("Items currently in database:")
    for item in items:
        print(f"  id={item.item_id}  name={item.name}  qty={item.quantity}  expires={item.expiry_date_str()}")

    delete_item(conn, new_id)
    print(f"Deleted item id={new_id} — DB restored to original state")

    conn.close()
