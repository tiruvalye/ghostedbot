import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import os
import json
import config
from datetime import datetime
import traceback
import requests

class Expenditure(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_dir = "/root/ghosted-bot/data/donations"
        self.expenditures_file = os.path.join(self.data_dir, "expenditures.json")

        # Ensure data directory exists
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

        # Ensure expenditures file exists
        if not os.path.exists(self.expenditures_file):
            with open(self.expenditures_file, "w") as f:
                json.dump([], f)

    def load_expenditures(self):
        """Loads the expenditures from the JSON file."""
        if os.path.exists(self.expenditures_file):
            with open(self.expenditures_file, "r") as f:
                return json.load(f)
        return []

    def save_expenditures(self, data):
        """Saves only the most recent 5 expenditures."""
        with open(self.expenditures_file, "w") as f:
            json.dump(data[:5], f, indent=4)

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

    @nextcord.slash_command(name="spend", description="Log an expenditure for Old School RuneScape or RuneScape 3.")
    async def spend(
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
        reason: str = SlashOption(
            name="reason",
            description="Enter the reason for the expenditure.",
            required=True,
        ),
    ):
        """Slash command to log an expenditure."""
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

        # Save the expenditure to JSON
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        timestamp = int(datetime.strptime(date, "%Y-%m-%d %H:%M:%S").timestamp())

        expenditures = self.load_expenditures()
        expenditures.insert(0, {  # Insert new entry at the beginning
            "date": date,
            "timestamp": timestamp,
            "amount": amount_full,
            "formatted_amount": self.format_amount(amount_full),
            "game": "Old School RuneScape" if game == "osrs" else "RuneScape 3",
            "reason": reason
        })
        self.save_expenditures(expenditures)  # Save only the latest 5

        # Create confirmation embed
        embed = nextcord.Embed(
            title="📜 Clan Expenditure Logged",
            description=f"Successfully logged expenditure for {game.upper()}!",
            color=0xFFA500
        )
        embed.add_field(name="💰 Amount", value=f"{self.format_amount(amount_full)} GP", inline=True)
        embed.add_field(name="📖 Reason", value=reason, inline=True)
        embed.add_field(name="🕒 Date", value=f"<t:{timestamp}:F>", inline=False)
        embed.set_footer(text=f"Logged by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

        # Log command usage
        await self.log_command_usage(interaction, "spend")

        # Update the expenditure post
        await self.update_expenditure_post(interaction, expenditures)

    async def update_expenditure_post(self, interaction, expenditures):
        """Updates the expenditure post via webhook."""
        try:
            webhook_url = config.WEBHOOK_URLS["donations"]
            message_id = config.COPY_MESSAGE["expenditurespost"].split("/")[-1]

            if not webhook_url or not message_id:
                raise ValueError("Webhook URL or Message ID is missing!")

            embeds = {
                "content": None,
                "embeds": [
                    {
                        "title": "Clan Expenditures",
                        "description": "Here are the 5 most recent clan expenditures from both OSRS and RS3.",
                        "color": 5814783,
                        "fields": []
                    }
                ]
            }

            for i, exp in enumerate(expenditures[:5]):
                field = {
                    "name": f"{i+1}. {exp['reason']}",
                    "value": f"🕹 **Game**: {exp['game']}\n💰 **Amount**: {exp['formatted_amount']} GP\n🕒 **Date**: <t:{exp['timestamp']}:F>",
                    "inline": False
                }
                embeds["embeds"][0]["fields"].append(field)

            headers = {"Content-Type": "application/json"}

            response = requests.patch(
                f"{webhook_url}/messages/{message_id}",
                json=embeds,
                headers=headers
            )

            if response.status_code not in [200, 204]:
                raise Exception(f"Failed to update webhook message: {response.status_code} {response.text}")

        except Exception as e:
            error_traceback = traceback.format_exc()
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS["debugging"])
            if debugging_channel:
                await debugging_channel.send(f"Exception while updating expenditure post: ```{error_traceback}```")

def setup(bot):
    bot.add_cog(Expenditure(bot))