import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import os
import json
import config
import requests
import traceback
from datetime import datetime

class Ledger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "/root/ghosted-bot/data/donations"
        self.ledger_file = os.path.join(self.data_dir, "ledger.json")

        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Ensure ledger file exists with default values
        if not os.path.exists(self.ledger_file):
            with open(self.ledger_file, "w") as f:
                json.dump({"rs3": 0, "osrs": 0}, f, indent=4)

    def load_ledger(self):
        """Loads ledger data from the JSON file."""
        with open(self.ledger_file, "r") as f:
            return json.load(f)

    def save_ledger(self, data):
        """Saves ledger data to the JSON file."""
        with open(self.ledger_file, "w") as f:
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

    def format_amount(self, amount):
        """Formats an integer amount into shorthand (e.g., 5m, 10k, 1b)."""
        if amount >= 1_000_000_000:
            return f"{amount / 1_000_000_000:.2f}b"
        elif amount >= 1_000_000:
            return f"{amount / 1_000_000:.2f}m"
        elif amount >= 1_000:
            return f"{amount / 1_000:.2f}k"
        return str(amount)

    @nextcord.slash_command(name="ledger", description="Set the clan coffer balance for Old School RuneScape or RuneScape 3.")
    async def ledger(
        self,
        interaction: Interaction,
        game: str = SlashOption(
            name="game",
            description="Select the game version",
            choices={"Old School RuneScape": "osrs", "RuneScape 3": "rs3"},
            required=True,
        ),
        amount: str = SlashOption(
            name="amount",
            description="Enter the amount (use K, M, or B for thousand, million, billion).",
            required=True,
        ),
    ):
        """Slash command to update the clan ledger."""
        # Restrict command to donationscp channel
        donationscp_channel = config.CHANNEL_IDS.get("donationscp")
        if interaction.channel_id != donationscp_channel:
            await interaction.response.send_message(
                f"This command can only be used in <#{donationscp_channel}>.",
                ephemeral=True
            )
            return

        # Restrict command to donationmod role
        authorized_roles = {config.ROLE_IDS["donationmod"]}
        if not any(role.id in authorized_roles for role in interaction.user.roles):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
            return

        # Convert the amount
        try:
            amount_full = self.convert_amount(amount)
        except ValueError:
            await interaction.response.send_message("Invalid amount format. Please enter a valid number.", ephemeral=True)
            return

        try:
            # Load ledger data
            ledger_data = self.load_ledger()

            # Update the ledger with the new value (REPLACE instead of ADD)
            ledger_data[game] = amount_full
            self.save_ledger(ledger_data)

            # Format amounts
            formatted_rs3 = self.format_amount(ledger_data["rs3"])
            formatted_osrs = self.format_amount(ledger_data["osrs"])

            # Update the ledger post
            await self.update_ledger_post(interaction, formatted_rs3, formatted_osrs)

            # Create an embed response
            embed = nextcord.Embed(
                title="📜 Clan Ledger Updated",
                description=f"The ledger for {game.upper()} has been updated successfully!",
                color=0x00FF00
            )
            embed.add_field(name="🏦 OSRS Ledger", value=f"{formatted_osrs} GP", inline=True)
            embed.add_field(name="🏦 RS3 Ledger", value=f"{formatted_rs3} GP", inline=True)
            embed.set_footer(text=f"Updated by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

            await interaction.response.send_message(embed=embed)

            # Log command usage
            await self.log_command_usage(interaction, "ledger")

        except Exception as e:
            error_traceback = traceback.format_exc()
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS['debugging'])
            if debugging_channel:
                await debugging_channel.send(f"Exception while updating ledger: ```{error_traceback}```")

    async def update_ledger_post(self, interaction, rs3_amount, osrs_amount):
        """Updates the ledger post via webhook."""
        try:
            webhook_message = {
                "content": "",
                "embeds": [
                    {
                        "title": "Clan Coffers",
                        "description": "Here are the current amounts of both clan banks.",
                        "color": 16753920,
                        "fields": [
                            {
                                "name": "Old School RuneScape",
                                "value": f"Amount: {osrs_amount} GP",
                                "inline": False
                            },
                            {
                                "name": "RuneScape 3",
                                "value": f"Amount: {rs3_amount} GP",
                                "inline": False
                            }
                        ],
                        "footer": {
                            "text": f"Updated by {interaction.user.display_name}",
                            "icon_url": str(interaction.user.display_avatar.url)
                        }
                    }
                ]
            }

            # Get the message ID from the ledger post URL
            message_id = config.COPY_MESSAGE['ledgerpost'].split('/')[-1]

            # Make the PATCH request to update the existing message
            response = requests.patch(
                f"{config.WEBHOOK_URLS['donations']}/messages/{message_id}",
                json=webhook_message
            )
            response.raise_for_status()

        except Exception as e:
            error_traceback = traceback.format_exc()
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS['debugging'])
            if debugging_channel:
                await debugging_channel.send(f"Exception while updating ledger post: ```{error_traceback}```")

def setup(bot):
    bot.add_cog(Ledger(bot))