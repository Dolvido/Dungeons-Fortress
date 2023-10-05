import os
import discord
from discord import app_commands
from dotenv import load_dotenv, find_dotenv
from firebase_admin import initialize_app, credentials, firestore
import traceback

from player import Player
from dungeon import Dungeon
from treasure import Treasure
from shop import Shop, Item

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
        player = await Player.load_from_db(interaction.user.name, db)
        if not player:
            player = Player(interaction.user.name, db)

        dungeon = Dungeon.load_dungeon(player, db)
        if dungeon is None:
            dungeon = Dungeon(player, db)
            dungeon.save_dungeon(db)

        player.dungeon = dungeon  
        response = dungeon.start(db)
        player.save_to_db(db)
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
        traceback.print_exc()
        await interaction.followup.send(content=error_message)


async def continue_command(interaction, db):
    try:
        await interaction.response.defer()
        player = await Player.load_from_db(interaction.user.name, db)
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
        player.save_to_db(db)
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
        traceback.print_exc()
        await interaction.followup.send(content=error_message)


async def inventory(interaction, db):
    await interaction.response.defer()
    player = await Player.load_from_db(interaction.user.name, db)
    if not player:
        error_message = "Player not found. Please start a new game."
        await interaction.followup.send(content=error_message)
        return

    embed = discord.Embed(title="Your Inventory", color=0x00ff00)
            
    if not player.inventory and not player.items:
        embed.description = "Your inventory is empty."
    else:
        if player.inventory:
            # add the treasures to the embed, add an integer field starting at 1 for each treasure
            embed.add_field(name="Treasures", value="\n".join([f"{idx+1}. {treasure}" for idx, treasure in enumerate(player.inventory)]), inline=False)
        if player.items:
            # add the items to the embed, add an integer field starting at 1 for each item
            embed.add_field(name="Items", value="\n".join([f"{idx+1}. {item}" for idx, item in enumerate(player.items)]), inline=False)

    await interaction.followup.send(embed=embed)

async def equip(interaction, db):
    """ equip command """
    try:
        await interaction.response.defer()
        player = await Player.load_from_db(interaction.user.name, db)
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
        player.save_to_db(db)
        await interaction.followup.send(content=equip_response)
    except Exception as e:  # Catching exceptions generically should be the last resort
        print(f"An error occurred: {e}")
        error_message = "An error occurred while equipping the item. Please try again."
        error_message += f"\nError Details: {e}"  # Adding error details for more context
        traceback.print_exc()
        await interaction.followup.send(content=error_message)

async def flee(interaction, db):
    try:
        await interaction.response.defer()
        player = await Player.load_from_db(interaction.user.name, db)
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
        fleeing_response = player.flee(db)
        player.save_to_db(db)
        dungeon.delete_dungeon(db)
        await interaction.followup.send(content=fleeing_response)
        
    except Exception as e: 
        print(f"An error occurred: {e}")
        error_message = "An error occurred while trying to flee. Please try again."
        error_message += f"\nError Details: {e}" 
        traceback.print_exc()
        await interaction.followup.send(content=error_message)

async def escape(interaction, db):
    try:
        await interaction.response.defer()
        player = await Player.load_from_db(interaction.user.name, db)
        if not player:
            error_message = "Player not found. Please start a new game."
            await interaction.followup.send(content=error_message)
            return

        dungeon = Dungeon.load_dungeon(player, db)
        if not dungeon:
            error_message = "Dungeon not found. Please start a new game."
            await interaction.followup.send(content=error_message)
            return
        
        # Check if the player is currently in an escape room
        if dungeon.room_type != "escape":
            error_message = "You can only use /escape while you're in an escape room."
            await interaction.followup.send(content=error_message)
            return

        player.dungeon = dungeon
        escaping_response = player.escape(db)
        player.save_to_db(db)
        player.restore_health(db)
        dungeon.delete_dungeon(db)
        await interaction.followup.send(content=escaping_response)
            
    except Exception as e: 
        print(f"An error occurred: {e}")
        error_message = "An error occurred while trying to escape. Please try again."
        error_message += f"\nError Details: {e}" 
        traceback.print_exc()
        await interaction.followup.send(content=error_message)

async def sell(interaction, item_index, db):
    try:
        item_index -= 1  # Adjust for 0-based indexing
        await interaction.response.defer()
                
        print(f"Debug: Item index: {item_index}")
                
        player = await Player.load_from_db(interaction.user.name, db)
                
        if not player:
            error_message = "Player not found. Please start a new game."
            await interaction.followup.send(content=error_message)
            return

        # Retrieve player's inventory from Firestore
        player_ref = db.collection('players').document(player.name)
        player_data = player_ref.get()
        if player_data.exists:
            player_data = player_data.to_dict()
            inventory = player_data.get('inventory', [])
            if item_index < 0 or item_index >= len(inventory):
                error_message = "Invalid item index. Please try again."
                await interaction.followup.send(content=error_message)
                return
            target_treasure_doc = inventory[item_index]

            target_treasure = Treasure.from_dict(target_treasure_doc)
                    
            # Add the item's value to player's doubloons
            player.doubloons += target_treasure.value

            #remove target treasure from player in Firestore
            inventory.pop(item_index)
            player_ref.update({"inventory": inventory, "doubloons": player.doubloons})

            sale_response = f"Sold {target_treasure.treasure_type} for {target_treasure.value} doubloons."
                
            # The sell operation is done, now save the player's updated state to the Firestore
            await interaction.followup.send(content=sale_response)
            
    except Exception as e:
        print(f"Debug: An error occurred while selling items: {e}")
        error_message = "An error occurred during the transaction. Please try again."
        error_message += f"\nError Details: {e}"
        await interaction.followup.send(content=error_message)

async def shop(interaction, db):
    await interaction.response.defer()
    shop = Shop()
    shop_display = shop.get_shop_display()
    await interaction.followup.send(content=shop_display)

async def buy(interaction, item_index, db):
    try:
        item_index -= 1  # Adjust for 0-based indexing
        await interaction.response.defer()

        print(f"Debug: Item index: {item_index}")

        player = await Player.load_from_db(interaction.user.name, db)  # Loading the player from the database

        if not player:
            error_message = "Player not found. Please start a new game."
            await interaction.followup.send(content=error_message)
            return

        # Initialise the Shop and buy the selected item
        shop = Shop()
            
        try:
            item_name = shop.buy(item_index, player, db)
            await interaction.followup.send(content=f"You bought the {item_name}!")
        except Exception as e:
            print(f"An error occurred while purchasing item: {e}")
            error_message = str(e)
            await interaction.followup.send(content=error_message)

    except Exception as e:
        print(f"An error occurred while purchasing item: {e}")
        error_message = "An error occurred during the transaction. Please try again."
        error_message += f"\nError Details: {e}"
        await interaction.followup.send(content=error_message)

async def stats(interaction, db):
    await interaction.response.defer()
    player = await Player.load_from_db(interaction.user.name, db)
    if not player:
        error_message = "Player not found. Please start a new game."
        await interaction.followup.send(content=error_message)
        return

    embed = discord.Embed(title="Your Stats", color=0x00ff00)
    embed.add_field(name="Health", value=f"{player.health}/{player.max_health}", inline=False)
    embed.add_field(name="Doubloons", value=f"{player.doubloons}", inline=False)
    await interaction.followup.send(embed=embed)

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

    @bot.tree.command(name="flee")
    async def flee_cmd(interaction):
        await flee(interaction, db=db)
    
    @bot.tree.command(name="escape")
    async def escape_cmd(interaction):
        await escape(interaction, db=db)

    @bot.tree.command(name="sell")
    async def sell_cmd(interaction, item_index: int):
        await sell(interaction, item_index, db=db)
    
    @bot.tree.command(name="shop")
    async def shop_cmd(interaction):
        await shop(interaction, db=db)

    @bot.tree.command(name="buy")
    async def buy_cmd(interaction, item_index: int):
        await buy(interaction, item_index, db=db)
    
    @bot.tree.command(name="stats")
    async def stats_cmd(interaction):
        await stats(interaction, db=db)

    bot.run(TOKEN)


if __name__ == "__main__":
    main()
