from datetime import datetime, date


class FoodItem:
    def __init__(self, item_id: int, name: str, quantity: int, expiry_date: str):
        self.item_id = item_id
        self.name = name
        self.quantity = quantity
        self.expiry_date: date = datetime.strptime(expiry_date, "%d/%m/%Y").date()

    def days_remaining(self):
        return (self.expiry_date - date.today()).days #maybe delete?

    def colour_tag(self):
        days = self.days_remaining()
        if days <= 3:
            return "red"
        if days <= 7:
            return "yellow"
        return "green"

    def expiry_date_str(self):
    #This is needed to display it back into GUI as a str   
        return self.expiry_date.strftime("%d/%m/%Y")


class Recipe:

    def __init__(self, title: str, ingredients: list[str], match_count: int = 0, is_cached: bool = False, id: int = None):
        self.id = id
        self.title = title
        self.ingredients = ingredients
        # number of food items chosen to load recipe
        self.match_count = match_count
        # true when this recipe was loaded from a local cache 
        self.is_cached = is_cached

    def match_score(self, items: list[FoodItem]):
        item_names = {item.name.lower() for item in items}
        return sum(
            1 for ingredient in self.ingredients
            if any(name in ingredient.lower() for name in item_names)
        )

    def is_manual_selection(self):
        return self.match_count > 0
