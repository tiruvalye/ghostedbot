import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import os
import json
import config
from datetime import datetime
import pytz  # Ensure timestamps are in UTC


class CheckActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "/root/ghosted-bot/data/activity"
        self.osrs_file = os.path.join(self.data_dir, "osrs-inactivity-list.json")
        self.rs3_file = os.path.join(self.data_dir, "rs3-inactivity-list.json")

    def load_data(self, file_path):
        """Loads data from a JSON file."""
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return []

    async def log_command_usage(self, interaction, command_name):
        """Logs command usage to the logs channel."""
        logs_channel = config.CHANNEL_IDS.get("logs")
        if logs_channel:
            channel = interaction.guild.get_channel(logs_channel)
            if channel:
                timestamp = int(datetime.now().timestamp())
                await channel.send(
                    f"<t:{timestamp}:F> <@{interaction.user.id}> used command `/{command_name}` in channel <#{interaction.channel.id}>."
                )

    def convert_to_timestamp(self, date_string):
        """Converts the Date & Time string into a Unix timestamp format for Discord."""
        if isinstance(date_string, int):  
            # If it's already a Unix timestamp, return it directly
            return date_string  

        try:
            # Ensure the input is a string before parsing
            if not isinstance(date_string, str):
                return None  

            # Attempt to parse the datetime string
            dt_object = datetime.strptime(date_string, "%Y-%m-%d %I:%M %p %Z")
            dt_object = dt_object.replace(tzinfo=pytz.UTC)  # Ensure UTC timezone
            return int(dt_object.timestamp())  # Convert to Unix timestamp
        except ValueError:
            return None  # Return None if parsing fails

    @nextcord.slash_command(name="checkactivity", description="View the list of inactive clan members.")
    async def checkactivity(
        self,
        interaction: Interaction,
        game: str = SlashOption(
            name="game",
            description="Select the game version",
            choices={"Both": "both", "Old School RuneScape": "osrs", "RuneScape 3": "rs3"},
            required=True,
        ),
    ):
        await interaction.response.defer()  # Prevents command timeout

        # Restrict command usage to 'controlpanel' channel
        controlpanel_channel = config.CHANNEL_IDS.get("controlpanel")
        if interaction.channel_id != controlpanel_channel:
            await interaction.followup.send(
                f"This command can only be used in <#{controlpanel_channel}>.",
                ephemeral=True
            )
            return

        # Restrict command to specific roles
        authorized_roles = {config.ROLE_IDS["osrsbotmod"], config.ROLE_IDS["rs3botmod"]}
        if not any(role.id in authorized_roles for role in interaction.user.roles):
            await interaction.followup.send(
                "You do not have permission to use this command.",
                ephemeral=True
            )
            return

        # Load data based on selected game
        osrs_data = self.load_data(self.osrs_file) if game in ["osrs", "both"] else []
        rs3_data = self.load_data(self.rs3_file) if game in ["rs3", "both"] else []

        # Embed storage
        embeds = []

        if osrs_data:
            osrs_embed = nextcord.Embed(
                title="📜 Old School RuneScape Inactivity List",
                color=0xFFD700  # Gold color for OSRS
            )
            for entry in osrs_data:
                timestamp = self.convert_to_timestamp(entry.get("Date & Time", ""))
                formatted_time = f"<t:{timestamp}:F>" if timestamp else entry["Date & Time"]

                osrs_embed.add_field(
                    name=f"👤 {entry['Display Name']}",
                    value=f"🆔 **Discord ID**: `{entry['Discord User ID']}`\n📅 **Date & Time**: {formatted_time}",
                    inline=False
                )
            embeds.append(osrs_embed)

        if rs3_data:
            rs3_embed = nextcord.Embed(
                title="📜 RuneScape 3 Inactivity List",
                color=0x1E90FF  # Blue color for RS3
            )
            for entry in rs3_data:
                timestamp = self.convert_to_timestamp(entry.get("Date & Time", ""))
                formatted_time = f"<t:{timestamp}:F>" if timestamp else entry["Date & Time"]

                rs3_embed.add_field(
                    name=f"👤 {entry['Display Name']}",
                    value=f"🆔 **Discord ID**: `{entry['Discord User ID']}`\n📅 **Date & Time**: {formatted_time}",
                    inline=False
                )
            embeds.append(rs3_embed)

        # If no inactive members exist, show a yellow embed
        if not osrs_data and not rs3_data:
            no_inactive_embed = nextcord.Embed(
                title="⚠ No Inactive Members",
                description="There are currently no inactive members in the clan.",
                color=0xFFFF00  # Yellow color for warning
            )
            embeds.append(no_inactive_embed)

        # Send all collected embeds
        for embed in embeds:
            await interaction.followup.send(embed=embed)

        # Log command usage
        await self.log_command_usage(interaction, "checkactivity")


def setup(bot):
    bot.add_cog(CheckActivity(bot))