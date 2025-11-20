# Modifications pour le déploiement

Ce document liste toutes les modifications apportées au projet WhisperX-FastAPI pour le rendre compatible avec votre environnement.

## Environnement cible
- **GPU**: NVIDIA GeForce RTX 5070
- **Driver NVIDIA**: 570.144
- **CUDA Version**: 12.8

## Modifications apportées

### 1. Dockerfile (`dockerfile`)

#### Changement 1: Version CUDA
**Ligne 1 - Image de base**
```diff
- FROM nvidia/cuda:13.0.1-base-ubuntu22.04
+ FROM nvidia/cuda:12.8.0-base-ubuntu22.04
```
**Raison**: L'image originale utilisait CUDA 13.0.1, incompatible avec votre configuration CUDA 12.8.

#### Changement 2: Versions de packages
**Lignes 11-15 - Installation des dépendances système**
```diff
- python3.11=3.11.0~rc1-1~22.04
- ffmpeg=7:4.4.2-0ubuntu0.22.04.1
- libcudnn9-cuda-12=9.8.0.87-1
+ python3.11
+ python3-pip
+ ffmpeg
+ libcudnn9-cuda-12
```
**Raison**: Les versions exactes spécifiées peuvent ne pas être disponibles dans les dépôts. La suppression des versions permet d'installer les versions les plus récentes disponibles.

#### Changement 3: Installation des packages Python
**Lignes 36-37 - Installation avec uv**
```diff
- RUN uv sync --frozen --no-dev \
+ RUN uv pip install --system -e . \
      && uv pip install --system ctranslate2==4.6.0 \
```
**Raison**: `uv sync` installe les packages dans un environnement virtuel, mais l'ENTRYPOINT du Dockerfile exécute `gunicorn` directement. L'utilisation de `--system` installe les packages au niveau système, rendant `gunicorn` accessible dans le PATH.

### 2. Docker Compose (`docker-compose.yml`)

#### Changement: Nom du fichier Dockerfile
**Ligne 6**
```diff
- dockerfile: Dockerfile
+ dockerfile: dockerfile
```
**Raison**: Le fichier s'appelle `dockerfile` (minuscule) et non `Dockerfile` (majuscule).

### 3. Fichier d'environnement (`.env`)

**Nouveau fichier créé** avec les paramètres suivants:
```env
ENVIRONMENT=production
DEVICE=cuda
COMPUTE_TYPE=float16
WHISPER_MODEL=tiny
HF_TOKEN=hf_changeme
LOG_LEVEL=INFO
```

**Important**: Remplacez `HF_TOKEN=hf_changeme` par votre véritable token HuggingFace pour permettre le téléchargement des modèles.

## Résultat

L'image Docker a été construite avec succès:
- **Taille de l'image**: 7.7 GB
- **Port exposé**: 8000
- **État**: Fonctionnel

## Vérification du fonctionnement

Le service est accessible et répond correctement:

```bash
# Health check
curl http://localhost:8000/health
# {"status":"ok","message":"Service is running"}

# Readiness check
curl http://localhost:8000/health/ready
# {"status":"ok","database":"connected","message":"Application is ready to accept requests"}

# Documentation Swagger
# Accessible sur http://localhost:8000/docs
```

## Commandes pour déployer

```bash
# 1. Cloner le repository
git clone https://github.com/pavelzbornik/whisperX-FastAPI.git
cd whisperX-FastAPI

# 2. Appliquer les modifications listées ci-dessus

# 3. Créer le fichier .env avec votre token HuggingFace

# 4. Build et démarrer
docker compose build
docker compose up -d

# 5. Vérifier les logs
docker logs whisperx-container

# 6. Tester l'API
curl http://localhost:8000/health
```

## Notes supplémentaires

- Docker a été configuré pour accéder automatiquement aux cartes Nvidia (pas besoin de spécifier `--gpus all`)
- Le conteneur utilise Gunicorn avec un worker Uvicorn pour de meilleures performances en production
- La base de données SQLite est utilisée par défaut pour stocker les tâches
- Les modèles WhisperX sont téléchargés au premier usage et cachés dans `/root/.cache`
- Le docker-compose.yml monte `/data/whisperx/cache` pour persister les modèles entre les redémarrages

## Prochaines étapes pour EasyPanel

Pour déployer sur EasyPanel, vous devrez:
1. Créer un fork du repository
2. Appliquer ces modifications sur votre fork
3. Configurer les variables d'environnement dans EasyPanel (notamment `HF_TOKEN`)
4. S'assurer que les volumes sont correctement configurés pour le cache des modèles
