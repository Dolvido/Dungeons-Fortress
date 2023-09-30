import random

from langchain import HuggingFaceHub, LLMChain
from langchain.agents import load_agent
from langchain.prompts import PromptTemplate, Prompt
from langchain.chains import ConversationChain, llm_requests
from langchain.memory import ConversationBufferMemory
from langchain.memory import ChatMessageHistory

from firebase_admin import firestore

db = firestore.client()

# Dungeon class to manage dungeon state and interactions
class Dungeon:
    def delete_dungeon(self):
        dungeon_ref = self.db.collection('dungeons').document(self.player.name)
        dungeon_ref.delete()


    def __init__(self, player, db):
        print("init dungeon class")
        self.player = player
        self.history = []
        self.db = db
        #self.repo_id_llm = "mosaicml/mpt-7b-instruct"
        self.repo_id_llm = "tiiuae/falcon-7b-instruct"  # See https://huggingface.co/models?pipeline_tag=text-generation&sort=downloads for some other options
        self.depth = 0
        self.threat_level = 1
        self.max_threat_level = 5
        self.threat_level_multiplier = 1.5
        self.chat_history = ChatMessageHistory()
        #self.memory = BufferMemory(chat_history=self.chat_history)
        self.memory = ConversationBufferMemory(memory_key="adventure_history")
        #self.memory.save_context({"input", "The hero enters the dungeon."}, {"output", "The hero enters the dungeon."})

    def start(self):
        print("start_dungeon")

        self.depth = 0
        self.threat_level = 1

        # Randomize the temperature between 0.1 and 1.0 to get a new adventure each time
        random_temperature = random.uniform(0.01, 1.0)

        dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                        model_kwargs={
                                            "temperature": random_temperature,
                                            "max_new_tokens": 250
                                        })

        # Define a dungeoneering adventure prompt template
        prompt_template = """{adventure_history} Describe the scene for a {adventure_type} adventure and set the stage for a dungeon adventure."""
        dungeon_start_prompt = PromptTemplate(template=prompt_template,
                                                input_variables=["adventure_history", "adventure_type"])

        llm_chain = LLMChain(prompt=dungeon_start_prompt, llm=dungeon_llm, memory=self.memory)

        try:
            response = llm_chain.predict(adventure_type="dungeoneering")
            #self.history.append(response)
            response += "\nDo you /continue or /flee?"
        except Exception as e:
            response = f"I couldn't generate a response due to the following error: {str(e)}"

        return response

    def continue_adventure(self):
        print("continue_dungeon")
        self.depth += 1
        damage_taken = 0
        response = ""

        # Calculate threat level
        self.update_threat_level()
        print(f"Threat Level: {self.threat_level}")
        response += f"\nThreat Level: {self.threat_level}"
        
        # Determine encounter based on threat level
        # Determine encounter type based on threat level using weighted random choice
        weights = {
            "combat": self.threat_level,  # combat becomes more likely as threat level increases
            "treasure": max(1, 5 - self.threat_level),  # adjust these formulas as needed
            "nothing": max(1, 10 - self.threat_level)   # adjust these formulas as needed
        }
        encounter = random.choices(
            population=["combat", "treasure", "nothing"], 
            weights=[weights["combat"], weights["treasure"], weights["nothing"]],
            k=1
        )[0]

        # if combat encounter
        if (encounter == "combat"):
            print("Combat event triggered")
            response += "\nCOMBAT ENCOUNTER\n"
            random_temperature = random.uniform(0.01, 1.0)

            dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                        model_kwargs={
                                            "temperature": random_temperature,
                                            "max_new_tokens": 250
                                        })

            # GENERATE ENEMY
            generate_enemy_prompt = """{adventure_history} In the depths of the dungeon, amidst the echoing sounds of distant horrors, our adventurer encounters a new threat at power level {enemy_threat_level}. Describe the enemy that emerges from the shadows to challenge the hero."""
            llm_enemy_prompt = PromptTemplate(template=generate_enemy_prompt,
                                                input_variables=["adventure_history", "enemy_threat_level"])

            # create language model chain and run against our prompt
            enemy_chain = LLMChain(prompt=llm_enemy_prompt, llm=dungeon_llm, memory=self.memory)
            enemy_description = enemy_chain.predict(enemy_threat_level=self.threat_level)

            # Handle combat and get the outcome and message
            combat_status, combat_message = self.player.handle_combat(self.threat_level)

            # Depending on the combat outcome, generate the appropriate narrative
            if combat_status == "won":
                # Generate a dynamic victory message using LLM
                random_temperature = random.uniform(0.01, 1.0)  # You can adjust the temperature as needed

                dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                            model_kwargs={
                                                "temperature": random_temperature,
                                                "max_new_tokens": 250
                                            })

                # Prepare the prompt for generating the victory message
                victory_prompt = """{adventure_history} The hero, with unmatched bravery and skill, faces the {enemy_description}. Describe the epic moment the hero vanquishes the beast."""
                llm_victory_prompt = PromptTemplate(template=victory_prompt,
                                                    input_variables=["adventure_history", "enemy_description"])

                # Create language model chain and run against our prompt
                victory_chain = LLMChain(prompt=llm_victory_prompt, llm=dungeon_llm, memory=self.memory)
                combat_narrative = victory_chain.predict(adventure_history=response, enemy_description=enemy_description)
            else:  # if the combat_status is "lost"
                # Generate a dynamic defeat message using LLM
                defeat_prompt = """{adventure_history} Despite the hero's valiant efforts, the {enemy_description} proves to be too powerful. Describe the tragic moment the hero is defeated by the beast."""
                llm_defeat_prompt = PromptTemplate(template=defeat_prompt,
                                                input_variables=["adventure_history", "enemy_description"])

                # Create language model chain and run against our prompt
                defeat_chain = LLMChain(prompt=llm_defeat_prompt, llm=dungeon_llm, memory=self.memory)
                combat_narrative = defeat_chain.predict(adventure_history=response, enemy_description=enemy_description)

            response += enemy_description
            response += combat_narrative
            response += combat_message

        # You can add any additional logic here if needed, like updating the dungeon state or player's inventory

            # If treasure encounter
        if encounter == "treasure":
            print("Treasure event triggered")
            response += "\nTREASURE ROOM\n"
            random_temperature = random.uniform(0.01, 1.0)

            dungeon_llm = HuggingFaceHub(
                repo_id=self.repo_id_llm,
                model_kwargs={
                    "temperature": random_temperature,
                    "max_new_tokens": 250
                }
            )

            #GENERATE TREASURE
            generate_treasure_prompt = "{adventure_history} In the depths of the ancient and mystical dungeon, amidst the eerie silence punctuated by the echoes of distant roars and clanks, a hidden chamber reveals itself. Shrouded in mystery, it harbors a {treasure_assembled_string}."
            llm_treasure_prompt = PromptTemplate(
                template=generate_treasure_prompt,
                input_variables=["adventure_history", "treasure_assembled_string"]
            )
             # Lists of possible attributes for each category and randomly selecting attributes for the treasure
            materials = ["golden", "silver", "crystalline", "jewel-encrusted", "ancient stone"]
            types = ["chest", "statue", "amulet", "crown", "sword"]
            adornments = ["intricate runes", "mystical symbols", "gemstones", "ancient inscriptions", "magical glyphs"]
            eras = ["Elvish", "Dwarven", "Ancient Human", "Lost Civilization", "Mythical"]
            powers = ["enigmatic magical aura", "curse of eternal slumber", "blessing of invincibility", "power of foresight", "charm of endless wealth"]

            treasure_attributes = {
                "material": random.choice(materials),
                "type": random.choice(types),
                "adornment": random.choice(adornments),
                "era": random.choice(eras),
                "power": random.choice(powers)
            }
            treasure_assembled_string = f'{treasure_attributes["material"]} {treasure_attributes["type"]} adorned with {treasure_attributes["adornment"]}, an artifact of the {treasure_attributes["era"]} era, believed to possess {treasure_attributes["power"]}'

            # Add the treasure to the player's inventory
            self.player.add_to_inventory('treasures', treasure_attributes)

            # Store the treasure in the database
            self.add_treasure_to_db(treasure_attributes)

            # ... (continue with the existing code to generate the treasure description and add it to the response)

            llm_treasure_prompt = PromptTemplate(
                template=generate_treasure_prompt,
                input_variables=["adventure_history", "treasure_assembled_string"]
            )

            materials = ["golden", "silver", "crystalline", "jewel-encrusted", "ancient stone"]
            types = ["chest", "statue", "amulet", "crown", "sword"]
            adornments = ["intricate runes", "mystical symbols", "gemstones", "ancient inscriptions", "magical glyphs"]
            eras = ["Elvish", "Dwarven", "Ancient Human", "Lost Civilization", "Mythical"]
            powers = ["enigmatic magical aura", "curse of eternal slumber", "blessing of invincibility", "power of foresight", "charm of endless wealth"]

            treasure_attributes = {
                "material": random.choice(materials),
                "type": random.choice(types),
                "adornment": random.choice(adornments),
                "era": random.choice(eras),
                "power": random.choice(powers)
            }

            treasure_assembled_string = f'{treasure_attributes["material"]} {treasure_attributes["type"]} adorned with {treasure_attributes["adornment"]}, an artifact of the {treasure_attributes["era"]} era, believed to possess {treasure_attributes["power"]}'

            # Create language model chain and run against our prompt
            treasure_chain = LLMChain(prompt=llm_treasure_prompt, llm=dungeon_llm, memory=self.memory)

            try:
                generated_treasure = treasure_chain.predict(treasure_assembled_string=treasure_assembled_string)
                response += generated_treasure
                print(generated_treasure)
                treasure_encounter_prompt = """{adventure_history} A glimmer of light pierces the overwhelming darkness of the dungeon. Our hero, intrigued and hopeful, follows the gleaming trail. Hidden away in the obscurity, a majestic treasure awaits; {treasure} a testament to the lost civilization that once thrived here, now promising power and wealth.

                Describe the next events in detail."""
                llm_prompt = PromptTemplate(
                    template=treasure_encounter_prompt,
                    input_variables=["adventure_history", "treasure"]
                )
    
                llm_chain = LLMChain(prompt=llm_prompt, llm=dungeon_llm, memory=self.memory)
                response += llm_chain.predict(treasure=generated_treasure)
                self.history.append(response)
    
            except Exception as e:
                response = f"I couldn't generate a response due to the following error: {str(e)}"

            # if nothing
        if (encounter == "nothing"):
            print("Nothing event triggered")
            response += "\nEMPTY ROOM\n"
            # Randomize the temperature between 0.1 and 1.0 to get a new adventure each time
            random_temperature = random.uniform(0.01, 1.0)

            dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                        model_kwargs={
                                            "temperature": random_temperature,
                                            "max_new_tokens": 250
                                        })

            continue_dungeon_prompt = """Describe an {quality} room in detail."""
            llm_prompt = PromptTemplate(template=continue_dungeon_prompt, input_variables=["quality"])

            llm_chain = LLMChain(prompt=llm_prompt, llm=dungeon_llm)
            """Generates a llm chain response to the given query."""

            try:

                response += llm_chain.run(quality="empty")
                self.history.append(response)

            except Exception as e:
                response = f"I couldn't generate a response due to the following error: {str(e)}"

        # end of continue_adventure            
        return response

    def update_threat_level(self):
        print("update_threat_level")
        # Update threat level exponentially
        self.threat_level *= self.threat_level_multiplier  # Adjust the multiplier as needed

        # Cap the threat level to the maximum value
        self.threat_level = min(self.threat_level, self.max_threat_level)


    def flee(self):
        """
        Handle the player's action to flee from the dungeon or combat.
        Implement penalties or rewards for fleeing, depending on the game design.
        """
        treasures = self.player.inventory.get(
            'treasures', [])  # Get the treasures from the player's inventory
        response = "You have fled from the dungeon. Safety first."
        if treasures:  # Check if the player has collected any treasures
            treasures_str = ', '.join([str(treasure) for treasure in treasures
                                        ])  # Convert treasures to strings
            response += f"\n\nYou managed to escape with the following treasures:\n{treasures_str}"
        else:
            response += "\nUnfortunately, you didn't manage to collect any treasures this time."
        self.history = []
        self.history.append("Player fled from the dungeon.")
        self.threat_level = 1 
        return response

    def check_player_has_died(self):
        if self.player.health <= 0:
            print("Player Death event triggered")
            self.threat_level = 1
            return "Game Over! You have died."
        else:
            return False
        
    def get_damage_message(self, base_damage, threat_level):
        response = self.player.decrement_health(base_damage, threat_level)

        # You can also return the response if needed
        return response

    def reset_dungeon(self):
        print("Resetting dungeon...")
        self.history = []
        self.player.reset_player()  # You need to add a reset_player method in the Player class

    def to_dict(self):
        return {
            'depth': self.depth,
            'threat_level': self.threat_level,
            'max_threat_level': self.max_threat_level,
            'threat_level_multiplier': self.threat_level_multiplier,
            'history': self.history,
        }

    @staticmethod
    def from_dict(data, player, db):
        dungeon = Dungeon(player, db)
        dungeon.depth = data['depth']
        dungeon.threat_level = data['threat_level']
        dungeon.max_threat_level = data['max_threat_level']
        dungeon.threat_level_multiplier = data['threat_level_multiplier']
        dungeon.history = data['history']
        return dungeon
    
    def save_dungeon(self):
        dungeon_ref = self.db.collection('dungeons').document(self.player.name)
        dungeon_ref.set(self.to_dict(), merge=True)

    @classmethod
    def load_dungeon(cls, player, db):
        doc_ref = db.collection('dungeons').document(player.name)
        doc = doc_ref.get()
        if doc.exists:
            return Dungeon.from_dict(doc.to_dict(), player, db)
        return None


    def add_treasure_to_db(self, treasure):
        # The 'treasures' collection stores all treasures
        # Documents are identified by player ID and contain an array of treasures
        treasures_ref = db.collection('treasures').document(self.player.name)

        # Fetch the current document
        doc = treasures_ref.get()

        if doc.exists:
            # Update the document with the new treasure
            # This code adds the new treasure to an array of treasures in the document
            treasures = doc.to_dict().get('treasures', [])
            treasures.append(treasure)
            treasures_ref.update({'treasures': treasures})
        else:
            # If the document does not exist, create it
            treasures_ref.set({'treasures': [treasure]})
