import discord
import yt_dlp
import asyncio
import random
import music.state as state

from db.playlist import get_user_playlist


YDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "default_search": "ytsearch",
    "extractor_args": {
        "youtube": {
            "player_client": ["android"]
        }
    }
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}


async def play_random(vc, discord_user_id):
    """
    Joue une musique aléatoire depuis la playlist utilisateur
    et enchaîne automatiquement à la fin.
    """

    playlist = get_user_playlist(discord_user_id)

    if not playlist:
        await vc.channel.send("📭 Ta playlist est vide.")
        return

    # 🔁 Évite répétition immédiate
    choices = [s for s in playlist if s != state.last_song]
    song = random.choice(choices if choices else playlist)

    state.last_song = song

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(song, download=False)

            if "entries" in info:
                info = info["entries"][0]

            state.current_title = info.get("title", "Titre inconnu")
            url = info["url"]

    except Exception as e:
        await vc.channel.send("❌ Erreur lors du chargement de la musique.")
        print("YTDLP ERROR:", e)
        return

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
        volume=0.7
    )

    def after_playing(error):
        if error:
            print("Playback error:", error)

        future = asyncio.run_coroutine_threadsafe(
            schedule_next(vc, discord_user_id),
            vc.loop
        )
        try:
            future.result()
        except Exception as e:
            print("Schedule error:", e)

    vc.play(source, after=after_playing)


async def play_track(vc, query: str) -> bool:
    """
    Joue une musique directement depuis une recherche ou un lien.
    Ne dépend PAS de la playlist.
    """

    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)

            if "entries" in info:
                info = info["entries"][0]

            state.current_title = info.get("title", "Titre inconnu")
            url = info["url"]

    except Exception as e:
        print("YTDLP ERROR:", e)
        return False

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
        volume=0.7
    )

    def after_playing(error):
        if error:
            print("Playback error:", error)

    vc.stop()
    vc.play(source, after=after_playing)
    return True


async def schedule_next(vc, discord_user_id):
    """
    Attends 1 seconde puis relance une musique si le bot est toujours connecté.
    """
    await asyncio.sleep(1)

    if vc and vc.is_connected():
        await play_random(vc, discord_user_id)
