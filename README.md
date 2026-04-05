# Stokk — Gestion de stock alimentaire

Application de gestion du stock alimentaire d'un foyer partagé. Scan de codes-barres, suivi des dates de péremption, gestion multi-utilisateurs.

---

## Stack

| Couche | Technologie |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2 (async), asyncpg |
| Base de données métier | PostgreSQL — utilisateurs, stock, DLC, emplacements |
| Base de données produits | MongoDB — dump OpenFoodFacts (lecture seule) |
| Frontend | Vue 3 + TypeScript + Vite |
| Gestionnaire de paquets (front) | npm |

---

## Structure du projet

```
foodtracker-poc/
├── docker-compose.yml             # Déploiement prod (NAS Synology)
├── .env.docker                    # Template de variables d'environnement pour le NAS
├── backend/
│   ├── main.py                    # App FastAPI, CORS, lifespan (init_db)
│   ├── requirements.txt
│   ├── .env                       # Config locale (non commité)
│   ├── .env.example               # Template
│   ├── seed.sql                   # Crée l'utilisateur admin par défaut
│   ├── migrate_locations.py       # Migration : table locations + FK location_id sur stock_items
│   ├── migrate_quantity.py        # Migration : colonne quantity_str sur products
│   ├── backfill_quantity.py       # Backfill quantity_str pour les produits déjà en cache
│   └── app/
│       ├── core/
│       │   ├── config.py          # pydantic-settings — lit .env
│       │   └── security.py        # JWT, get_current_user, get_current_admin
│       ├── db/
│       │   └── database.py        # AsyncSession, client MongoDB (Motor), init_db()
│       ├── models/
│       │   └── models.py          # Modèles ORM SQLAlchemy
│       ├── schemas/
│       │   └── schemas.py         # Schémas Pydantic requête/réponse
│       ├── services/
│       │   └── product_service.py # Lookup produit : cache PG → fallback MongoDB
│       └── routes/
│           ├── auth.py            # POST /auth/login → token JWT
│           ├── stock.py           # CRUD stock
│           ├── locations.py       # CRUD emplacements hiérarchiques
│           └── users.py           # CRUD utilisateurs (admin seulement)
└── frontend/
    ├── index.html
    ├── vite.config.ts
    ├── nginx.conf                 # Config nginx pour le container frontend (prod)
    ├── .env                       # VITE_API_URL
    └── src/
        ├── main.ts
        ├── App.vue                # Auth wrapper : LoginForm ou AppLayout
        ├── style.css              # Système de design global (vars CSS, thèmes clair/sombre)
        ├── router/index.ts        # 4 routes : /, /recipes, /settings, /users
        ├── types/index.ts         # Interfaces TypeScript miroir des schémas backend
        ├── composables/
        │   ├── useApi.ts          # Tous les appels fetch
        │   ├── useAuth.ts         # Ref utilisateur module-level, fetchMe(), helpers JWT
        │   ├── useTheme.ts        # Thème clair/sombre/système, persisté localStorage
        │   └── usePreferences.ts  # Préférences utilisateur (showImages…)
        ├── views/
        │   ├── StockView.vue      # Vue principale scan/stock
        │   ├── RecipesView.vue    # Placeholder
        │   ├── SettingsView.vue   # Thème + gestionnaire d'emplacements
        │   └── UsersView.vue      # Gestion utilisateurs (admin)
        └── components/
            ├── AppLayout.vue      # Sidebar (desktop) + onglets bas (mobile)
            ├── LoginForm.vue
            ├── ScanInput.vue      # Saisie code-barres (USB HID + Entrée clavier)
            ├── ProductCard.vue    # Info produit + badge source
            ├── AddStockForm.vue   # Ajout au stock : qté/unité pré-remplis
            ├── StockList.vue      # Liste stock : filtres, tri, suppression en masse
            ├── EditStockModal.vue # Modal édition
            ├── ExpiryDashboard.vue# Alertes de péremption
            └── NutriScore.vue     # Badge coloré A→E
```

---

## Développement local

### Prérequis

- **Python 3.13** avec `venv`
- **Node.js 20+** et `npm`
- **PostgreSQL 16** en local (ou via Docker)
- **MongoDB 7** en local avec le dump OpenFoodFacts importé

### Importer le dump OpenFoodFacts (une seule fois)

Le dump est disponible sur [le site OpenFoodFacts](https://world.openfoodfacts.org/data). Télécharger le fichier BSON (`openfoodfacts-mongodbdump.tar.gz`) puis :

```bash
tar -xzf openfoodfacts-mongodbdump.tar.gz
mongorestore --db openfoodfacts dump/off/products.bson
```

Le dump fait plusieurs Go et peut prendre du temps à importer.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
cp .env.example .env          # puis remplir les valeurs
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
# Créer frontend/.env avec :
# VITE_API_URL=http://localhost:8000/api/v1
npm run dev
```

- API : http://localhost:8000
- Swagger UI : http://localhost:8000/docs
- Frontend : http://localhost:5173

### Variables d'environnement — dev

**`backend/.env`**
```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/foodtracker
MONGO_URL=mongodb://localhost:27017
MONGO_DB=openfoodfacts
MONGO_COLLECTION=products
SECRET_KEY=changeme_generate_a_real_secret
CORS_ORIGINS=http://localhost:5173
```

**`frontend/.env`**
```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Déploiement NAS (Synology)

### Prérequis

1. **Docker** installé sur le NAS (via le gestionnaire de paquets Synology ou Container Manager)
2. **MongoDB avec le dump OpenFoodFacts déjà en place** — le projet suppose qu'un container MongoDB tourne séparément avec le dump importé, et expose le port `27017` sur l'IP du NAS. Exemple de compose pour ce container :

```yaml
services:
  mongodb:
    image: mongo:7
    container_name: openfoodfacts-mongo
    restart: unless-stopped
    ports:
      - "27017:27017"
    volumes:
      - /volume1/TorrentBox/docker/openfoodfacts/data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=openfoodfacts
    command: mongod --wiredTigerCacheSizeGB 2
```

3. **L'IP locale fixe du NAS** — à vérifier avec `hostname -I | awk '{print $1}'` dans le SSH du NAS

### Structure des fichiers sur le NAS

Créer le dossier de déploiement :

```bash
mkdir -p /volume1/TorrentBox/docker/stokk
```

Y placer les fichiers suivants depuis le repo :
- `docker-compose.yml`
- `frontend/nginx.conf` → copier vers `/volume1/TorrentBox/docker/stokk/nginx.conf`

### Certificat SSL (requis pour l'accès caméra)

Le frontend tourne en HTTPS — obligatoire pour que `getUserMedia()` (scan caméra) fonctionne dans le navigateur. Générer un certificat auto-signé :

```bash
mkdir -p /volume1/TorrentBox/docker/stokk/ssl
openssl req -x509 -newkey rsa:4096 -keyout /volume1/TorrentBox/docker/stokk/ssl/key.pem \
  -out /volume1/TorrentBox/docker/stokk/ssl/cert.pem -days 3650 -nodes \
  -subj "/CN=NAS_IP" \
  -addext "subjectAltName=IP:NAS_IP"
```

Remplacer `NAS_IP` par l'IP du NAS (ex: `192.168.1.100`).

> Le certificat auto-signé déclenchera un avertissement dans le navigateur. Accepter l'exception de sécurité une fois — ensuite l'appli fonctionne normalement.

### Fichier `.env`

Créer `/volume1/TorrentBox/docker/stokk/.env` :

```bash
cat > /volume1/TorrentBox/docker/stokk/.env << 'EOF'
# Obligatoire — générer avec : python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=remplace_par_une_vraie_cle

# Mot de passe PostgreSQL (libre choix)
POSTGRES_PASSWORD=un_mot_de_passe_solide

# MongoDB — pointer vers l'IP du NAS (pas localhost, le backend est dans un container)
MONGO_URL=mongodb://192.168.1.XXX:27017
MONGO_DB=openfoodfacts
MONGO_COLLECTION=products

# CORS — URL d'accès au frontend depuis le navigateur
CORS_ORIGINS=https://192.168.1.XXX:9300
EOF
```

> **Pourquoi l'IP du NAS et pas `localhost` ?**
> Le backend tourne dans un container Docker. `localhost` dans un container pointe vers le container lui-même, pas vers le NAS hôte. Il faut donc utiliser l'IP locale du NAS pour atteindre le MongoDB qui tourne sur l'hôte.

### Lancement

```bash
cd /volume1/TorrentBox/docker/stokk
sudo docker compose up -d
```

L'application est accessible sur `https://IP_DU_NAS:9300`.

### Migrations (premier démarrage)

Après le premier `docker compose up`, exécuter les migrations dans l'ordre :

```bash
sudo docker exec stokk-backend python migrate_locations.py
sudo docker exec stokk-backend python migrate_quantity.py
sudo docker exec stokk-backend python backfill_quantity.py  # optionnel
```

### Mise à jour

```bash
cd /volume1/TorrentBox/docker/stokk
sudo docker compose pull
sudo docker compose up -d
```

---

## Base de données

### Tables PostgreSQL

| Table | Rôle |
|---|---|
| `users` | Utilisateurs, mots de passe bcrypt, flag `is_admin` |
| `products` | Cache local des données OpenFoodFacts (PK = code-barres EAN) |
| `locations` | Emplacements de rangement hiérarchiques (FK auto-référentielle `parent_id`) |
| `stock_items` | Articles en stock, FK → products + locations |
| `expiry_dates` | Une DLC optionnelle par article (1-à-0..1) |

Toutes les colonnes PK/FK utilisent le type natif PostgreSQL `UUID`. **Ne pas utiliser VARCHAR pour les UUID** — asyncpg impose une correspondance stricte des types.

Les tables sont créées automatiquement au démarrage via `init_db()` (SQLAlchemy `create_all`).

### Logique de cache produit (`product_service.py`)

1. Chercher dans la table `products` (PostgreSQL) → retour immédiat si trouvé
2. Interroger MongoDB par code-barres si pas en cache
3. Sauvegarder dans `products` via `INSERT ... ON CONFLICT DO NOTHING`
4. Retourner le produit avec un tag source (`"cache"` ou `"openfoodfacts"`)

Le champ `quantity_str` (ex: `"330 ml"`, `"500 g"`) est extrait de MongoDB et parsé côté frontend pour pré-remplir quantité/unité dans le formulaire d'ajout.

---

## Endpoints API

### Auth
| Méthode | Route | Description |
|---|---|---|
| POST | `/api/v1/auth/login` | form-data username/password → token JWT |

### Stock
| Méthode | Route | Description |
|---|---|---|
| GET | `/api/v1/scan/{barcode}` | Lookup produit (cache PG → MongoDB) |
| POST | `/api/v1/stock` | Ajouter un article au stock |
| GET | `/api/v1/stock` | Lister tout le stock |
| PATCH | `/api/v1/stock/{item_id}` | Mise à jour partielle (qté, unité, emplacement, DLC…) |
| DELETE | `/api/v1/stock/{item_id}` | Supprimer un article (204 No Content) |

### Emplacements
| Méthode | Route | Description |
|---|---|---|
| GET | `/api/v1/locations` | Lister tous les emplacements |
| POST | `/api/v1/locations` | Créer un emplacement (parent_id optionnel) |
| PATCH | `/api/v1/locations/{loc_id}` | Renommer / recolorer |
| DELETE | `/api/v1/locations/{loc_id}` | Supprimer (les enfants passent à la racine) |

### Utilisateurs (admin seulement)
| Méthode | Route | Description |
|---|---|---|
| GET | `/api/v1/users` | Lister les utilisateurs |
| POST | `/api/v1/users` | Créer un utilisateur |
| PATCH | `/api/v1/users/{id}` | Modifier mot de passe / flag admin |
| DELETE | `/api/v1/users/{id}` | Supprimer (impossible de se supprimer soi-même) |

Tous les endpoints sauf `/auth/login` nécessitent `Authorization: Bearer <token>`.

---

## Problèmes connus / TODOs

- Pas de pagination sur la liste de stock
- Pas de tests unitaires
- MongoDB accédé de manière synchrone (pymongo) dans les scripts de migration — Motor utilisé dans l'app principale
- Pas de notifications push pour les alertes de péremption (le flag `alerted` existe en BDD mais rien ne le lit)
- Les produits déjà en cache ne verront pas `quantity_str` mis à jour (`ON CONFLICT DO NOTHING`) — relancer `backfill_quantity.py` manuellement si nécessaire
- `image_url` depuis OpenFoodFacts est souvent `None` — emoji de remplacement affiché (masquable via la préférence `showImages`)
