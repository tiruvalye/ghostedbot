import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption, Embed
import logging
import traceback
import config
from logic.promos_rs3_logic import run_promotions

logger = logging.getLogger(__name__)

class PromotionsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="promotions", description="Run promotions for RuneScape 3 members.")
    async def promotions(
        self,
        interaction: Interaction,
        game: str = SlashOption(
            name="game",
            description="Specify the game version for promotions.",
            choices={"RuneScape 3": "rs3"},
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

            if config.ROLE_IDS['rs3botmod'] not in [role.id for role in user.roles]:
                await interaction.response.send_message(
                    f"<@{user.id}> you do not have permission to use this command.",
                    ephemeral=True
                )
                return

            # Run the promotion logic
            promotion_summary, debug_details = run_promotions()

            if promotion_summary:
                embed = Embed(
                    title="Promotion Summary",
                    description=promotion_summary,
                    color=nextcord.Color.green()
                )
            else:
                embed = Embed(
                    title="Promotion Summary",
                    description="No promotions were processed.",
                    color=nextcord.Color.orange()
                )

            await interaction.response.send_message(embed=embed)

            # Send debug details to the debugging channel
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS['debugging'])
            if debugging_channel:
                await debugging_channel.send(f"Promotion Debug Details:\n{debug_details}")

        except Exception as e:
            error_traceback = traceback.format_exc()
            logger.error(f"Error executing promotions command: {error_traceback}")
            await interaction.response.send_message(
                f"<@{interaction.user.id}>, there was an error executing this command. Please check the debugging channel for more details.",
                ephemeral=True
            )
            debugging_channel = self.bot.get_channel(config.CHANNEL_IDS['debugging'])
            if debugging_channel:
                await debugging_channel.send(
                    f"Exception while executing `/promotions`: ```{error_traceback}```"
                )

def setup(bot):
    bot.add_cog(PromotionsCog(bot))