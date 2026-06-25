import discord
from discord.ext import commands
import logging

logger = logging.getLogger('discord_bot.moderation')

class Moderation(commands.Cog):
    """Moderation features, including locked nickname controls."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Fires whenever a member's details are updated."""
        # Detect if nickname changed
        if before.nick != after.nick:
            logger.info(f"Nickname change detected: '{before.nick}' -> '{after.nick}' for user {after} (ID: {after.id})")
            
            # Check if the bot has nickname management permission
            if not after.guild.me.guild_permissions.manage_nicknames:
                logger.warning(f"Unable to revert nickname change: Bot lacks 'Manage Nicknames' permission in guild '{after.guild.name}'")
                return

            try:
                # Revert the nickname to its previous state (before.nick can be None if they had no nickname)
                await after.edit(
                    nick=before.nick,
                    reason="Locked Nicknames: Bot automatically reverted nickname change."
                )
                logger.info(f"Successfully reverted nickname for {after} to '{before.nick}'")
            except discord.Forbidden:
                logger.warning(
                    f"Failed to revert nickname for {after} in '{after.guild.name}'. "
                    f"Reason: Discord hierarchy prevents changing nickname of the server owner or members with roles higher than the bot."
                )
            except Exception as e:
                logger.error(f"Error while reverting nickname for {after}: {e}", exc_info=True)

async def setup(bot: commands.Bot):
    """Loads the Moderation cog."""
    await bot.add_cog(Moderation(bot))
