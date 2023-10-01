from langchain import HuggingFaceHub, LLMChain
from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from langchain.prompts import PromptTemplate

from firebase_admin import firestore

import random

# The firestore client should be initialized in the bot.py file. The Dungeon class uses the instance previously created.
# You don't need to initialize it again here. Please remove: db = firestore.client()

class Dungeon:
    def __init__(self, player, db):
        self.player = player
        self.history = []
        self.db = db
        self.repo_id_llm = "tiiuae/falcon-7b-instruct"  # Moved to init method to avoid hard-coding in multiple places
        self.depth = 0
        self.threat_level = None
        self.max_threat_level = 5
        self.threat_level_multiplier = 1.5
        self.chat_history = ChatMessageHistory()
        self.memory = ConversationBufferMemory(memory_key="adventure_history")

    def delete_dungeon(self, db):
        # Get a reference to the Dungeon document and then call the delete() method.
        dungeon_ref = db.collection('dungeons').document(self.player.name)
        dungeon_ref.delete()


    def start(self):
        self.depth = 0
        self.threat_level = 1
        random_temperature = random.uniform(0.01, 1.0)

        dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                    model_kwargs={
                                        "temperature": random_temperature,
                                        "max_new_tokens": 250
                                    })

        prompt_template = "{adventure_history} Describe the scene for a {adventure_type} adventure and set the stage for a dungeon adventure."
        dungeon_start_prompt = PromptTemplate(template=prompt_template,
                                                input_variables=["adventure_history", "adventure_type"])

        llm_chain = LLMChain(prompt=dungeon_start_prompt, llm=dungeon_llm, memory=self.memory)

        try:
            response = llm_chain.predict(adventure_type="dungeoneering")
            response += "\nDo you /continue or /flee?"
        except Exception as e:
            response = f"I couldn't generate a response due to the following error: {str(e)}"

        return response

    def continue_adventure(self, db):
        self.depth += 1
        damage_taken = 0
        response = ""
        print(self.player.name +'is continuing the dungeon adventure at depth ' + str(self.depth))

        self.print_threat_level()

        weights = {
            "combat": self.threat_level,
            "treasure": max(1, 5 - self.threat_level),
            "nothing": max(1, 10 - self.threat_level)
        }

        encounter = random.choices(
            population=["combat", "treasure", "nothing"], 
            weights=[weights["combat"], weights["treasure"], weights["nothing"]],
            k=1
        )[0]

        if (encounter == "combat"):
            print('encountered a combat encounter: ', self.player.name)
            response += self.combat_operation(db)

        if encounter == "treasure":
            print('encountered a treasure room: ', self.player.name)
            response += self.treasure_operation(db)

        if (encounter == "nothing"):
            print('encountered an empty room: ', self.player.name)
            response += self.no_encounter_operation(db)

        self.end_of_continue_adventure_phase(db)
        return response

    def print_threat_level(self):
        print(f"Threat Level: {self.threat_level}")
        response = f"\nThreat Level: {self.threat_level}"

    # Implement the remaining needed methods as per the task and recorrecting where needed

    def combat_operation(self, db):
        # Generate random temperature variable for the language model chain
        random_temperature = random.uniform(0.01, 1.0)

        dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                    model_kwargs={
                                        "temperature": random_temperature,
                                        "max_new_tokens": 250
                                    })
        
        enemy_attributes = {
            "type": random.choice(["goblin", "troll", "dragon", "skeleton", "zombie"]),
            "weapon": random.choice(["claws", "sword", "magic", "fangs", "axe"]),
            "appearance": random.choice(["horrifying", "grotesque", "terrifying", "ghastly", "hideous"]),
            "strength": random.choice(["immense strength", "magical powers", "swift agility", "overwhelming numbers", "deadly precision"]),
            "weakness": random.choice(["fear of light", "slow movements", "limited vision", "low intelligence", "magic susceptibility"])
        }

        enemy_assembled_string = f'A {enemy_attributes["appearance"]} {enemy_attributes["type"]} wielding a {enemy_attributes["weapon"]} with {enemy_attributes["strength"]}, but has a {enemy_attributes["weakness"]}'
        print("Enemy string: " + enemy_assembled_string)
        generate_enemy_prompt = "{adventure_history} In the depths of the dungeon, amidst the echoing sounds of distant horrors, our adventurer encounters a new threat. The enemy that emerges from the shadows to challenge the hero is a {enemy}."
        llm_enemy_prompt = PromptTemplate(template=generate_enemy_prompt, input_variables=["adventure_history", "enemy"])

        print("generating enemy")
        enemy_chain = LLMChain(prompt=llm_enemy_prompt, llm=dungeon_llm, memory=self.memory)
        enemy_description = enemy_chain.predict(enemy=enemy_assembled_string)

        combat_status, combat_message = self.player.handle_combat(self.threat_level, db)

        print("generating narrative")
        print("enemy description: " + enemy_description)
        if combat_status == "won":
            combat_narrative = self.get_victory_narrative(enemy_assembled_string)
        else:  # if the combat_status is "lost"
            combat_narrative = self.get_defeat_narrative(enemy_assembled_string)

        response = f"\nCOMBAT ENCOUNTER\n"
        response += enemy_description
        response += combat_narrative
        response += combat_message

        return response

    def get_victory_narrative(self, enemy_description):
        print("get_victory_narrative")
        random_temperature = random.uniform(0.01, 1.0)  # You can adjust the temperature as needed

        dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                        model_kwargs={
                                            "temperature": random_temperature,
                                            "max_new_tokens": 250
                                        })

        victory_prompt = "{adventure_history} The hero, with unmatched bravery and skill, faces the {enemy_description}. Describe the epic moment the hero vanquishes the beast."
        llm_victory_prompt = PromptTemplate(template=victory_prompt, input_variables=["adventure_history", "enemy_description"])

        victory_chain = LLMChain(prompt=llm_victory_prompt, llm=dungeon_llm, memory=self.memory)
        combat_narrative = victory_chain.predict(enemy_description=enemy_description.format())
    
        return combat_narrative

    def get_defeat_narrative(self, enemy_description):
        print("get_defeat_narrative")
        random_temperature = random.uniform(0.01, 1.0)  # You can adjust the temperature as needed

        dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                        model_kwargs={
                                            "temperature": random_temperature,
                                            "max_new_tokens": 250
                                        })
        
        defeat_prompt = "{adventure_history} Despite the hero's valiant efforts, the {enemy_description} proves to be too powerful. Describe the tragic moment the hero is defeated by the beast."
        llm_defeat_prompt = PromptTemplate(template=defeat_prompt, input_variables=["adventure_history", "enemy_description"])

        defeat_chain = LLMChain(prompt=llm_defeat_prompt, llm=dungeon_llm, memory=self.memory)
        combat_narrative = defeat_chain.predict(enemy_description=enemy_description.format())
    
        return combat_narrative


    def treasure_operation(self, db):
        """
        Handles the operation where the adventure enters a treasure room.
        """
        random_temperature = random.uniform(0.01, 1.0)

        dungeon_llm = HuggingFaceHub(
            repo_id=self.repo_id_llm,
            model_kwargs={
                "temperature": random_temperature,
                "max_new_tokens": 250
            }
        )

        treasure_attributes = {
            "material": random.choice(["golden", "silver", "crystalline", "jewel-encrusted", "ancient stone"]),
            "type": random.choice(["chest", "statue", "amulet", "crown", "sword"]),
            "adornment": random.choice(["intricate runes", "mystical symbols", "gemstones", "ancient inscriptions", "magical glyphs"]),
            "era": random.choice(["Elvish", "Dwarven", "Ancient Human", "Lost Civilization", "Mythical"]),
            "power": random.choice(["enigmatic magical aura", "curse of eternal slumber", "blessing of invincibility", "power of foresight", "charm of endless wealth"])
        }

        treasure_assembled_string = f'{treasure_attributes["material"]} {treasure_attributes["type"]} adorned with {treasure_attributes["adornment"]}, an artifact of the {treasure_attributes["era"]} era, believed to possess {treasure_attributes["power"]}'
        
        generate_treasure_prompt = "{adventure_history} In the depths of the ancient and mystical dungeon, amidst the eerie silence punctuated by the echoes of distant roars and clanks, a hidden chamber reveals itself. Shrouded in mystery, it harbors a {treasure}."  # Changed {treasure_assembled_string} to {treasure}
        llm_treasure_prompt = PromptTemplate(template=generate_treasure_prompt,
                                            input_variables=["adventure_history", "treasure"])  # Changed "treasure_assembled_string" to "treasure"

        # Create language model chain and run against our prompt
        treasure_chain = LLMChain(prompt=llm_treasure_prompt, llm=dungeon_llm, memory=self.memory)
        generated_treasure = treasure_chain.predict(treasure=treasure_assembled_string)  # Changed {treasure_assembled_string={treasure_assembled_string}} to treasure=treasure_assembled_string

        # Add the treasure to the player's inventory and database
        self.player.add_to_inventory('treasures', treasure_attributes, db)
        self.add_treasure_to_db(treasure_attributes, db)

        response = "\nTREASURE ROOM\n" + generated_treasure
        return response

    def no_encounter_operation(self, db):
        """
        Handles the operation where the adventure enters an empty room.
        """
        random_temperature = random.uniform(0.01, 1.0)

        dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                    model_kwargs={
                                        "temperature": random_temperature,
                                        "max_new_tokens": 250
                                    })

        continue_dungeon_prompt = "{adventure_history} Describe an {quality} room in detail."
        llm_prompt = PromptTemplate(template=continue_dungeon_prompt, input_variables=["adventure_history", "quality"])

        llm_chain = LLMChain(prompt=llm_prompt, llm=dungeon_llm, memory=self.memory)

        try:
            generated_description = llm_chain.run(quality="empty")
            self.history.append(generated_description)

        except Exception as e:
            generated_description = f"I couldn't generate a description due to the following error: {str(e)}"

        response = "\nEMPTY ROOM\n" + generated_description
        return response

    def end_of_continue_adventure_phase(self, db):
        """
        Called at the end of continue_adventure function to update threat level and dungeon state in the database.
        """
        print("end_of_continue_adventure_phase")
        self.update_threat_level(db)
        self.save_dungeon(db)

    def update_threat_level(self, db):
        """
        Update threat level exponentially and cap the threat level to the maximum value.
        """
        print("update_threat_level")
        self.threat_level *= self.threat_level_multiplier
        print("calculated threat level: " + str(self.threat_level))
        self.threat_level = min(self.threat_level, self.max_threat_level)
        dungeon_ref = self.db.collection('dungeons').document(self.player.name)
        dungeon_ref.update({'threat_level': self.threat_level})

    @staticmethod
    def load_dungeon(player, db):
        dungeon_data = db.collection('dungeons').document(player.name).get()
        if dungeon_data.exists:
            data = dungeon_data.to_dict()
            d = Dungeon(player, db)
            
            d.repo_id_llm = data.get('repo_id_llm')
            d.depth = data.get('depth')
            d.threat_level = data.get('threat_level')
            d.max_threat_level = data.get('max_threat_level')
            d.threat_level_multiplier = data.get('threat_level_multiplier')
            
            return d
        else:
            return None

    def save_dungeon(self, db):
        data = {
            'repo_id_llm': self.repo_id_llm,
            'depth' : self.depth,
            'threat_level' : self.threat_level,
            'max_threat_level' : self.max_threat_level,
            'threat_level_multiplier' : self.threat_level_multiplier
        }
        
        db.collection('dungeons').document(self.player.name).set(data)

