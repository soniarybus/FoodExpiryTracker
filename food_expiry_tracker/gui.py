# https://www.freecodecamp.org/news/python-gui-development-using-tkinter/

import tkinter as tk 
from tkinter import ttk, messagebox 
from datetime import datetime
import db_manager as db
from models import FoodItem
import api


RED_BG    = "#ffcccc"   # ≤ 3 days remaining
YELLOW_BG = "#fff3cd"   # ≤ 7 days remaining
GREEN_BG  = "#d4edda"   # > 7 days remaining


def validate_date(date_str: str, name: str):
    #first we check wether the name isn't blank
    if not name.strip():
        messagebox.showerror("Input Error", "Food name cannot be blank")
        return False
    try:
        datetime.strptime(date_str, "%d/%m/%Y") 
    except ValueError:
        messagebox.showerror("Input Error", "Date must be in DD/MM/YYYY format (e.g. 28/05/2026).")
        return False

    return True


def _restore_placeholder(entry: tk.Entry, placeholder: str):
    entry.delete(0, tk.END)
    entry.insert(0, placeholder)
    entry.config(fg="grey")


def _attach_placeholder(entry: tk.Entry, placeholder: str):
    entry.insert(0, placeholder)
    entry.config(fg="grey")

    def _focus_in(_event):
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg="black")

    def _focus_out(_event):
        if entry.get().strip() == "":
            entry.insert(0, placeholder)
            entry.config(fg="grey")

    entry.bind("<FocusIn>",  _focus_in)
    entry.bind("<FocusOut>", _focus_out)

# TAB 1: Items Tab

def _build_items_tab(notebook: ttk.Notebook, conn, update_recipes):
    tab = ttk.Frame(notebook, padding=8)
    notebook.add(tab, text=" ITEMS ")

    # ADD NEW ITEM BOX
    add_section = tk.LabelFrame(tab, text=" ADD NEW ITEM ", padx=8, pady=8)
    add_section.pack(fill="x", pady=(0, 8))

    # food name input field LABEL
    tk.Label(add_section, text="Food Name:").grid(
        row=0, column=0, sticky="w", padx=(0, 8), pady=3)

    # entry for the food name; placeholder cleared on focus
    name_entry = tk.Entry(add_section, width=28)
    name_entry.grid(row=0, column=1, sticky="w", pady=3)
    _attach_placeholder(name_entry, "e.g. Apple")

    # quantity input field LABEL
    tk.Label(add_section, text="Quantity:").grid(
        row=1, column=0, sticky="w", padx=(0, 8), pady=3)

    # entry for quantity
    qty_entry = tk.Entry(add_section, width=10)
    qty_entry.grid(row=1, column=1, sticky="w", pady=3)
    _attach_placeholder(qty_entry, "e.g. 3")

    # expiry date input field LABEL
    tk.Label(add_section, text="Expiry Date:").grid(
        row=2, column=0, sticky="nw", padx=(0, 8), pady=3)

    # plain text entry — can type a date or click a day on the calendar below
    expiry_entry = tk.Entry(add_section, width=12)
    expiry_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))
    expiry_entry.grid(row=2, column=1, sticky="w", pady=3)

    # calendar embedded directly in the Add Item area (no separate window)
    from tkcalendar import Calendar
    _today = datetime.today()
    _cal = Calendar(
        add_section,
        selectmode="day",
        year=_today.year,
        month=_today.month,
        day=_today.day,
        showweeknumbers=False,
        background="#4a4a4a",
        foreground="#ffffff",
        headersbackground="#d0d0d0",
        headersforeground="#000000",
        normalbackground="#ffffff",
        normalforeground="#000000",
        weekendbackground="#f0f0f0",
        weekendforeground="#333333",
        othermonthforeground="#aaaaaa",
        selectbackground="#1565C0",
        selectforeground="#ffffff",
    )
    _cal.grid(row=3, column=0, columnspan=2, pady=(4, 8))

    def _on_cal_select(_event=None):
        selected = _cal.selection_get()
        if selected:
            expiry_entry.delete(0, tk.END)
            expiry_entry.insert(0, selected.strftime("%d/%m/%Y"))

    _cal.bind("<<CalendarSelected>>", _on_cal_select)


    # sorting by section
    sort_frame = tk.Frame(tab)
    sort_frame.pack(fill="x", pady=(0, 4))

    tk.Label(sort_frame, text="Sort by:").pack(side="left", padx=(0, 6))

    list_section = tk.LabelFrame(tab, text=" Items ", padx=4, pady=4)
    list_section.pack(fill="both", expand=True, pady=(0, 6))

    #keeps the scrollbar and listbox together
    tree_frame = tk.Frame(list_section)
    tree_frame.pack(fill="both", expand=True)

    # MAIN LIST WITH COLOR CODE
    # columns: checkbox state | food name | quantity | expiry date | days left | edit action
    columns = ("check", "name", "qty", "expiry", "days", "action")
    tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)

    tree.heading("check",  text="☐")
    tree.heading("name",   text="Food Name")
    tree.heading("qty",    text="Qty")
    tree.heading("expiry", text="Expiry Date")
    tree.heading("days",   text="Days Left")
    tree.heading("action", text="")

    tree.column("check",  width=30,  anchor="center", stretch=False)
    tree.column("name",   width=160, anchor="w")
    tree.column("qty",    width=50,  anchor="center", stretch=False)
    tree.column("expiry", width=100, anchor="center", stretch=False)
    tree.column("days",   width=80,  anchor="center", stretch=False)
    tree.column("action", width=80,  anchor="center", stretch=False)

    tree.tag_configure("red",    background=RED_BG)
    tree.tag_configure("yellow", background=YELLOW_BG)
    tree.tag_configure("green",  background=GREEN_BG)

    # vertical scrollbar linked to the Treeview
    tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=tree_scroll.set)

    tree.pack(side="left", fill="both", expand=True)
    tree_scroll.pack(side="right", fill="y")

    # COLOUR LEGEND
    legend_frame = tk.Frame(tab)
    legend_frame.pack(fill="x", pady=(0, 6))

    tk.Label(legend_frame, text="Legend:").pack(side="left", padx=(0, 8))

    # Label with bg colour pattern
    for _bg, _lbl in (
        (RED_BG,    "≤ 3 days"),
        (YELLOW_BG, "≤ 7 days"),
        (GREEN_BG,  "> 7 days"),
    ):
        tk.Label(legend_frame, text=f"  {_lbl}  ",
                 bg=_bg, relief="groove").pack(side="left", padx=3)

    # REMOVE SELECTED/GET RECIPES buttons
    btn_frame = tk.Frame(tab)
    btn_frame.pack(fill="x", pady=(0, 6))

    # REMOVE SELECTED button
    remove_button = tk.Button(
        btn_frame, text="REMOVE SELECTED",
        bg="#3420e5", fg="black", activebackground="#2816ca",
        padx=10, pady=4,
    )
    remove_button.pack(side="left", padx=(0, 8))

    # GET RECIPES button
    recipes_button = tk.Button(
        btn_frame, text="GET RECIPES",
        bg="#1565C0", fg="black", activebackground="#0d47a1",
        padx=10, pady=4,
    )
    recipes_button.pack(side="left")

    # Warning banner (Label pattern)
    warning_label = tk.Label(
        tab,
        text="⚠  Expiry alerts will appear here",
        bg="#FFF3CD", fg="#856404",
        anchor="w", padx=8, pady=6,
        relief="solid", bd=1,
    )
    warning_label.pack(fill="x")

    _sort_key = "days"
    checked_items = set()
    editing_item_id = None

    def _days_label(days: int):
        if days < 0:
            return f"Expired ({abs(days)}d ago)"
        if days == 0:
            return "Expires today"
        return str(days)

    def update_warning(items: list):
        urgent = [it for it in items if it.days_remaining() <= 3]
        if urgent:
            parts = []
            for it in urgent:
                d = it.days_remaining()
                if d < 0:
                    parts.append(f"{it.name}: expired {abs(d)}d ago")
                elif d == 0:
                    parts.append(f"{it.name}: expires today")
                else:
                    parts.append(f"{it.name}: {d}d left")
            warning_label.config(
                text="⚠  " + "   |   ".join(parts),
                bg="#F09898", fg="#8e1c1c",
            )
        else:
            warning_label.config(
                text="✓  All items are not to expire soon",
                bg="#d4edda", fg="#155724",
            )

    def _populate_tree(items):
        # wipe every existing row before re-inserting; this is the full-refresh pattern
        # that avoids duplicates when the DB changes
        for row_id in tree.get_children():
            tree.delete(row_id)

        for item in items:
            # use the food_items row id as the Treeview row's iid
            row_iid = str(item.item_id)
            check_symbol = "☑" if row_iid in checked_items else "☐"

            tree.insert("", "end", iid=row_iid,
                        values=(
                            check_symbol,
                            item.name,
                            item.quantity,
                            item.expiry_date_str(),
                            _days_label(item.days_remaining()),
                            "Edit",
                        ),
                        tags=(item.colour_tag(),))

        update_warning(items)


    def refresh_listbox():
        items = db.fetch_all_items(conn)
        key = _sort_key
        if key == "days":
            items.sort(key=lambda it: (it.days_remaining(), it.name.lower()))
        elif key == "name":
            items.sort(key=lambda it: (it.name.lower(), it.days_remaining()))
        elif key == "qty":
            items.sort(key=lambda it: (it.quantity, it.name.lower()))
        _populate_tree(items)

    def _sort_by(key: str):
        nonlocal _sort_key
        _sort_key = key
        refresh_listbox()

    def _validate_inputs():
        # read raw text from every entry field
        raw_name   = name_entry.get()
        raw_qty    = qty_entry.get()
        raw_expiry = expiry_entry.get()

        # treat placeholder text as "nothing entered" before validating
        name_val   = "" if raw_name   == "e.g. Apple" else raw_name.strip()
        expiry_val = raw_expiry.strip()

        if not validate_date(expiry_val, name_val):
            return None

        # show an error if it isn't a plain integer (MAKE FIX HERE)
        qty_raw = raw_qty if raw_qty != "e.g. 3" else ""
        try:
            qty_val = int(qty_raw)
        except ValueError:
            messagebox.showerror("Input Error", "Quantity must be a whole number.")
            return None
        if qty_val <= 0:
            messagebox.showerror("Input Error", "Quantity must be a positive whole number.")
            return None
        return name_val, qty_val, expiry_val

    def _reset_form():
        nonlocal editing_item_id
        # clears the entry fields back to their placeholder text
        _restore_placeholder(name_entry, "e.g. Apple")
        _restore_placeholder(qty_entry,  "e.g. 3")
        _now = datetime.today()
        expiry_entry.delete(0, tk.END)
        expiry_entry.insert(0, _now.strftime("%d/%m/%Y"))
        _cal.selection_set(_now)

        # and switches the form back to "add a new item" mode
        editing_item_id = None
        save_button.config(text="+ ADD ITEM")

    def _on_save():
        result = _validate_inputs()
        if result is None:
            return
        name_val, qty_val, expiry_val = result

        if editing_item_id is None:
            # ADD MODE: no existing row is selected, so insert a brand new item
            item = FoodItem(item_id=None, name=name_val, quantity=qty_val, expiry_date=expiry_val)
            db.insert_item(conn, item)
        else:
            # EDIT MODE: overwrite the row that was loaded by _start_edit
            db.update_item(conn, editing_item_id, name_val, qty_val, expiry_val)

        _reset_form()
        refresh_listbox()

    def _start_edit(row_id: str):
        nonlocal editing_item_id
        values = tree.item(row_id, "values")
        name_val, qty_val, expiry_val = values[1], values[2], values[3]

        name_entry.delete(0, tk.END)
        name_entry.insert(0, name_val)
        name_entry.config(fg="black")

        qty_entry.delete(0, tk.END)
        qty_entry.insert(0, str(qty_val))
        qty_entry.config(fg="black")

        _dt = datetime.strptime(expiry_val, "%d/%m/%Y")
        expiry_entry.delete(0, tk.END)
        expiry_entry.insert(0, expiry_val)
        _cal.selection_set(_dt)

        editing_item_id[0] = int(row_id)
        save_button.config(text="Save Changes")

    def _on_tree_click(event):
        if tree.identify_region(event.x, event.y) != "cell":
            return 

        row_id = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if not row_id:
            return

        if column == "#1":
            if row_id in checked_items:
                checked_items.discard(row_id)
                new_symbol = "☐"
            else:
                checked_items.add(row_id)
                new_symbol = "☑"

            row_values = list(tree.item(row_id, "values"))
            row_values[0] = new_symbol
            tree.item(row_id, values=row_values)

        elif column == "#6":
            _start_edit(row_id)

    def _on_remove_selected():
        if not checked_items:
            messagebox.showerror(
                "Selection Error",
                "No items selected. Tick the checkbox next to the item(s) you want to remove."
            )
            return

        for item_id in checked_items:
            db.delete_item(conn, int(item_id))

        checked_items.clear()
        refresh_listbox()

    def _on_get_recipes():
        all_items = db.fetch_all_items(conn)
        if checked_items:
            items_to_use = [it for it in all_items if str(it.item_id) in checked_items]
        else:
            all_items.sort(key=lambda it: it.days_remaining())
            items_to_use = all_items[:3]

        if not items_to_use:
            messagebox.showinfo("No Items", "Add some food items first.")
            return

        try:
            recipes = api.get_recipes(items_to_use)
            if checked_items:
                for r in recipes:
                    r.is_manual_selection = True

            recipes.sort(key=lambda r: r.match_count, reverse=True)
            for r in recipes:
                db.insert_recipe(conn, r)
            update_recipes(recipes)
            notebook.select(1)

        except api.OfflineError:
            cached = db.fetch_saved_recipes(conn)
            update_recipes(cached, note="Showing cached recipes")
            notebook.select(1)

        except api.APIError as exc:
            messagebox.showerror("API Error", str(exc))

    # ADD ITEM / SAVE CHANGES button
    save_button = tk.Button(
        add_section, text="+ ADD ITEM",
        bg="#E877B5", fg="black", activebackground="#155b19",
        padx=10, pady=4,
        command=_on_save,
    )
    save_button.grid(row=4, column=1, sticky="e", pady=(8, 0))

    remove_button.config(command=_on_remove_selected)
    recipes_button.config(command=_on_get_recipes)

    tree.bind("<Button-1>", _on_tree_click)

    for _sort_label, _key in (
        ("Name",        "name"),
        ("Quantity",    "qty"),
        ("Days Left",   "days"),
    ):
        ttk.Button(
            sort_frame, text=_sort_label,
            command=lambda k=_key: _sort_by(k),
        ).pack(side="left", padx=2)

    refresh_listbox()

# TAB 2 – RECIPES

def _build_details_tab(notebook: ttk.Notebook):
    tab = ttk.Frame(notebook, padding=8)

    title_label = tk.Label(
        tab, text="Select a recipe to see its full details",
        font=("TkDefaultFont", 14, "bold"),
    )
    title_label.pack(anchor="w", pady=(0, 8))

    text_frame = tk.Frame(tab)
    text_frame.pack(fill="both", expand=True)

    text_area = tk.Text(
        text_frame, wrap="word", state="disabled",
        font=("TkDefaultFont", 11), relief="flat",
        padx=6, pady=6,
    )
    text_area.tag_configure("heading", font=("TkDefaultFont", 11, "bold"))
    text_area.tag_configure("rule",    foreground="#888888")

    scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_area.yview)
    text_area.configure(yscrollcommand=scrollbar.set)
    text_area.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    def update_details(title, ingredients=None, steps=None, error=None):
        text_area.config(state="normal")
        text_area.delete("1.0", tk.END)
        title_label.config(text=title)

        if error:
            text_area.insert(tk.END, error)
        else:
            text_area.insert(tk.END, "INGREDIENTS\n", "heading")
            text_area.insert(tk.END, "─" * 44 + "\n", "rule")
            for ing in (ingredients or []):
                text_area.insert(tk.END, f"• {ing}\n")
            text_area.insert(tk.END, "\n")
            text_area.insert(tk.END, "INSTRUCTIONS\n", "heading")
            text_area.insert(tk.END, "─" * 44 + "\n", "rule")
            for num, step in (steps or []):
                text_area.insert(tk.END, f"{num}. {step}\n\n")

        text_area.config(state="disabled")
        text_area.yview_moveto(0)

    return tab, update_details


def _build_recipes_tab(notebook: ttk.Notebook, update_details=None, details_tab=None):
    tab = ttk.Frame(notebook, padding=8)

    tk.Label(tab, text="Recipe Suggestions",
             font=("TkDefaultFont", 14, "bold")).pack(anchor="w", pady=(0, 6))

    note_label = tk.Label(
        tab, text="",
        bg="#fff3cd", fg="#856404",
        anchor="w", padx=8, pady=4,
        relief="solid", bd=1,
    )

    current_recipes = [[]]
    selected_idx    = [None] 

    recipe_widgets = []

    for i in range(3):
        lframe = tk.LabelFrame(tab, text=f" Recipe {i + 1} ", padx=8, pady=8)
        lframe.pack(fill="x", pady=4)

        title_lbl = tk.Label(lframe, text="Recipe title will appear here",
                             font=("TkDefaultFont", 11, "bold"))
        title_lbl.pack(anchor="w")

        detail_lbl = tk.Label(lframe,
                              text="Ingredients and details will be listed here.",
                              wraplength=480, justify="left")
        detail_lbl.pack(anchor="w", pady=(2, 0))

        recipe_widgets.append((lframe, title_lbl, detail_lbl))

    def _select_slot(idx):
        selected_idx[0] = idx
        for j, (lf, _, _) in enumerate(recipe_widgets):
            lf.config(relief="solid" if j == idx else "groove")

        if update_details is None or details_tab is None:
            return
        recipes = current_recipes[0]
        if not recipes or idx >= len(recipes):
            return
        r = recipes[idx]

        if r.id is None:
            update_details(
                r.title,
                error="Full details not available for cached recipes (no Spoonacular ID).",
            )
            notebook.select(details_tab)
            return

        try:
            details = api.get_recipe_details(r.id)
            update_details(
                details["title"],
                ingredients=details["ingredients"],
                steps=details["steps"],
            )
        except (api.OfflineError, api.APIError):
            update_details(
                r.title,
                error="Could not load full recipe (offline or API error).",
            )
        notebook.select(details_tab)

    for i, (lf, title_lbl, detail_lbl) in enumerate(recipe_widgets):
        for widget in (lf, title_lbl, detail_lbl):
            widget.bind("<Button-1>", lambda _, idx=i: _select_slot(idx))

    def _on_show_instructions():
        idx = selected_idx[0]
        if idx is None:
            messagebox.showinfo("No Selection", "Click a recipe box to select it first.")
            return
        recipes = current_recipes[0]
        if not recipes or idx >= len(recipes):
            messagebox.showinfo("No Recipe", "No recipe loaded in that slot.")
            return
        r = recipes[idx]
        body = (
            "\n".join(f"• {ing}" for ing in r.ingredients)
            if r.ingredients else "No ingredients available."
        )
        messagebox.showinfo(r.title, body)

    # SELECT TO SEE INSTRUCTIONS button
    tk.Button(
        tab, text="SELECT TO SEE INSTRUCTIONS",
        bg="#1565C0", fg="black", activebackground="#0d47a1",
        padx=12, pady=6,
        command=_on_show_instructions,
    ).pack(anchor="w", pady=(12, 0))

    def update_recipes(recipes: list, note: str = None):
        current_recipes[0] = recipes
        selected_idx[0] = None
        if note:
            note_label.config(text=f"ℹ  {note}")
            note_label.pack(fill="x", pady=(0, 6), before=recipe_widgets[0][0])
        else:
            note_label.pack_forget()

        for i, (lf, title_lbl, detail_lbl) in enumerate(recipe_widgets):
            lf.config(relief="groove")
            if i < len(recipes):
                r = recipes[i]
                title_lbl.config(text=r.title)
                detail_lbl.config(
                    text=f"{r.match_count} ingredient(s) matched"
                         + (" (cached)" if r.is_cached else "")
                )
            else:
                title_lbl.config(text="—")
                detail_lbl.config(text="")

    return tab, update_recipes


#first function that runs when app is launched
# tk root window pattern
def main():
    root = tk.Tk()
    root.title("Food Expiry Tracker")
    root.geometry("640x920")
    root.minsize(520, 700)

    ttk.Style(root).theme_use("clam")
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    conn = db.create_connection()
    db.create_table(conn)

    details_frame, update_details = _build_details_tab(notebook)
    recipes_frame, update_recipes = _build_recipes_tab(
        notebook, update_details=update_details, details_tab=details_frame
    )
    _build_items_tab(notebook, conn, update_recipes)
    notebook.add(recipes_frame, text=" RECIPES ")
    notebook.add(details_frame, text=" Recipe Details ")

    root.mainloop()
