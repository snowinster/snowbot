from collections import defaultdict, deque

last_song = None
current_title = None

queued_tracks = defaultdict(deque)

# Historique complet par serveur
history = defaultdict(list)

# Index courant dans l'historique
history_index = {}
