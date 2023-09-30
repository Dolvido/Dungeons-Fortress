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
cred = credentials.Certificate('./firebase.json')
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
    await interaction.response.defer()
    player = Player(interaction.user.name, db)  
    dungeon = Dungeon(player, db)  
    response = dungeon.start()
    player.save_player()
    dungeon.save_dungeon()
    await interaction.followup.send(content=response)  # Updated this line

async def continue_command(interaction, db):
    await interaction.response.defer()
    player = Player(interaction.user.name, db)  
    dungeon = Dungeon(player, db)  
    response = dungeon.continue_adventure()
    player.save_player()
    dungeon.save_dungeon()
    await interaction.followup.send(content=response)  # Updated this line

async def flee(interaction, db):
    await interaction.response.defer()
    player = Player(interaction.user.name, db)
    dungeon = Dungeon(player, db)
    response = dungeon.flee()  # Assuming the flee method returns a string response
    player.save_player()
    dungeon.save_dungeon()
    await interaction.followup.send(content=response)  # Send the response as a follow-up message


async def stop(interaction, db):
    await interaction.response.defer()
    player = Player(interaction.user.name, db)  
    response = "Your adventure has been stopped. You can resume anytime by typing `/dungeon continue`."
    player.delete_player()
    await interaction.followup.send(content=response)  # Updated this line

async def inventory(interaction, db):
    await interaction.response.defer()
    player = Player(interaction.user.name, db)  
    inventory = await player.get_inventory()

    # Create an embed
    embed = Embed(title="Your Inventory", color=0x00ff00)

    # If inventory is empty, send a specific message
    if not inventory:
        embed.description = "Your inventory is empty."
    else:
        # Otherwise, add each item as a field in the embed
        for item in inventory:
            item_name = item['type'].title()
            item_description = (
                f"Material: {item['material']}\n"
                f"Adornment: {item['adornment']}\n"
                f"Power: {item['power']}\n"
                f"Era: {item['era']}"
            )
            embed.add_field(name=item_name, value=item_description, inline=False)

    # Send the embed as a follow-up message
    await interaction.followup.send(embed=embed)



def main():
    db = firestore.client()
    intents = discord.Intents.default()
    bot = DungeonBot(db, intents=intents)

    @bot.tree.command(name="start")
    async def start_cmd(interaction):
        await start(interaction, db)

    @bot.tree.command(name="continue")
    async def continue_cmd(interaction):
        await continue_command(interaction, db)

    @bot.tree.command(name="stop")
    async def stop_cmd(interaction):
        await stop(interaction, db)

    @bot.tree.command(name="flee")
    async def flee_cmd(interaction):
        """Flee from the current dungeon. You will lose all your treasures and doubloons."""
        await flee(interaction, db)

    @bot.tree.command(name="inventory")
    async def inventory_cmd(interaction):
        await inventory(interaction, db)

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
