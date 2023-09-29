import os
import discord
from dotenv import load_dotenv, find_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

cred = credentials.Certificate('../firebase.json')
firebase_admin.initialize_app(cred)

# Ensure you're using the asynchronous Firestore client
db = firestore.client()

from player import Player  # Make sure to import the Player class correctly
from dungeon import Dungeon  # Make sure to import the Dungeon class correctly

load_dotenv(find_dotenv())
TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

    
async def send_message(message, response):
    # Append user ID to the response for debugging
    response = f"User ID {message.author.id}: {response}"
    message_chunks = [response[i:i + 2000] for i in range(0, len(response), 2000)]
    for chunk in message_chunks:
        await message.channel.send(chunk)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    user_id = message.author.id
    player = Player(message.author.name, db)

    if message.content.startswith('/start'):   
        player = Player(message.author.name, db)
        dungeon = Dungeon(player, db)
        response = dungeon.start()
        player.save_player()  # Save player data to the database
        dungeon.save_dungeon()  # Save dungeon data to the database
        await send_message(message, response)

    elif message.content.startswith('/stop'):
        dungeon = Dungeon.load_dungeon(player, db)  # Load dungeon data from the database
        if not dungeon:
            await send_message(message, "Prepare for the adventure!")
            return
        response = dungeon.stop()
        await send_message(message, response)
        dungeon.save_dungeon()  # Save updated dungeon data to the database

    elif message.content.startswith('/continue'):
        dungeon = Dungeon.load_dungeon(player, db)  # Load dungeon data from the database
        if not dungeon:
                await send_message(message, "No ongoing dungeon adventure found!")
                return
        response = dungeon.continue_adventure()
        await send_message(message, response)
        dungeon.save_dungeon()  # Save updated dungeon data to the database
        player.save_player()  # Save updated player data to the database

    elif message.content.startswith('/stats'):
        if player:
            player_data = await player.get_stats_from_db()  # Retrieving player data from the DB
            if player_data:
                player_stats = '\n'.join([f"{key}: {value}" for key, value in player_data.items()])
                await send_message(message, player_stats)
            else:
                await send_message(message, "You need to start a dungeon adventure first!")
        else:
            await send_message(message, "You need to start a dungeon adventure first!")

    elif message.content.startswith('/flee'):
        dungeon = Dungeon.load_dungeon(player, db)  # Load dungeon data from the database
        if not dungeon:
            await send_message(message, "No ongoing dungeon adventure found!")
            return
        response = dungeon.flee()
        await send_message(message, response)
        dungeon.save_dungeon()  # Save updated dungeon data to the database
        player.save_player()  # Save updated player data to the database

    elif message.content.startswith('/inventory'):
        if not player:
            await send_message(message, "You need to start a dungeon adventure first!")
            return
        inventory = player.view_inventory()
        response = f"Your Inventory:\n{inventory}"
        await send_message(message, response)
try:
    if not TOKEN:
        raise Exception("Please add your token to the environment variables.")
    client.run(TOKEN)
except discord.HTTPException as e:
    print(f"An error occurred: {e}")
