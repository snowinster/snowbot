FROM python:3.11-slim

# Installer ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Dossier de travail
WORKDIR /app

# Copier les fichiers
COPY . .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Lancer le bot
CMD ["python", "snowbot/snowbot.py"]