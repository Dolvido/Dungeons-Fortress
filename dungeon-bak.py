import random

from langchain import HuggingFaceHub, LLMChain
from langchain.agents import load_agent
from langchain.prompts import PromptTemplate, Prompt
from langchain.chains import ConversationChain, llm_requests
from langchain.memory import ConversationBufferMemory
from langchain.memory import ChatMessageHistory



# Dungeon class to manage dungeon state and interactions
class Dungeon:

    def __init__(self, player):
        print("init dungeon class")
        self.player = player
        self.history = []
        self.repo_id_llm = "tiiuae/falcon-7b-instruct"  # See https://huggingface.co/models?pipeline_tag=text-generation&sort=downloads for some other options
        self.depth = 0
        self.threat_level = 1
        self.max_threat_level = 5
        self.threat_level_multiplier = 1.5
        self.chat_history = ChatMessageHistory()
        self.memory = BufferMemory(chat_history=self.chat_history)


    def start(self):
        print("start_dungeon")

        # Randomize the temperature between 0.1 and 1.0 to get a new adventure each time
        random_temperature = random.uniform(0.01, 1.0)

        dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                        model_kwargs={
                                            "temperature": random_temperature,
                                            "max_new_tokens": 250
                                        })

        # Define a dungeoneering adventure prompt template
        dung_start_template = """Describe the beginning of a fantasy {target}. The adventurer is about to depart on a grisly adventure into a dungeon that they may not survive. Set the stage."""

        dungeon_start_prompt = PromptTemplate(template=dung_start_template,
                                                input_variables=["target"])

        llm_chain = LLMChain(prompt=dungeon_start_prompt, llm=dungeon_llm, memory=self.memory)
        """Generates a llm chain response to the given query."""
        try:
            response = llm_chain.run("adventure")
            self.history.append(response)
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
            response += "\nCOMBAT ENCOUNTER\n"
            random_temperature = random.uniform(0.01, 1.0)

            dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                        model_kwargs={
                                            "temperature": random_temperature,
                                            "max_new_tokens": 250
                                        })

            #GENERATE ENEMY
            generate_enemy_prompt = """In the depths of the dungeon, amidst the echoing sounds of distant horrors, our adventurer encounters a new threat at power level {enemy_threat_level} Describe the enemy that emerges from the shadows to challenge the hero."""
            llm_enemy_prompt = PromptTemplate(template=generate_enemy_prompt,
                                            input_variables=["enemy_threat_level"])

            # create language model chain and run against our prompt
            enemy_chain = LLMChain(prompt=llm_enemy_prompt, llm=dungeon_llm, memory=self.memory)
            enemy_description = enemy_chain.run(str(encounter))

            combat_encounter_prompt = """The previous step in our adventure follows: {encounter}
            Amidst the eerie silence of the dungeon, a menacing enemy emerges from the shadows; {enemy} its eyes gleaming with hostility. The air grows cold and tense as the impending clash of forces looms. Armed with {weapon}, our hero faces the beast.
            
            Describe the battle in depth."""
            llm_prompt = PromptTemplate(
                template=combat_encounter_prompt,
                input_variables=["encounter", "enemy", "weapon"])

            llm_chain = LLMChain(prompt=llm_prompt, llm=dungeon_llm, memory=self.memory)

            try:
                response += enemy_description
                response += llm_chain.run(encounter=self.history[-1],
                                            enemy=enemy_description,
                                            weapon="short sword")
                self.history.append(response)
                earned_exp = 5
                self.player.award_exp(earned_exp)

                damage_taken = random.randint(5, 20)  # Example: Random damage taken
                response += "\n"+self.get_damage_message(damage_taken, self.threat_level)
                self.check_player_has_died()

            except Exception as e:
                response = f"I couldn't generate a response due to the following error: {str(e)}"

        # if treasure encounter
        if (encounter == "treasure"):
            response += "\nTREASURE ROOM\n"
            random_temperature = random.uniform(0.01, 1.0)

            dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                        model_kwargs={
                                            "temperature": random_temperature,
                                            "max_new_tokens": 250
                                        })

            treasure_encounter_prompt = """ A glimmer of light pierces the overwhelming darkness of the dungeon. Our hero, intrigued and hopeful, follows the gleaming trail. Hidden away in the obscurity, a majestic treasure awaits; {treasure} a testament to the lost civilization that once thrived here, now promising power and wealth.

        Describe the next events in detail."""
            llm_prompt = PromptTemplate(template=treasure_encounter_prompt,
                                        input_variables=["treasure"])

            generate_treasure_prompt = """In the depths of the ancient and mystical dungeon, amidst the eerie silence punctuated by the echoes of distant roars and clanks, a hidden chamber reveals itself. Shrouded in mystery, it harbors a {material} {type} adorned with {adornment}, an artifact of the {era} era, believed to possess {power}."""
            llm_treasure_prompt = PromptTemplate(
                template=generate_treasure_prompt,
                input_variables=["material", "type", "adornment", "era", "power"])

            # Lists of possible attributes for each category
            materials = [
                "golden", "silver", "crystalline", "jewel-encrusted", "ancient stone"
            ]
            types = ["chest", "statue", "amulet", "crown", "sword"]
            adornments = [
                "intricate runes", "mystical symbols", "gemstones",
                "ancient inscriptions", "magical glyphs"
            ]
            eras = [
                "Elvish", "Dwarven", "Ancient Human", "Lost Civilization", "Mythical"
            ]
            powers = [
                "enigmatic magical aura", "curse of eternal slumber",
                "blessing of invincibility", "power of foresight",
                "charm of endless wealth"
            ]

            # Randomly selecting attributes for the treasure
            treasure_attributes = {
                "material": random.choice(materials),
                "type": random.choice(types),
                "adornment": random.choice(adornments),
                "era": random.choice(eras),
                "power": random.choice(powers)
            }
            self.player.add_to_inventory('treasures', treasure_attributes)
            treasure_chain = LLMChain(prompt=llm_treasure_prompt, llm=dungeon_llm, memory=self.memory)
            generated_treasure = treasure_chain.run(treasure_attributes)

            llm_chain = LLMChain(prompt=llm_prompt, llm=dungeon_llm, memory=self.memory)

            try:
                response += generated_treasure
                response += llm_chain.run(encounter=self.history[-1],
                                            treasure=generated_treasure)
                self.history.append(response)
                #earned_exp = self.player.award_exp()
                #self.player.award_exp(earned_exp)
                #response += f"\nYou Earned:\n{earned_exp} exp"

            except Exception as e:
                response = f"I couldn't generate a response due to the following error: {str(e)}"
                # Strip the "Human:" string and the rest of the string after it

            # if nothing
        if (encounter == "nothing"):
            response += "\nEMPTY ROOM\n"
            # Randomize the temperature between 0.1 and 1.0 to get a new adventure each time
            random_temperature = random.uniform(0.01, 1.0)

            dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                        model_kwargs={
                                            "temperature": random_temperature,
                                            "max_new_tokens": 250
                                        })

            continue_dungeon_prompt = """The previous step in our adventure follows: {history} 
            What happens next?"""
            llm_prompt = PromptTemplate(template=continue_dungeon_prompt,
                                        input_variables=["history"])

            llm_chain = LLMChain(prompt=llm_prompt, llm=dungeon_llm, memory=self.memory)
            """Generates a llm chain response to the given query."""

            try:

                response += llm_chain.run(self.history[-1])
                self.history.append(response)

            except Exception as e:
                response = f"I couldn't generate a response due to the following error: {str(e)}"

        # end of continue_adventure            
        return response

    def stop(self):
        # Implement the logic to stop the dungeon
        response = "Stopping the dungeon..."  # Placeholder, replace with actual implementation
        return response

    def update_threat_level(self):
        # Update threat level exponentially
        self.threat_level *= self.threat_level_multiplier  # Adjust the multiplier as needed

        # Cap the threat level to the maximum value
        self.threat_level = min(self.threat_level, self.max_threat_level)


    def flee(self):
        """
        Handle the player's action to flee from the dungeon or combat.
        Implement penalties or rewards for fleeing, depending on the game design.
        """
        inventory = self.player.view_inventory()
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

