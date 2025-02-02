import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import os
import json
import config
import requests
import traceback
from datetime import datetime

class Donate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "/root/ghosted-bot/data/donations/leaderboard"

        # Ensure the leaderboard directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def load_donator_data(self, user_id):
        """Loads a donator's data from their JSON file."""
        file_path = os.path.join(self.data_dir, f"{user_id}.json")
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                return json.load(f)
        return {"rs3_donated": 0, "osrs_donated": 0}

    def save_donator_data(self, user_id, data):
        """Saves a donator's data to their JSON file."""
        file_path = os.path.join(self.data_dir, f"{user_id}.json")
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)

    def get_leaderboard(self):
        """Retrieves and sorts the top donators based on total donations."""
        leaderboard_data = []
        for file in os.listdir(self.data_dir):
            if file.endswith(".json"):
                file_path = os.path.join(self.data_dir, file)
                with open(file_path, "r") as f:
                    try:
                        data = json.load(f)
                        total_donated = data.get("rs3_donated", 0) + data.get("osrs_donated", 0)
                        leaderboard_data.append({
                            "id": file.replace(".json", ""),
                            "total_donated": total_donated,
                            "rs3_donated": data.get("rs3_donated", 0),
                            "osrs_donated": data.get("osrs_donated", 0)
                        })
                    except json.JSONDecodeError:
                        continue

        return sorted(leaderboard_data, key=lambda x: x["total_donated"], reverse=True)[:10]

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

    def convert_amount(self, amount_str):
        """Converts an amount string (e.g., 5m, 10k, 1b) into an integer."""
        amount_str = amount_str.lower()
        if amount_str.endswith('k'):
            return int(float(amount_str[:-1]) * 1_000)
        elif amount_str.endswith('m'):
            return int(float(amount_str[:-1]) * 1_000_000)
        elif amount_str.endswith('b'):
            return int(float(amount_str[:-1]) * 1_000_000_000)
        else:
            return int(amount_str)

    @nextcord.slash_command(name="donate", description="Log a new donation for Old School RuneScape or RuneScape 3.")
    async def donate(
        self,
        interaction: Interaction,
        game: str = SlashOption(
            name="game",
            description="Select the game version",
            choices={"Old School RuneScape": "osrs", "RuneScape 3": "rs3"},
            required=True,
        ),
        donator_id: str = SlashOption(
            name="donator_id",
            description="Enter the Discord User ID of the player who donated.",
            required=True,
        ),
        amount: str = SlashOption(
            name="amount",
            description="Enter the amount (use K, M, or B for thousand, million, billion).",
            required=True,
        ),
    ):
        """Slash command to log a donation."""
        try:
            await interaction.response.defer()  # Prevent timeout while processing

            # Restrict command usage
            donationscp_channel = config.CHANNEL_IDS.get("donationscp")
            if interaction.channel_id != donationscp_channel:
                await interaction.followup.send(
                    f"This command can only be used in <#{donationscp_channel}>.",
                    ephemeral=True
                )
                return

            authorized_roles = {config.ROLE_IDS["donationmod"]}
            if not any(role.id in authorized_roles for role in interaction.user.roles):
                await interaction.followup.send(
                    "You do not have permission to use this command.",
                    ephemeral=True
                )
                return

            # Convert amount
            try:
                amount_full = self.convert_amount(amount)
            except ValueError:
                await interaction.followup.send("Invalid amount format. Please enter a valid number.", ephemeral=True)
                return

            # Load and update donator data
            donator_data = self.load_donator_data(donator_id)
            if game == "rs3":
                donator_data["rs3_donated"] += amount_full
            else:
                donator_data["osrs_donated"] += amount_full
            self.save_donator_data(donator_id, donator_data)

            # Create an embed confirmation
            embed = nextcord.Embed(
                title="🏆 Donation Recorded",
                description=f"Successfully logged a donation for <@{donator_id}>!",
                color=0x8A2BE2  # Purple
            )
            embed.add_field(name="🎮 Game", value="Old School RuneScape" if game == "osrs" else "RuneScape 3", inline=True)
            embed.add_field(name="💰 Amount", value=f"{amount_full:,} GP", inline=True)
            embed.add_field(name="📅 Date", value=f"<t:{int(datetime.now().timestamp())}:F>", inline=False)
            embed.set_footer(text=f"Logged by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

            await interaction.followup.send(embed=embed)

            # Log command usage
            await self.log_command_usage(interaction, "donate")

            # Update leaderboard post
            await self.update_donations_post(interaction)

        except Exception as e:
            error_traceback = traceback.format_exc()
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS['debugging'])
            if debugging_channel:
                await debugging_channel.send(f"Exception while processing /donate: ```{error_traceback}```")

    async def update_donations_post(self, interaction):
        """Updates the donation leaderboard post."""
        try:
            leaderboard = self.get_leaderboard()
            embeds = {
                "content": None,
                "embeds": [
                    {
                        "title": "🏆 Donation Leaderboard",
                        "description": "Top 10 donators for the clan from both OSRS and RS3.",
                        "color": 0x8A2BE2,
                        "fields": []
                    }
                ],
                "attachments": []
            }

            place_format = ["1st Place", "2nd Place", "3rd Place", "4th Place", "5th Place",
                            "6th Place", "7th Place", "8th Place", "9th Place", "10th Place"]

            for i, donor in enumerate(leaderboard[:10]):
                position = place_format[i]
                field = {
                    "name": position,
                    "value": f"**Clan Member:** <@{donor['id']}>\n"
                             f"💰 **Total Donated:** {donor['total_donated']:,} GP",
                    "inline": False
                }
                embeds['embeds'][0]['fields'].append(field)

            message_id = config.COPY_MESSAGE['leaderboardpost'].split('/')[-1]
            response = requests.patch(f"{config.WEBHOOK_URLS['donations']}/messages/{message_id}", json=embeds)
            response.raise_for_status()

        except Exception as e:
            error_traceback = traceback.format_exc()
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS['debugging'])
            if debugging_channel:
                await debugging_channel.send(f"Exception while updating donation leaderboard: ```{error_traceback}```")

def setup(bot):
    bot.add_cog(Donate(bot))