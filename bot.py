import os
import discord
from discord import app_commands
from dotenv import load_dotenv, find_dotenv
from tabulate import tabulate

import firebase_admin
from firebase_admin import credentials, firestore

from player import Player
from dungeon import Dungeon

from discord import Embed

load_dotenv(find_dotenv())
TOKEN = os.getenv("TOKEN")
MY_GUILD = discord.Object(id=1129568088472420372)  # replace with your guild id

class DungeonBot(discord.Client):
    def __init__(self, db, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.db = db
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self):
        await self.setup_hook()
        print(f'We have logged in as {self.user}')

async def start(interaction, db):
    try:
        await interaction.response.defer()
        player = await Player.load_player(interaction.user.name, db)
        if not player:
            player = Player(interaction.user.name, db)
        
        dungeon = await Dungeon.load_dungeon(player, db)
        if not dungeon:
            dungeon = Dungeon(player, db)

        player.dungeon = dungeon  
        response = dungeon.start()
        player.save_player()
        dungeon.save_dungeon()
        await interaction.followup.send(content=response)
    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = "An error occurred while starting the dungeon. Please try again later."
        await interaction.followup.send(content=error_message)

async def continue_command(interaction, db):
    try:
        await interaction.response.defer()
        player = await Player.load_player(interaction.user.name, db)  
        dungeon = await Dungeon.load_dungeon(player, db)
        player.dungeon = dungeon  
        response = dungeon.continue_adventure()
        player.save_player()
        dungeon.save_dungeon()
        await interaction.followup.send(content=response)
    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = "An error occurred while continuing the dungeon. Please try again later."
        await interaction.followup.send(content=error_message)

async def inventory(interaction, db):
    try:
        await interaction.response.defer()
        player = await Player.load_player(interaction.user.name, db)  
        inventory = await player.get_inventory()
        embed = Embed(title="Your Inventory", color=0x00ff00)
        if inventory:
            for category, items in inventory.items():
                for item in items:
                    embed.add_field(name=f"{category.title()}", value=f"{item}", inline=False)
        else:
            embed.description = "Your inventory is empty."
        
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = "An error occurred while retrieving the inventory. Please try again later."
        await interaction.followup.send(content=error_message)

def main():
    load_dotenv()
    db = firestore.client()
    intents = discord.Intents.default()
    bot = DungeonBot(db, intents=intents)

    @bot.tree.command(name="start")
    async def start_cmd(interaction):
        await start(interaction, db)

    @bot.tree.command(name="continue")
    async def continue_cmd(interaction):
        await continue_command(interaction, db)

    @bot.tree.command(name="inventory")
    async def inventory_cmd(interaction):
        await inventory(interaction, db)

    bot.run(TOKEN)

if __name__ == "__main__":
    main()