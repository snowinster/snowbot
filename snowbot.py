import discord
import yt_dlp
import asyncio
import random
import os
import psycopg2

# ─────────────── CONFIG ───────────────
TOKEN = os.environ["DISCORD_TOKEN"]
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquant dans l'environnement")

conn = psycopg2.connect(DATABASE_URL)

# ─────────────── INTENTS ───────────────
intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

client = discord.Client(intents=intents)

last_song = None
current_title = None

# ─────────────── HELP TEXT ───────────────
HELP_MESSAGE = (
    "🎶 **SnowBot – Aide & commandes**\n\n"
    "▶️ **Musique**\n"
    "• `!play <nom ou lien>` → Joue une musique\n"
    "• `!playlist` → Lance ta playlist personnelle (aléatoire)\n"
    "• `!np` → Affiche la musique en cours\n"
    "• `!pause` → Met la musique en pause\n"
    "• `!resume` → Reprend la musique\n"
    "• `!skip` → Passe à la musique suivante\n"
    "• `!leave` → Déconnecte le bot du vocal\n\n"
    "📚 **Playlist**\n"
    "• `!add <nom>` → Ajoute une musique à ta playlist\n"
    "• `!remove <nom>` → Supprime une musique de ta playlist\n"
    "• `!list` → Affiche ta playlist personnelle\n\n"
    "ℹ️ Astuce : chaque utilisateur a **sa propre playlist**."
)

# ─────────────── DB HELPERS ───────────────


def get_user_playlist(discord_user_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT musique
            FROM "Playlist"
            WHERE discord_user_id = %s
            ORDER BY id
            """,
            (discord_user_id,)
        )
        rows = cur.fetchall()
    return [r[0] for r in rows]


def add_track(discord_user_id, track):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO "Playlist" (discord_user_id, musique)
            VALUES (%s, %s)
            """,
            (discord_user_id, track)
        )
        conn.commit()


def remove_track(discord_user_id, track):
    with conn.cursor() as cur:
        cur.execute(
            """
            DELETE FROM "Playlist"
            WHERE discord_user_id = %s
              AND musique = %s
            """,
            (discord_user_id, track)
        )
        deleted = cur.rowcount
        conn.commit()
    return deleted


# ─────────────── YTDL (non-bloquant) ───────────────
YDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
    "default_search": "ytsearch",
}


async def ytdl_extract(query: str):
    """
    Exécute yt-dlp dans un thread pour ne pas bloquer Discord.
    Retourne (url, title).
    """
    loop = asyncio.get_running_loop()

    def _extract():
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            info = ydl.extract_info(query, download=False)
            if not info:
                return None
            if "entries" in info:
                if not info["entries"]:
                    return None
                info = info["entries"][0]
            return info.get("url"), info.get("title")

    return await loop.run_in_executor(None, _extract)


# ─────────────── VOICE HELPERS ───────────────
async def ensure_voice(message: discord.Message):
    """
    Join automatiquement le vocal de l'utilisateur (si possible) et retourne le voice_client.
    """
    if not message.author.voice or not message.author.voice.channel:
        await message.channel.send("❌ Tu dois être en vocal")
        return None

    vc = message.guild.voice_client
    channel = message.author.voice.channel

    if not vc:
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)

    return vc


# ─────────────── MUSIQUE ───────────────
async def play_random(vc, discord_user_id, text_channel: discord.abc.Messageable):
    global last_song, current_title

    playlist = get_user_playlist(discord_user_id)
    if not playlist:
        await text_channel.send("📭 Ta playlist est vide.")
        return

    choices = [s for s in playlist if s != last_song]
    song = random.choice(choices if choices else playlist)
    last_song = song

    extracted = await ytdl_extract(song)
    if not extracted:
        await text_channel.send("⚠️ Impossible de trouver cette musique (playlist).")
        return

    url, title = extracted
    current_title = title

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(
            url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        ),
        volume=0.7
    )

    def after_playing(_):
        client.loop.call_soon_threadsafe(
            asyncio.create_task,
            schedule_next(vc, discord_user_id, text_channel)
        )

    if vc.is_playing() or vc.is_paused():
        vc.stop()

    vc.play(source, after=after_playing)
    print(f"🎶 Lecture : {current_title}")


async def play_one_track(vc, query, discord_user_id, text_channel: discord.abc.Messageable):
    global current_title

    extracted = await ytdl_extract(query)
    if not extracted:
        await text_channel.send("⚠️ Je ne trouve pas ce titre / lien.")
        return

    url, title = extracted
    current_title = title

    source = discord.PCMVolumeTransformer(
        discord.FFmpegPCMAudio(
            url,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            options="-vn"
        ),
        volume=0.7
    )

    def after_playing(_):
        # Après le morceau demandé → on revient à la playlist perso
        client.loop.call_soon_threadsafe(
            asyncio.create_task,
            schedule_next(vc, discord_user_id, text_channel)
        )

    if vc.is_playing() or vc.is_paused():
        vc.stop()

    vc.play(source, after=after_playing)
    await text_channel.send(f"🎧 **Lecture :** {current_title}")
    print(f"🎧 Lecture manuelle : {current_title}")


async def schedule_next(vc, discord_user_id, text_channel: discord.abc.Messageable):
    await asyncio.sleep(1)
    if vc.is_connected():
        await play_random(vc, discord_user_id, text_channel)


# ─────────────── AUTO-LEAVE ───────────────
async def auto_leave(vc):
    await asyncio.sleep(30)
    if vc.is_connected():
        humans = [m for m in vc.channel.members if not m.bot]
        if not humans:
            await vc.disconnect()


@client.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    vc = member.guild.voice_client
    if vc and vc.channel:
        humans = [m for m in vc.channel.members if not m.bot]
        if not humans:
            client.loop.create_task(auto_leave(vc))


# ─────────────── BOUTONS ───────────────
class MusicControls(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild

    def vc(self):
        return self.guild.voice_client

    @discord.ui.button(label="Pause", emoji="⏸️", style=discord.ButtonStyle.secondary)
    async def pause(self, interaction, _):
        if self.vc() and self.vc().is_playing():
            self.vc().pause()
            await interaction.response.send_message("⏸️ Pause", ephemeral=True)

    @discord.ui.button(label="Resume", emoji="▶️", style=discord.ButtonStyle.success)
    async def resume(self, interaction, _):
        if self.vc() and self.vc().is_paused():
            self.vc().resume()
            await interaction.response.send_message("▶️ Reprise", ephemeral=True)

    @discord.ui.button(label="Skip", emoji="⏭️", style=discord.ButtonStyle.primary)
    async def skip(self, interaction, _):
        if self.vc() and (self.vc().is_playing() or self.vc().is_paused()):
            self.vc().stop()
            await interaction.response.send_message("⏭️ Skip", ephemeral=True)

    @discord.ui.button(label="Now Playing", emoji="🎵", style=discord.ButtonStyle.secondary)
    async def np(self, interaction, _):
        if current_title:
            await interaction.response.send_message(f"🎶 **En cours :** {current_title}", ephemeral=True)
        else:
            await interaction.response.send_message("😴 Rien en cours.", ephemeral=True)

    @discord.ui.button(label="Help", emoji="❓", style=discord.ButtonStyle.secondary)
    async def help(self, interaction, _):
        await interaction.response.send_message(HELP_MESSAGE, ephemeral=True)

    @discord.ui.button(label="Leave", emoji="👋", style=discord.ButtonStyle.danger)
    async def leave(self, interaction, _):
        if self.vc():
            self.vc().stop()
            await self.vc().disconnect()
            await interaction.response.send_message("👋 Déconnecté", ephemeral=True)


# ─────────────── COMMANDES ───────────────
@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()
    vc = message.guild.voice_client
    user_id = message.author.id

    if content == "!help":
        await message.channel.send(HELP_MESSAGE)
        return

    if content.startswith("!play "):
        query = content[6:].strip()
        if not query:
            await message.channel.send("❌ Exemple: `!play linkin park numb` ou `!play <lien>`")
            return

        vc = await ensure_voice(message)
        if not vc:
            return

        await play_one_track(vc, query, user_id, message.channel)
        return

    if content == "!playlist":
        vc = await ensure_voice(message)
        if not vc:
            return

        if not vc.is_playing() and not vc.is_paused():
            await play_random(vc, user_id, message.channel)

        await message.channel.send("🎶 **SnowBot Controls**", view=MusicControls(message.guild))
        return

    if content.startswith("!add "):
        track = content[5:].strip()
        if not track:
            await message.channel.send("❌ Exemple: `!add you say run`")
            return
        add_track(user_id, track)
        await message.channel.send(f"✅ Ajouté : **{track}**")
        return

    if content == "!list":
        playlist = get_user_playlist(user_id)
        if not playlist:
            await message.channel.send("📭 Ta playlist est vide.")
            return

        msg = "**🎵 Ta playlist :**\n"
        for i, track in enumerate(playlist, start=1):
            msg += f"{i}. {track}\n"
        await message.channel.send(msg)
        return

    if content.startswith("!remove "):
        track = content[8:].strip()
        if not track:
            await message.channel.send("❌ Exemple: `!remove you say run`")
            return

        deleted = remove_track(user_id, track)
        if deleted == 0:
            await message.channel.send(f"⚠️ **{track}** n'est pas dans ta playlist.")
        else:
            await message.channel.send(f"🗑️ **{track}** supprimé.")
        return

    # Contrôles texte
    if content == "!skip" and vc:
        vc.stop()
    elif content == "!pause" and vc:
        vc.pause()
    elif content == "!resume" and vc:
        vc.resume()
    elif content == "!np":
        if current_title:
            await message.channel.send(f"🎶 **En cours :** {current_title}")
        else:
            await message.channel.send("😴 Rien en cours.")
    elif content == "!leave" and vc:
        vc.stop()
        await vc.disconnect()


# ─────────────── READY ───────────────
@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")


client.run(TOKEN)
