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

    def delete_dungeon(self):
        # Get a reference to the Dungeon document and then call the delete() method.
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

    # Implement the remaining needed methods as per the task and recorrecting where needed

    def combat_operation(self):
        pass

    def get_victory_narrative(self, response, enemy_description):
        pass

    def get_defeat_narrative(self, response, enemy_description):
        pass

    def treasure_operation(self):
        pass

    def no_encounter_operation(self):
        pass

    def end_of_continue_adventure_phase(self):
        pass

    def update_threat_level(self):
        pass
