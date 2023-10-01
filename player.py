import random
from firebase_admin import firestore
from treasure import Treasure
import json


class Player:

    def __init__(self, name):
        self.name = name
        
        self.level = 1
        self.experience = 0
        self.exp = 0
        self.doubloons = 0
        self.health = 100
        self.max_base_damage = 10
        self.inventory = []
        self.armor = None

    def get_stats(self):
        return self.exp, self.health

    def take_damage(self, damage, db):
        if self.armor is not None:
            # If player has armor equipped, reduce the damage taken
            damage -= self.armor.defense_value
        self.health = max(self.health - damage, 0)
        self.health = max(0, self.health)  # Ensure health does not go below 0

        response = f"\nYou took {damage} damage and have {self.health} health remaining."

        if self.health == 0:
            death_message, lost_treasures = self.die(db)
            self.dungeon.delete_dungeon(db)  
            response += f"\n{death_message}\n{lost_treasures}"

        return response



    def die(self, db):
        death_message = "You have died."

        # Clear inventory and treasures in database
        self.clear_treasures(db)
        self.delete_treasures(db)
            
        # Print out the inventory before it's lost
        if self.inventory:    
            treasures = ', '.join([f"{item}" for item in self.inventory])
            lost_treasures = f"You've lost all your treasures: {treasures}"
        else:
            lost_treasures = "You died with no treasures in your possession."

        # Now reset the player's state including the inventory
        self.reset_player()

        return death_message, lost_treasures

    def flee(self, db):
        # Clear the player's treasures
        self.clear_treasures(db)

        # Reset the player's state
        self.reset_player()
        self.clear_treasures(db)

        self.dungeon.delete_dungeon(db)
        return "You have fled the dungeon. You have lost all your treasures and doubloons."

    def clear_treasures(self, db):
        # Get the reference to the player's document in Firestore
        # Adjust the path according to your Firestore structure
        player_doc_ref = db.collection('players').document(self.name).collection('treasures')

        # Run a query to fetch all the treasure documents for the given player
        treasures_snapshot = player_doc_ref.stream()

        # Iterate through the snapshot and delete each document (treasure)
        for treasure_doc in treasures_snapshot:
            treasure_doc.reference.delete()

        print(f"Treasures cleared for player {self.name}")

    def use_treasure(self, index):
        if index < len(self.inventory):
            treasure = self.inventory.pop(index)
            return f'You used the {treasure}. Effect: {treasure.use()}'
        else:
            return "Invalid index. No such treasure in the inventory."

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
   
    def handle_combat(self, enemy_threat_level, db):
        # Calculate combat outcome
        combat_outcome = self.max_base_damage - enemy_threat_level  # Simplified for example
        
        # Take damage, returns string message about the combat outcome
        combat_message = self.take_damage(combat_outcome, db)
            
        # Award experience - this can be modified as per the game's logic
        self.award_exp(enemy_threat_level)
            
        # Check if player won or lost
        if self.health > 0:
            # Player won the combat, update health and experience in the database
            player_ref = db.collection('players').document(self.name)
            player_ref.update({'health': self.health, 'experience': self.experience})
            return "won", combat_message
        else:  
            return "lost", combat_message
        
    def award_exp(self, exp):
        self.experience += exp

    def delete_treasures(self, db):
        print(f"Deleting treasures for player {self.name}")
        treasures_ref = db.collection('treasures').document(self.name)
        treasures_ref.delete()

        
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
        player = Player(data['name'])
        player.level = data['level']
        player.experience = data['experience']
        player.exp = data['exp']
        player.doubloons = data['doubloons']
        player.health = data['health']
        player.max_base_damage = data['max_base_damage']
        player.inventory = data['inventory']
        return player
    
    def save_player(self, db):
        try:
            print(f"Saving player {self.name}")

            print(f"Player's Inventory before Assignment: {self.inventory}")
            print(f"Player's Inventory Type: {type(self.inventory)}")

            # Ensure inventory is not empty and items can be converted to dict
            for item in self.inventory:
                firestore_inventory = [item.to_dict() for item in self.inventory]
                
                # Replace the inventory with the Firestore format
                firestore_player = self.to_dict()
                firestore_player['inventory'] = firestore_inventory

                player_ref = db.collection('players').document(self.name)
                player_ref.set(firestore_player, merge=True)
                print(f"Player {self.name} saved to Firestore")
            else:
                print(f"Player {self.name} has an empty inventory or inventory items cannot be converted to dict")
        except Exception as e:
            print(f"An error occurred within save_player: {e}")
            print(f"Player {self.name} not saved to Firestore")

    def load_player_inventory(self, db):
        try:
            # Load player's treasures from the database
            treasures_ref = db.collection('players').document(self.name).collection('treasures')
            treasures_docs = treasures_ref.stream()

            self.inventory = []
            for treasure_doc in treasures_docs:
                if treasure_doc.exists:
                    treasure_data = treasure_doc.to_dict()
                    print(f"Treasure Data from DB: {treasure_data}")  # Debug print
                    self.inventory.append(Treasure.from_dict(treasure_data))

            print(f"Player's Inventory after Loading: {self.inventory}")  # Debug print
        except Exception as e:
            print(f"An error occurred within load_player_inventory: {e}")
            print(f"Player {self.name} not loaded from Firestore")

    async def get_inventory(self, db):
        self.load_player_inventory(db)  # Load the inventory from the database
        return self.inventory
    
    @classmethod
    async def load_player(cls, player_name, db):
        # Asynchronously load player data from the database
        doc_ref = db.collection('players').document(player_name)
        doc = doc_ref.get()

        if doc.exists:
            player_data = doc.to_dict()

            # Create a Player object with the fetched data
            player = cls(name=player_name)
            player.level = player_data.get('level', 1)
            player.experience = player_data.get('experience', 0)
            player.exp = player_data.get('exp', 0)
            player.doubloons = player_data.get('doubloons', 0)
            player.health = player_data.get('health', 100)
            player.max_base_damage = player_data.get('max_base_damage', 10)

            player.load_player_inventory(db)  # Load player's inventory

            return player
        else:
            print(f"No player found with the name {player_name}")
            # make an entry in the database for new player
            player = cls(name=player_name)
            player.save_player(db)
            return player

    async def get_stats_from_db(self, db):
        player_ref = db.collection('players').document(self.name)
        player_doc = await player_ref.get()
        if player_doc.exists:
            return player_doc.to_dict()
        else:
            return None

    def __str__(self):
        inventory = ', '.join(str(item) for item in self.inventory)
        return f"Player: {self.name}, Level: {self.level}, Health: {self.health}, Inventory: [{inventory}]"
            
    def add_to_inventory(self, treasure, db):
        """
        Add the treasure object to the player's inventory.
        """
        self.inventory.append(treasure)
        self.save_player(db)
            
    def use_treasure(self, index):
        """
        Use a treasure from the inventory based on its index.
        """
        if 0 <= index < len(self.inventory):
            treasure = self.inventory.pop(index)  # Remove and get the treasure from the inventory
            return treasure.use()
        else:
            return "Invalid index. No such treasure in the inventory."
        
    def equip_armor(self, index):
        """
        Equip a armor from the inventory based on its index.
        """
        if 0 <= index < len(self.inventory) and self.inventory[index].treasure_type == 'armor':
            if self.armor is not None:
                # If another armor is already equipped, put it back to the inventory
                self.inventory.append(self.armor)
            # Equip the new armor and remove it from the inventory
            self.armor = self.inventory.pop(index)  
        else:
            return "Invalid index or the chosen item is not a armor."




