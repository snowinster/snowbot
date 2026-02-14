import os
import psycopg2

TOKEN = os.environ["DISCORD_TOKEN"]
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL manquant dans l'environnement")

conn = psycopg2.connect(DATABASE_URL)
