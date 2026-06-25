import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger('discord_bot.voice')

class Voice(commands.Cog):
    """Voice channel management commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="join",
        description="Instructs the bot to join your current voice channel."
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def join(self, ctx: commands.Context):
        """Joins the caller's active voice channel."""
        # Defer response to handle connection delays without timing out the interaction
        if ctx.interaction:
            await ctx.interaction.response.defer()

        # 1. Check if the user is in a voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            embed = discord.Embed(
                description="❌ You must be connected to a voice channel to use this command!",
                color=discord.Color.red()
            )
            if ctx.interaction:
                await ctx.interaction.followup.send(embed=embed)
            else:
                await ctx.send(embed=embed)
            return

        target_channel = ctx.author.voice.channel
        
        # 2. Check if the bot is already in a voice channel in this server
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        
        if voice_client:
            # If already in the target channel
            if voice_client.channel.id == target_channel.id:
                embed = discord.Embed(
                    description=f"ℹ️ I am already connected to {target_channel.mention}.",
                    color=discord.Color.blue()
                )
                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
                return
            
            # Move to the target channel
            await voice_client.move_to(target_channel)
            logger.info(f"Bot moved to voice channel: '{target_channel.name}' (ID: {target_channel.id})")
            embed = discord.Embed(
                description=f"🚚 Moved to {target_channel.mention}.",
                color=discord.Color.brand_green() if hasattr(discord.Color, 'brand_green') else discord.Color.green()
            )
            if ctx.interaction:
                await ctx.interaction.followup.send(embed=embed)
            else:
                await ctx.send(embed=embed)
        else:
            # Connect to the target channel
            try:
                await target_channel.connect()
                logger.info(f"Bot successfully joined voice channel: '{target_channel.name}' (ID: {target_channel.id})")
                embed = discord.Embed(
                    description=f"📥 Connected to {target_channel.mention}.",
                    color=discord.Color.brand_green() if hasattr(discord.Color, 'brand_green') else discord.Color.green()
                )
                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to join voice channel '{target_channel.name}': {e}", exc_info=True)
                embed = discord.Embed(
                    description=f"❌ Failed to connect to voice: {e}",
                    color=discord.Color.red()
                )
                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="sleep",
        description="Instructs the bot to disconnect from the voice channel."
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def sleep(self, ctx: commands.Context):
        """Disconnects the bot from the voice channel."""
        # Defer response to handle disconnection delays
        if ctx.interaction:
            await ctx.interaction.response.defer()

        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        
        if voice_client and voice_client.is_connected():
            connected_channel = voice_client.channel.name
            await voice_client.disconnect()
            logger.info(f"Bot disconnected from voice channel: '{connected_channel}'")
            embed = discord.Embed(
                description=f"👋 Disconnected from voice channel: **{connected_channel}**.",
                color=discord.Color.gold()
            )
            if ctx.interaction:
                await ctx.interaction.followup.send(embed=embed)
            else:
                await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ I am not connected to any voice channel in this server.",
                color=discord.Color.red()
            )
            if ctx.interaction:
                await ctx.interaction.followup.send(embed=embed)
            else:
                await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    """Loads the Voice cog."""
    await bot.add_cog(Voice(bot))
