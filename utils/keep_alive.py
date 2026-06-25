from aiohttp import web
import logging

logger = logging.getLogger('discord_bot.keep_alive')

async def index(request):
    """Simple health check endpoint returning bot status."""
    return web.Response(text="Bot is online and active!", content_type='text/plain')

async def start_keep_alive(port: int = 8080):
    """Starts the keep-alive web server asynchronously on the main event loop."""
    app = web.Application()
    app.router.add_get('/', index)
    
    # Set up and start the web runner asynchronously
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    try:
        await site.start()
        logger.info(f"Keep-alive web server is running on http://0.0.0.0:{port}")
        return runner
    except Exception as e:
        logger.critical(f"Could not start keep-alive web server: {e}")
        return None
