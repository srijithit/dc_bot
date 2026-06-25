import discord
from discord.ext import commands
from discord import app_commands

class General(commands.Cog):
    """General utility commands for the bot."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        description="Replies with the bot's current API latency."
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def ping(self, ctx: commands.Context):
        """Replies with the bot's WebSocket/API latency."""
        # Calculate API latency in milliseconds
        latency = round(self.bot.latency * 1000)
        
        # Design a professional embed response
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"My latency is **{latency}ms**.",
            color=discord.Color.brand_green() if hasattr(discord.Color, 'brand_green') else discord.Color.green()
        )
        
        # Set footer with the user's name and avatar
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)

async def setup(bot: commands.Bot):
    """Standard setup function to load the cog."""
    await bot.add_cog(General(bot))
