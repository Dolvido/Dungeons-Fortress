import random
from firebase_admin import firestore
from treasure import Treasure

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
        self.health = max(self.health - damage, 0) # Ensure health does not go below 0
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
        self.reset_player()  # Now reset the player's state including the inventory
        self.dungeon.delete_dungeon(db)  # finally delete the dungeon document from the db
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
        # Run a query to fetch all the treasure documents for the given player
        treasures_reference = db.collection('players').document(self.name).collection('treasures')
        treasures_snapshot = treasures_reference.stream()
        # Iterate through the snapshot and delete each document (treasure)
        for treasure_doc in treasures_snapshot:
            treasure_doc.reference.delete()
        print(f"Treasures cleared for player {self.name}")

    def use_treasure(self, index):
        if index < len(self.inventory):
            treasure = self.inventory.pop(index)  # Remove and get the treasure from the inventory
            return f'You used the {treasure}. Effect: {treasure.use()}'
        else:
            return "Invalid index. No such treasure in the inventory."

    def reset_player(self):
        self.exp = 0
        self.doubloons = 0
        self.health = 100
        self.inventory = []

    def gain_experience(self, amount):
        self.experience += amount
        print(f"You gained {amount} experience points!")
        self.save_to_db()  # Update the database whenever player's state changes

    def handle_combat(self, enemy_threat_level, db):
        # Calculate combat outcome
        combat_outcome = self.max_base_damage - enemy_threat_level  # Simplified for example
        # Take damage, returns string message about the combat outcome
        combat_message = self.take_damage(combat_outcome, db)
        # Award experience - this can be modified as per the game's logic
        self.award_exp(enemy_threat_level)

        if self.health > 0:
            return "won", combat_message
        else:  
            return "lost", combat_message

    def award_exp(self, exp):
        self.experience += exp

    def delete_treasures(self, db):
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
            'inventory': [item.to_dict() for item in self.inventory],
        }

    def save_to_db(self, db):
        player_ref = db.collection('players').document(self.name)
        player_ref.set(self.to_dict(), merge=True)

    @staticmethod
    async def load_from_db(player_name, db):
        player_ref = db.collection('players').document(player_name)
        player_doc = player_ref.get()
        if player_doc.exists:
            player_data = player_doc.to_dict()
            player = Player(player_data['name'])
            player.level = player_data.get('level', 1)
            player.experience = player_data.get('experience', 0)
            player.exp = player_data.get('exp', 0)
            player.doubloons = player_data.get('doubloons',0)
            player.health = player_data.get('health', 100)
            player.max_base_damage = player_data.get('max_base_damage', 10)

            # Load player's treasures
            treasures_reference = db.collection('players').document(player.name).collection('treasures')
            return player
        else:
            player = Player(player_name)
            return player
        
    def add_to_inventory(self, treasure, db):
        self.inventory.append(treasure)
        self.save_to_db(db)

    def escape(self, db):
    # Implement your escape logic here
        return "You have successfully escaped."
    
    def get_inventory(self):
        return self.inventory
        
           

