import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed
import logging
import traceback
import config
import os
import json

logger = logging.getLogger(__name__)

class CheckJoinDateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rs3_data_dir = "/root/ghosted-bot/data/members/runescape3"

    @nextcord.slash_command(name="checkjoindate", description="Check the join date for a RuneScape 3 member.")
    async def checkjoindate(
        self,
        interaction: Interaction,
        game: str = SlashOption(
            name="game",
            description="Specify the game version to check.",
            choices={"RuneScape 3": "rs3"},
            required=True,
        ),
        member_name: str = SlashOption(
            name="member_name",
            description="Name of the clan member.",
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

            if config.ROLE_IDS['rs3botmod'] not in [role.id for role in user.roles]:
                await interaction.response.send_message(
                    f"<@{user.id}> you do not have permission to use this command.",
                    ephemeral=True
                )
                return

            # Load RS3 member data
            file_path = os.path.join(self.rs3_data_dir, "rs3_memberlist.json")

            if not os.path.exists(file_path):
                await interaction.response.send_message(
                    "No RS3 member list found. Please run `/fetch game: RuneScape 3` first.",
                    ephemeral=True
                )
                return

            with open(file_path, "r") as f:
                members_data = json.load(f)

            if member_name not in members_data:
                await interaction.response.send_message(
                    f"Member `{member_name}` not found in the member list.",
                    ephemeral=True
                )
                return

            join_date = members_data[member_name].get("Join Date", "Unknown")

            embed = Embed(
                title="Join Date Check",
                description=f"**{member_name}**'s join date is **{join_date}**.",
                color=nextcord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error executing checkjoindate command: {error_traceback}")
            await interaction.response.send_message(
                f"<@{interaction.user.id}>, there was an error executing this command. Please check the debugging channel for more details.",
                ephemeral=True
            )
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS['debugging'])
            if debugging_channel:
                await debugging_channel.send(
                    f"Exception while executing `/checkjoindate`: ```{error_traceback}```"
                )

def setup(bot):
    bot.add_cog(CheckJoinDateCog(bot))