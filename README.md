# Three

Three est un outil de simulation généraliste (Flask + SQL) pour explorer les liens entre économie et écosystèmes.

## Fonctionnalités implémentées

- Affichage du prix moyen 2025 des objets.
- Navigation des objets économiques (filtres + tri).
- Recherche de l’origine d’un objet.
- Exécution de requêtes SQL `SELECT` (sandbox simple côté serveur).
- Simulation de propagation de variation de prix via des liaisons pondérées.
- Inspection du schéma SQL (tables + colonnes + aperçu des données).

## Lancer le projet

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Puis ouvrir: `http://127.0.0.1:5000`

## Base de données

- Chemin par défaut: `data/economic_objects.db`
- Variable d’environnement possible: `THREE_DB_PATH`
- Si la base n’existe pas, l’application crée une base de démonstration compatible.

## Documentation

- Spécification fonctionnelle: [`docs/THREE_SIMULATION_SPEC.md`](docs/THREE_SIMULATION_SPEC.md)
