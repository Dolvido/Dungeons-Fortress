import random

class Player:

    def __init__(self):
        self.exp = 0
        self.doubloons = 0
        self.health = 100
        self.max_base_damage = 10
        self.inventory = {}

    def award_exp(self, exp):
        self.exp += exp

    def get_stats(self):
        return self.exp, self.health


    def decrement_health(self, base_damage, threat_level):
        base_damage = random.randint(1, self.max_base_damage)  # Random base damage up to max_base_damage
        scaled_damage = base_damage * (threat_level ** 2)  # Adjusted scaling formula
        self.health -= scaled_damage
        self.health = max(0, self.health)  # Ensure health does not go below 0

        response = f"\nYou took {scaled_damage} damage and have {self.health} health remaining."

        if self.health == 0:
            death_message, lost_treasures = self.die()  
            response += f"\n{death_message}\n{lost_treasures}"

        return response

    def die(self):
        death_message = "You have died."

        # Print out the inventory before it's lost
        if self.inventory and any(self.inventory.values()):
            treasures = ', '.join([f"{item}" for category, items in self.inventory.items() for item in items if items])
            lost_treasures = f"You've lost all your treasures: {treasures}"
        else:
            lost_treasures = "You died with no treasures in your possession."

        # Now reset the player's state including the inventory
        self.reset_player()

        return death_message, lost_treasures

    def add_to_inventory(self, category, item):
        if category not in self.inventory:
            self.inventory[category] = []
        self.inventory[category].append(item)

    def view_inventory(self):
        if not any(self.inventory.values()):
            return "Your inventory is empty."
        inventory_items = []
        for category, items in self.inventory.items():
            if items:
                items_str = [str(item) for item in items]
                inventory_items.append(f"{category.capitalize()}: {', '.join(items_str)}")
        return '\n'.join(inventory_items)

    def reset_player(self):
        self.exp = 0
        self.doubloons = 0
        self.health = 100
        self.inventory = {}