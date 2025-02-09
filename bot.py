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

# Event to sync commands once the bot is ready
@bot.event
async def on_ready():
    print("[DEBUG] on_ready event triggered")
    try:
        for guild in bot.guilds:
            try:
                members = await guild.fetch_members().flatten()
                for member in members:
                    user_id = getattr(member, 'id', None)
                    if user_id is not None:
                        user_id = int(user_id)
                    else:
                        print(f"[WARNING] Missing user_id for member: {member}")
                print(f"[DEBUG] Fetched members for guild: {guild.name}")
            except Exception as e:
                print(f"[ERROR] Failed to fetch members for guild {guild.name}: {e}")

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
                bot.load_extension(f'cogs.{filename[:-3]}')
                print(f"[DEBUG] Loaded {filename}")
            except Exception as e:
                print(f"[ERROR] Failed to load {filename}. Exception: {e}")

# Run the bot
if __name__ == "__main__":
    async def main():
        await load_cogs()
        await bot.start(config.BOT_TOKEN)

    print("[DEBUG] Starting bot...")
    asyncio.run(main())