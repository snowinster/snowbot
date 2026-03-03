FROM python:3.11-slim

# Dépendances système : ffmpeg + tout ce qu'il faut pour compiler PyNaCl
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsodium-dev \
    libffi-dev \
    gcc \
    g++ \
    make \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Dossier de travail
WORKDIR /app

# Installer PyNaCl en premier, séparément, pour détecter toute erreur
RUN pip install --no-cache-dir PyNaCl

# Copier et installer le reste des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Vérification que PyNaCl est bien disponible
RUN python -c "import nacl; print('✅ PyNaCl OK')"

# Copier le reste des fichiers
COPY . .

# Lancer le bot
CMD ["python", "snowbot.py"]