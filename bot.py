import nextcord
from nextcord.ext import commands
import os
import config
import traceback
import asyncio
from datetime import datetime

# Initialize the bot with appropriate intents
intents = nextcord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.guild_messages = True
intents.members = True  # Enable members intent for fetching and caching members
bot = commands.Bot(command_prefix="!", intents=intents)

# Centralized logging function to handle both logs and debugging
async def log_message(channel_key, message):
    channel_id = config.CHANNEL_IDS.get(channel_key)
    print(f"[DEBUG] Attempting to log message to channel key '{channel_key}', ID: {channel_id}")
    
    if channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            print(f"[DEBUG] Found channel '{channel_key}' with ID: {channel_id}. Sending message...")
            try:
                await channel.send(message)
                print(f"[DEBUG] Successfully sent message to channel {channel_id}")
            except Exception as e:
                print(f"[ERROR] Failed to send message to channel ID {channel_id}. Exception: {e}")
        else:
            print(f"[ERROR] Channel with ID {channel_id} not found in the bot's current cache.")
    else:
        print(f"[ERROR] Channel key '{channel_key}' not found in CHANNEL_IDS configuration.")

# Log every command use in the logs channel
@bot.event
async def on_command(ctx):
    print("[DEBUG] on_command event triggered")
    timestamp = int(datetime.now().timestamp())
    # Creating the log message
    log_message_content = (
        f"<t:{timestamp}:F> <@{ctx.author.id}> issued command "
        f"{ctx.message.content} in <#{ctx.channel.id}>."
    )
    # Send the log message to the logs channel
    await log_message('logs', log_message_content)

# Error handler to log errors in the debugging channel
@bot.event
async def on_command_error(ctx, error):
    print("[DEBUG] on_command_error event triggered")
    timestamp = int(datetime.now().timestamp())

    # Formatting the traceback
    error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    formatted_traceback = f"<t:{timestamp}:F>\n```traceback\n{error_traceback}```"

    # Splitting the traceback if it exceeds Discord's character limit (2000 characters)
    for i in range(0, len(formatted_traceback), 2000):
        await log_message('debugging', formatted_traceback[i:i + 2000])

# Event to sync commands once the bot is ready
@bot.event
async def on_ready():
    print("[DEBUG] on_ready event triggered")
    try:
        # Preload all members for all guilds
        for guild in bot.guilds:
            await guild.fetch_members().flatten()
            print(f"[DEBUG] Fetched members for guild: {guild.name}")

        # Sync application commands globally
        await bot.sync_application_commands()
        print("[DEBUG] Successfully synced application commands globally")
    except Exception as e:
        error_traceback = traceback.format_exc()
        print(f"[ERROR] Failed to sync application commands: {error_traceback}")

# Add cogs explicitly including event cog and news cog
async def load_cogs():
    print("[DEBUG] Loading cogs")
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')  # No 'await' needed here
                print(f"[DEBUG] Loaded {filename}")
            except Exception as e:
                await log_message('debugging', f"Failed to load {filename}: {e}")
                print(f"[ERROR] Failed to load {filename}. Exception: {e}")

# Run the bot
if __name__ == "__main__":
    async def main():
        # Load cogs and start the bot
        await load_cogs()
        await bot.start(config.BOT_TOKEN)

    print("[DEBUG] Starting bot...")
    asyncio.run(main())