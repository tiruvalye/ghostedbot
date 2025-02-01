import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import os
import json
import config
from datetime import datetime

class SetActivity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "/root/ghosted-bot/data/activity"
        self.osrs_file = os.path.join(self.data_dir, "osrs-inactivity-list.json")
        self.rs3_file = os.path.join(self.data_dir, "rs3-inactivity-list.json")

        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Ensure the files exist
        for file in [self.osrs_file, self.rs3_file]:
            if not os.path.exists(file):
                with open(file, "w") as f:
                    json.dump([], f)

    def load_data(self, file_path):
        """Loads data from a JSON file."""
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return []

    def save_data(self, file_path, data):
        """Saves data to a JSON file."""
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

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

    @nextcord.slash_command(name="setactivity", description="Manually set a clan member's activity status.")
    async def setactivity(
        self,
        interaction: Interaction,
        clanmember_id: str = SlashOption(
            name="clanmember_id",
            description="Enter the Discord ID of the clan member.",
            required=True,
        ),
        status: str = SlashOption(
            name="status",
            description="Select the type of activity report",
            choices={"Active": "active", "Inactive": "inactive"},
            required=True,
        ),
        game: str = SlashOption(
            name="game",
            description="Select the game version",
            choices={"Both": "both", "Old School RuneScape": "osrs", "RuneScape 3": "rs3"},
            required=True,
        ),
    ):
        # Restrict command usage to 'controlpanel' channel
        controlpanel_channel = config.CHANNEL_IDS.get("controlpanel")
        if interaction.channel_id != controlpanel_channel:
            await interaction.response.send_message(
                f"This command can only be used in <#{controlpanel_channel}>.",
                ephemeral=True
            )
            return

        # Restrict command to specific roles
        authorized_roles = {config.ROLE_IDS["osrsbotmod"], config.ROLE_IDS["rs3botmod"]}
        if not any(role.id in authorized_roles for role in interaction.user.roles):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
            return

        # Try fetching the user's actual display name
        member = interaction.guild.get_member(int(clanmember_id))
        display_name = member.display_name if member else f"Unknown ({clanmember_id})"

        file_paths = []
        if game in ["osrs", "both"]:
            file_paths.append(self.osrs_file)
        if game in ["rs3", "both"]:
            file_paths.append(self.rs3_file)

        affected_games = []
        for file_path in file_paths:
            data = self.load_data(file_path)

            if status == "inactive":
                if not any(entry["Discord User ID"] == clanmember_id for entry in data):
                    data.append({
                        "Display Name": display_name,  # Correctly store actual display name
                        "Discord User ID": clanmember_id,
                        "Date & Time": datetime.now().strftime("%Y-%m-%d %I:%M %p UTC")
                    })
                    self.save_data(file_path, data)
                    affected_games.append("Old School RuneScape" if "osrs" in file_path else "RuneScape 3")

            elif status == "active":
                new_data = [entry for entry in data if entry["Discord User ID"] != clanmember_id]
                if len(new_data) != len(data):
                    self.save_data(file_path, new_data)
                    affected_games.append("Old School RuneScape" if "osrs" in file_path else "RuneScape 3")

        # Determine the message
        if not affected_games:
            await interaction.response.send_message(
                f"**{status.capitalize()} status** for <@{clanmember_id}> was **unchanged** (already {status}).",
                ephemeral=True
            )
            return

        if len(affected_games) == 2:
            message = f"Successfully marked **{display_name}** as {status} for Old School RuneScape and RuneScape 3."
        else:
            message = f"Successfully marked **{display_name}** as {status} for {affected_games[0]}."

        # Create an embed for the response
        embed = nextcord.Embed(
            title="📌 Activity Status Updated",
            description=message,
            color=0x00FF00 if status == "active" else 0xFF0000
        )

        await interaction.response.send_message(embed=embed)

        # Log command usage
        await self.log_command_usage(interaction, "setactivity")

def setup(bot):
    bot.add_cog(SetActivity(bot))