import os
import random
import discord
import os
import re
import random
import discord
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
HUGGINGFACEHUB_API_TOKEN = os.environ["HUGGINGFACEHUB_API_TOKEN"]
TOKEN=os.environ["TOKEN"]


from player import Player
from dungeon import Dungeon



# Assuming you have necessary imports for langchain and other required modules
# Add them here as needed

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Global player and dungeon objects
player = Player()
dungeon = Dungeon(player)


# Discord client events
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

async def send_message(message, response):
    # Split the message into chunks of 2000 characters or less
    message_chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]

    for chunk in message_chunks:
        await message.channel.send(chunk)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('/start'):
        response = dungeon.start()
        await send_message(message, response)

    elif message.content.startswith('/stop'):
        response = dungeon.stop()
        await send_message(message, response)

    elif message.content.startswith('/continue'):
        response = dungeon.continue_adventure()
        await send_message(message, response)

    elif message.content.startswith('/stats'):
        exp, health = player.get_stats()
        response = f"EXP: {exp}\nHealth: {health}"
        await send_message(message, response)

    elif message.content.startswith('/flee'):
        response = dungeon.flee()
        await send_message(message, response)

    elif message.content.startswith('/inventory'):
        inventory = player.view_inventory()  # This will now display items categorically
        response = f"Your Inventory:\n{inventory}"
        await send_message(message, response)


# Starting the Discord client
try:
    token = os.getenv("TOKEN")
    if not token:
        raise Exception("Please add your token to the environment variables.")
    client.run(token)
except discord.HTTPException as e:
    print(f"An error occurred: {e}")

# Assuming keep_awake() is defined elsewhere, and it's necessary for your use case
# keep_awake()
