# README for the Text-Based Dungeon Adventure Game

## Overview
Welcome to the Text-Based Dungeon Adventure Game! Embark on an interactive and dynamic journey where you, the adventurer, navigate through mysterious and dangerous dungeons. Utilizing the power of advanced language models, every adventure is unique, offering new challenges and surprises.

## Features
- **Dynamic Storytelling:** Powered by GPT-based language models, experience a new adventure every time you enter the dungeon.
- **Player Progression:** Gain experience, improve your health, and collect doubloons as you navigate through the dungeon's various challenges.
- **Interactive Gameplay:** Make choices that affect your journey. Will you bravely continue or flee from the dangers that lurk in the darkness?
- **Inventory System:** Collect and manage an inventory of items that you find during your adventures.
- **Discord Integration:** Play directly on Discord! Interact with the game in real-time through a Discord bot.

## Files
- `dungeon.py`: Contains the Dungeon class for managing dungeon state and interactions.
- `main.py`: Handles the game's main logic, including user inputs and responses, and integrates with Discord for real-time interaction.
- `player.py`: Defines the Player class for managing player attributes like experience, health, and inventory.

## Setup
### Requirements
- Python 3.x
- A Discord account and server for bot integration
- Required Python packages: discord.py, langchain

### Installation
1. Clone this repository to your local machine.
2. Install the required Python packages. You can do this using pip:
   ```bash
   pip install discord.py
   pip install langchain

Set up a Discord bot and add it to your server. Note the bot token; you will need it to run the game.

#Running the Game
python main.py

Go to the Discord server and interact with the bot to start your adventure!
