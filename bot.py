import os
import discord
from discord import app_commands
from dotenv import load_dotenv, find_dotenv
from firebase_admin import initialize_app, credentials, firestore

from player import Player
from dungeon import Dungeon

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Initialise Firebase
cred = credentials.Certificate("firebase.json")  # Add the path to your Firebase service account key
default_app = initialize_app(cred)

MY_GUILD = discord.Object(id=1129568088472420372)  # replace with your guild id


class DungeonBot(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
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

        dungeon = Dungeon.load_dungeon(player, db)
        if not dungeon:
            dungeon = Dungeon(player, db)

        player.dungeon = dungeon  
        response = dungeon.start(db)
        player.save_player(db)
        dungeon.save_dungeon(db)  # Added the db argument
        await interaction.followup.send(content=response)
    
    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except KeyError as e:
        print(f"Key error: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except Exception as e:  # Catching other types of exceptions generically should be the last resort
    
        print(f"An error occurred: {e}")
        
        error_message = "An error occurred while starting the dungeon. Please try again later."
        error_message += f"\nError Details: {e}"  # Adding error details for more context
    
        await interaction.followup.send(content=error_message)


async def continue_command(interaction, db):
    try:
        await interaction.response.defer()
        player = await Player.load_player(interaction.user.name, db)
        if not player:
            error_message = "Player not found. Please start a new game."
            await interaction.followup.send(content=error_message)
            return

        dungeon = Dungeon.load_dungeon(player, db)
        if not dungeon:
            error_message = "Dungeon not found. Please start a new game."
            await interaction.followup.send(content=error_message)
            return

        player.dungeon = dungeon  
        response = dungeon.continue_adventure(db)
        player.save_player(db)
        dungeon.save_dungeon(db)
        await interaction.followup.send(content=response)
    
    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except KeyError as e:
        print(f"Key error: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except Exception as e:  # Catching other types of exceptions generically should be the last resort
    
        print(f"An error occurred: {e}")
        
        error_message = "An error occurred while continuing the dungeon. Please try again later."
        error_message += f"\nError Details: {e}"  # Adding error details for more context
    
        await interaction.followup.send(content=error_message)


async def inventory(interaction, db):
    try:
        await interaction.response.defer()
        player = await Player.load_player(interaction.user.name, db)
        inventory = await player.get_inventory(db)
        embed = discord.Embed(title="Your Inventory", color=0x00ff00)
            
        if inventory:
            for item in inventory:
                # Assuming the Treasure object has a __str__() method
                item_description = str(item)  

                    
                embed.add_field(name=f"{item.treasure_type}", value=f"{item_description}", inline=False)
        else:
            embed.description = "Your inventory is empty."
            
        await interaction.followup.send(embed=embed)
    
    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except KeyError as e:
        print(f"Key error: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except Exception as e:  # Catching other types of exceptions generically should be the last resort
    
        print(f"An error occurred while displaying the inventory: {e}")
        
        error_message = "An error occurred while retrieving your inventory."
        error_message += f"\nError Details: {e}"  # Adding error details for more context
        await interaction.followup.send(content=error_message)
    


def main():
    intents = discord.Intents.default()
    bot = DungeonBot(intents=intents)
    db = firestore.client()

    @bot.tree.command(name="start")
    async def start_cmd(interaction):
        await start(interaction, db=db)

    @bot.tree.command(name="continue")
    async def continue_cmd(interaction):
        await continue_command(interaction, db=db)

    @bot.tree.command(name="inventory")
    async def inventory_cmd(interaction):
        await inventory(interaction, db=db)

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
