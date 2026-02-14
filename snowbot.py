import discord
import music.state as state

from config import TOKEN
from db.playlist import add_track, remove_track, get_user_playlist
from music.player import play_random
from music.controls import MusicControls
from utils.help_text import HELP_MESSAGE


intents = discord.Intents.default()
intents.voice_states = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)


# ─────────────────────────────
# 🎶 /playlist
# ─────────────────────────────
@tree.command(name="playlist", description="Lance ta playlist personnelle")
async def playlist(interaction: discord.Interaction):

    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ Tu dois être en vocal.",
            ephemeral=True
        )
        return

    channel = interaction.user.voice.channel
    vc = interaction.guild.voice_client

    if not vc:
        vc = await channel.connect()
    elif vc.channel != channel:
        await vc.move_to(channel)

    if not vc.is_playing():
        await play_random(vc, interaction.user.id)

    await interaction.response.send_message(
        "🎶 **SnowBot Controls**",
        view=MusicControls(interaction.guild)
    )


# ─────────────────────────────
# ➕ /add
# ─────────────────────────────
@tree.command(name="add", description="Ajoute une musique à ta playlist")
async def add(interaction: discord.Interaction, track: str):

    add_track(interaction.user.id, track)

    await interaction.response.send_message(
        f"✅ Ajouté : **{track}**",
        ephemeral=True
    )


# ─────────────────────────────
# ➖ /remove
# ─────────────────────────────
@tree.command(name="remove", description="Supprime une musique de ta playlist")
async def remove(interaction: discord.Interaction, track: str):

    deleted = remove_track(interaction.user.id, track)
    msg = "🗑️ Supprimé." if deleted else "⚠️ Pas trouvé."

    await interaction.response.send_message(msg, ephemeral=True)


# ─────────────────────────────
# 📜 /list
# ─────────────────────────────
@tree.command(name="list", description="Affiche ta playlist")
async def list_playlist(interaction: discord.Interaction):

    playlist = get_user_playlist(interaction.user.id)

    if not playlist:
        await interaction.response.send_message(
            "📭 Playlist vide.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        "**🎵 Ta playlist :**\n" +
        "\n".join(f"{i+1}. {t}" for i, t in enumerate(playlist)),
        ephemeral=True
    )


# ─────────────────────────────
# 🎵 /np
# ─────────────────────────────
@tree.command(name="np", description="Musique en cours")
async def now_playing(interaction: discord.Interaction):

    if state.current_title:
        await interaction.response.send_message(
            f"🎶 **En cours :** {state.current_title}",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❄️ Aucune musique en cours.",
            ephemeral=True
        )


# ─────────────────────────────
# ⏸️ /pause
# ─────────────────────────────
@tree.command(name="pause", description="Met la musique en pause")
async def pause(interaction: discord.Interaction):

    vc = interaction.guild.voice_client

    if vc and vc.is_playing():
        vc.pause()
        await interaction.response.send_message("⏸️ Pause")
    else:
        await interaction.response.send_message(
            "❄️ Aucune musique en cours.",
            ephemeral=True
        )


# ─────────────────────────────
# ▶️ /resume
# ─────────────────────────────
@tree.command(name="resume", description="Reprend la musique")
async def resume(interaction: discord.Interaction):

    vc = interaction.guild.voice_client

    if vc and vc.is_paused():
        vc.resume()
        await interaction.response.send_message("▶️ Reprise")
    else:
        await interaction.response.send_message(
            "❄️ Rien à reprendre.",
            ephemeral=True
        )


# ─────────────────────────────
# ⏭️ /skip
# ─────────────────────────────
@tree.command(name="skip", description="Passe à la musique suivante")
async def skip(interaction: discord.Interaction):

    vc = interaction.guild.voice_client

    if vc and (vc.is_playing() or vc.is_paused()):
        vc.stop()
        await interaction.response.send_message("⏭️ Skip")
    else:
        await interaction.response.send_message(
            "❄️ Aucune musique en cours.",
            ephemeral=True
        )


# ─────────────────────────────
# 👋 /leave
# ─────────────────────────────
@tree.command(name="leave", description="Déconnecte le bot du vocal")
async def leave(interaction: discord.Interaction):

    vc = interaction.guild.voice_client

    if vc:
        vc.stop()
        await vc.disconnect()
        await interaction.response.send_message("👋 Déconnecté.")
    else:
        await interaction.response.send_message(
            "❄️ Pas connecté.",
            ephemeral=True
        )


# ─────────────────────────────
# ❓ /help
# ─────────────────────────────
@tree.command(name="help", description="Affiche l'aide")
async def help_command(interaction: discord.Interaction):

    await interaction.response.send_message(
        HELP_MESSAGE,
        ephemeral=True
    )


@client.event
async def on_ready():
    await tree.sync()
    print(f"Connecté en tant que {client.user}")

client.run(TOKEN)
