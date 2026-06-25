import discord
from discord.ext import commands
from discord import app_commands
import discord.ext.voice_recv as voice_recv
import logging
import threading

logger = logging.getLogger('discord_bot.voice')

class QueueAudioSource(discord.AudioSource):
    """A custom thread-safe AudioSource that reads from a PCM packet queue buffer."""
    def __init__(self):
        self.buffer = bytearray()
        self.lock = threading.Lock()

    def is_opus(self):
        # We are providing raw PCM frames, not Opus encoded ones
        return False

    def read(self):
        with self.lock:
            # 20ms of stereo PCM at 48kHz is 960 samples * 2 channels * 2 bytes/sample = 3840 bytes
            if len(self.buffer) >= 3840:
                data = bytes(self.buffer[:3840])
                del self.buffer[:3840]
                return data
            else:
                # Return silence frame when buffer is empty to keep stream alive
                return b'\x00' * 3840

    def add_data(self, data):
        with self.lock:
            # Limit the buffer size (e.g. 192,000 bytes is ~1 sec of delay) to prevent RAM exhaustion
            if len(self.buffer) < 192000:
                self.buffer.extend(data)

    def clear(self):
        with self.lock:
            self.buffer.clear()

class EchoSink(voice_recv.AudioSink):
    """A custom voice receiver Sink that filters incoming audio packets and buffers them for echoing."""
    def __init__(self, source: QueueAudioSource):
        self.source = source
        self.speaker_id = None
        self.active = False

    def write(self, user, data):
        # Only buffer audio if the mic loop is active and the speaking user matches the designated speaker
        if self.active and user and user.id == self.speaker_id:
            # data.pcm contains the decoded PCM frame from the user
            self.source.add_data(data.pcm)

    def wants_opus(self):
        # We want raw PCM packets, not Opus
        return False

    def cleanup(self):
        pass


class Voice(commands.Cog):
    """Voice channel management and microphone echoing commands."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sessions = {}  # guild_id -> { 'source': QueueAudioSource, 'sink': EchoSink }

    @commands.hybrid_command(
        name="join",
        description="Instructs the bot to join your current voice channel."
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def join(self, ctx: commands.Context):
        """Joins the caller's active voice channel."""
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
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        bot_label = f"[{self.bot.user}]"
        
        # 2. Check if the bot is already in a voice channel in this server
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
            logger.info(f"{bot_label} Moved to voice channel: '{target_channel.name}' (ID: {target_channel.id})")
        else:
            # Connect to the target channel using the voice_recv client class
            try:
                # Stagger connections to avoid gateway rate limits when all 10 bots connect at once
                import random
                import asyncio
                delay = random.uniform(0.5, 4.5)
                logger.info(f"{bot_label} Staggering connection. Sleeping for {delay:.2f}s...")
                await asyncio.sleep(delay)

                voice_client = await target_channel.connect(cls=voice_recv.VoiceRecvClient, timeout=30.0)
                logger.info(f"{bot_label} Connected to voice channel: '{target_channel.name}' using VoiceRecvClient")
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
                return

        # 3. Initialize the loopback session if it doesn't exist
        guild_id = ctx.guild.id
        if guild_id not in self.sessions:
            source = QueueAudioSource()
            sink = EchoSink(source)
            self.sessions[guild_id] = {
                'source': source,
                'sink': sink
            }
            logger.info(f"{bot_label} Echo session initialized for guild {guild_id}.")

        session = self.sessions[guild_id]

        # 4. Start playing the source (silence initially) and listening using the sink
        if not voice_client.is_playing():
            voice_client.play(session['source'])
        
        try:
            # Register the receiving sink to start listening to incoming audio packets
            voice_client.listen(session['sink'])
        except Exception:
            pass  # Already listening

        embed = discord.Embed(
            description=f"📥 Connected to {target_channel.mention}.\nUse `/mic status:on` or `!mic on` to enable voice echo!",
            color=discord.Color.brand_green() if hasattr(discord.Color, 'brand_green') else discord.Color.green()
        )
        if ctx.interaction:
            await ctx.interaction.followup.send(embed=embed)
        else:
            await ctx.send(embed=embed)

    @commands.hybrid_command(
        name="mic",
        description="Turns the spoken voice echo ON or OFF."
    )
    @app_commands.describe(status="Choose 'on' to enable voice echoing, or 'off' to disable.")
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def mic(self, ctx: commands.Context, status: str):
        """Turns the microphone loopback ON or OFF."""
        guild_id = ctx.guild.id
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        bot_label = f"[{self.bot.user}]"

        if not voice_client or guild_id not in self.sessions:
            embed = discord.Embed(
                description="❌ I must be connected to a voice channel first! Use `/join` first.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        status_lower = status.lower().strip()
        session = self.sessions[guild_id]

        if status_lower == "on":
            # Enable echoing and bind it ONLY to the user ID who ran the command to prevent feedback loops
            session['sink'].speaker_id = ctx.author.id
            session['sink'].active = True
            session['source'].clear()

            logger.info(f"{bot_label} Microphone loopback enabled for user '{ctx.author}' (ID: {ctx.author.id})")
            embed = discord.Embed(
                description=f"🎤 **Mic Echo ON**: I am now echoing the voice of {ctx.author.mention}!",
                color=discord.Color.brand_green() if hasattr(discord.Color, 'brand_green') else discord.Color.green()
            )
            await ctx.send(embed=embed)
        elif status_lower == "off":
            # Disable echoing
            session['sink'].active = False
            session['source'].clear()

            logger.info(f"{bot_label} Microphone loopback disabled.")
            embed = discord.Embed(
                description="🔇 **Mic Echo OFF**: Voice echo has been disabled.",
                color=discord.Color.gold()
            )
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                description="❌ Invalid status. Please specify `on` or `off`.",
                color=discord.Color.red()
            )
            await ctx.send(embed=embed, ephemeral=True)

    @commands.hybrid_command(
        name="sleep",
        description="Instructs the bot to disconnect from the voice channel."
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def sleep(self, ctx: commands.Context):
        """Disconnects the bot from the voice channel."""
        if ctx.interaction:
            await ctx.interaction.response.defer()

        guild_id = ctx.guild.id
        voice_client = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        bot_label = f"[{self.bot.user}]"

        if voice_client and voice_client.is_connected():
            connected_channel = voice_client.channel.name
            
            # Stop playing and listening before disconnecting
            try:
                voice_client.stop()
            except Exception:
                pass

            await voice_client.disconnect()
            logger.info(f"{bot_label} Disconnected from voice channel: '{connected_channel}'")
            
            # Cleanup session state
            if guild_id in self.sessions:
                self.sessions[guild_id]['source'].clear()
                del self.sessions[guild_id]

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
