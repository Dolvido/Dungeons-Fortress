import random
import json

class Treasure:
    # A class to represent different types of treasures
    rarity_levels = ['Common', 'Uncommon', 'Rare', 'Very rare', 'Legendary']
    def __init__(self, treasure_type, material, origin, rarity, value, defense_value=None):
        self.treasure_type = treasure_type  # e.g., jewel, artifact, scroll, potion, grimoire
        self.material = material  # e.g., gold, silver, diamond, ruby
        self.origin = origin  # e.g., dwarven, elvish, dragon hoard
        self.rarity = random.choice(self.rarity_levels)
        self.value = self.rarity_levels.index(self.rarity) * 10  # set the value based on rarity, adjust as needed

        self.defense_value = defense_value if treasure_type == 'armor' else None

        
    def __str__(self):
        return f"{self.rarity} {self.material.capitalize()} {self.treasure_type.capitalize()} of {self.origin.capitalize()} origin valued at {self.value} doubloons"
        
    def use(self):
        # A method to use or activate the treasure and apply its effects
        # This is a basic example; you can expand this based on your game's mechanics
        if self.treasure_type == "scroll":
            return "You unrolled the scroll and read the mystical writings."
        elif self.treasure_type == "potion":
            return "You drank the potion. You feel its magical energy course through your body."
        else:       
            return f"You used the {self.material} {self.treasure_type}. Its {self.rarity} rarity sparkles with the mystique of its {self.origin} origin."
    

    def to_dict(self):
        """
        Convert the Treasure object to a dictionary for database storage.
        """
        return {
            "treasure_type": self.treasure_type,
            "material": self.material,
            "origin": self.origin,
            "rarity": self.rarity,
            "value": self.value,
            "defense_value": self.defense_value
        }

    @staticmethod
    def from_dict(data):  
        return Treasure(
            data.get('treasure_type', 'Unknown'), 
            data.get('material', 'Unknown'), 
            data.get('origin', 'Unknown'), 
            data.get('rarity', 'Unknown'), 
            data.get('value', 'Unknown'),
            data.get('defense_value')
        )        
