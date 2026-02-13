import discord
import yt_dlp
import asyncio
import random
import os

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_NAME = "Poto-gang"

PLAYLIST = [
    "you say run",
    "Departure",
    "black clover Opening 10",
    "Heavy is the crown avec linkin park",
    "Mashle: magic and muscles The divine visionary cadidate exam arc",
    "Overlord clattanoia",
    "Tanya the evil JINGO JUNGLE",
    "Inflation my hero academia",
    "Akiaura Sleepwalker",
    "We'll put a stop to them for sure my hero academia",
    "The demon lord my hero academia",
    "Undertale CORE",
    "Undertale Megalovania",
    "Overlord HYDRA",
    "Overlord HOLLOW HUNGER",
    "Death note opening",
    "Snk opening",
    "Snk you see big girl",
    "Donne moi ton cœur Louane",
    "Fly By blue",
    "STYX HELIX",
    "Infinite Power the fatrat",
    "Got well soon breton",
    "All rise blue",
    "Save your tears the week-end",
    "I kissed a girl Katy Perry",
    "I love it Katy perry",
    "Sing Ed sheeran",
    "Vagrant feint veela",
    "Survival league voicians",
    "Shake your coconuts junior senior",
    "Nightcall kavinsky",
    "Place je passe mozart opéra rock",
    "Bloody stream coda",
    "Death note ost",
    "Little dark age mgmt",
    "Take me out Franz ferdinand",
    "FEEL SOMETHING DIFFERENT bea miller",
    "Animals maroon 5",
    "Theater D myth and roid",
    "Happy doja cat",
    "bleach number one"
]

# ─────────────── INTENTS ───────────────
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

client = discord.Client(intents=intents)

last_song = None
current_title = None


# ─────────────── MUSIQUE ───────────────
async def play_random(voice_client):
    global last_song, current_title

    choices = [s for s in PLAYLIST if s != last_song]
    song = random.choice(choices)
    last_song = song

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,   # ⬅️ AJOUT ICI
        "noplaylist": True,
        "default_search": "ytsearch"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(song, download=False)
        if "entries" in info:
            info = info["entries"][0]

        url = info["url"]
        current_title = info["title"]

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(
            url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        ),
        volume=0.7
    )

    def after_playing(error):
        if error:
            print(f"❌ Erreur audio : {error}")

        client.loop.call_soon_threadsafe(
            asyncio.create_task,
            schedule_next(voice_client)
        )

    voice_client.play(source, after=after_playing)
    print(f"🎶 Lecture : {current_title}")


async def schedule_next(voice_client):
    await asyncio.sleep(1)

    if not voice_client.is_connected():
        return

    await play_random(voice_client)


# ─────────────── UTILITAIRE ───────────────
async def join_and_play(guild, author):
    if not author.voice:
        return None, "❌ Tu dois être dans un salon vocal"

    channel = author.voice.channel
    vc = guild.voice_client

    if not vc:
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)

    if not vc.is_playing() and not vc.is_paused():
        await play_random(vc)
        return vc, "▶️ Playlist lancée"
    else:
        return vc, "ℹ️ La musique est déjà en cours"


# ─────────────── EVENTS ───────────────
@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")


@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    vc = message.guild.voice_client

    # ───── PLAYLIST ─────
    if content == "!playlist":
        vc, msg = await join_and_play(message.guild, message.author)
        await message.channel.send(msg)

    # ───── SKIP ─────
    elif content == "!skip":
        if vc and vc.is_playing():
            vc.stop()
            await message.channel.send("⏭️ Musique suivante")
        else:
            await message.channel.send("❌ Aucune musique en cours")

    # ───── PAUSE ─────
    elif content == "!pause":
        if vc and vc.is_playing():
            vc.pause()
            await message.channel.send("⏸️ Musique en pause")
        else:
            await message.channel.send("❌ Rien à mettre en pause")

    # ───── RESUME ─────
    elif content == "!resume":
        if vc and vc.is_paused():
            vc.resume()
            await message.channel.send("▶️ Reprise de la musique")
        else:
            await message.channel.send("❌ La musique n'est pas en pause")

    # ───── NOW PLAYING ─────
    elif content == "!np":
        if vc and (vc.is_playing() or vc.is_paused()):
            await message.channel.send(f"🎶 **En cours :** {current_title}")
        else:
            await message.channel.send("❌ Aucune musique en cours")

    # ───── LEAVE ─────
    elif content == "!leave":
        if vc:
            if vc.is_playing() or vc.is_paused():
                vc.stop()
            await vc.disconnect()
            await message.channel.send("👋 Bot déconnecté du salon vocal")
        else:
            await message.channel.send("❌ Le bot n'est pas connecté")


# ─────────────── RUN ───────────────
client.run(TOKEN)
