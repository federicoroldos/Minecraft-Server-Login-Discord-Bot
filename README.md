# MinecraftServerNotifications
A simple connection between Discord and your own Minecraft server that sends notifications every time a player logs in.

## What this does
Runs a Discord bot on your Windows PC and watches your Spigot `latest.log`. When it sees lines like:
- `[Server thread/INFO]: [+] playerName`
- `[Server thread/INFO]: [-] playerName`

it posts a message to a Discord channel.

## Discord setup
1. Create a bot:
   - Go to https://discord.com/developers/applications
   - **New Application** -> name it
   - **Bot** -> **Add Bot**
2. Get your bot token:
   - **Bot** -> **Reset Token** / **Copy Token**
   - Put it in `.env` as `DISCORD_TOKEN=...`
   - Do not paste the token in chat or commit it to git.
3. Invite the bot to your server:
   - **OAuth2** -> **URL Generator**
   - Scopes: `bot`
   - Bot Permissions: `View Channels`, `Send Messages` (and `Embed Links` if you want)
   - Open the generated URL and select your Discord server
4. Get the channel ID:
   - Discord **User Settings** -> **Advanced** -> enable **Developer Mode**
   - Right-click the channel -> **Copy Channel ID**
   - Put it in `config.json` as `channel_id`

## Local setup (Windows)
From the repo folder `MinecraftServerNotifications`:
1. Run:
   - `.\run.ps1`

On first run, the script will prompt you for:
- `DISCORD_TOKEN` (saved into `.env`)
- `channel_id` and `log_path` (saved into `config.json`)

If you want it to start posting immediately on launch, set `start_from_end` to `false` (otherwise it starts at the end to avoid spamming old logins).

## Troubleshooting
- Bot doesn't post anything: make sure `config.json` points to the real `logs\\latest.log` via `log_path`.
- `Unknown Channel`: `channel_id` is wrong, the bot isn't in that server, or it lacks `View Channel` / `Send Messages` in that channel.

## Notes
- Python 3.13+: this repo installs `audioop-lts` because `audioop` was removed from the Python standard library (it's skipped on older Python versions).
