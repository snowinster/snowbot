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


# ─────────────────────────────
# 🗄️ DATABASE
# ─────────────────────────────

DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquant")

conn = psycopg2.connect(DATABASE_URL)
