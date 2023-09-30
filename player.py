import random
import firebase_admin
from firebase_admin import credentials, firestore
import json


class Player:

    def __init__(self, name, db):
        self.name = name
        self.db = db
        self.level = 1
        self.experience = 0
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

    async def get_inventory(self):
        await self.load_player_inventory()  # Load the inventory from the database
        return self.inventory

    def reset_player(self):
        self.exp = 0
        self.doubloons = 0
        self.health = 100
        self.inventory = {}

    def gain_experience(self, amount):
        self.experience += amount
        print(f"You gained {amount} experience points!")
        # Save player state to Firestore whenever it changes
        self.save_player()

    def to_dict(self):
        return {
            'name': self.name,
            'level': self.level,
            'experience': self.experience,
            'exp': self.exp,
            'doubloons': self.doubloons,
            'health': self.health,
            'max_base_damage': self.max_base_damage,
            'inventory': self.inventory,
        }

    @staticmethod
    def from_dict(data, db):
        player = Player(data['name'], db)
        player.level = data['level']
        player.experience = data['experience']
        player.exp = data['exp']
        player.doubloons = data['doubloons']
        player.health = data['health']
        player.max_base_damage = data['max_base_damage']
        player.inventory = data['inventory']
        return player
    
    def save_player(self):
        player_ref = self.db.collection('players').document(self.name)
        player_ref.set(self.to_dict(), merge=True)

    @classmethod
    async def load_player(cls, player_name, db):
        # Asynchronously load player data from the database
        doc_ref = db.collection('players').document(player_name)
        doc = await doc_ref.get()

        if doc.exists:
            player_data = doc.to_dict()

            # Create a Player object with the fetched data
            player = cls(name=player_name, db=db)
            player.level = player_data.get('level', 1)
            player.experience = player_data.get('experience', 0)
            player.exp = player_data.get('exp', 0)
            player.doubloons = player_data.get('doubloons', 0)
            player.health = player_data.get('health', 100)
            player.max_base_damage = player_data.get('max_base_damage', 10)

            await player.load_player_inventory(player_name)  # Load player's inventory

            return player
        else:
            print(f"No player found with the name {player_name}")
            return None

    async def load_player_inventory(self):
        # Asynchronously load player's treasures from the database
        treasure_ref = self.db.collection('treasures').document(self.name)
        treasure_doc = treasure_ref.get()  # Removed 'await'

        if treasure_doc.exists:
            treasures_data = treasure_doc.to_dict()
            print(f"Treasures Data from DB: {treasures_data}")  # Debug print
            self.inventory = treasures_data.get('treasures', [])
            print(f"Player's Inventory after Assignment: {self.inventory}")  # Debug print
        else:
            self.inventory = []
            print("Treasure Document does not exist.")  # Debug print

    async def get_stats_from_db(self):
        player_ref = self.db.collection('players').document(self.name)
        player_doc = await player_ref.get()
        if player_doc.exists:
            return player_doc.to_dict()
        else:
            return None

    def add_to_inventory(self, category, item):
        """
        Add the item to the player's inventory under the given category.
        """
        if category not in self.inventory:
            self.inventory[category] = []
        self.inventory[category].append(item)



