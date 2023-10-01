import random
import json

class Treasure:
    # A class to represent different types of treasures
    
    def __init__(self, treasure_type, material, origin, rarity, value):
        self.treasure_type = treasure_type  # e.g., jewel, artifact, scroll, potion, grimoire
        self.material = material  # e.g., gold, silver, diamond, ruby
        self.origin = origin  # e.g., dwarven, elvish, dragon hoard
        self.rarity = rarity  # rarity of the treasure
        self.value = value  # value of the treasure
        
    def __str__(self):
        # A string representation of the treasure with its details
        return f"{self.material} {self.treasure_type} of {self.origin} origin rated as {self.rarity} rarity with a value of {self.value} "
        
    def use(self):
        # A method to use or activate the treasure and apply its effects
        # This is a basic example; you can expand this based on your game's mechanics
        if self.treasure_type == "scroll":
            return "You unrolled the scroll and read the mystical writings."
        elif self.treasure_type == "potion":
            return "You drank the potion. You feel its magical energy course through your body."
        else:
            return f"You used the {self.material} {self.treasure_type}."

    def to_dict(self):
        """
        Convert the Treasure object to a dictionary for database storage.
        """
        return {
            "treasure_type": self.treasure_type,
            "material": self.material,
            "origin": self.origin,
            "rarity": self.rarity,
            "value": self.value
        }

    @staticmethod
    def from_dict(data):
        return Treasure(data['treasure_type'], data['material'], data['origin'], data['rarity'], data['value'])
