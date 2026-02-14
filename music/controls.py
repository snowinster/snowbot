import discord
from music.state import current_title
from utils.help_text import HELP_MESSAGE


class MusicControls(discord.ui.View):
    def __init__(self, guild):
        super().__init__(timeout=None)
        self.guild = guild

    def vc(self):
        return self.guild.voice_client

    @discord.ui.button(label="Pause", emoji="⏸️")
    async def pause(self, interaction, _):
        if self.vc() and self.vc().is_playing():
            self.vc().pause()
            await interaction.response.send_message("⏸️ Pause", ephemeral=True)

    @discord.ui.button(label="Resume", emoji="▶️")
    async def resume(self, interaction, _):
        if self.vc() and self.vc().is_paused():
            self.vc().resume()
            await interaction.response.send_message("▶️ Reprise", ephemeral=True)

    @discord.ui.button(label="Skip", emoji="⏭️")
    async def skip(self, interaction, _):
        if self.vc():
            self.vc().stop()
            await interaction.response.send_message("⏭️ Skip", ephemeral=True)

    @discord.ui.button(label="Now Playing", emoji="🎵")
    async def np(self, interaction, _):
        if current_title:
            await interaction.response.send_message(
                f"🎶 **En cours :** {current_title}",
                ephemeral=True
            )

    @discord.ui.button(label="Help", emoji="❓")
    async def help(self, interaction, _):
        await interaction.response.send_message(
            HELP_MESSAGE,
            ephemeral=True
        )

    @discord.ui.button(label="Leave", emoji="👋", style=discord.ButtonStyle.danger)
    async def leave(self, interaction, _):
        if self.vc():
            self.vc().stop()
            await self.vc().disconnect()
            await interaction.response.send_message("👋 Déconnecté", ephemeral=True)
