FROM python:3.11-slim

# Installer ffmpeg + dépendances de compilation pour PyNaCl (libsodium)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsodium-dev \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Dossier de travail
WORKDIR /app

# Copier les fichiers
COPY . .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Lancer le bot
CMD ["python", "snowbot.py"]