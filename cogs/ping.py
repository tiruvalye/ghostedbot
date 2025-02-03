import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import config

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_command_usage(self, interaction, command_name):
        """Logs command usage to the logs channel."""
        logs_channel = config.CHANNEL_IDS.get("logs")
        if logs_channel:
            channel = interaction.guild.get_channel(logs_channel)
            if channel:
                await channel.send(
                    f"🛠 **Command Used:** `{command_name}`\n"
                    f"👤 **User:** <@{interaction.user.id}>\n"
                    f"📌 **Channel:** <#{interaction.channel.id}>\n"
                    f"⏳ **Time:** <t:{int(interaction.created_at.timestamp())}:F>"
                )

    @nextcord.slash_command(name="ping", description="Check the bot's response time.")
    async def ping(self, interaction: Interaction):
        """Returns the bot's latency in a stylish embed."""
        
        # Check if command is used in the correct channel
        if interaction.channel_id != config.CHANNEL_IDS["controlpanel"]:
            await interaction.response.send_message(
                f"This command can only be used in <#{config.CHANNEL_IDS['controlpanel']}>.",
                ephemeral=True
            )
            return

        # Check if user has Developer role
        developer_role_id = config.ROLE_IDS["developermod"]
        if not any(role.id == developer_role_id for role in interaction.user.roles):
            await interaction.response.send_message(
                "You do not have permission to use this command.",
                ephemeral=True
            )
            return

        # Calculate bot latency
        latency = round(self.bot.latency * 1000, 2)

        # Embed message
        embed = nextcord.Embed(
            title="📶 Bot Latency",
            description=f"🏓 Pong! The bot's latency is **{latency}ms**.",
            color=0x1ABC9C  # Teal color
        )
        embed.set_footer(text="Ghosted Bot | System Metrics")
        
        await interaction.response.send_message(embed=embed)

        # Log command usage
        await self.log_command_usage(interaction, "ping")

def setup(bot):
    bot.add_cog(Ping(bot))