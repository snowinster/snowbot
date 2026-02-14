import discord

from config import TOKEN
from db.playlist import add_track, remove_track, get_user_playlist
from music.player import play_random
from music.controls import MusicControls
from music.state import current_title
from utils.help_text import HELP_MESSAGE


intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True

client = discord.Client(intents=intents)


@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.strip()
    vc = message.guild.voice_client
    user_id = message.author.id

    if content == "!help":
        await message.channel.send(HELP_MESSAGE)

    elif content == "!playlist":
        if not message.author.voice:
            await message.channel.send("❌ Tu dois être en vocal")
            return

        channel = message.author.voice.channel
        if not vc:
            vc = await channel.connect()
        elif vc.channel != channel:
            await vc.move_to(channel)

        if not vc.is_playing():
            await play_random(vc, user_id)

        await message.channel.send(
            "🎶 **SnowBot Controls**",
            view=MusicControls(message.guild)
        )

    elif content.startswith("!add "):
        track = content[5:].strip()
        add_track(user_id, track)
        await message.channel.send(f"✅ Ajouté : **{track}**")

    elif content.startswith("!remove "):
        track = content[8:].strip()
        deleted = remove_track(user_id, track)
        msg = "🗑️ Supprimé." if deleted else "⚠️ Pas trouvé."
        await message.channel.send(msg)

    elif content == "!list":
        playlist = get_user_playlist(user_id)
        if not playlist:
            await message.channel.send("📭 Playlist vide.")
            return

        await message.channel.send(
            "**🎵 Ta playlist :**\n" +
            "\n".join(f"{i+1}. {t}" for i, t in enumerate(playlist))
        )

    elif content == "!np" and current_title:
        await message.channel.send(f"🎶 **En cours :** {current_title}")

    elif content == "!pause":
        if vc and vc.is_playing():
            vc.pause()
            await message.channel.send("⏸️ Pause")
        else:
            await message.channel.send("❄️ Aucune musique en cours.")

    elif content == "!resume":
        if vc and vc.is_paused():
            vc.resume()
            await message.channel.send("▶️ Reprise")
        else:
            await message.channel.send("❄️ Rien à reprendre.")

    elif content == "!skip":
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await message.channel.send("⏭️ Skip")
        else:
            await message.channel.send("❄️ Aucune musique en cours.")

    elif content == "!leave" and vc:
        vc.stop()
        await vc.disconnect()


@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")


client.run(TOKEN)
