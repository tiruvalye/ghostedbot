import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
from datetime import datetime
import config
import traceback
import os

class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_cog_choices():
        """Fetch the list of all cogs dynamically."""
        cogs_directory = os.path.join(os.getcwd(), 'cogs')
        return [
            f.replace('.py', '')
            for f in os.listdir(cogs_directory)
            if os.path.isfile(os.path.join(cogs_directory, f)) and f.endswith('.py') and not f.startswith('__')
        ]

    async def log_command_usage(self, interaction, command_name, cog_name):
        """Logs command usage in the logs channel."""
        logs_channel = config.CHANNEL_IDS.get("logs")
        if logs_channel:
            channel = interaction.guild.get_channel(logs_channel)
            if channel:
                timestamp = int(datetime.now().timestamp())
                await channel.send(
                    f"📌 <t:{timestamp}:F> <@{interaction.user.id}> used `/{command_name} {cog_name}` in <#{interaction.channel.id}>."
                )

    @nextcord.slash_command(name="reload", description="Reload a specified cog.")
    async def reload(
        self,
        interaction: Interaction,
        cog_name: str = SlashOption(
            name="cog_name",
            description="Enter the name of the cog to reload.",
            required=True,
        ),
    ):
        """Reload the specified cog."""
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

        cog_choices = self.get_cog_choices()
        if cog_name not in cog_choices:
            await interaction.response.send_message(
                embed=nextcord.Embed(
                    title="❌ Invalid Cog Name",
                    description=f"Available cogs are:\n`{', '.join(cog_choices)}`",
                    color=0xFF0000
                ),
                ephemeral=True,
            )
            return

        try:
            self.bot.reload_extension(f'cogs.{cog_name}')
            embed = nextcord.Embed(
                title="✅ Cog Reloaded Successfully",
                description=f"The `{cog_name}` cog has been reloaded.",
                color=0x00FF00
            )
            embed.set_footer(text=f"Reloaded by {interaction.user.display_name}")

            await interaction.response.send_message(embed=embed, ephemeral=True)

            # Log command usage
            await self.log_command_usage(interaction, "reload", cog_name)

        except Exception as e:
            error_traceback = traceback.format_exc()
            embed = nextcord.Embed(
                title="⚠️ Reload Failed",
                description=f"An error occurred while reloading `{cog_name}`:\n```{error_traceback}```",
                color=0xFF0000
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
    bot.add_cog(Reload(bot))