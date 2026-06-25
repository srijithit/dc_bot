import os
import sys
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# Import utilities
from utils.logger import setup_logging
from utils.keep_alive import start_keep_alive

# Initialize logging
logger = setup_logging()

# Load environment variables
load_dotenv()

# We support a single token or a comma-separated list of multiple tokens
tokens_str = os.getenv("DISCORD_TOKEN", "")
TOKENS = [t.strip() for t in tokens_str.split(",") if t.strip()]

PREFIX = os.getenv("COMMAND_PREFIX", "!")
ENABLE_KEEP_ALIVE = os.getenv("ENABLE_KEEP_ALIVE", "true").lower() == "true"
PORT = int(os.getenv("PORT", "8080"))

class DiscordBot(commands.Bot):
    def __init__(self):
        # Configure intents: Default intents plus members and message content
        intents = discord.Intents.default()
        intents.message_content = True  # Enable for prefix commands
        intents.members = True          # Enable to receive member nickname changes
        
        super().__init__(
            command_prefix=PREFIX,
            intents=intents,
            help_command=commands.MinimalHelpCommand()
        )
        
        # Override tree error handler with custom logger
        self.tree.on_error = self.on_tree_error

    async def setup_hook(self):
        """Asynchronous initialization hook called before the bot connects."""
        bot_label = f"[{self.user}]" if self.user else "[Bot]"
        logger.info(f"{bot_label} Initializing setup hook...")
        
        # Resolve cogs directory relative to bot.py
        cogs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cogs')
        
        # Dynamically load all cogs
        if os.path.exists(cogs_dir):
            for filename in os.listdir(cogs_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    cog_name = f'cogs.{filename[:-3]}'
                    try:
                        await self.load_extension(cog_name)
                        logger.info(f"{bot_label} Loaded extension: {cog_name}")
                    except Exception as e:
                        logger.error(f"{bot_label} Failed to load extension {cog_name}: {e}", exc_info=True)
        else:
            logger.warning(f"Cogs directory not found at: {cogs_dir}")
            
        # Sync slash commands globally
        logger.info(f"{bot_label} Syncing commands globally to Discord...")
        try:
            synced = await self.tree.sync()
            logger.info(f"{bot_label} Successfully synced {len(synced)} slash command(s) globally.")
        except Exception as e:
            logger.error(f"{bot_label} Error syncing slash commands: {e}", exc_info=True)

    async def on_connect(self):
        bot_label = f"[{self.user}]" if self.user else "[Bot]"
        logger.info(f"{bot_label} Connected to Discord Gateway.")

    async def on_ready(self):
        bot_label = f"[{self.user}]"
        logger.info(f"{bot_label} Logged in as: {self.user} (ID: {self.user.id})")
        
        # Set persistent status "Watching the server"
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="the server"
        )
        await self.change_presence(activity=activity)
        logger.info(f"{bot_label} Bot presence set to 'Watching the server'")

    async def on_disconnect(self):
        bot_label = f"[{self.user}]" if self.user else "[Bot]"
        logger.warning(f"{bot_label} Disconnected from Discord Gateway. discord.py will attempt auto-reconnect.")

    async def on_resumed(self):
        bot_label = f"[{self.user}]" if self.user else "[Bot]"
        logger.info(f"{bot_label} Gateway session successfully resumed.")

    async def on_error(self, event_method: str, *args, **kwargs):
        bot_label = f"[{self.user}]" if self.user else "[Bot]"
        logger.error(f"{bot_label} Unhandled exception in gateway event handler '{event_method}'", exc_info=sys.exc_info())

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Global handler for classic prefix command errors."""
        bot_label = f"[{self.user}]"
        if isinstance(error, commands.CommandNotFound):
            return  # Quietly ignore non-existent prefix commands
        elif isinstance(error, commands.MissingPermissions):
            try:
                await ctx.send("❌ You do not have permissions to run this command.", delete_after=10)
            except Exception:
                pass
        elif isinstance(error, commands.MissingRequiredArgument):
            try:
                await ctx.send(f"❌ Missing required argument: `{error.param.name}`", delete_after=10)
            except Exception:
                pass
        else:
            logger.error(f"{bot_label} Prefix command error in '{ctx.command}': {error}", exc_info=error)
            try:
                await ctx.send("❌ An unexpected error occurred executing that command.", delete_after=10)
            except Exception:
                pass

    async def on_tree_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Global handler for slash command (AppCommand) errors."""
        bot_label = f"[{self.user}]"
        if isinstance(error, app_commands.CommandOnCooldown):
            msg = f"⏳ Command is on cooldown. Try again in {error.retry_after:.2f}s."
        elif isinstance(error, app_commands.MissingPermissions):
            msg = "❌ You lack the necessary permissions to run this command."
        else:
            logger.error(f"{bot_label} Slash command error in '{interaction.command.name if interaction.command else 'unknown'}': {error}", exc_info=error)
            msg = "❌ An unexpected error occurred while executing this command."

        try:
            if interaction.response.is_done():
                await interaction.followup.send(msg, ephemeral=True)
            else:
                await interaction.response.send_message(msg, ephemeral=True)
        except Exception as e:
            logger.error(f"{bot_label} Failed to send error response to Discord: {e}")

async def main():
    if not TOKENS:
        logger.critical("DISCORD_TOKEN is missing or set to placeholder value! Please configure it in your .env file.")
        sys.exit(1)

    # Filter out defaults or empty keys
    valid_tokens = [t for t in TOKENS if t != "your_bot_token_here" and t != ""]

    if not valid_tokens:
        logger.critical("No valid bot tokens configured in .env!")
        sys.exit(1)

    # Optional: Start Keep Alive Web Server (for Render, Koyeb, etc.) - run once
    runner = None
    if ENABLE_KEEP_ALIVE:
        runner = await start_keep_alive(port=PORT)

    # Create Bot instances and corresponding startup tasks
    bot_instances = []
    startup_tasks = []
    
    for token in valid_tokens:
        bot = DiscordBot()
        bot_instances.append(bot)
        startup_tasks.append(bot.start(token))

    logger.info(f"Starting {len(valid_tokens)} Discord Bot instance(s) concurrently...")
    
    try:
        # Run all bots concurrently using asyncio.gather
        await asyncio.gather(*startup_tasks)
    except asyncio.CancelledError:
        logger.info("Bot startup tasks were cancelled.")
    except Exception as e:
        logger.critical(f"Fatal error during bots runtime: {e}", exc_info=True)
    finally:
        # Clean shutdown of keep alive server
        if runner:
            logger.info("Shutting down keep-alive web server...")
            await runner.cleanup()
        logger.info("All bot instances shut down successfully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bots manually terminated via KeyboardInterrupt.")
