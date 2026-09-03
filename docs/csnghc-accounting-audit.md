# Audit comptable et technique CSN-GHC

Date de l'audit : 1er septembre 2026  
Dépôt audité : `csnohada/csn_ohada`, branche `main`, commit initial `a89a442`  
Périmètre : application Frappe/ERPNext `csn_ohada`; aucune opération sur la base de production.

## Verdict exécutif

Le dépôt constitue une bonne extension Frappe de départ, mais pas encore un système financier complet. Il contient le socle PTBA et quelques référentiels institutionnels. La comptabilité générale observée dans l'instance repose principalement sur ERPNext; une partie des adaptations historiques visibles sur le serveur (tableau de bord, démonstration comptable, workflows et personnalisation) n'était pas versionnée dans ce dépôt au début de l'audit.

La décision d'architecture est donc de conserver Frappe/ERPNext et d'ajouter les contrôles CSN-GHC dans l'application `csn_ohada`. La CSN-GHC reste une seule `Company`. Les directions, divisions, bureaux, antennes, projets, programmes, entrepôts et unités de gestion sont des unités organisationnelles et dimensions, jamais des sociétés supplémentaires.

## Stack et structure constatées

- Frappe/ERPNext 17 en développement, Python 3.14, MariaDB, Redis, Nginx et Docker sur le VPS.
- Paquet Python `csn_ohada` géré par `pyproject.toml`; aucune dépendance applicative additionnelle.
- Hooks actifs : `after_install` et `after_migrate` vers `csn_ohada.install`.
- Pas de `composer.json`, `package.json`, contrôleur Laravel ni routes Laravel : les consignes Laravel ne s'appliquent pas.
- Les API doivent utiliser les méthodes Frappe autorisées (`@frappe.whitelist`) et ses permissions serveur.
- Les schémas sont portés par les fichiers JSON des DocTypes et appliqués avec `bench migrate`; aucune migration destructive n'est requise.
- L'authentification, les sessions, CSRF, utilisateurs et rôles de base sont fournis par Frappe.

## Inventaire fonctionnel avant Phase 1

DocTypes présents :

- `CSN PTBA` et `CSN Ligne PTBA`;
- `CSN Bailleur`;
- `CSN Convention Financement`;
- `CSN EMO`;
- `CSN Secteur Humanitaire`;
- `CSN Source Financement`;
- `CSN Zone Intervention`.

Fonctions utiles déjà présentes :

- contrôle des dates du PTBA contre `Fiscal Year`;
- calcul automatique du montant des lignes et du total du PTBA;
- contrôle de cohérence entre société, compte, centre de coûts, convention et source de financement;
- blocage de la modification des lignes d'un PTBA soumis;
- permissions de lecture/écriture par rôles sur les DocTypes existants;
- initialisation idempotente des rôles, secteurs et sources de financement.

## Écarts critiques identifiés

| Priorité | Écart | Risque | Traitement |
|---|---|---|---|
| Critique | Aucun référentiel comptable officiel versionné | Mélange ou présentation erronée de comptes comme officiels | Phase 1 : référentiel, version, compte de référence et activation contrôlée |
| Critique | Aucun profil principal/secondaire explicite | Mélange silencieux SYSCOHADA/PCE | Phase 1 : paramètres comptables et validation serveur |
| Critique | Pas de périodes comptables propres à la CSN-GHC | Comptabilisation possible hors période autorisée | Phase 1 : périodes ouvertes, clôturées et réouvertes avec justification |
| Haute | Structure institutionnelle partielle (`CSN EMO` uniquement) | Reporting incohérent par direction/antenne | Phase 1 : unités organisationnelles liées à une seule `Company` |
| Haute | Liste de rôles incomplète | Séparation des fonctions insuffisante | Phase 1 : rôles fonctionnels complets; affectation utilisateur à faire nominativement |
| Haute | Aucun test automatisé dans le dépôt | Régressions non détectées; la CI échoue à l'étape de découverte | Ajouter progressivement des tests Frappe à chaque phase |
| Haute | Aucun importeur XLSX/CSV/JSON n'existait | Comptes difficiles à vérifier et tracer | Traité en Phase 1 : prévisualisation, validation et import atomique |
| Haute | Pas de moteur comptable CSN central | Immutabilité et dimensions dépendantes d'ERPNext sans garde métier globale | Phase 2 |
| Haute | Pas de contrôle budgétaire d'engagement | Dépassement du crédit possible | Phase 3 |
| Haute | Pas de connecteur Par Amour versionné | Dons et comptabilité peuvent diverger | Phase 5 |
| Moyenne | README minimal et branche CI configurée sur `CSN` au lieu de `main` | Installation et CI ambiguës | Corriger avec la documentation de déploiement |
| Moyenne | Les champs `Float` servent aux quantités PTBA | Acceptable pour quantité, interdit pour les montants | Les montants restent `Currency`/DECIMAL; vérifier la précision du site |

## Phase 1 implémentée dans cette livraison

Les éléments suivants sont ajoutés sous forme de DocTypes Frappe versionnés :

1. `CSN Unite Organisationnelle`
   - rattachement obligatoire à une seule `Company`;
   - hiérarchie par unité parente;
   - types direction, division, bureau, antenne, projet, programme, entrepôt et unité de gestion;
   - liens facultatifs vers `Cost Center` et `User`;
   - contrôle serveur de cohérence de la société.
2. `CSN Referentiel Comptable`
   - codes admis : `SYSCOHADA_REVISED`, `PCE_RDC`, `OTHER_OFFICIAL_FRAMEWORK`;
   - référence juridique et document source obligatoires.
3. `CSN Version Referentiel Comptable`
   - dates de validité et cycle Brouillon → Importée → Validée → Approuvée → Active;
   - trois validateurs obligatoires avant activation;
   - une seule version active par référentiel;
   - empreinte SHA-256 du document source.
4. `CSN Compte Referentiel`
   - tous les champs minimaux prescrits pour l'import officiel;
   - identité stable `version::code`;
   - interdiction de supprimer un compte actif ou historique;
   - aucun numéro de compte n'est livré comme officiel.
5. `CSN Periode Comptable`
   - rattachement à `Company` et `Fiscal Year`;
   - contrôle des bornes et des chevauchements;
   - statuts ouverte, en clôture, clôturée, réouverte;
   - justification et identité du responsable lors d'une réouverture.
6. `CSN Parametres Comptables`
   - référentiel principal et référentiel secondaire;
   - activation du dual reporting;
   - rejet d'une version non active ou insuffisamment approuvée.
7. Rôles complémentaires
   - gouvernance, finance, comptabilité, trésorerie, contrôle, audit, achats, logistique, stocks, projets, antennes, tutelle et administration.
8. Importeur de plan officiel
   - formats XLSX, CSV et JSON;
   - contrôle des colonnes, doublons, référentiel, hiérarchie et sens normal;
   - prévisualisation des 100 premières lignes avant import;
   - import hiérarchique dans une transaction Frappe;
   - refus de modifier une version active ou historique.

## Limites conscientes de cette livraison

- Aucun utilisateur réel n'est créé automatiquement : les comptes nominatifs et les responsabilités doivent être validés par la CSN-GHC.
- Aucun compte SYSCOHADA ou PCE n'est créé par cette phase; seul le modèle d'accueil du plan officiel est créé.
- Le rapprochement entre un `CSN Compte Referentiel` et le DocType ERPNext `Account` sera fait par un importeur contrôlé, pas par modification rétroactive.
- La double approbation des réouvertures nécessite un workflow dédié prévu avec la clôture complète; la présente phase exige déjà justification et permission serveur.
- Les tableaux de bord et personnalisations présents seulement sur le VPS devront être rapatriés dans Git avant durcissement.

## Déploiement sûr

Après revue et sauvegarde du site :

```bash
cd /opt/finance-csnghc/source/csn_ohada
git pull --ff-only origin main

docker compose -p finance-csnghc \
  -f /opt/finance-csnghc/gitops/compose.yaml \
  exec -T backend \
  bench --site finance-csnghc.cloud migrate

docker compose -p finance-csnghc \
  -f /opt/finance-csnghc/gitops/compose.yaml \
  exec -T backend \
  bench --site finance-csnghc.cloud clear-cache
```

Ces commandes n'utilisent ni `migrate:fresh`, ni `db:wipe`, ni suppression de table ou de données. Elles ne modifient pas le site Nginx de Par Amour.

## Suite recommandée

1. Relire les rôles et nommer les titulaires.
2. Importer le document officiel du référentiel choisi, sans activer de plan provisoire.
3. Faire valider le modèle d'import et l'essayer sur une copie du plan officiel.
4. Implémenter la Phase 2 autour des écritures ERPNext en renforçant périodes, immutabilité, extournes et dimensions.
5. Rapatrier dans Git les scripts de dashboard/workflow actuellement présents uniquement sur le serveur.
