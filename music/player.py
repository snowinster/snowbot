import discord
import yt_dlp
import asyncio
import random
import music.state as state

from db.playlist import get_user_playlist


# ─────────────── YTDLP CONFIG ───────────────

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "default_search": "ytsearch",
    "ignoreerrors": True,
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


# ────────────────────────────────────────────
# UTIL
# ────────────────────────────────────────────

async def _extract_audio(query: str, vc) -> tuple | None:
    try:
        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)

            if not info:
                return None

            if "entries" in info:
                info = info["entries"][0]

            title = info.get("title", "Titre inconnu")
            url = info.get("url")

            if not url:
                return None

            return title, url

    except yt_dlp.utils.DownloadError as e:
        print("YTDLP DownloadError:", e)

        if "Sign in to confirm your age" in str(e):
            try:
                await vc.channel.send("🔞 Vidéo bloquée (restriction d'âge YouTube).")
            except:
                pass
        else:
            try:
                await vc.channel.send("❌ Impossible de charger la musique.")
            except:
                pass

        return None

    except Exception as e:
        print("YTDLP ERROR:", e)
        return None


def _create_source(url: str):
    return discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS),
        volume=0.7
    )


def _safe_stop(vc):
    if vc and (vc.is_playing() or vc.is_paused()):
        vc.stop()


# ────────────────────────────────────────────
# PLAY RANDOM (playlist perso)
# ────────────────────────────────────────────

async def play_random(vc, discord_user_id):

    playlist = get_user_playlist(discord_user_id)

    if not playlist:
        await vc.channel.send("📭 Ta playlist est vide.")
        return

    choices = [s for s in playlist if s != state.last_song]
    song = random.choice(choices if choices else playlist)

    state.last_song = song

    extracted = await _extract_audio(song, vc)
    if not extracted:
        return

    title, url = extracted
    state.current_title = title

    source = _create_source(url)

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

    _safe_stop(vc)

    if not vc.is_connected():
        print("play_random: vc not connected, aborting play")
        return

    vc.play(source, after=after_playing)


# ────────────────────────────────────────────
# PLAY DIRECT
# ────────────────────────────────────────────

async def play_track(vc, query: str) -> bool:

    extracted = await _extract_audio(query, vc)
    if not extracted:
        return False

    title, url = extracted
    state.current_title = title

    source = _create_source(url)

    def after_playing(error):
        if error:
            print("Playback error:", error)

        future = asyncio.run_coroutine_threadsafe(
            play_next_queued(vc),
            vc.loop
        )
        try:
            future.result()
        except Exception as e:
            print("Queue error:", e)

    guild_id = vc.guild.id

    state.history.setdefault(guild_id, [])
    state.history_index.setdefault(guild_id, -1)

    history = state.history[guild_id]
    index = state.history_index[guild_id]

    if index < len(history) - 1:
        history[:] = history[:index + 1]

    history.append(query)
    state.history_index[guild_id] = len(history) - 1

    _safe_stop(vc)

    if not vc.is_connected():
        print("play_track: vc not connected, aborting play")
        return False

    vc.play(source, after=after_playing)

    return True


# ────────────────────────────────────────────
# SCHEDULER
# ────────────────────────────────────────────

async def schedule_next(vc, discord_user_id):
    await asyncio.sleep(1)

    if vc and vc.is_connected():
        started = await play_next_queued(vc)
        if started:
            return

        await play_random(vc, discord_user_id)


# ────────────────────────────────────────────
# QUEUE
# ────────────────────────────────────────────

async def enqueue_track(vc, query: str):

    state.queued_tracks.setdefault(vc.guild.id, [])

    if vc.is_playing() or vc.is_paused():
        queue = state.queued_tracks[vc.guild.id]
        queue.append(query)
        return True, False, len(queue)

    started = await play_track(vc, query)
    return started, started, 0


async def play_next_queued(vc) -> bool:

    await asyncio.sleep(0.5)

    if not vc or not vc.is_connected() or vc.is_playing() or vc.is_paused():
        return False

    queue = state.queued_tracks.get(vc.guild.id)

    if not queue:
        return False

    while queue:
        query = queue.pop(0)

        started = await play_track(vc, query)

        if started:
            return True

        try:
            await vc.channel.send(f"❌ Impossible de charger : **{query}**")
        except:
            pass

    return False


# ────────────────────────────────────────────
# PREVIOUS
# ────────────────────────────────────────────

async def play_previous(vc) -> bool:

    guild_id = vc.guild.id

    history = state.history.get(guild_id, [])
    index = state.history_index.get(guild_id, 0)

    if not history or index <= 0:
        return False

    state.history_index[guild_id] = index - 1
    previous_query = history[state.history_index[guild_id]]

    state.queued_tracks.setdefault(guild_id, []).clear()

    _safe_stop(vc)
    await asyncio.sleep(0.5)

    return await play_track_without_history(vc, previous_query)


async def play_track_without_history(vc, query: str) -> bool:

    extracted = await _extract_audio(query, vc)
    if not extracted:
        return False

    title, url = extracted
    state.current_title = title

    source = _create_source(url)

    def after_playing(error):
        if error:
            print("Playback error:", error)

        future = asyncio.run_coroutine_threadsafe(
            play_next_queued(vc),
            vc.loop
        )
        try:
            future.result()
        except Exception as e:
            print("Queue error:", e)

    _safe_stop(vc)

    if not vc.is_connected():
        print("play_track_without_history: vc not connected, aborting play")
        return False

    vc.play(source, after=after_playing)

    return True
