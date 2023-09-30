import random
from firebase_admin import firestore


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

    @property
    def stats(self):
        return self.exp, self.health

    def take_damage(self, damage):
        self.health -= damage
        if self.health < 0: 
            self.health = 0
        response = f"\nYou took {damage} damage and have {self.health} health remaining."
        if self.health == 0:
            death_message, lost_treasures = self.die()
            response += f"\n{death_message}\n{lost_treasures}"
        return response

    def die(self):
        self.clear_all_items_from_inventory()
        death_message = "You have died."
        lost_treasures = "You've lost all your treasures." if any(self.inventory.values()) else \
                         "You died with no treasures in your possession."
        self.reset_player_stat()
        self.delete_treasures_from_db()
        return death_message, lost_treasures

    def flee(self):
        self.clear_all_items_from_inventory()
        self.reset_player_stat()
        self.delete_treasures_from_db()
        return "You have fled the dungeon. You've lost all your treasures and doubloons."

    def clear_all_items_from_inventory(self):
        firestore_update_query = self.db.collection('players').document(self.name).update({'treasures': firestore.DELETE_FIELD})
        print(f"Treasures cleared for player {self.name}")

    def add_to_inventory(self, category, item):
        if category not in self.inventory:
            self.inventory[category] = []
        self.inventory[category].append(item)

    async def get_inventory(self):
        await self.load_player_inventory_from_db()
        return self.inventory

    def reset_player_stat(self):
        self.exp = 0
        self.doubloons = 0
        self.health = 100
        self.inventory = {}

    def gain_experience(self, amount):
        self.experience += amount
        print(f"You gained {amount} experience points!")
        self.save_player_stat_to_db()
   
    def handle_combat(self, enemy_threat_level):
        combat_outcome = enemy_threat_level - self.max_base_damage
        self.take_damage(combat_outcome)
        self.award_exp(enemy_threat_level)
        player_stat_update_query = self.db.collection('players').document(self.name)
        player_stat_update_query.update({'health': self.health, 'experience': self.experience})
        if self.health > 0:
            return "won", f"You took {combat_outcome} damage and have {self.health} health remaining."
        else:
            death_message, lost_treasures = self.die()
            return "lost", f"You have died due to taking {combat_outcome} damage.\n{death_message}\n{lost_treasures}"

    def award_exp(self, exp):
        self.experience += exp

    def delete_treasures_from_db(self):
        treasures_ref = self.db.collection('treasures').document(self.name)
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
        player = Player(data['name'], db)
        for key in ['level', 'experience', 'exp', 'doubloons', 'health', 'max_base_damage', 'inventory']: 
            setattr(player, key, data[key])
        return player
    
    def save_player_stat_to_db(self):
        self.db.collection('players').document(self.name).set(self.to_dict(), merge=True)

    @classmethod
    async def load_player(cls, player_name, db):
        player_db_ref = db.collection('players').document(player_name)
        player_data = await player_db_ref.get()
        return cls.from_dict(player_data.to_dict(), db) if player_data.exists else None

    async def load_player_inventory_from_db(self):
        treasure_data_db_ref = self.db.collection('treasures').document(self.name)
        treasure_data_from_db = treasure_data_db_ref.get()
        if treasure_data_from_db.exists:
            treasures_data = treasure_data_from_db.to_dict()
            self.inventory = treasures_data.get('treasures', [])
        else:
            self.inventory = []
            print("Treasure Document does not exist.")  # Debug print

    async def get_stats_from_db(self):
        player_stat_db_ref = self.db.collection('players').document(self.name)
        player_stat_from_db = await player_stat_db_ref.get()
        return player_stat_from_db.to_dict() if player_stat_from_db.exists else None

    def add_item_to_inventory(self, category, item):
        if category not in self.inventory:
            self.inventory[category] = []
        self.inventory[category].append(item)
