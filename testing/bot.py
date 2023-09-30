import os
import discord
from discord import app_commands
from dotenv import load_dotenv, find_dotenv
from tabulate import tabulate

#firebase must use this import structure
import firebase_admin
from firebase_admin import credentials, firestore
#must be before the import of firebase
# Initialize Firebase 
cred = credentials.Certificate('../firebase.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

from player import Player
from dungeon import Dungeon

from discord import Embed



# Load environment variables
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
        player = Player(interaction.user.name, db)  
        dungeon = Dungeon(player, db)
        player.dungeon = dungeon  
        response = dungeon.start()
        player.save_player()
        dungeon.save_dungeon()
        await interaction.followup.send(content=response)

    except Exception as e:
        print(f"An error occurred: {e}")  # Log the error for debugging
        error_message = "An error occurred while starting the dungeon. Please try again later."
        await interaction.followup.send(content=error_message)

async def continue_command(interaction, db):
    try:
        await interaction.response.defer()
        player = Player(interaction.user.name, db)  
        dungeon = Dungeon(player, db)
        player.dungeon = dungeon  
        response = dungeon.continue_adventure()
        player.save_player()
        dungeon.save_dungeon()
        await interaction.followup.send(content=response)
    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = "An error occurred while continuing the dungeon. Please try again later."
        await interaction.followup.send(content=error_message)

async def flee(interaction, db):
    try:
        await interaction.response.defer()
        player = Player(interaction.user.name, db)
        dungeon = Dungeon(player, db)
        player.dungeon = dungeon
        response = dungeon.flee()
        player.delete_treasures()
        player.save_player()
        dungeon.save_dungeon()
        await interaction.followup.send(content=response)
    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = "An error occurred while trying to flee the dungeon. Please try again later."
        await interaction.followup.send(content=error_message)


async def inventory(interaction, db):
    try:
        await interaction.response.defer()
        player = Player(interaction.user.name, db)  
        inventory = await player.get_inventory()
        embed = Embed(title="Your Inventory", color=0x00ff00)

        if not inventory:
            embed.description = "Your inventory is empty."
        else:
            for item in inventory:
                item_name = item['type'].title()
                item_description = (
                    f"Material: {item['material']}\n"
                    f"Adornment: {item['adornment']}\n"
                    f"Power: {item['power']}\n"
                    f"Era: {item['era']}"
                )
                embed.add_field(name=item_name, value=item_description, inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        print(f"An error occurred: {e}")
        error_message = "An error occurred while retrieving the inventory. Please try again later."
        await interaction.followup.send(content=error_message)


def main():
    db = firestore.client()
    intents = discord.Intents.default()
    bot = DungeonBot(db, intents=intents)

    @bot.tree.command(name="start")
    async def start_cmd(interaction):
        """Start a dungeon adventure."""
        await start(interaction, db)

    @bot.tree.command(name="continue")
    async def continue_cmd(interaction):
        """Continue your dungeon adventure."""
        await continue_command(interaction, db)

    @bot.tree.command(name="flee")
    async def flee_cmd(interaction):
        """Flee the dungeon and lose all your treasures and doubloons."""
        await flee(interaction, db)

    @bot.tree.command(name="inventory")
    async def inventory_cmd(interaction):
        """View your inventory."""
        await inventory(interaction, db)

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
