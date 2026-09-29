import os
import sqlite3
import json
from datetime import datetime
from models import FoodItem, Recipe
from api import clean_ingredient

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "food_tracker.db")

def create_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


def create_table(conn):
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS food_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            expiry_date TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL
        )
    """)
    cursor.execute("PRAGMA table_info(recipes)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    required_columns = {
        "recipe_id":    "INTEGER",
        "ingredients":  "TEXT",
        "instructions": "TEXT",
        "match_count":  "INTEGER",
        "cached_at":    "TEXT",
    }
    for column, col_type in required_columns.items():
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE recipes ADD COLUMN {column} {col_type}")

    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_recipes_recipe_id "
        "ON recipes(recipe_id)"
    )
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS favourites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            ingredients TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meal_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT UNIQUE NOT NULL,
            recipe_title TEXT NOT NULL
        )
    """)

    conn.commit()
    _migrate_clean_ingredients(conn)


def _migrate_clean_ingredients(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, ingredients FROM recipes")
    rows = cursor.fetchall()
    for row_id, raw in rows:
        cleaned_list = [clean_ingredient(i) for i in _parse_ingredients(raw)]
        cleaned_str = ", ".join(i for i in cleaned_list if i)
        if cleaned_str != (raw or ""): #only if there was a cleanup needed 
            cursor.execute( 
                "UPDATE recipes SET ingredients = ? WHERE id = ?",
                (cleaned_str, row_id)
            )
    conn.commit()


def insert_item(conn, item):

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO food_items (name, quantity, expiry_date) VALUES (?, ?, ?)",  # prevents SQL injection
        (item.name, item.quantity, item.expiry_date_str())
    )
    conn.commit()
    return cursor.lastrowid 


def fetch_all_items(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, quantity, expiry_date FROM food_items")
    rows = cursor.fetchall()
    return [FoodItem(item_id=row[0], name=row[1], quantity=row[2], expiry_date=row[3]) for row in rows]
#doesnt return raw tuples but puts them back into FoodItem

def delete_item(conn, item_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM food_items WHERE id = ?", (item_id,))
    conn.commit()


def update_item(conn, item_id, name, quantity, expiry_date):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE food_items SET name = ?, quantity = ?, expiry_date = ? WHERE id = ?",  
        (name, quantity, expiry_date, item_id)
    )
    conn.commit()


def find_duplicate(conn, name, expiry_date):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, quantity, expiry_date FROM food_items "
        "WHERE LOWER(name) = LOWER(?) AND expiry_date = ?",
        (name, expiry_date)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return FoodItem(item_id=row[0], name=row[1], quantity=row[2], expiry_date=row[3])


def update_quantity(conn, item_id, new_quantity):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE food_items SET quantity = ? WHERE id = ?",
        (new_quantity, item_id)
    )
    conn.commit()


def _parse_ingredients(raw):
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("["):
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            pass
    return [i.strip() for i in raw.split(",") if i.strip()]


def insert_recipe(conn, recipe):
    cursor = conn.cursor()
    cached_at = datetime.today().strftime("%d/%m/%Y")
    cleaned = [clean_ingredient(i) for i in recipe.ingredients] if recipe.ingredients else []
    ingredients_str = ", ".join(i for i in cleaned if i)
    cursor.execute(
        """INSERT OR REPLACE INTO recipes
           (recipe_id, title, ingredients, instructions, match_count, cached_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (recipe.recipe_id, recipe.title, ingredients_str, recipe.instructions,
         recipe.match_count, cached_at)
    )
    conn.commit()
    return cursor.lastrowid
#fix so that no duplicates, but rather updates

def fetch_saved_recipes(conn):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT recipe_id, title, ingredients, instructions, match_count, cached_at FROM recipes"
    )
    rows = cursor.fetchall()
    return [
        Recipe(
            recipe_id=row[0],
            title=row[1],
            ingredients=_parse_ingredients(row[2]),
            instructions=row[3],
            match_count=row[4] or 0,
            is_cached=True,
        )
        for row in rows
    ]


def fetch_recipe_by_title(conn, title):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT recipe_id, title, ingredients, instructions, match_count, cached_at "
        "FROM recipes WHERE LOWER(title) = LOWER(?) "
        "ORDER BY (recipe_id IS NOT NULL) DESC, (instructions IS NOT NULL) DESC, id DESC "
        "LIMIT 1",
        (title,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return Recipe(
        recipe_id=row[0],
        title=row[1],
        ingredients=_parse_ingredients(row[2]),
        instructions=row[3],
        match_count=row[4] or 0,
        is_cached=True,
    )

def insert_favourite(conn, recipe):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO favourites (title, ingredients) VALUES (?, ?)",
        (recipe.title, ", ".join(recipe.ingredients) if recipe.ingredients else "")
    )
    conn.commit()
    return cursor.lastrowid

def fetch_favourites(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, ingredients FROM favourites")
    rows = cursor.fetchall()
    return [
        Recipe(
            id=row[0],
            title=row[1],
            ingredients=_parse_ingredients(row[2]),
            match_count=0,
            is_cached=True,
        )
        for row in rows
    ]


def delete_favourite(conn, recipe_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favourites WHERE id = ?", (recipe_id,))
    conn.commit()


def find_favourite(conn, title):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id FROM favourites WHERE LOWER(title) = LOWER(?)", (title,)
    )
    return cursor.fetchone() is not None


def insert_meal(conn, day, recipe_title):
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO meal_plan (day, recipe_title) VALUES (?, ?)",
        (day, recipe_title)
    )
    conn.commit()


def fetch_meal_plan(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT day, recipe_title FROM meal_plan")
    return {row[0]: row[1] for row in cursor.fetchall()}


def clear_meal(conn, day):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meal_plan WHERE day = ?", (day,))
    conn.commit()


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
