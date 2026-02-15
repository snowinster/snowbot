import discord
import music.state as state
from utils.help_text import HELP_MESSAGE


class MusicControls(discord.ui.View):

    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild

    def vc(self):
        return self.guild.voice_client

    # ─────────────── PAUSE ───────────────
    @discord.ui.button(label="Pause", emoji="⏸️")
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = self.vc()

        if not vc:
            await interaction.response.send_message("❄️ Pas connecté.", ephemeral=True)
            return

        if vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Pause", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Aucune musique en cours.", ephemeral=True)

    # ─────────────── RESUME ───────────────
    @discord.ui.button(label="Resume", emoji="▶️")
    async def resume(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = self.vc()

        if not vc:
            await interaction.response.send_message("❄️ Pas connecté.", ephemeral=True)
            return

        if vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Reprise", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Rien à reprendre.", ephemeral=True)

    # ─────────────── SKIP ───────────────
    @discord.ui.button(label="Skip", emoji="⏭️")
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = self.vc()

        if not vc:
            await interaction.response.send_message("❄️ Pas connecté.", ephemeral=True)
            return

        vc.stop()
        await interaction.response.send_message("⏭️ Skip", ephemeral=True)

    # ─────────────── PREVIOUS ───────────────
    @discord.ui.button(label="Previous", emoji="⏮️")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):

        from music.player import play_previous

        await interaction.response.defer(ephemeral=True)

        vc = self.vc()

        if not vc:
            await interaction.followup.send("❄️ Pas connecté.", ephemeral=True)
            return

        started = await play_previous(vc)

        if not started:
            await interaction.followup.send("⚠️ Aucun historique.", ephemeral=True)
            return

        await interaction.followup.send("⏮️ Musique précédente", ephemeral=True)

    # ─────────────── NOW PLAYING ───────────────

    @discord.ui.button(label="Now Playing", emoji="🎵")
    async def np(self, interaction: discord.Interaction, button: discord.ui.Button):

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

    # ─────────────── HELP ───────────────
    @discord.ui.button(label="Help", emoji="❓")
    async def help(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            HELP_MESSAGE,
            ephemeral=True
        )

    # ─────────────── LEAVE ───────────────
    @discord.ui.button(label="Leave", emoji="👋", style=discord.ButtonStyle.danger)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):

        vc = self.vc()

        if not vc:
            await interaction.response.send_message("❄️ Pas connecté.", ephemeral=True)
            return

        vc.stop()
        await vc.disconnect()
        await interaction.response.send_message("👋 Déconnecté", ephemeral=True)
