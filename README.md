# 🤖 Professional Discord Bot (python & discord.py)

A production-ready, asynchronous, containerized Discord bot built with Python and the latest `discord.py` (v2.x). Features clean class-based design, slash (hybrid) command support, integrated automatic reconnection, error logs, and a built-in keep-alive web server to ensure 24/7 uptime on free hosting platforms.

---

## 📁 Project Structure

```text
discord-bot/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions verification workflow
├── cogs/
│   ├── __init__.py
│   └── general.py              # Cog containing the /ping command
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Rotating logging system
│   └── keep_alive.py           # Web server for 24/7 hosting pings
├── .env                        # Local environment secrets (ignored by git)
├── .env.example                # Template for environment variables
├── bot.py                      # Main entrypoint and event loops
├── Dockerfile                  # Multi-stage Docker packaging configuration
├── docker-compose.yml          # Local container composition runner
├── requirements.txt            # Dependency list
└── README.md                   # Setup and deployment documentation
```

---

## ⚙️ Discord Portal Configuration (Pre-requisites)

Before running the bot, you must create a Discord Application:
1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and give your bot a name.
3. Navigate to the **Bot** tab on the left:
   - Click **Add Bot**.
   - Under **Token**, click **Reset Token** and copy the resulting string (keep this secret!).
   - Scroll down to **Privileged Gateway Intents** and enable **Message Content Intent** (needed to process commands using prefix `!`).
4. Navigate to the **OAuth2** -> **URL Generator** tab:
   - Under **Scopes**, select `bot` and `applications.commands`.
   - Under **Bot Permissions**, select:
     - `Send Messages`
     - `Embed Links`
     - `Read Message History`
     - `Use Slash Commands`
   - Copy the generated URL at the bottom and open it in a new tab to invite the bot to your server.

---

## 💻 Local Quick Start

### 1. Set Up Environment Variables
Rename `.env.example` to `.env` and enter your Discord bot token:
```bash
cp .env.example .env
```
Open `.env` and fill in:
```env
DISCORD_TOKEN=your_copied_bot_token_here
COMMAND_PREFIX=!
ENABLE_KEEP_ALIVE=true
PORT=8080
```

### 2. Run Locally (Standard Python)
Ensure you have Python 3.11+ installed. Create a virtual environment and launch:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the bot
python bot.py
```

### 3. Run Locally (With Docker)
To build and run in an isolated environment without needing Python on your host machine:

```bash
# Build and start container in detached mode
docker-compose up -d

# View live bot logs
docker logs -f discord_bot

# Stop the container
docker-compose down
```

---

## ⚡ Hosting & Deploying 24/7 (Free Options)

Here is how you can host this bot 24/7 completely free of charge.

### Option 1: Koyeb (Highly Recommended - Free Tier)
Koyeb provides a generous free tier that supports Docker and doesn't put containers to sleep as long as you keep your server within free-tier resource limits.

1. Create a free account on [Koyeb](https://www.koyeb.com/).
2. Click **Create Service** and choose **GitHub** (or **Docker** if you push to Docker Hub).
3. Connect your GitHub repository containing this bot.
4. Set the builder type to **Dockerfile** (it will auto-detect your `Dockerfile`).
5. Under **Environment Variables**, add:
   - `DISCORD_TOKEN` = `your_token`
   - `COMMAND_PREFIX` = `!`
   - `ENABLE_KEEP_ALIVE` = `true`
   - `PORT` = `8000` (Koyeb uses port 8000 for standard web applications).
6. Set the exposed port to `8000` and path to `/` (this maps to our `keep_alive.py` web handler).
7. Deploy the service. Koyeb will run the bot continuously.

---

### Option 2: Render (Free Web Service)
Render allows running web applications for free, but they will sleep after 15 minutes of inactivity. We solve this by using the keep-alive server and an external ping.

1. Go to [Render](https://render.com/) and create an account.
2. Click **New +** -> **Web Service**.
3. Connect your GitHub repository.
4. Set the environment settings:
   - **Language**: `Python 3` (or choose **Docker** if deploying with the Dockerfile).
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Add Environment Variables under **Advanced**:
   - `DISCORD_TOKEN` = `your_token`
   - `COMMAND_PREFIX` = `!`
   - `ENABLE_KEEP_ALIVE` = `true`
   - `PORT` = `10000` (Render defaults to port 10000).
6. Once deployed, copy your web service URL (e.g., `https://my-discord-bot.onrender.com`).
7. Keep it awake 24/7:
   - Register at [UptimeRobot](https://uptimerobot.com/) or [Cron-Job.org](https://cron-job.org/).
   - Set up an HTTP monitor pinging your Render URL (`https://my-discord-bot.onrender.com`) every 10 minutes. This prevents Render from putting the bot to sleep!

---

### Option 3: Oracle Cloud Always Free VPS (Best Overall - VM Instance)
Oracle Cloud offers two VM.Standard.E2.1.Micro instances (1 CPU, 1GB RAM) for free indefinitely. This runs a full Ubuntu VM where you can host the bot.

1. Sign up for an [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/) account.
2. Create a Compute VM Instance using Ubuntu.
3. Download the SSH private key generated during creation.
4. Connect to your instance:
   ```bash
   ssh -i private_key.key ubuntu@YOUR_INSTANCE_IP
   ```
5. Install Docker and Docker-Compose:
   ```bash
   sudo apt update
   sudo apt install -y docker.io docker-compose git
   sudo systemctl enable --now docker
   ```
6. Clone your bot repository, create your `.env` file, and run:
   ```bash
   sudo docker-compose up -d --build
   ```
7. Because it's a dedicated VPS, the bot will run forever without needing keep-alive pings.

---

### Option 4: Railway (Paid but cheap / Trial Credits)
Railway is extremely developer-friendly. It offers a $5 trial credit which can run the bot for a month or two.

1. Sign up on [Railway.app](https://railway.app/).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Add environment variables: `DISCORD_TOKEN`, `COMMAND_PREFIX`, and `ENABLE_KEEP_ALIVE=false` (Railway does not require a web port for bots; you can select a worker setup).
4. Railway will automatically build and run the bot.

---

### Option 5: Fly.io (Free Allowances)
Fly.io provides free allowances up to 3 VMs.

1. Install `flyctl` command-line tool on your local machine.
2. Run `fly launch` in your `discord-bot` directory (it will detect the `Dockerfile` and configure a `fly.toml` file).
3. Set your token as a secret:
   ```bash
   fly secrets set DISCORD_TOKEN="your_token" COMMAND_PREFIX="!"
   ```
4. Run `fly deploy` to launch the bot.

---

## 🛠️ Verification & Maintenance

- **Log Auditing**: The bot writes to stdout and logs to `logs/bot.log`. If running via Docker Compose, logs can be read at `docker-compose logs -f bot` or directly in `./logs/bot.log`.
- **Latency Verification**: Run the `/ping` slash command in your discord server. The bot will return its WebSocket heartbeat round-trip duration in milliseconds.
- **Graceful Error Recovery**: If the Discord Gateway undergoes a short outage, `discord.py` will automatically trigger reconnection sequences. Custom error handlers catch and log command exceptions to prevent runtime crashes.
