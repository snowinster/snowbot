import discord
import yt_dlp
import asyncio
import random

from music.state import last_song, current_title
from db.playlist import get_user_playlist


async def play_random(vc, discord_user_id):
    global last_song, current_title

    playlist = get_user_playlist(discord_user_id)
    if not playlist:
        await vc.channel.send("📭 Ta playlist est vide.")
        return

    choices = [s for s in playlist if s != last_song]
    song = random.choice(choices if choices else playlist)
    last_song = song

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "default_search": "ytsearch"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(song, download=False)
        if "entries" in info:
            info = info["entries"][0]
        current_title = info["title"]
        url = info["url"]

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(
            url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        ),
        volume=0.7
    )

    vc.play(source, after=lambda _: asyncio.run_coroutine_threadsafe(
        schedule_next(vc, discord_user_id),
        vc.loop
    ))


async def schedule_next(vc, discord_user_id):
    await asyncio.sleep(1)
    if vc.is_connected():
        await play_random(vc, discord_user_id)
