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
            idx = 1
            for item in inventory:
                # Assuming the Treasure object has a __str__() method
                item_name = f"{idx}: {item.material} {item.treasure_type}" 
                item_description = f"Origin: {item.origin}\nRarity: {item.rarity}\nValue: {item.value}"  
                        
                embed.add_field(name=f"Item: {item_name}", value=f"{item_description}", inline=False)
                idx += 1
        else:
            embed.description = "Your inventory is empty."
                
        await interaction.followup.send(embed=embed)
        
    except FileNotFoundError as e:
        print(f"File not found error: {e}")
    except KeyError as e:
        print(f"Key error: {e}")
    except ValueError as e:
        print(f"Value error: {e}")
    except Exception as e:  # Cat
        print(f"An error occurred: {e}")
            
        error_message = "An error occurred while displaying the inventory."
        error_message += f"\nError Details: {e}"  # Adding error details for more context
        await interaction.followup.send(content=error_message)

async def equip(interaction, db):
    try:
        await interaction.response.defer()
        player = await Player.load_player(interaction.user.name, db)
        if not player:
            error_message = "Player not found. Please start a new game."
            await interaction.followup.send(content=error_message)
            return

        if isinstance(interaction.data, dict) and 'options' in interaction.data:
            inventory_index = interaction.data['options'][0].get('value')  # Assuming that index of inventory item to equip is passed
        else:
            error_message = "Invalid command format. Please use the correct format to equip item."
            await interaction.followup.send(content=error_message)
            return

        equip_response = player.equip_armor(inventory_index)
        player.save_player(db)
        await interaction.followup.send(content=equip_response)
    except Exception as e:  # Catching exceptions generically should be the last resort
        print(f"An error occurred: {e}")
        error_message = "An error occurred while equipping the item. Please try again."
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

    @bot.tree.command(name="equip")
    async def equip_cmd(interaction):
        await equip(interaction, db=db)

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
