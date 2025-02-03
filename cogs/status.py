import nextcord
from nextcord.ext import commands
from nextcord import Interaction
import config
import psutil
import time

class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()  # Bot start time for uptime calculation

    def get_uptime(self):
        """Calculate bot uptime in HH:MM:SS format."""
        uptime_seconds = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours}h {minutes}m {seconds}s"

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

    @nextcord.slash_command(name="status", description="Check the bot's system status.")
    async def status(self, interaction: Interaction):
        """Displays the bot's uptime, memory usage, and loaded cogs."""
        
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

        # Get system stats
        memory_usage = psutil.virtual_memory().percent  # RAM Usage
        cpu_usage = psutil.cpu_percent(interval=1)  # CPU Usage
        uptime = self.get_uptime()  # Bot uptime
        loaded_cogs = ", ".join(self.bot.cogs.keys())  # List of loaded cogs

        # Embed message
        embed = nextcord.Embed(
            title="📋 Ghosted Bot Status",
            description="Here's the current system status for the bot.",
            color=0x3498DB  # Blue color
        )
        embed.add_field(name="🕒 Uptime", value=f"`{uptime}`", inline=True)
        embed.add_field(name="💾 RAM Usage", value=f"`{memory_usage}%`", inline=True)
        embed.add_field(name="⚡ CPU Usage", value=f"`{cpu_usage}%`", inline=True)
        embed.add_field(name="🧩 Loaded Cogs", value=f"`{loaded_cogs}`", inline=False)
        embed.set_footer(text="Ghosted Bot | System Metrics")

        await interaction.response.send_message(embed=embed)

        # Log command usage
        await self.log_command_usage(interaction, "status")

def setup(bot):
    bot.add_cog(Status(bot))