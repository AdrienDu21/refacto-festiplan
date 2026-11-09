# FestiPlan

API FastAPI de gestion d'un festival metal fictif (festivals, artistes, scènes, concerts, planning, publication, incidents), refactorisée en architecture hexagonale avec les concepts DDD pertinents. Les données sont fictives.

## Architecture
```
app/
  domain/        cœur métier (objets-valeurs, entités, politique de programmation, événements, erreurs)
  application/   cas d'usage et ports (contrats des repositories et de la notification)
  adapters/
    inbound/http/            routes FastAPI, schémas Pydantic, traduction des erreurs en HTTP
    outbound/persistence/    repositories SQLAlchemy, modèles ORM
    outbound/notification/   notification par (faux) email
  composition.py             assemblage des dépendances
```
Règle : `domain` n'importe rien, `application` n'importe que `domain`, les adaptateurs importent `application` et `domain`.

Documentation détaillée dans [docs/livrable.md](docs/livrable.md) : défauts reproduits, diagnostic, modèle de domaine, diagramme de composants, diagramme de séquence, note d'architecture. Sources UML dans [docs/diagrams/](docs/diagrams/).

## Installation (Python 3.11+)
```bash
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1 ; macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```
Copier `.env.example` vers `.env` si nécessaire.

## Initialisation de la base
```bash
python -m app.seed
```
Charge le festival **Hellforge Open Air** (18 au 20 juin 2027), 4 scènes (Mainstage, Warzone, Valley, Temple), 12 artistes et 14 concerts. Attention : cette commande **efface** les données de la base configurée. SQLite crée `festiplan.db` dans le dossier courant.

## Lancement
```bash
uvicorn app.main:app --reload
```
Documentation interactive : http://127.0.0.1:8000/docs

## Tests
```bash
pytest
```
| Dossier | Contenu |
|---|---|
| `tests/domain/` | Règles métier, sans FastAPI ni base de données |
| `tests/application/` | Cas d'usage avec repositories en mémoire et notifier factice |
| `tests/adapters/` | Repositories SQL (SQLite en mémoire) et notification |
| `tests/test_api_endpoints.py` et autres `tests/test_*_api.py` | Routes HTTP de bout en bout |
| `tests/test_regression.py` | Les 3 défauts initiaux |

Exemples : `pytest tests/domain`, `pytest tests/test_regression.py -v`.

## Endpoints principaux
| Méthode | Route | Rôle |
|---|---|---|
| POST | `/festivals/{id}/publish` | Publier le planning (vérifie les règles de programmation) |
| POST | `/festivals/{id}/unpublish` | Repasser le planning en préparation pour pouvoir le modifier |
| POST | `/concerts` | Programmer un concert |
| PATCH | `/concerts/{id}/reschedule` | Déplacer un concert |
| POST | `/concerts/{id}/cancel` | Annuler un concert |
| GET | `/concerts/schedule/{festival_id}` | Planning chronologique |
| POST | `/incidents` | Déclarer un incident |

Les autres routes (festivals, artistes, scènes, lecture des concerts et incidents) sont visibles dans Swagger.

## Règles métier et codes HTTP
- Règles de programmation violées (chevauchement de scène ou d'artiste, équipement manquant, hors période, créneau invalide) : **400**.
- Planning publié, ou concert annulé, pour une opération de modification : **409**. Pour modifier un planning publié, appeler `unpublish`, modifier, puis `publish`.
- Ressource introuvable : **404**.
- Si l'envoi d'une notification échoue après une modification, la modification reste valide et l'API répond normalement. L'échec est journalisé.

## Configuration
Variables d'environnement préfixées `FESTIPLAN_` (voir `.env.example`) :
- `FESTIPLAN_DATABASE_URL` : base de données (défaut `sqlite:///./festiplan.db`).
- `FESTIPLAN_FAIL_NOTIFICATIONS=true` : simule une panne du service de notification.

## Scénarios corrigés (défauts initiaux)
1. Déplacer un concert sur un créneau occupé (même scène ou même artiste ailleurs) est refusé.
2. Avec `FESTIPLAN_FAIL_NOTIFICATIONS=true`, un déplacement valide répond 200 et reste enregistré.
3. Après publication du planning, déplacer un concert répond 409.
