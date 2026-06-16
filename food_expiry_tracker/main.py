# GUI structure based on: FreeCodeCamp Tkinter Tutorial
# https://www.freecodecamp.org/news/python-gui-development-using-tkinter/

import tkinter as tk #imports whole library 
from tkinter import ttk, messagebox #widgets and error message 
from datetime import datetime 
import db_manager as db
from models import FoodItem


RED_BG    = "#ffcccc"   # ≤ 3 days remaining
YELLOW_BG = "#fff3cd"   # ≤ 7 days remaining
GREEN_BG  = "#d4edda"   # > 7 days remaining


def validate_date(date_str: str, name: str): #bool if both okay True, if not False
    #first we check wether the name isn't blank
    if not name.strip():
        messagebox.showerror("Input Error", "Food name cannot be blank")
        return False
    #checks the date: strptime enforces both format AND calendar rules
    try:
        datetime.strptime(date_str, "%d/%m/%Y") #turns it into format python can understand, if not the following format
    except ValueError:
        messagebox.showerror("Input Error", "Date must be in DD/MM/YYYY format (e.g. 28/05/2026).")
        return False
    
    return True


def _restore_placeholder(entry: tk.Entry, placeholder: str):
    entry.delete(0, tk.END)
    entry.insert(0, placeholder)
    entry.config(fg="grey")


#placeholder helper tutorial, widget with placeholder pattern
def _attach_placeholder(entry: tk.Entry, placeholder: str):
    # writing a grey placeholder to a text entry 
    # clears the hint text when the field gains focus
    entry.insert(0, placeholder)
    entry.config(fg="grey")

    def _focus_in(_event):
        # removes the placeholder as soon as the user clicks on it
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.config(fg="black")

    def _focus_out(_event):
        # if the field is left empty restore the placeholder
        if entry.get().strip() == "":
            entry.insert(0, placeholder)
            entry.config(fg="grey")

    entry.bind("<FocusIn>",  _focus_in)
    entry.bind("<FocusOut>", _focus_out)
    # binds the event to the function

# TAB 1: Items Tab

def _build_items_tab(notebook: ttk.Notebook, conn):
    tab = ttk.Frame(notebook, padding=8)
    notebook.add(tab, text=" ITEMS ")

    # ADD NEW ITEM BOX(used LabelFrame pattern)
    add_section = tk.LabelFrame(tab, text=" ADD NEW ITEM ", padx=8, pady=8)
    add_section.pack(fill="x", pady=(0, 8))

    # food name input field LABEL
    tk.Label(add_section, text="Food Name:").grid(
        row=0, column=0, sticky="w", padx=(0, 8), pady=3)

    # entry for the food name; placeholder cleared on focus (Entry pattern)
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
        row=2, column=0, sticky="w", padx=(0, 8), pady=3)

    # entry for expiry date 
    expiry_entry = tk.Entry(add_section, width=14)
    expiry_entry.grid(row=2, column=1, sticky="w", pady=3)
    _attach_placeholder(expiry_entry, "DD/MM/YYYY")




    # sorting by section (Frame as layout container pattern)
    sort_frame = tk.Frame(tab)
    sort_frame.pack(fill="x", pady=(0, 4))

    tk.Label(sort_frame, text="Sort by:").pack(side="left", padx=(0, 6))

    list_section = tk.LabelFrame(tab, text=" Items ", padx=4, pady=4)
    list_section.pack(fill="both", expand=True, pady=(0, 6))

    #keeps the scrollbar and listbox together
    tree_frame = tk.Frame(list_section)
    tree_frame.pack(fill="both", expand=True)

    # MAIN LIST WITH COLOR CODE (Treeview pattern)
    # columns: checkbox state | food name | quantity | expiry date | days left | edit action
    # "check" column holds a ☐/☑ character, toggled by clicking it (see _on_tree_click).
    # "action" column holds "Edit" text representing the per-row EDIT ITEM button,
    # also handled in _on_tree_click.
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

    # vertical scrollbar linked to the Treeview (Scrollbar pattern)
    tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=tree_scroll.set)

    tree.pack(side="left", fill="both", expand=True)
    tree_scroll.pack(side="right", fill="y")

    # COLOUR LEGEND (Frame as layout container pattern)
    legend_frame = tk.Frame(tab)
    legend_frame.pack(fill="x", pady=(0, 6))

    tk.Label(legend_frame, text="Legend:").pack(side="left", padx=(0, 8))

    # (Label with bg colour pattern)
    for _bg, _lbl in (
        (RED_BG,    "≤ 3 days"),
        (YELLOW_BG, "≤ 7 days"),
        (GREEN_BG,  "> 7 days"),
    ):
        tk.Label(legend_frame, text=f"  {_lbl}  ",
                 bg=_bg, relief="groove").pack(side="left", padx=3)

    # REMOVE SELECTED / GET RECIPES buttons
    # tk.Frame holds the two action buttons side by side (Frame layout pattern)
    btn_frame = tk.Frame(tab)
    btn_frame.pack(fill="x", pady=(0, 6))

    # REMOVE SELECTED button
    # kept as a variable so its command can be attached further down,
    # once _on_remove_selected (which needs refresh_listbox) has been defined
    remove_button = tk.Button(
        btn_frame, text="REMOVE SELECTED",
        bg="#3420e5", fg="black", activebackground="#2816ca",
        padx=10, pady=4,
    )
    remove_button.pack(side="left", padx=(0, 8))

    # Blue GET RECIPES button
    tk.Button(
        btn_frame, text="GET RECIPES",
        bg="#1565C0", fg="black", activebackground="#0d47a1",
        padx=10, pady=4,
    ).pack(side="left")

    # Warning banner (Label pattern)
    warning_label = tk.Label(
        tab,
        text="⚠  Expiry alerts will appear here",
        bg="#FFF3CD", fg="#856404",
        anchor="w", padx=8, pady=6,
        relief="solid", bd=1,
    )
    warning_label.pack(fill="x")

    _sort_key = ["days"]

    checked_items = set()
    editing_item_id = [None]

    def _days_label(days: int):
        if days < 0:
            return f"Expired ({abs(days)}d ago)"
        if days == 0:
            return "Expires today"
        return str(days)

    def update_warning(items: list):
        # collects every item expiring within three days or already expired
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

    def _populate_tree(items: list):
        # wipe every existing row before re-inserting; this is the full-refresh pattern
        # that avoids duplicates when the DB changes
        for row_id in tree.get_children():
            tree.delete(row_id)

        for item in items:
            # use the food_items row id as the Treeview row's iid so a click on a
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

        # apply the user-selected sort; name is always the tiebreaker so items
        # with the same primary value appear in consistent alphabetical order
        key = _sort_key[0]
        if key == "days":
            items.sort(key=lambda it: (it.days_remaining(), it.name.lower()))
        elif key == "name":
            items.sort(key=lambda it: (it.name.lower(), it.days_remaining()))
        elif key == "qty":
            items.sort(key=lambda it: (it.quantity, it.name.lower()))

        _populate_tree(items)

    def _sort_by(key: str):
        # record the new sort preference and immediately re-render the list
        _sort_key[0] = key
        refresh_listbox()

    def _validate_inputs():
        # reads and validates the three entry fields, shared by both the
        # "add new item" and "save edited item" flows.
        # returns (name, quantity, expiry_date) on success, or None on failure
        # (an error messagebox has already been shown in the failure case).

        # read raw text from every entry field
        raw_name   = name_entry.get()
        raw_qty    = qty_entry.get()
        raw_expiry = expiry_entry.get()

        # treat placeholder text as "nothing entered" before validating
        name_val   = "" if raw_name   == "e.g. Apple" else raw_name.strip()
        expiry_val = "" if raw_expiry == "DD/MM/YYYY"  else raw_expiry.strip()

        # validate_date checks the name isn't blank AND the date parses correctly;
        # it shows its own messagebox.showerror on failure
        if not validate_date(expiry_val, name_val):
            return None

        # show an error if it isn't a plain integer
        qty_raw = raw_qty if raw_qty != "e.g. 3" else ""
        try:
            qty_val = int(qty_raw)
        except ValueError:
            messagebox.showerror("Input Error", "Quantity must be a whole number.")
            return None

        # all inputs are valid
        return name_val, qty_val, expiry_val

    def _reset_form():
        # clears the entry fields back to their placeholder text...
        _restore_placeholder(name_entry,   "e.g. Apple")
        _restore_placeholder(qty_entry,    "e.g. 3")
        _restore_placeholder(expiry_entry, "DD/MM/YYYY")

        # ...and switches the form back to "add a new item" mode
        editing_item_id[0] = None
        save_button.config(text="+ ADD ITEM")

    def _on_save():
        # called by the form's main button, in either "+ ADD ITEM" or
        # "Save Changes" mode depending on editing_item_id
        result = _validate_inputs()
        if result is None:
            return
        name_val, qty_val, expiry_val = result

        if editing_item_id[0] is None:
            # ADD MODE: no existing row is selected, so insert a brand new item
            item = FoodItem(item_id=None, name=name_val, quantity=qty_val, expiry_date=expiry_val)
            db.insert_item(conn, item)
        else:
            # EDIT MODE: overwrite the row that was loaded by _start_edit
            db.update_item(conn, editing_item_id[0], name_val, qty_val, expiry_val)

        _reset_form()
        refresh_listbox()

    def _start_edit(row_id: str):
        # called when the "Edit" cell in a row is clicked; copies that row's
        # current values into the form and switches it into "Save Changes" mode
        values = tree.item(row_id, "values")
        name_val, qty_val, expiry_val = values[1], values[2], values[3]

        # drop the row's current values into the entries, overwriting
        # whatever placeholder/previous text was there
        name_entry.delete(0, tk.END)
        name_entry.insert(0, name_val)
        name_entry.config(fg="black")

        qty_entry.delete(0, tk.END)
        qty_entry.insert(0, str(qty_val))
        qty_entry.config(fg="black")

        expiry_entry.delete(0, tk.END)
        expiry_entry.insert(0, expiry_val)
        expiry_entry.config(fg="black")

        # remember which db row the form now represents, and relabel the
        # button so the user knows the next click will save, not add
        editing_item_id[0] = int(row_id)
        save_button.config(text="Save Changes")

    def _on_tree_click(event):
        # handles clicks on the Treeview: toggles the checkbox column and
        # triggers edit mode when the "Edit" action column is clicked
        if tree.identify_region(event.x, event.y) != "cell":
            return  # ignore clicks on headings/empty space

        row_id = tree.identify_row(event.y)
        column = tree.identify_column(event.x)
        if not row_id:
            return

        if column == "#1":
            # "check" column: flip this row's ticked/unticked state
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
            # "action" column: load this row into the form for editing
            _start_edit(row_id)

    def _on_remove_selected():
        # deletes every row whose checkbox is ticked
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


    # ADD ITEM / SAVE CHANGES button (Button bg pattern)
    # this single button is reused for both modes; _on_save checks
    # editing_item_id to decide whether to insert or update, and
    # _reset_form()/_start_edit() flip its text between the two labels
    save_button = tk.Button(
        add_section, text="+ ADD ITEM",
        bg="#E877B5", fg="black", activebackground="#155b19",
        padx=10, pady=4,
        command=_on_save,
    )
    save_button.grid(row=3, column=1, sticky="e", pady=(8, 0))

    # now that _on_remove_selected exists, attach it to the button
    # created earlier alongside btn_frame
    remove_button.config(command=_on_remove_selected)

    # clicking the checkbox or "Edit" cell of any row is routed through _on_tree_click
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

def _build_recipes_tab(notebook: ttk.Notebook):
    tab = ttk.Frame(notebook, padding=8)
    notebook.add(tab, text=" RECIPES ")

    tk.Label(tab, text="Recipe Suggestions",
             font=("TkDefaultFont", 14, "bold")).pack(anchor="w", pady=(0, 10))

    # three recipe result boxes
    for _i in range(1, 4):
        # one per suggestion slot (LabelFrame pattern)
        box = tk.LabelFrame(tab, text=f" Recipe {_i} ", padx=8, pady=8)
        box.pack(fill="x", pady=4)

        # placeholder title 
        tk.Label(box, text="Recipe title will appear here",
                 font=("TkDefaultFont", 11, "bold")).pack(anchor="w")

        # placeholder body
        tk.Label(box,
                 text="Ingredients and details will be listed here.",
                 wraplength=480, justify="left").pack(anchor="w", pady=(2, 0))

    # blue SELECT TO SEE INSTRUCTIONS button (Button widget pattern)
    tk.Button(
        tab, text="SELECT TO SEE INSTRUCTIONS",
        bg="#1565C0", fg="black", activebackground="#0d47a1",
        padx=12, pady=6,
    ).pack(anchor="w", pady=(12, 0))



#first function that runs when app is launched 
# tk root window pattern

def main():
    root = tk.Tk()
    root.title("Food Expiry Tracker")
    root.geometry("640x740")
    root.minsize(520, 520)

    # creates the two-tab layout from: Notebook tabbed interface pattern
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=8, pady=8)

    conn = db.create_connection()
    db.create_table(conn)

    _build_items_tab(notebook, conn)
    _build_recipes_tab(notebook)

    root.mainloop()

if __name__ == "__main__":
    main()
