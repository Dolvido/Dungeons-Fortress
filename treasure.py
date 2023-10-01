import random

class Treasure:
    # A class to represent different types of treasures
    
    def __init__(self, treasure_type, material, origin, magical_properties=None):
        self.treasure_type = treasure_type  # e.g., jewel, artifact, scroll, potion, grimoire
        self.material = material  # e.g., gold, silver, diamond, ruby
        self.origin = origin  # e.g., dwarven, elvish, dragon hoard
        self.magical_properties = magical_properties or {}  # e.g., boosts stats, adds abilities, curses
        
    def __str__(self):
        # A string representation of the treasure with its details
        properties = ', '.join([f"{k}: {v}" for k, v in self.magical_properties.items()])
        return f"A {self.material} {self.treasure_type} of {self.origin} origin with magical properties ({properties})"
        
    def use(self):
        # A method to use or activate the treasure and apply its effects
        # This is a basic example; you can expand this based on your game's mechanics
        effects = ', '.join([f"{v}" for v in self.magical_properties.values()])
        return f"You used the {self.material} {self.treasure_type} and gained the following effects: {effects}"

    def to_dict(self):
        """
        Convert the Treasure object to a dictionary for database storage.
        """
        return {
            "treasure_type": self.treasure_type,
            "material": self.material,
            "origin": self.origin,
            "magical_properties": self.magical_properties
        }
