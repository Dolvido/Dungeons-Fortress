import random
import json

class Treasure:
    # A class to represent different types of treasures
    
    def __init__(self, treasure_type, material, origin):
        self.treasure_type = treasure_type  # e.g., jewel, artifact, scroll, potion, grimoire
        self.material = material  # e.g., gold, silver, diamond, ruby
        self.origin = origin  # e.g., dwarven, elvish, dragon hoard
        
    def __str__(self):
        # A string representation of the treasure with its details
        return f"{self.material} {self.treasure_type} of {self.origin} origin"
        
    def use(self):
        # A method to use or activate the treasure and apply its effects
        # This is a basic example; you can expand this based on your game's mechanics
        return f"You used the {self.material} {self.treasure_type}."

    def to_dict(self):
        """
        Convert the Treasure object to a dictionary for database storage.
        """
        return {
            "treasure_type": self.treasure_type,
            "material": self.material,
            "origin": self.origin
        }

    @staticmethod
    def from_dict(data):
        return Treasure(data['treasure_type'], data['material'], data['origin'])
