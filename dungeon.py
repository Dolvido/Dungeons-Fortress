from langchain import HuggingFaceHub, LLMChain
from langchain.memory import ConversationBufferMemory, ChatMessageHistory
from langchain.prompts import PromptTemplate

from firebase_admin import firestore

import random

db = firestore.client()

class Dungeon:
    def __init__(self, player, db):
        self.player = player
        self.history = []
        self.db = db
        self.repo_id_llm = "tiiuae/falcon-7b-instruct"
        self.depth = 0
        self.threat_level = None
        self.max_threat_level = 5
        self.threat_level_multiplier = 1.5
        self.chat_history = ChatMessageHistory()
        self.memory = ConversationBufferMemory(memory_key="adventure_history")

    def delete_dungeon(self):
        dungeon_ref = self.db.collection('dungeons').document(self.player.name)
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

    def continue_adventure(self):
        self.depth += 1
        damage_taken = 0
        response = ""

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
            response += self.combat_operation()

        if encounter == "treasure":
            response += self.treasure_operation()

        if (encounter == "nothing"):
            response += self.no_encounter_operation()

        self.end_of_continue_adventure_phase()
        return response

    def print_threat_level(self):
        print(f"Threat Level: {self.threat_level}")
        response = f"\nThreat Level: {self.threat_level}"

    def combat_operation(self):
        response = "\nCOMBAT ENCOUNTER\n"
        random_temperature = random.uniform(0.01, 1.0)

        dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                    model_kwargs={
                                        "temperature": random_temperature,
                                        "max_new_tokens": 250
                                    })

        generate_enemy_prompt = "{adventure_history} In the depths of the dungeon, amidst the echoing sounds of distant horrors, our adventurer encounters a new threat at power level {enemy_threat_level}. Describe the enemy that emerges from the shadows to challenge the hero."
        llm_enemy_prompt = PromptTemplate(template=generate_enemy_prompt,
                                            input_variables=["adventure_history", "enemy_threat_level"])

        enemy_chain = LLMChain(prompt=llm_enemy_prompt, llm=dungeon_llm, memory=self.memory)
        enemy_description = enemy_chain.predict(enemy_threat_level=self.threat_level)

        combat_status, combat_message = self.player.handle_combat(self.threat_level)

        if combat_status == "won":
            combat_narrative = self.get_victory_narrative(response, enemy_description)
        else:  
            combat_narrative = self.get_defeat_narrative(response, enemy_description)

        response += enemy_description
        response += combat_narrative
        response += combat_message

        return response

    def get_victory_narrative(self, response, enemy_description):
        random_temperature = random.uniform(0.01, 1.0)  # You can adjust the temperature as needed

        dungeon_llm = HuggingFaceHub(repo_id=self.repo_id_llm,
                                    model_kwargs={
                                        "temperature": random_temperature,
                                        "max_new_tokens": 250
                                    })

        victory_prompt = "{adventure_history} The hero, with unmatched bravery and skill, faces the {enemy_description}. Describe the epic moment the hero vanquishes the beast."
        llm_victory_prompt = PromptTemplate(template=victory_prompt,
                                                input_variables=["adventure_history", "enemy_description"])

        victory_chain = LLMChain(prompt=llm_victory_prompt, llm=dungeon_llm, memory=self.memory)
        combat_narrative = victory_chain.predict(adventure_history=response, enemy_description=enemy_description)

        return combat_narrative

    def get_defeat_narrative(self, response, enemy_description):
        defeat_prompt = "{adventure_history} Despite the hero's valiant efforts, the {enemy_description} proves to be too powerful. Describe the tragic moment the hero is defeated by the beast."
        llm_defeat_prompt = PromptTemplate(template=defeat_prompt, input_variables=["adventure_history", "enemy_description"])

        defeat_chain = LLMChain(prompt=llm_defeat_prompt, llm=dungeon_llm, memory=self.memory)
        combat_narrative = defeat_chain.predict(adventure_history=response, enemy_description=enemy_description)

        return combat_narrative

    def treasure_operation(self):
        response = "\nTREASURE ROOM\n"
        random_temperature = random.uniform
