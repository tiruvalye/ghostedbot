import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import config
import requests
import traceback
from datetime import datetime

class News(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_command_usage(self, interaction, command_name):
        """Logs command usage to the logs channel."""
        logs_channel = self.bot.get_channel(config.CHANNEL_IDS['logs'])
        timestamp_now = int(datetime.now().timestamp())
        log_message = f"<t:{timestamp_now}:F> <@{interaction.user.id}> issued command `/{command_name}` in <#{interaction.channel_id}>."
        if logs_channel:
            await logs_channel.send(log_message)

    @nextcord.slash_command(name="news", description="Post a news update for Discord, Old School RuneScape, or RuneScape 3.")
    async def news(
        self,
        interaction: Interaction,
        game: str = SlashOption(
            name="game",
            description="Select the game version",
            choices={"Discord": "discord", "Old School RuneScape": "osrs", "RuneScape 3": "rs3"},
        ),
        news_title: str = SlashOption(
            name="news_title",
            description="Enter the title of the news post.",
            required=True,
        ),
        news_description: str = SlashOption(
            name="news_description",
            description="Enter a description of the news post.",
            required=True,
        ),
        thumbnail_image: str = SlashOption(
            name="thumbnail_image",
            description="URL of the thumbnail image (optional)",
            required=False,
        ),
        banner_image: str = SlashOption(
            name="banner_image",
            description="URL of the banner image (optional)",
            required=False,
        ),
        hex_color: str = SlashOption(
            name="hex_color",
            description="Enter a custom hex color for the embed (optional, format: AABBCC)",
            required=False,
        ),
    ):
        # Check if command is used in controlpanel channel
        if interaction.channel_id != config.CHANNEL_IDS["controlpanel"]:
            await interaction.response.send_message(
                f"This command can only be used in <#{config.CHANNEL_IDS['controlpanel']}>.", ephemeral=True
            )
            return

        # Check if user has newsmod role
        role = nextcord.utils.get(interaction.guild.roles, id=config.ROLE_IDS["newsmod"])
        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "You do not have the required permission. You must be a News Mod to use this command.", ephemeral=True
            )
            return

        # Log command usage
        await self.log_command_usage(interaction, "news")

        # Use the news webhook URL for all game choices
        webhook_url = config.WEBHOOK_URLS.get("news")

        if not webhook_url:
            await interaction.response.send_message(f"Webhook URL for news not configured.", ephemeral=True)
            return

        # Set the color and tag roles based on the game
        game_details = {
            "osrs": {"color": 0xFFFF00, "roles_to_tag": "<@&1255912535542988954> <@&1086485830018797650>", "game_name": "Old School RuneScape News"},
            "rs3": {"color": 0x00A2E8, "roles_to_tag": "<@&1255912535542988954> <@&973796251835432970>", "game_name": "RuneScape 3 News"},
            "discord": {"color": 0x7289DA, "roles_to_tag": "@everyone", "game_name": "Discord News"},
        }

        details = game_details[game]
        roles_to_tag = details["roles_to_tag"]
        embed_color = details["color"]  # Default color
        game_version = details["game_name"]

        # Apply custom hex color if provided
        if hex_color:
            try:
                embed_color = int(hex_color, 16)
            except ValueError:
                await interaction.response.send_message("Invalid hex color format. Use AABBCC.", ephemeral=True)
                return

        # Get user nickname or fallback to username
        user_nickname = interaction.user.nick or interaction.user.name
        user_avatar = interaction.user.display_avatar.url

        # Create the embed
        embed = nextcord.Embed(
            title=news_title,
            description=news_description,
            color=embed_color,
        )
        embed.set_footer(
            text=f"{game_version} posted by {user_nickname}",
            icon_url=user_avatar
        )

        if thumbnail_image:
            embed.set_thumbnail(url=thumbnail_image)
        if banner_image:
            embed.set_image(url=banner_image)

        # Send the embed to the appropriate webhook
        try:
            response = requests.post(
                webhook_url, json={"content": roles_to_tag, "embeds": [embed.to_dict()]}
            )

            if response.status_code == 204:
                confirmation_embed = nextcord.Embed(
                    title="✅ News Successfully Posted",
                    description=f"Your news update **{news_title}** has been posted!",
                    color=embed_color,
                )
                confirmation_embed.set_footer(text="News posted by Ghosted Bot")

                confirmation_channel = self.bot.get_channel(config.CHANNEL_IDS["controlpanel"])
                if confirmation_channel:
                    await confirmation_channel.send(embed=confirmation_embed)

            else:
                await interaction.response.send_message(
                    f"Failed to post the news. Status Code: {response.status_code}, Response: {response.text}",
                    ephemeral=True
                )

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred when trying to post the news: {e}", ephemeral=True
            )

# Setup function
def setup(bot):
    bot.add_cog(News(bot))