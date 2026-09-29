# https://www.freecodecamp.org/news/python-gui-development-using-tkinter/

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import threading
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


def filter_items(items: list, query: str):
    if not query:
        return items 

    query_lower = query.lower()
    result = []
    for item in items:                          
        if query_lower in item.name.lower():    
            result.append(item)                 
    return result


def _match_count_text(match_count: int):
    if match_count <= 0:
        return "No direct matches"
    if match_count == 1:
        return "1 of your items matched"
    return f"{match_count} of your items matched"


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
    expiry_entry = tk.Entry(add_section, width=12)
    expiry_entry.insert(0, datetime.today().strftime("%d/%m/%Y"))
    expiry_entry.grid(row=2, column=1, sticky="w", pady=3)

    from tkcalendar import Calendar

    def _open_cal_popup():
        popup = tk.Toplevel(add_section)
        popup.grab_set()
        popup.resizable(False, False)
        popup.title("")

        try:
            _sel = datetime.strptime(expiry_entry.get().strip(), "%d/%m/%Y")
        except ValueError:
            _sel = datetime.today()

        _cal = Calendar(
            popup,
            selectmode="day",
            year=_sel.year,
            month=_sel.month,
            day=_sel.day,
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
        _cal.pack(padx=4, pady=4)

        def _on_select(_event=None):
            selected = _cal.selection_get()
            if selected:
                expiry_entry.delete(0, tk.END)
                expiry_entry.insert(0, selected.strftime("%d/%m/%Y"))
                popup.destroy()

        _cal.bind("<<CalendarSelected>>", _on_select)

        # Position the popup just below the calendar button
        bx = cal_btn.winfo_rootx()
        by = cal_btn.winfo_rooty() + cal_btn.winfo_height()
        popup.geometry(f"+{bx}+{by}")

    cal_btn = tk.Button(add_section, text="📅", command=_open_cal_popup, padx=2, pady=1)
    cal_btn.grid(row=2, column=2, sticky="w", padx=(4, 0), pady=3)


    # sorting by section
    sort_frame = tk.Frame(tab)
    sort_frame.pack(fill="x", pady=(0, 4))

    tk.Label(sort_frame, text="Sort by:").pack(side="left", padx=(0, 6))

    list_section = tk.LabelFrame(tab, text=" Items ", padx=4, pady=4)
    list_section.pack(fill="both", expand=True, pady=(0, 6))

    # Search bar — sits directly above the Treeview inside the Items section
    search_entry = tk.Entry(list_section, fg="grey")
    search_entry.pack(fill="x", padx=2, pady=(2, 4))
    _attach_placeholder(search_entry, "Search by name...")

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
    _all_items = []     
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
        nonlocal _all_items
        items = db.fetch_all_items(conn)
        key = _sort_key
        if key == "days":
            items.sort(key=lambda it: (it.days_remaining(), it.name.lower()))
        elif key == "name":
            items.sort(key=lambda it: (it.name.lower(), it.days_remaining()))
        elif key == "qty":
            items.sort(key=lambda it: (it.quantity, it.name.lower()))
        _all_items = items
        _apply_search()

    def _current_search_query() :
        raw = search_entry.get()
        return "" if raw == "Search by name..." else raw.strip()

    def _apply_search():
        filtered = filter_items(_all_items, _current_search_query())
        _populate_tree(filtered)

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

        # and switches the form back to "add a new item" mode
        editing_item_id = None
        save_button.config(text="+ ADD ITEM")

    def _on_save():
        result = _validate_inputs()
        if result is None:
            return
        name_val, qty_val, expiry_val = result

        if editing_item_id is None:
            duplicate = db.find_duplicate(conn, name_val, expiry_val)
            if duplicate is not None:
                new_qty = duplicate.quantity + qty_val
                db.update_quantity(conn, duplicate.item_id, new_qty)
                messagebox.showinfo(
                    "Quantity Updated",
                    f"Quantity updated: {duplicate.name} now has {new_qty} in stock"
                )
            else:
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

        expiry_entry.delete(0, tk.END)
        expiry_entry.insert(0, expiry_val)

        editing_item_id = int(row_id)
        save_button.config(text="SAVE CHANGES")

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

    def _show_cached_recipes():
        cached = db.fetch_saved_recipes(conn)
        if not cached:
            update_recipes(
                [],
                note="No cached recipes available. Connect to the internet to fetch recipes."
            )
        else:
            update_recipes(cached, note="Showing cached recipes — you are offline")
        notebook.select(1)

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

        recipes_button.config(state="disabled", text="Loading…")

        def _reset_button():
            recipes_button.config(state="normal", text="GET RECIPES")

        def _finish_online(recipes):
            if checked_items:
                for r in recipes:
                    r.is_manual_selection = True

            recipes.sort(key=lambda r: r.match_count, reverse=True)
            for r in recipes:
                db.insert_recipe(conn, r)
            display_recipes = [db.fetch_recipe_by_title(conn, r.title) for r in recipes]
            update_recipes(display_recipes)
            notebook.select(1)
            _reset_button()

        def _finish_offline():
            _show_cached_recipes()
            _reset_button()

        def _finish_error(exc):
            messagebox.showerror("API Error", str(exc))
            _reset_button()

        def _worker():
            if not api.is_online():
                tab.after(0, _finish_offline)
                return
            try:
                recipes = api.get_recipes(items_to_use)
                tab.after(0, _finish_online, recipes)
            except api.OfflineError:
                tab.after(0, _finish_offline)
            except api.APIError as exc:
                tab.after(0, _finish_error, exc)

        threading.Thread(target=_worker, daemon=True).start()

    # ADD ITEM / SAVE CHANGES button
    save_button = tk.Button(
        add_section, text="+ ADD ITEM",
        bg="#E877B5", fg="black", activebackground="#155b19",
        padx=10, pady=4,
        command=_on_save,
    )
    save_button.grid(row=3, column=1, sticky="e", pady=(8, 0))

    remove_button.config(command=_on_remove_selected)
    recipes_button.config(command=_on_get_recipes)

    tree.bind("<Button-1>", _on_tree_click)
    search_entry.bind("<KeyRelease>", lambda _event: _apply_search())

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


def _build_recipes_tab(notebook: ttk.Notebook, conn, update_details=None, details_tab=None):
    tab = ttk.Frame(notebook, padding=8)
    inner_nb = ttk.Notebook(tab)
    inner_nb.pack(fill="both", expand=True)

    DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    #  SUB-TAB 2: FAVOURITES
    fav_tab = ttk.Frame(inner_nb, padding=8)

    tk.Label(fav_tab, text="Saved Favourites",
             font=("TkDefaultFont", 13, "bold")).pack(anchor="w", pady=(0, 6))

    fav_list_frame = tk.Frame(fav_tab)
    fav_list_frame.pack(fill="x")

    fav_listbox = tk.Listbox(fav_list_frame, height=8, selectmode="single",
                             exportselection=False)
    fav_scroll = ttk.Scrollbar(fav_list_frame, orient="vertical",
                               command=fav_listbox.yview)
    fav_listbox.configure(yscrollcommand=fav_scroll.set)
    fav_listbox.pack(side="left", fill="x", expand=True)
    fav_scroll.pack(side="right", fill="y")

    tk.Label(fav_tab, text="Ingredients:",
             font=("TkDefaultFont", 10, "bold")).pack(anchor="w", pady=(8, 2))

    ing_frame = tk.Frame(fav_tab)
    ing_frame.pack(fill="both", expand=True)

    ing_text = tk.Text(ing_frame, height=6, state="disabled", wrap="word",
                       relief="solid", bd=1, font=("TkDefaultFont", 10))
    ing_scroll = ttk.Scrollbar(ing_frame, orient="vertical", command=ing_text.yview)
    ing_text.configure(yscrollcommand=ing_scroll.set)
    ing_text.pack(side="left", fill="both", expand=True)
    ing_scroll.pack(side="right", fill="y")

    fav_btn_frame = tk.Frame(fav_tab)
    fav_btn_frame.pack(fill="x", pady=(8, 0))
    _fav_data = []

    def refresh_favs():
        nonlocal _fav_data
        _fav_data = db.fetch_favourites(conn)
        fav_listbox.delete(0, tk.END)
        for r in _fav_data:
            fav_listbox.insert(tk.END, r.title)
        ing_text.config(state="normal")
        ing_text.delete("1.0", tk.END)
        ing_text.config(state="disabled")

    def _on_fav_select(_event=None):
        sel = fav_listbox.curselection()
        if not sel:
            return
        recipe = _fav_data[sel[0]]
        # The favourites table only stores title + ingredients; instructions
        # are pulled from the recipes cache (keyed by title) so favourites
        # show full details offline too.
        cached = db.fetch_recipe_by_title(conn, recipe.title)
        ing_text.config(state="normal")
        ing_text.delete("1.0", tk.END)
        for ing in (recipe.ingredients or []):
            ing_text.insert(tk.END, f"• {ing}\n")
        ing_text.insert(tk.END, "\nINSTRUCTIONS\n")
        ing_text.insert(tk.END, (cached.instructions if cached else "No instructions available.") + "\n")
        ing_text.config(state="disabled")

    fav_listbox.bind("<<ListboxSelect>>", _on_fav_select)

    #  SUB-TAB 3: MEAL PLANNER 
    meal_tab = ttk.Frame(inner_nb, padding=8)

    tk.Label(meal_tab, text="Weekly Meal Plan",
             font=("TkDefaultFont", 13, "bold")).pack(anchor="w", pady=(0, 8))

    grid_frame = tk.Frame(meal_tab)
    grid_frame.pack(fill="x")
    day_title_vars = {}

    for col, day in enumerate(DAYS):
        slot = tk.LabelFrame(grid_frame, text=day[:3], padx=4, pady=4)
        slot.grid(row=0, column=col, padx=2, pady=4, sticky="n")

        var = tk.StringVar(value="—")
        day_title_vars[day] = var

        day_label = tk.Label(slot, textvariable=var, wraplength=68, justify="center",
                             width=8, font=("TkDefaultFont", 9), cursor="hand2")
        day_label.pack()

        def _make_day_click(d=day):
            def _on_day_click(_event=None):
                title = day_title_vars[d].get()
                if title == "—" or update_details is None or details_tab is None:
                    return
                cached = db.fetch_recipe_by_title(conn, title)
                if cached is None:
                    update_details(title, error="No cached details available for this recipe.")
                else:
                    steps = [
                        (i + 1, step)
                        for i, step in enumerate(cached.instructions.split("\n"))
                        if step.strip()
                    ]
                    update_details(cached.title, ingredients=cached.ingredients, steps=steps)
                notebook.select(details_tab)
            return _on_day_click

        day_label.bind("<Button-1>", _make_day_click())

        def _make_clear(d=day):
            def _do_clear():
                db.clear_meal(conn, d)
                day_title_vars[d].set("—")
            return _do_clear

        tk.Button(slot, text="Clear", command=_make_clear(), pady=1,
                  font=("TkDefaultFont", 8)).pack(pady=(4, 0))

    def refresh_meal():
        plan = db.fetch_meal_plan(conn)
        for d in DAYS:
            day_title_vars[d].set(plan.get(d, "—"))
    refresh_meal()

    # ADD YOUR OWN MEAL BOX
    # lets the user type any meal (not just a saved recipe) and put it on a day;
    # meal_plan already stores day + title as plain text, so no DB change needed
    own_meal_section = tk.LabelFrame(meal_tab, text=" ADD YOUR OWN MEAL ", padx=8, pady=8)
    own_meal_section.pack(fill="x", pady=(8, 0))

    tk.Label(own_meal_section, text="Meal:").grid(
        row=0, column=0, sticky="w", padx=(0, 8), pady=3)

    own_meal_entry = tk.Entry(own_meal_section, width=28)
    own_meal_entry.grid(row=0, column=1, sticky="w", pady=3)
    _attach_placeholder(own_meal_entry, "e.g. Leftover pasta")

    tk.Label(own_meal_section, text="Day:").grid(
        row=1, column=0, sticky="w", padx=(0, 8), pady=3)

    # readonly so only one of the seven days can be picked
    own_day_var = tk.StringVar(value=DAYS[0])
    ttk.Combobox(own_meal_section, textvariable=own_day_var, values=DAYS,
                 state="readonly", width=14).grid(row=1, column=1, sticky="w", pady=3)

    def _on_add_own_meal():
        # placeholder text counts as empty
        raw_name = own_meal_entry.get()
        meal_name = "" if raw_name == "e.g. Leftover pasta" else raw_name.strip()
        if not meal_name:
            messagebox.showerror("Input Error", "Meal name cannot be blank.")
            return
        if len(meal_name) > 40:
            messagebox.showerror("Input Error", "Meal name must be 40 characters or fewer.")
            return
        # replaces any meal already on that day, same as Favourites "Add to Meal Plan"
        db.insert_meal(conn, own_day_var.get(), meal_name)
        refresh_meal()
        _restore_placeholder(own_meal_entry, "e.g. Leftover pasta")
        # move focus off the entry so the next click clears the placeholder
        own_meal_section.focus_set()

    tk.Button(own_meal_section, text="+ ADD MEAL", command=_on_add_own_meal,
              padx=10, pady=4).grid(row=2, column=1, sticky="e", pady=(8, 0))

    # SUB-TAB 1: SUGGESTIONS
    sug_tab = ttk.Frame(inner_nb, padding=8)

    tk.Label(sug_tab, text="Recipe Suggestions",
             font=("TkDefaultFont", 13, "bold")).pack(anchor="w", pady=(0, 4))

    note_label = tk.Label(
        sug_tab, text="",
        bg="#fff3cd", fg="#856404",
        anchor="w", padx=8, pady=4,
        relief="solid", bd=1,
    )

    current_recipes = [[]]
    selected_idx    = [None]
    card_widgets = []

    for i in range(3):
        lframe = tk.LabelFrame(sug_tab, text=f" Recipe {i + 1} ", padx=8, pady=6)
        lframe.pack(fill="x", pady=4)

        title_lbl = tk.Label(lframe, text="—",
                             font=("TkDefaultFont", 11, "bold"), anchor="w")
        title_lbl.pack(anchor="w")
        match_lbl = tk.Label(lframe, text="", wraplength=480, justify="left",
                             anchor="w", font=("TkDefaultFont", 9), fg="grey")
        match_lbl.pack(anchor="w", pady=(2, 4))

        save_var = tk.StringVar(value="♡ Save to Favourites")
        save_btn = tk.Button(lframe, textvariable=save_var, padx=6, pady=2,
                             state="disabled")
        save_btn.pack(anchor="e")

        card_widgets.append((lframe, title_lbl, match_lbl, save_btn, save_var))

    def _select_slot(idx):
        selected_idx[0] = idx
        for j, (lf, *_) in enumerate(card_widgets):
            lf.config(relief="solid" if j == idx else "groove")

        if update_details is None or details_tab is None:
            return
        recipes = current_recipes[0]
        if not recipes or idx >= len(recipes):
            return
        r = recipes[idx]

        steps = [
            (i + 1, step)
            for i, step in enumerate(r.instructions.split("\n"))
            if step.strip()
        ]
        update_details(r.title, ingredients=r.ingredients, steps=steps)
        notebook.select(details_tab)

    def _make_save_cb(idx):
        def _save():
            recipes = current_recipes[0]
            if idx >= len(recipes):
                return
            recipe = recipes[idx]
            if db.find_favourite(conn, recipe.title):
                messagebox.showinfo("Already Saved", "Already in favourites")
                return
            db.insert_favourite(conn, recipe)
            _, _, _, btn, var = card_widgets[idx]
            var.set("✓ Saved")
            btn.config(state="disabled")
            messagebox.showinfo("Saved", "Recipe saved to favourites")
            refresh_favs()
        return _save

    for i, (lf, title_lbl, match_lbl, save_btn, save_var) in enumerate(card_widgets):
        save_btn.config(command=_make_save_cb(i))
        for w in (lf, title_lbl, match_lbl):
            w.bind("<Button-1>", lambda _, idx=i: _select_slot(idx))

    def update_recipes(recipes: list, note: str = None):
        inner_nb.select(sug_tab)
        current_recipes[0] = recipes
        selected_idx[0] = None
        if note:
            note_label.config(text=f"ℹ  {note}")
            note_label.pack(fill="x", pady=(0, 6), before=card_widgets[0][0])
        else:
            note_label.pack_forget()

        for i, (lf, title_lbl, match_lbl, save_btn, save_var) in enumerate(card_widgets):
            lf.config(relief="groove")
            if i < len(recipes):
                r = recipes[i]
                title_lbl.config(text=r.title)
                match_lbl.config(text=_match_count_text(r.match_count))
                save_var.set("♡ Save to Favourites")
                save_btn.config(state="normal")
            else:
                title_lbl.config(text="—")
                match_lbl.config(text="")
                save_btn.config(state="disabled")

    def _on_add_to_meal():
        sel = fav_listbox.curselection()
        if not sel:
            messagebox.showinfo("No Selection", "Click a recipe in the list first.")
            return
        recipe = _fav_data[sel[0]]

        popup = tk.Toplevel(fav_tab)
        popup.title("Add to Meal Plan")
        popup.grab_set()
        popup.resizable(False, False)

        tk.Label(popup, text=f"Add  '{recipe.title}'  to which day?",
                 padx=12, pady=8).pack()

        day_var = tk.StringVar(value=DAYS[0])
        combo = ttk.Combobox(popup, textvariable=day_var, values=DAYS,
                             state="readonly", width=14)
        combo.pack(padx=12, pady=(0, 8))

        def _confirm():
            db.insert_meal(conn, day_var.get(), recipe.title)
            refresh_meal()
            popup.destroy()
            messagebox.showinfo("Meal Plan",
                                f"'{recipe.title}' added to {day_var.get()}")

        tk.Button(popup, text="Add", command=_confirm,
                  padx=8, pady=4).pack(pady=(0, 10))

        bx = fav_btn_frame.winfo_rootx()
        by = fav_btn_frame.winfo_rooty()
        popup.geometry(f"+{bx}+{by}")

    def _on_remove_fav():
        sel = fav_listbox.curselection()
        if not sel:
            messagebox.showinfo("No Selection", "Click a recipe to select it first.")
            return
        recipe = _fav_data[sel[0]]
        db.delete_favourite(conn, recipe.id)
        refresh_favs()

    tk.Button(fav_btn_frame, text="Add to Meal Plan",
              command=_on_add_to_meal, padx=8, pady=4).pack(side="left", padx=(0, 8))
    tk.Button(fav_btn_frame, text="Remove from Favourites",
              command=_on_remove_fav, padx=8, pady=4).pack(side="left")

    # Load favourites from DB on startup so saved recipes persist across restarts.
    refresh_favs()

    # Add sub-tabs to inner notebook in the order the user sees them.
    inner_nb.add(sug_tab,  text=" SUGGESTIONS ")
    inner_nb.add(fav_tab,  text=" FAVOURITES ")
    inner_nb.add(meal_tab, text=" MEAL PLANNER ")

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
        notebook, conn, update_details=update_details, details_tab=details_frame
    )
    _build_items_tab(notebook, conn, update_recipes)
    notebook.add(recipes_frame, text=" RECIPES ")
    notebook.add(details_frame, text=" Recipe Details ")

    root.mainloop()
