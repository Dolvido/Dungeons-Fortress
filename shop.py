class Item:
    def __init__(self, name, cost, description):
        self.name = name
        self.cost = cost
        self.description = description

    def __str__(self):
        return f"{self.name} - {self.cost} doubloons - {self.description}"
    
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
        # check if player has enough doubloons
        if player.doubloons < self.items[item_index].cost:
            raise Exception("You don't have enough doubloons!")
        # deduct doubloons
        player.doubloons -= self.items[item_index].cost
        # Add item to player's in-memory inventory
        player.inventory.append(self.items[item_index])
        # Add item to player's inventory in Firestore
        db.collection('players').document(player.name).collection('items').add(
            self.items[item_index].to_dict()
        )
        player.save_to_db(db)  # Ensure player data, including doubloons and inventory, is saved in the database
        return self.items[item_index].name