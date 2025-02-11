import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed
import logging
import traceback
import config
import os
import json
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class FetchCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rs3_data_dir = "/root/ghosted-bot/data/members/runescape3"
        self.discord_data_dir = "/root/ghosted-bot/data/members/discord"
        self.api_url = "http://services.runescape.com/m=clan-hiscores/members_lite.ws?clanName=Ghosted"

        # Ensure the data directories exist
        os.makedirs(self.rs3_data_dir, exist_ok=True)
        os.makedirs(self.discord_data_dir, exist_ok=True)

        # Role IDs
        self.discord_guest_role = 973795302752518235
        self.osrs_member_role = 1086485830018797650
        self.rs3_member_role = 973796251835432970

    @nextcord.slash_command(name="fetch", description="Fetch data for RuneScape 3 or Discord.")
    async def fetch(
        self,
        interaction: Interaction,
        game: str = SlashOption(
            name="game",
            description="Specify the game version to fetch data for.",
            choices={"RuneScape 3": "rs3", "Discord": "discord"},
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

                # Fetch RS3 clan data
                response = requests.get(self.api_url)
                if response.status_code != 200:
                    await interaction.response.send_message(
                        f"Failed to fetch data from RuneScape API. Status code: {response.status_code}",
                        ephemeral=True
                    )
                    return

                lines = response.text.strip().split('\n')[1:]  # Skip header
                members_data = {}
                file_path = os.path.join(self.rs3_data_dir, "rs3_memberlist.json")

                if os.path.exists(file_path):
                    with open(file_path, "r") as f:
                        members_data = json.load(f)

                current_members = {}
                for line in lines:
                    name, rank, xp, _ = line.split(",")
                    current_members[name] = {
                        "Clan Rank": rank,
                        "Total XP": int(xp),
                        "Join Date": members_data.get(name, {}).get("Join Date", "Unknown")
                    }

                # Remove members no longer in the clan
                removed_members = set(members_data.keys()) - set(current_members.keys())
                for member in removed_members:
                    del members_data[member]

                # Update members and add new ones
                members_data.update(current_members)

                with open(file_path, "w") as f:
                    json.dump(members_data, f, indent=4)

                confirmation_message = "The RuneScape 3 clan member list has been fetched and updated successfully."

            elif game == "discord":
                if config.ROLE_IDS['discordbotmod'] not in [role.id for role in user.roles]:
                    await interaction.response.send_message(
                        f"<@{user.id}> you do not have permission to use this command.",
                        ephemeral=True
                    )
                    return

                guild = interaction.guild
                discord_guests = []
                osrs_members = []
                rs3_members = []

                for member in guild.members:
                    roles = [role.id for role in member.roles]

                    # Discord Guests
                    if self.discord_guest_role in roles and not (
                        self.osrs_member_role in roles or self.rs3_member_role in roles
                    ):
                        discord_guests.append({
                            "DiscordID": member.id,
                            "Nickname": member.nick if member.nick else member.display_name
                        })

                    # OSRS Members
                    if self.osrs_member_role in roles:
                        osrs_members.append({
                            "DiscordID": member.id,
                            "Nickname": member.nick if member.nick else member.display_name
                        })

                    # RS3 Members
                    if self.rs3_member_role in roles:
                        rs3_members.append({
                            "DiscordID": member.id,
                            "Nickname": member.nick if member.nick else member.display_name
                        })

                # Save the data
                with open(os.path.join(self.discord_data_dir, "discord_guests.json"), "w") as f:
                    json.dump(discord_guests, f, indent=4)

                with open(os.path.join(self.discord_data_dir, "osrs_members.json"), "w") as f:
                    json.dump(osrs_members, f, indent=4)

                with open(os.path.join(self.discord_data_dir, "rs3_members.json"), "w") as f:
                    json.dump(rs3_members, f, indent=4)

                confirmation_message = "The Discord member lists have been fetched and updated successfully."

            # Logging command usage
            log_channel = self.bot.get_channel(config.CHANNEL_IDS['logs'])
            timestamp = int(datetime.utcnow().timestamp())
            log_message = f"<t:{timestamp}:F> <@{user.id}> used command `/fetch` in channel <#{interaction.channel.id}>."
            if log_channel:
                await log_channel.send(log_message)

            # Sending a confirmation embed
            embed = Embed(
                title="Fetch Command Successful",
                description=confirmation_message,
                color=nextcord.Color.green()
            )
            await interaction.response.send_message(embed=embed)

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error executing fetch command for {game}: {error_traceback}")
            await interaction.response.send_message(
                f"<@{interaction.user.id}>, there was an error executing this command. Please check the debugging channel for more details.",
                ephemeral=True
            )
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS['debugging'])
            if debugging_channel:
                await debugging_channel.send(
                    f"Exception while executing `/fetch {game}`: ```{error_traceback}```"
                )

def setup(bot):
    bot.add_cog(FetchCog(bot))