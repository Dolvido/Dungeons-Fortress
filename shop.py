class Item:
    def __init__(self, name, cost, description):
        self.name = name
        self.cost = cost
        self.description = description

    def to_dict(self):
        """
        Convert the Item object to a dictionary for database storage.
        """
        return {
            "name": self.name,
            "cost": self.cost,
            "description": self.description
        }

    @staticmethod
    def from_dict(data):
        item = Item(
            name = data.get("name"),
            cost = data.get("cost"),
            description = data.get("description")
        )
        return item

class Shop:
    def __init__(self):
        self.items = [
            Item("health_potion", 10, "Restores 50 points of health."),
            Item("strength_potion", 20, "Increases attack power by 5 for the next 3 turns."),
            # additional items could be added here
        ]

    def get_shop_display(self):
        return "\n".join([f"{idx+1}. {item.name} - {item.cost} doubloons - {item.description}" for idx, item in enumerate(self.items)])

    def buy(self, item_index, player, db):
        if item_index < 0 or item_index >= len(self.items):
            return "Invalid item index."

        item_to_buy = self.items[item_index]
        if player.doubloons < item_to_buy.cost:
            return "Not enough doubloons."
            
        player.doubloons -= item_to_buy.cost
        player.items.append(item_to_buy)

        player.save_to_db(db)
        return f"You bought {item_to_buy.name}."