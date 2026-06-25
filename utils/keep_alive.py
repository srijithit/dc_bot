import os
import hashlib
from datetime import datetime
from aiohttp import web
import logging

logger = logging.getLogger('discord_bot.dashboard')

# Global variables for real-time tracking
active_bots = {}    # bot_id -> bot_tag
activity_logs = []  # list of dicts for recent command usages

# Load password from environment (default to 'admin' for ease of use)
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")

def register_bot(bot_id: int, bot_tag: str):
    """Registers a bot instance as online."""
    active_bots[bot_id] = bot_tag

def unregister_bot(bot_id: int):
    """Unregisters a bot instance when it disconnects."""
    if bot_id in active_bots:
        del active_bots[bot_id]

def log_activity(bot_tag: str, user_tag: str, user_id: int, command: str, guild_name: str):
    """Logs command execution details for the dashboard activity feed."""
    now = datetime.now().strftime("%H:%M:%S")
    activity_logs.append({
        'timestamp': now,
        'bot': bot_tag,
        'user': user_tag,
        'user_id': user_id,
        'command': command,
        'guild': guild_name
    })
    # Keep logs capped at last 100 entries to manage memory
    if len(activity_logs) > 100:
        activity_logs.pop(0)

def verify_session(request: web.Request) -> bool:
    """Verifies if the client session cookie is valid and authorized."""
    cookie = request.cookies.get('session_token', '')
    expected = hashlib.sha256(ADMIN_PASSWORD.encode('utf-8')).hexdigest()
    return cookie == expected

# ==========================================
# HTTP Request Handlers
# ==========================================

async def handle_root(request: web.Request):
    """Serves the main dashboard page or redirect to login."""
    if not verify_session(request):
        # Redirect to login page
        return web.HTTPFound('/login')

    # Load access controls list
    from utils.access_control import load_access
    access_data = load_access()
    allowed_users = access_data.get("allowed_users", [])
    blocked_users = access_data.get("blocked_users", [])

    # HTML code for the premium dark-mode glassmorphism dashboard
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🤖 Discord Bot Admin Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #09090b;
                --card-bg: rgba(20, 20, 25, 0.6);
                --border: rgba(255, 255, 255, 0.08);
                --text: #f4f4f5;
                --text-muted: #a1a1aa;
                --primary: #8b5cf6;
                --primary-glow: rgba(139, 92, 246, 0.35);
                --green: #10b981;
                --red: #ef4444;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: 'Outfit', sans-serif;
            }}
            body {{
                background-color: var(--bg);
                color: var(--text);
                min-height: 100vh;
                background-image: 
                    radial-gradient(circle at 10% 20%, rgba(139, 92, 246, 0.08) 0%, transparent 40%),
                    radial-gradient(circle at 90% 80%, rgba(16, 185, 129, 0.05) 0%, transparent 40%);
                padding: 2rem;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2rem;
                border-bottom: 1px solid var(--border);
                padding-bottom: 1.5rem;
            }}
            h1 {{
                font-size: 2.2rem;
                font-weight: 800;
                background: linear-gradient(to right, #a78bfa, #34d399);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .btn {{
                background: var(--primary);
                color: white;
                border: none;
                padding: 0.6rem 1.2rem;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                box-shadow: 0 0 15px var(--primary-glow);
                text-decoration: none;
            }}
            .btn:hover {{
                transform: translateY(-2px);
                box-shadow: 0 0 25px var(--primary-glow);
                background: #7c3aed;
            }}
            .btn-red {{
                background: var(--red);
                box-shadow: 0 0 15px rgba(239, 68, 68, 0.35);
            }}
            .btn-red:hover {{
                background: #dc2626;
                box-shadow: 0 0 25px rgba(239, 68, 68, 0.35);
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 2rem;
                margin-bottom: 2rem;
            }}
            @media (max-width: 1024px) {{
                .grid {{
                    grid-template-columns: 1fr;
                }}
            }}
            .card {{
                background: var(--card-bg);
                backdrop-filter: blur(12px);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 2rem;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                transition: border-color 0.3s ease;
            }}
            .card:hover {{
                border-color: rgba(255, 255, 255, 0.15);
            }}
            h2 {{
                font-size: 1.4rem;
                margin-bottom: 1.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                border-bottom: 1px solid var(--border);
                padding-bottom: 0.5rem;
            }}
            /* Status Indicators */
            .bot-list {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.8rem;
            }}
            .bot-badge {{
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid var(--border);
                padding: 0.5rem 1rem;
                border-radius: 30px;
                font-size: 0.95rem;
                font-weight: 600;
            }}
            .status-dot {{
                width: 10px;
                height: 10px;
                background-color: var(--green);
                border-radius: 50%;
                box-shadow: 0 0 10px var(--green);
                display: inline-block;
            }}
            /* Forms */
            .form-group {{
                margin-bottom: 1.2rem;
            }}
            label {{
                display: block;
                font-size: 0.9rem;
                color: var(--text-muted);
                margin-bottom: 0.5rem;
                font-weight: 600;
            }}
            .input-field {{
                width: 100%;
                background: rgba(0, 0, 0, 0.25);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 0.8rem;
                color: white;
                font-size: 1rem;
                margin-bottom: 1rem;
                transition: border-color 0.2s;
            }}
            .input-field:focus {{
                outline: none;
                border-color: var(--primary);
            }}
            /* Table Styling */
            .table-container {{
                overflow-x: auto;
                max-height: 400px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                text-align: left;
            }}
            th, td {{
                padding: 0.8rem 1rem;
                border-bottom: 1px solid var(--border);
            }}
            th {{
                color: var(--text-muted);
                font-weight: 600;
                font-size: 0.9rem;
                text-transform: uppercase;
                background: rgba(255, 255, 255, 0.02);
            }}
            td {{
                font-size: 0.95rem;
            }}
            tr:hover td {{
                background: rgba(255, 255, 255, 0.01);
            }}
            .badge-cmd {{
                background: rgba(139, 92, 246, 0.15);
                color: #a78bfa;
                padding: 0.2rem 0.5rem;
                border-radius: 4px;
                font-family: monospace;
                font-weight: 600;
            }}
            /* Access List badges */
            .list-container {{
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-top: 1rem;
                min-height: 50px;
                background: rgba(0, 0, 0, 0.15);
                padding: 0.8rem;
                border-radius: 8px;
                border: 1px solid var(--border);
            }}
            .user-badge {{
                display: flex;
                align-items: center;
                gap: 0.5rem;
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid var(--border);
                padding: 0.3rem 0.7rem;
                border-radius: 6px;
                font-size: 0.9rem;
            }}
            .remove-btn {{
                background: none;
                border: none;
                color: var(--red);
                cursor: pointer;
                font-size: 1rem;
                font-weight: bold;
            }}
            .remove-btn:hover {{
                color: #ff6b6b;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div>
                    <h1>⚙️ Bot Orchestrator Panel</h1>
                    <p style="color: var(--text-muted); margin-top: 0.25rem;">Real-time diagnostics and access controls</p>
                </div>
                <form action="/logout" method="post">
                    <button type="submit" class="btn btn-red">Logout</button>
                </form>
            </header>

            <div class="grid">
                <!-- Status Card -->
                <div class="card" style="grid-column: 1 / -1;">
                    <h2>🟢 Online Bots Status ({len(active_bots)} Active)</h2>
                    <div class="bot-list">
                        {"".join(f'<div class="bot-badge"><span class="status-dot"></span>{tag}</div>' for tag in active_bots.values()) if active_bots else '<p style="color: var(--text-muted);">No bots are currently online.</p>'}
                    </div>
                </div>

                <!-- Access Management Card -->
                <div class="card">
                    <h2>🔒 Access Control Manager</h2>
                    <form action="/action" method="post">
                        <div class="form-group">
                            <label for="user_id">Discord User ID</label>
                            <input type="text" id="user_id" name="user_id" placeholder="e.g. 1519664245644464138" class="input-field" required>
                        </div>
                        <div style="display: flex; gap: 1rem;">
                            <button type="submit" name="action" value="allow" class="btn">Allow User</button>
                            <button type="submit" name="action" value="block" class="btn btn-red">Block User</button>
                        </div>
                    </form>
                    
                    <h3 style="margin-top: 2rem; font-size: 1.1rem;">Allowlist (Explicit access overrides)</h3>
                    <div class="list-container">
                        {"".join(f'<div class="user-badge">{uid}<form action="/action" method="post" style="display:inline;"><input type="hidden" name="user_id" value="{uid}"><button type="submit" name="action" value="remove_allow" class="remove-btn">×</button></form></div>' for uid in allowed_users) if allowed_users else '<p style="color: var(--text-muted); font-size: 0.9rem;">Allowlist is empty. Anyone who isn\'t blocked can use the bot.</p>'}
                    </div>

                    <h3 style="margin-top: 1.5rem; font-size: 1.1rem;">Blocklist (Globally banned users)</h3>
                    <div class="list-container">
                        {"".join(f'<div class="user-badge" style="border-color: rgba(239, 68, 68, 0.2);">{uid}<form action="/action" method="post" style="display:inline;"><input type="hidden" name="user_id" value="{uid}"><button type="submit" name="action" value="remove_block" class="remove-btn">×</button></form></div>' for uid in blocked_users) if blocked_users else '<p style="color: var(--text-muted); font-size: 0.9rem;">Blocklist is empty. No users are banned.</p>'}
                    </div>
                    
                    <form action="/action" method="post" style="margin-top: 1.5rem;">
                        <button type="submit" name="action" value="clear" class="btn btn-red" style="width: 100%;" onclick="return confirm('Are you sure you want to clear all configurations?')">Reset Access Configurations</button>
                    </form>
                </div>

                <!-- Log Card -->
                <div class="card">
                    <h2>📜 Live Activity Logs</h2>
                    <div class="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Time</th>
                                    <th>Bot</th>
                                    <th>User</th>
                                    <th>Command</th>
                                    <th>Server</th>
                                </tr>
                            </thead>
                            <tbody>
                                {"".join(f'<tr><td>{log["timestamp"]}</td><td>{log["bot"]}</td><td title="ID: {log["user_id"]}">{log["user"]}</td><td><span class="badge-cmd">{log["command"]}</span></td><td>{log["guild"]}</td></tr>' for log in reversed(activity_logs)) if activity_logs else '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">No activity recorded yet.</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def handle_login_page(request: web.Request):
    """Serves the login page."""
    if verify_session(request):
        return web.HTTPFound('/')



    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - Admin Panel</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: #09090b;
                --card-bg: rgba(20, 20, 25, 0.6);
                --border: rgba(255, 255, 255, 0.08);
                --text: #f4f4f5;
                --text-muted: #a1a1aa;
                --primary: #8b5cf6;
                --primary-glow: rgba(139, 92, 246, 0.35);
                --red: #ef4444;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
                font-family: 'Outfit', sans-serif;
            }}
            body {{
                background-color: var(--bg);
                color: var(--text);
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background-image: radial-gradient(circle at center, rgba(139, 92, 246, 0.1) 0%, transparent 60%);
            }}
            .login-card {{
                width: 100%;
                max-width: 400px;
                background: var(--card-bg);
                backdrop-filter: blur(12px);
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 2.5rem;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
            }}
            h1 {{
                font-size: 1.8rem;
                font-weight: 800;
                margin-bottom: 0.5rem;
                text-align: center;
                background: linear-gradient(to right, #a78bfa, #8b5cf6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            p {{
                color: var(--text-muted);
                text-align: center;
                margin-bottom: 2rem;
                font-size: 0.95rem;
            }}
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            label {{
                display: block;
                font-size: 0.9rem;
                color: var(--text-muted);
                margin-bottom: 0.5rem;
                font-weight: 600;
            }}
            .input-field {{
                width: 100%;
                background: rgba(0, 0, 0, 0.25);
                border: 1px solid var(--border);
                border-radius: 8px;
                padding: 0.8rem;
                color: white;
                font-size: 1rem;
                transition: border-color 0.2s;
            }}
            .input-field:focus {{
                outline: none;
                border-color: var(--primary);
            }}
            .btn {{
                width: 100%;
                background: var(--primary);
                color: white;
                border: none;
                padding: 0.8rem;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                font-size: 1rem;
                transition: all 0.2s ease;
                box-shadow: 0 0 15px var(--primary-glow);
            }}
            .btn:hover {{
                transform: translateY(-1px);
                box-shadow: 0 0 25px var(--primary-glow);
                background: #7c3aed;
            }}
        </style>
    </head>
    <body>
        <div class="login-card">
            <h1>Panel Authorization</h1>
            <p>Please log in to manage your bot fleet</p>

            <form action="/login" method="post">
                <div class="form-group">
                    <label for="password">Admin Password</label>
                    <input type="password" id="password" name="password" class="input-field" required autofocus>
                </div>
                <button type="submit" class="btn">Log In</button>
            </form>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html_content, content_type='text/html')

async def handle_login(request: web.Request):
    """Processes login POST request."""
    data = await request.post()
    password = data.get('password', '')
    
    if password == ADMIN_PASSWORD:
        # Set authorization cookie
        response = web.HTTPFound('/')
        token = hashlib.sha256(ADMIN_PASSWORD.encode('utf-8')).hexdigest()
        response.set_cookie('session_token', token, max_age=86400, httponly=True) # Valid for 24h
        return response
    else:
        # Redirect back to login with a query parameter (or just retry)
        return web.HTTPFound('/login')

async def handle_logout(request: web.Request):
    """Processes logout POST request."""
    response = web.HTTPFound('/login')
    response.del_cookie('session_token')
    return response

async def handle_action(request: web.Request):
    """Processes access control form actions."""
    if not verify_session(request):
        return web.HTTPForbidden()

    data = await request.post()
    action = data.get('action', '')
    user_id = data.get('user_id', '').strip()

    from utils.access_control import load_access, save_access
    access_data = load_access()

    if action == "allow" and user_id:
        if user_id not in access_data["allowed_users"]:
            # If a user is added to allowlist, remove them from blocklist first
            if user_id in access_data["blocked_users"]:
                access_data["blocked_users"].remove(user_id)
            access_data["allowed_users"].append(user_id)
            save_access(access_data)
            logger.info(f"User {user_id} added to Allowlist via Web Panel.")
            
    elif action == "block" and user_id:
        if user_id not in access_data["blocked_users"]:
            # If a user is added to blocklist, remove them from allowlist first
            if user_id in access_data["allowed_users"]:
                access_data["allowed_users"].remove(user_id)
            access_data["blocked_users"].append(user_id)
            save_access(access_data)
            logger.info(f"User {user_id} added to Blocklist via Web Panel.")
            
    elif action == "remove_allow" and user_id:
        if user_id in access_data["allowed_users"]:
            access_data["allowed_users"].remove(user_id)
            save_access(access_data)
            logger.info(f"User {user_id} removed from Allowlist.")
            
    elif action == "remove_block" and user_id:
        if user_id in access_data["blocked_users"]:
            access_data["blocked_users"].remove(user_id)
            save_access(access_data)
            logger.info(f"User {user_id} removed from Blocklist.")
            
    elif action == "clear":
        access_data = {"allowed_users": [], "blocked_users": []}
        save_access(access_data)
        logger.info("Access configurations reset via Web Panel.")

    return web.HTTPFound('/')

# ==========================================
# Server Launch Orchestration
# ==========================================

async def start_keep_alive(port: int = 8080):
    """Starts the keep-alive / dashboard web server asynchronously."""
    app = web.Application()
    
    # Routes
    app.router.add_get('/', handle_root)
    app.router.add_get('/login', handle_login_page)
    app.router.add_post('/login', handle_login)
    app.router.add_post('/logout', handle_logout)
    app.router.add_post('/action', handle_action)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', port)
    try:
        await site.start()
        logger.info(f"Keep-alive dashboard successfully running on http://0.0.0.0:{port}")
        return runner
    except Exception as e:
        logger.critical(f"Could not start dashboard web server: {e}")
        return None
