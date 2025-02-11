import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed
import logging
import traceback
import config
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class ChangeJoinDateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rs3_data_dir = "/root/ghosted-bot/data/members/runescape3"

    @nextcord.slash_command(name="changejoindate", description="Change the join date for a RuneScape 3 member.")
    async def changejoindate(
        self,
        interaction: Interaction,
        member_name: str = SlashOption(
            name="member_name",
            description="Name of the clan member.",
            required=True,
        ),
        join_date: str = SlashOption(
            name="join_date",
            description="Join date in MM/DD/YYYY format.",
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

            # Validate date format
            try:
                datetime.strptime(join_date, "%m/%d/%Y")
            except ValueError:
                await interaction.response.send_message(
                    "Invalid date format. Please use MM/DD/YYYY.",
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

            # Update join date
            members_data[member_name]["Join Date"] = join_date

            with open(file_path, "w") as f:
                json.dump(members_data, f, indent=4)

            embed = Embed(
                title="Join Date Updated",
                description=f"Successfully updated join date for **{member_name}** to **{join_date}**.",
                color=nextcord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error executing changejoindate command: {error_traceback}")
            await interaction.response.send_message(
                f"<@{interaction.user.id}>, there was an error executing this command. Please check the debugging channel for more details.",
                ephemeral=True
            )
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS['debugging'])
            if debugging_channel:
                await debugging_channel.send(
                    f"Exception while executing `/changejoindate`: ```{error_traceback}```"
                )

def setup(bot):
    bot.add_cog(ChangeJoinDateCog(bot))