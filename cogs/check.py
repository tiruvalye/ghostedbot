import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed
import logging
import traceback
import config
import os
import json

logger = logging.getLogger(__name__)

class CheckCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rs3_data_dir = "/root/ghosted-bot/data/members/runescape3"
        self.osrs_data_dir = "/root/ghosted-bot/data/members/oldschoolrunescape"

    @nextcord.slash_command(name="check", description="Check members without join dates for RuneScape 3 or Old School RuneScape.")
    async def check(
        self,
        interaction: Interaction,
        game: str = SlashOption(
            name="game",
            description="Specify the game version to check.",
            choices={"RuneScape 3": "rs3", "Old School RuneScape": "osrs"},
            required=True,
        ),
    ):
        try:
            user = interaction.user

            # Restrict command to controlpanel channel
            controlpanel_channel_id = config.CHANNEL_IDS['controlpanel']
            if interaction.channel.id != controlpanel_channel_id:
                await interaction.response.send_message(
                    f"This command can only be used in the <#{controlpanel_channel_id}> channel.",
                    ephemeral=True
                )
                return

            if game == "rs3":
                if config.ROLE_IDS['rs3botmod'] not in [role.id for role in user.roles]:
                    await interaction.response.send_message(
                        f"<@{user.id}> you do not have permission to use this command.",
                        ephemeral=True
                    )
                    return

                file_path = os.path.join(self.rs3_data_dir, "rs3_memberlist.json")

            elif game == "osrs":
                if config.ROLE_IDS['osrsbotmod'] not in [role.id for role in user.roles]:
                    await interaction.response.send_message(
                        f"<@{user.id}> you do not have permission to use this command.",
                        ephemeral=True
                    )
                    return

                file_path = os.path.join(self.osrs_data_dir, "osrs_memberlist.json")

            if not os.path.exists(file_path):
                await interaction.response.send_message(
                    f"No {game.upper()} member list found. Please run `/fetch game: {game.upper()}` first.",
                    ephemeral=True
                )
                return

            with open(file_path, "r") as f:
                members_data = json.load(f)

            members_without_join_date = [name for name, data in members_data.items() if data.get("Join Date") == "Unknown"]

            # Chunking the message if needed
            chunk_size = 50  # Adjust based on Discord's message limits
            chunks = [members_without_join_date[i:i + chunk_size] for i in range(0, len(members_without_join_date), chunk_size)]

            for i, chunk in enumerate(chunks):
                embed = Embed(
                    title=f"Members without Join Dates (Part {i+1}/{len(chunks)})" if len(chunks) > 1 else "Members without Join Dates",
                    description=f"Total: {len(members_without_join_date)}\n" + "\n".join([f"{idx + 1}. {name}" for idx, name in enumerate(chunk, start=i*chunk_size + 1)]),
                    color=nextcord.Color.orange()
                )
                await interaction.channel.send(embed=embed)

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error executing check command for {game}: {error_traceback}")
            await interaction.response.send_message(
                f"<@{interaction.user.id}>, there was an error executing this command. Please check the debugging channel for more details.",
                ephemeral=True
            )
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS['debugging'])
            if debugging_channel:
                await debugging_channel.send(
                    f"Exception while executing `/check {game}`: ```{error_traceback}```"
                )

def setup(bot):
    bot.add_cog(CheckCog(bot))