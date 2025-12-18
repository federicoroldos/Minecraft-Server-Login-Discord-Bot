from __future__ import annotations

import asyncio
import time
from pathlib import Path
from threading import Thread

import discord
from dotenv import load_dotenv
import os

from src.mc_discord_notifier.config import load_config
from src.mc_discord_notifier.parser import EventType, PlayerEvent
from src.mc_discord_notifier.tailer import LogTailer, TailerSettings

class Debouncer:
    def __init__(self, window_seconds: float) -> None:
        self._window = window_seconds
        self._last: dict[tuple[str, str], float] = {}

    def allow(self, event: PlayerEvent) -> bool:
        now = time.time()
        key = (event.type.value, event.player.lower())
        last = self._last.get(key, 0.0)
        if now - last < self._window:
            return False
        self._last[key] = now
        return True


async def main() -> None:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit("Missing DISCORD_TOKEN. Copy .env.example to .env and fill it in.")

    config = load_config(Path("config.json"))

    intents = discord.Intents.none()
    client = discord.Client(intents=intents)

    queue: asyncio.Queue[PlayerEvent] = asyncio.Queue()
    debouncer = Debouncer(window_seconds=config.debounce_seconds)

    def on_event(event: PlayerEvent) -> None:
        if debouncer.allow(event):
            try:
                queue.put_nowait(event)
            except Exception:
                pass

    tailer = LogTailer(
        TailerSettings(
            log_path=config.log_path,
            start_from_end=config.start_from_end,
            poll_interval_seconds=config.poll_interval_seconds,
            state_path="state.json",
        ),
        on_event=on_event,
    )

    tailer_thread = Thread(target=tailer.run_forever, name="log-tailer", daemon=True)

    @client.event
    async def on_ready() -> None:
        tailer_thread.start()
        print(f"Logged in as {client.user} (ready).")

    async def sender_loop() -> None:
        await client.wait_until_ready()
        channel = client.get_channel(config.channel_id)
        if channel is None:
            try:
                channel = await client.fetch_channel(config.channel_id)
            except Exception as e:
                raise SystemExit(f"Unable to access channel_id={config.channel_id}: {e}") from e

        join_template = (config.messages or {}).get("join", "**{player}** joined")
        leave_template = (config.messages or {}).get("leave", "**{player}** left")

        while not client.is_closed():
            event = await queue.get()
            template = join_template if event.type == EventType.JOIN else leave_template
            content = template.format(player=event.player)
            try:
                await channel.send(content)
            except Exception:
                pass

    sender_task = asyncio.create_task(sender_loop())
    try:
        await client.start(token)
    finally:
        tailer.stop()
        sender_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
