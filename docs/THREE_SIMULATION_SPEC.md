# Three — Spécification fonctionnelle (version structurée)

## 1) Objectif

Three est un moteur de simulation **généraliste** qui sert de socle à des modules spécialisés:
- inflation (économie),
- évolution,
- écosystème,
- toute simulation personnalisée de l’utilisateur.

Le but est de relier des données économiques et naturelles, puis d’observer les effets en chaîne (ex: achat → production → extraction de ressources → impact sur la biodiversité).

---

## 2) Univers de simulation

- Un utilisateur crée un **univers**.
- L’univers peut être basé sur:
  - une copie de base de données existante,
  - ou une nouvelle base de données.
- Limite visée: **3 univers** par utilisateur.

Chaque univers est isolé et modifiable sans affecter les autres.

---

## 3) Liaisons entre objets

Deux types de liaisons:

- `A => B` : A impacte B.
- `A <=> B` : impact bidirectionnel (A impacte B et B impacte A).

Chaque liaison possède une probabilité `p ∈ [0,1]`, par défaut `p = 1`.

Ces liaisons forment un **graphe orienté pondéré**.

---

## 4) Réseaux

Three manipule plusieurs réseaux:
- réseau d’objets,
- réseau d’événements,
- réseau de patterns,
- réseau de propagation.

Les calculs d’impact indirect peuvent être modélisés via matrices d’adjacence (puissances de matrice pour impacts à distance n).

---

## 5) Arbres de composition

Un arbre représente la composition/fusion d’objets.

Exemples:
- `A = 2B + 3C + D + E + F`
- `B = T + Y + U`
- `C = U + X`

Règles:
- un composant peut apparaître dans plusieurs branches,
- des coefficients de quantité sont autorisés,
- la pondération de liaison aide à simplifier la représentation mais ne redéfinit pas l’identité de l’objet.

Usage principal:
- craft/fusion,
- décomposition d’objet,
- visualisation des dépendances de composants.

---

## 6) Types d’objets

1. **Objet réel**
   - existe physiquement dans la simulation,
   - unique,
   - possède coordonnées (et éventuellement surface/volume).

2. **Objet abstrait**
   - existe mais sans géométrie exploitable (ou non localisable),
   - ex: marque, trou noir, donnée web.

3. **Objet définition**
   - définit un type d’objet via composants/contraintes,
   - peut être instancié en objets réels.

4. **Objet simple**
   - sans composition, sans coordonnées obligatoires.

---

## 7) Craft et fusion

- **Fusion**: créer un objet via composants (`D = 2A`, `A = D + C`).
- **Craft alternatif**: plusieurs recettes possibles pour un même résultat.
- Le système doit permettre:
  - de lister ce qu’on peut fabriquer à partir d’un stock donné,
  - d’afficher l’arbre de composition d’un objet,
  - de gérer des préférences de craft via patterns.

---

## 8) Passage en objet réel

Un objet (définition/abstrait/simple) peut être **inséré comme réel**:
- attribution de coordonnées,
- métadonnées facultatives (marque, point de création, point de livraison, etc.).

---

## 9) Marque / entreprise / producteur

Une marque est un **panel de pilotage** (événements + paramètres) généralement orienté économie.

Une marque peut contenir:
- objets produits (souvent objets définition),
- usines/magasins (coordonnées),
- cadence de production/vente (`n / h,j,m,a`),
- prix,
- liaisons vers zones, objets, événements.

Un pays peut être modélisé comme un type de marque.

---

## 10) Routes et empreinte carbone

Pour les objets réels et les marques:
- identifier sources de composants (PX), fabrication (PF), livraison (PL),
- proposer des choix si données incomplètes,
- optimiser (ex: coût minimal),
- calculer l’empreinte carbone des trajets.

---

## 11) Projection temporelle

Le moteur fonctionne par pas de temps avec conversion d’unités projetées:
- `J = 24H`, `S = 7J`, `M = 4S`, `A = 12M` (paramétrable),
- possibilité d’ajouter des unités custom (ex: décennie).

Les patterns/événements s’appliquent selon fréquence + durée.

Règle d’arrondi proposée: arrondi final à l’entier inférieur.

---

## 12) États et inversion

Gestion d’états binaires inversables:
- vivant/mort,
- on/off,
- activé/désactivé,
- +/-.

L’inversion applique le passage vers l’état opposé défini.

---

## 13) Événements (cause → conséquence)

Un événement comprend:
- une **cause** (observation/condition),
- une **action** (paramètre appliqué),
- une cible,
- une probabilité.

Causes typiques:
- pattern actif,
- événement actif,
- objet modifié,
- comparaison numérique (`=`, `<`, `>`, `<=`, `>=`).

Actions typiques:
- activer/désactiver un événement (temporairement ou en continu),
- remplacer une donnée,
- inverser un état,
- ajouter/soustraire/multiplier/diviser une valeur,
- modifier une fréquence.

---

## 14) Patterns

Un pattern est une règle calculée qui s’applique sur:
- une durée,
- une fréquence,
- ou les deux.

Exemples:
- coefficient d’augmentation,
- formule `5n+3` (où `n` est une valeur mesurée),
- alternance probabiliste entre patterns (`P3` choisit `P1` ou `P2`).

Les patterns peuvent former des réseaux (patterns de patterns).

---

## 15) Propagation

La propagation diffuse un effet dans un réseau.

Trois modes clés:
1. **Amortie**: perte avec la distance réseau.
2. **Exponentielle**: amplification avec la distance (contagion/emballement).
3. **Filtrée par probabilité**: tirage aléatoire selon la probabilité de liaison.

Formalisme général proposé:
`VB(t+1) = VB(t) ⊕ pAB · fp(fAB(VA(t)), VB(t))`

---

## 16) Visualisations

- courbes d’évolution temporelle,
- points marquant les événements,
- consultation détaillée d’un objet (statistiques, historique).

Bonus envisagé: graphe animé (non prioritaire).

---

## 17) Zones géographiques

Les zones (ou pays) peuvent porter:
- prix,
- coefficients,
- événements spécifiques.

Exemple: un événement géopolitique modifie le prix d’une ressource.

---

## 18) Partie calcul et logique

Le système doit permettre de:
- créer des calculs personnalisés,
- associer variables à des données/ensembles,
- créer des arbres logiques avec opérateurs:
  - ET,
  - OU,
  - EXCLU.

Des calculs pré-générés peuvent être fournis pour les cas essentiels.

---

## 19) Démonstration cible

Le projet final doit démontrer:
- simulation à partir de données utilisateur,
- simulation préconstruite (économie + nature),
- mise en évidence de l’impact de l’économie sur les écosystèmes.

---

## 20) Résumé opérationnel (MVP)

Pour une première version exploitable de Three:

1. CRUD objets (types réel/abstrait/définition/simple).
2. Graphes de liaisons (`=>`, `<=>`) avec probabilités.
3. Événements conditionnels + actions arithmétiques.
4. Patterns (fréquence + durée).
5. Propagation configurable (au moins amortie + probabiliste).
6. Arbres de composition/craft.
7. Projection temporelle (H/J/S/M/A).
8. Interface de visualisation (courbe + inspection objet).

Ce socle permet ensuite de construire les modules spécialisés (Inflation, Évolution, Écosystème).
