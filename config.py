import os
import psycopg2


# ─────────────────────────────
# 🔐 DISCORD
# ─────────────────────────────

TOKEN = os.environ["DISCORD_TOKEN"]


# ─────────────────────────────
# 🌍 ENV MODE (DEV / PROD)
# ─────────────────────────────

ENV = os.getenv("ENV", "PROD")
DEV_GUILD_ID = os.getenv("DEV_GUILD_ID")

if ENV == "DEV":
    if not DEV_GUILD_ID:
        raise RuntimeError("DEV_GUILD_ID manquant en mode DEV")
    DEV_GUILD_ID = int(DEV_GUILD_ID)


# ─────────────────────────────
# 🗄️ DATABASE
# ─────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquant")

conn = psycopg2.connect(DATABASE_URL)
