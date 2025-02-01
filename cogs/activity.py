import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import os
import json
from datetime import datetime
import config

class ActivityManagement(commands.Cog):
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

    @nextcord.slash_command(name='activity', description="Report your activity status for Old School RuneScape and/or RuneScape 3.")
    async def activity(
        self,
        interaction: Interaction,
        status: str = SlashOption(
            name="status",
            description="Select your activity status",
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
        user_id = str(interaction.user.id)
        display_name = interaction.user.display_name
        formatted_date = datetime.now().strftime("%Y-%m-%d %I:%M %p %Z")

        # Restrict command to the "inactives" channel
        inactives_channel = config.CHANNEL_IDS.get("inactives")
        if interaction.channel_id != inactives_channel:
            await interaction.response.send_message(
                f"This command can only be used in <#{inactives_channel}>.",
                ephemeral=True
            )
            return

        # Restrict command usage to specific roles
        authorized_roles = {config.ROLE_IDS["osrsmember"], config.ROLE_IDS["rs3member"]}
        if not any(role.id in authorized_roles for role in interaction.user.roles):
            await interaction.response.send_message(
                f"You aren't authorized to use this command, <@{user_id}>. "
                "If you are a clan member, please tag a Clan Admin for your specific game, or reach out to a Discord Mod.",
                ephemeral=True
            )
            return

        affected_files = []
        if game in ["osrs", "both"]:
            affected_files.append(self.osrs_file)
        if game in ["rs3", "both"]:
            affected_files.append(self.rs3_file)

        try:
            if status == "inactive":
                for file_path in affected_files:
                    data = self.load_data(file_path)

                    # Check if already inactive
                    if any(entry["Discord User ID"] == user_id for entry in data):
                        continue  # Skip adding again if already inactive

                    # Add new inactivity entry in the correct order
                    data.append({
                        "Display Name": display_name,
                        "Discord User ID": user_id,
                        "Date & Time": formatted_date
                    })

                    self.save_data(file_path, data)

                await interaction.response.send_message(
                    f"Thanks for your inactivity report, <@{user_id}>. "
                    "Please remember to report your return with the `/activity` command.",
                    ephemeral=True
                )

            elif status == "active":
                for file_path in affected_files:
                    data = self.load_data(file_path)
                    new_data = [entry for entry in data if entry["Discord User ID"] != user_id]

                    if len(new_data) == len(data):
                        continue  # Skip if no change

                    self.save_data(file_path, new_data)

                await interaction.response.send_message(
                    f"Welcome back, <@{user_id}>! You have been marked as active again.",
                    ephemeral=True
                )

            # Log command usage
            await self.log_command_usage(interaction, "activity")

        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

def setup(bot):
    bot.add_cog(ActivityManagement(bot))