import nextcord
from nextcord.ext import commands
from datetime import datetime
import config

class Sync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_command_usage(self, interaction):
        """Logs command usage in the logs channel."""
        logs_channel = config.CHANNEL_IDS.get("logs")
        if logs_channel:
            channel = interaction.guild.get_channel(logs_channel)
            if channel:
                timestamp = int(datetime.now().timestamp())
                await channel.send(
                    f"🔄 <t:{timestamp}:F> <@{interaction.user.id}> used `/sync` in <#{interaction.channel.id}>."
                )

    @nextcord.slash_command(name="sync", description="Force sync all application commands.")
    async def sync(self, interaction: nextcord.Interaction):
        """Force sync all application commands."""
        controlpanel_channel = config.CHANNEL_IDS.get("controlpanel")

        if interaction.channel_id != controlpanel_channel:
            await interaction.response.send_message(
                f"🚫 This command can only be used in <#{controlpanel_channel}>.",
                ephemeral=True
            )
            return

        authorized_role = config.ROLE_IDS.get("developermod")
        if authorized_role not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.",
                ephemeral=True
            )
            return

        try:
            await self.bot.sync_application_commands()
            embed = nextcord.Embed(
                title="✅ Commands Synced",
                description="All application commands have been successfully synchronized.",
                color=0x00FF00
            )
            embed.set_footer(text=f"Synced by {interaction.user.display_name}")

            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Log command usage
            await self.log_command_usage(interaction)

        except Exception as e:
            embed = nextcord.Embed(
                title="⚠️ Sync Failed",
                description=f"An error occurred while syncing commands:\n```{e}```",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Sync(bot))