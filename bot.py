import os
import discord
from discord.ext import commands

from dotenv import load_dotenv, find_dotenv
from firebase_admin import initialize_app, credentials, firestore

from player import Player
from dungeon import Dungeon

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Initialise Firebase
cred = credentials.Certificate("firebase.json")  # Add the path to your Firebase service account key
default_app = initialize_app(cred)
db = firestore.client()

intents = discord.Intents.default()

class DungeonBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        print(f'We have logged in as {self.user}')

# Initialising bot
bot = DungeonBot(command_prefix="/", intents=intents)

@bot.command()
async def start(ctx):
    try:
        player = Player.load_player(ctx.user.name, db)
        if not player:
            player = Player(ctx.user.name)

        dungeon = Dungeon.load_dungeon(player, db)
        if not dungeon:
            dungeon = Dungeon(player, db)

        player.dungeon = dungeon
        response = dungeon.start()
        player.save_player(db)
        dungeon.save_dungeon(db)     # Added the db argument
        await ctx.send(content=response)
    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = "An error occurred while starting the dungeon. Please try again later."
        await ctx.send(content=error_message)

@bot.command()
async def continue_command(ctx):
    try:
        player = Player.load_player(ctx.user.name, db)
        dungeon = Dungeon.load_dungeon(player, db)
        player.dungeon = dungeon
        response = dungeon.continue_adventure()
        player.save_player(db)
        dungeon.save_dungeon(db)
        await ctx.send(content=response)
    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = "An error occurred while continuing the dungeon. Please try again later."
        await ctx.send(content=error_message)
        
@bot.command()
async def inventory(ctx):
    try:
        player = Player.load_player(ctx.message.author.name, db)
        inventory = player.get_inventory()
        embed = discord.Embed(title="Your Inventory", color=0x00ff00)
        if inventory:
            for category, items in inventory.items():
                for item in items:
                    embed.add_field(name=f"{category.title()}", value=f"{item}", inline=False)
        else:
            embed.description = "Your inventory is empty."
        
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = "An error occurred while retrieving the inventory. Please try again later."
        await ctx.send(content=error_message)

bot.run(TOKEN)