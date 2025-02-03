import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import config
import requests
import traceback
from datetime import datetime

class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def log_command_usage(self, interaction, command_name):
        """Logs command usage to the logs channel."""
        logs_channel = self.bot.get_channel(config.CHANNEL_IDS["logs"])
        timestamp_now = int(datetime.now().timestamp())
        log_message = f"<t:{timestamp_now}:F> <@{interaction.user.id}> issued command `/{command_name}` in <#{interaction.channel_id}>."
        if logs_channel:
            await logs_channel.send(log_message)

    @nextcord.slash_command(name="event", description="Create a new event for Discord, Old School RuneScape, or RuneScape 3.")
    async def event(
        self,
        interaction: Interaction,
        game: str = SlashOption(
            name="game",
            description="Select the game version",
            choices={"Discord": "discord", "Old School RuneScape": "osrs", "RuneScape 3": "rs3"},
            required=True,
        ),
        timestamp_start: int = SlashOption(
            name="timestamp_start",
            description="Enter the Unix Timestamp for the event start.",
            required=True,
        ),
        event_title: str = SlashOption(
            name="event_title",
            description="Enter the title of your event.",
            required=True,
        ),
        location: str = SlashOption(
            name="location",
            description="Enter the meeting location. For Discord channels, use the Channel ID.",
            required=True,
        ),
        event_description: str = SlashOption(
            name="event_description",
            description="Enter a description of your event.",
            required=True,
        ),
        host_id: str = SlashOption(
            name="host_id",
            description="Enter the Discord User ID of the Host (optional).",
            required=False,
        ),
        side_image: str = SlashOption(
            name="side_image",
            description="URL of the thumbnail image (optional)",
            required=False,
        ),
        banner_image: str = SlashOption(
            name="banner_image",
            description="URL of the banner image (optional)",
            required=False,
        ),
        timestamp_end: int = SlashOption(
            name="timestamp_end",
            description="Enter the Unix Timestamp for the event end (optional).",
            required=False,
        ),
        hex_color: str = SlashOption(
            name="hex_color",
            description="Enter a custom hex color for the embed (optional, format: RRGGBB)",
            required=False,
        ),
    ):
        """Slash command to create and announce an event."""

        # Check if command is used in controlpanel channel
        if interaction.channel_id != config.CHANNEL_IDS["controlpanel"]:
            await interaction.response.send_message(
                f"This command can only be used in <#{config.CHANNEL_IDS['controlpanel']}>.", ephemeral=True
            )
            return

        # Check if user has eventsmod role
        role = nextcord.utils.get(interaction.guild.roles, id=config.ROLE_IDS["eventsmod"])
        if role not in interaction.user.roles:
            await interaction.response.send_message(
                "You do not have the required permission. You must be an Events Mod to use this command.", ephemeral=True
            )
            return

        # Log command usage
        await self.log_command_usage(interaction, "event")

        # Determine the webhook URL based on game choice
        webhook_key = f"events{game}"
        webhook_url = config.WEBHOOK_URLS.get(webhook_key, None)

        if not webhook_url:
            await interaction.response.send_message(f"Webhook URL for {game} not configured.", ephemeral=True)
            return

        # Define role ID mappings
        event_roles = {
            "osrs": {
                "default_color": 0xFFFF00,
                "roles_to_tag": [1086485830018797650, 1033478577737441310],
                "game_name": "Old School RuneScape Event"
            },
            "rs3": {
                "default_color": 0x00A2E8,
                "roles_to_tag": [973796251835432970, 1033478577737441310],
                "game_name": "RuneScape 3 Event"
            },
            "discord": {
                "default_color": 0x7289DA,
                "roles_to_tag": [1086485830018797650, 973796251835432970, 1033478577737441310],
                "game_name": "Discord Event"
            }
        }

        if game not in event_roles:
            await interaction.response.send_message("Invalid game choice.", ephemeral=True)
            return

        # Get game-specific details
        details = event_roles[game]
        roles_to_tag = " ".join(f"<@&{role_id}>" for role_id in details["roles_to_tag"])
        game_version = details["game_name"]

        # Convert hex color to Discord-compatible integer
        embed_color = details["default_color"]  # Default color
        if hex_color:
            try:
                embed_color = int(hex_color, 16)  # Convert hex to int, assumes input is "RRGGBB"
            except ValueError:
                await interaction.response.send_message("Invalid hex color format. Use RRGGBB.", ephemeral=True)
                return

        # Format timestamps and location
        formatted_timestamp_start = f"<t:{timestamp_start}:F>"
        formatted_timestamp_end = f"<t:{timestamp_end}:F>" if timestamp_end else "N/A"
        formatted_location = f"<#{location}>" if location.isdigit() else location

        # Create the event embed
        embed = nextcord.Embed(
            title=event_title,
            description=event_description,
            color=embed_color,
        )
        embed.add_field(name="🎤 Event Host", value=f"<@{host_id}>" if host_id else f"<@{interaction.user.id}>", inline=False)
        embed.add_field(name="📅 Start Time", value=formatted_timestamp_start, inline=False)
        if timestamp_end:
            embed.add_field(name="⏳ End Time", value=formatted_timestamp_end, inline=False)
        embed.add_field(name="📍 Location", value=formatted_location, inline=False)
        embed.add_field(name="🎮 Game Version", value=game_version, inline=False)

        # Add optional images
        if side_image:
            embed.set_thumbnail(url=side_image)
        if banner_image:
            embed.set_image(url=banner_image)

        # Send the embed to the appropriate webhook
        try:
            response = requests.post(
                webhook_url, json={"content": roles_to_tag, "embeds": [embed.to_dict()]}
            )

            # Check the response and send confirmation embed
            if response.status_code == 204:
                confirmation_embed = nextcord.Embed(
                    title="✅ Event Successfully Created",
                    description=f"Your event **{event_title}** has been announced!",
                    color=embed_color,
                )
                confirmation_embed.add_field(name="📅 Start Time", value=formatted_timestamp_start, inline=True)
                confirmation_embed.add_field(name="📍 Location", value=formatted_location, inline=True)
                confirmation_embed.add_field(name="🎮 Game Version", value=game_version, inline=True)
                confirmation_embed.set_footer(text="Use /event to create more events.")

                confirmation_channel = self.bot.get_channel(config.CHANNEL_IDS["controlpanel"])
                if confirmation_channel:
                    await confirmation_channel.send(embed=confirmation_embed)

        except Exception as e:
            await interaction.response.send_message(
                f"An error occurred when trying to post the event: {e}", ephemeral=True
            )

def setup(bot):
    bot.add_cog(Event(bot))