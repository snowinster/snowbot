from config import conn


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
