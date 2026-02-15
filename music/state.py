from collections import defaultdict, deque

last_song = None
current_title = None

# Queue des demandes /play par serveur Discord (guild_id -> deque[str])
queued_tracks = defaultdict(deque)
