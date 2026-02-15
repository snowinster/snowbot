from collections import defaultdict, deque

last_song = None
current_title = None

queued_tracks = defaultdict(deque)
played_history = defaultdict(list)
current_query = {}
