# Architecture comptable et budgétaire CSN-GHC

## Principe directeur

ERPNext demeure le système de tenue des comptes. `Journal Entry` produit les `GL Entry`; l'application CSN-GHC ajoute les règles institutionnelles sans créer un grand livre parallèle.

## Phase 2 — comptabilité générale

- `CSN Journal Comptable` configure les journaux, séries, pièces et double validation.
- Les champs CSN de `Journal Entry` portent période, journal, origine, pièce, initiateur, validateur, empreinte et extourne.
- `accounting_engine.py` contrôle partie double, période ouverte, compte imputable, dimensions et séparation des fonctions.
- Une écriture soumise ne peut pas être annulée. `create_reversal` génère une contre-passation en brouillon, à valider par une autre personne.
- `CSN Balance Generale` et `CSN Grand Livre` lisent directement `GL Entry` et conservent le drill-down vers la pièce.

## Phase 3 — exécution budgétaire

Flux de référence :

1. `CSN Demande Depense` identifie l'objet, la ligne PTBA, l'unité, le fournisseur éventuel et les justificatifs.
2. Une personne différente approuve la demande.
3. `CSN Engagement Budgetaire` vérifie le crédit disponible et réserve le montant.
4. `Purchase Order` est limité au montant engagé.
5. `Purchase Invoice` génère une liquidation budgétaire.
6. `Payment Entry` génère un paiement budgétaire, limité au montant liquidé.
7. Les annulations créent des mouvements inverses; elles ne suppriment jamais l'historique.

`CSN Mouvement Budgetaire` est un registre immuable créé uniquement par `budget_engine.py`. Les crédits disponibles sont calculés comme budget de la ligne PTBA moins engagements nets. Les liquidations et paiements sont suivis séparément.

## Contrôles

- montant demandé et engagé strictement positif;
- demande approuvée avant engagement;
- cohérence entité, ligne PTBA, devise et fournisseur;
- fournisseur validé et dossier légal présent;
- interdiction de dépasser le crédit disponible;
- facture limitée au solde engagé non liquidé;
- paiement limité au solde liquidé non payé;
- mouvements inverses lors des annulations;
- droits serveur sur chaque objet.

## Limites restant à traiter

- seuils d'approbation configurables et workflow multi-niveaux;
- marchés publics et comité de sélection;
- retenues fiscales et garanties détaillées;
- fonds affectés et règles d'éligibilité (Phase 5);
- connecteurs automatiques avec les banques et opérateurs Mobile Money;
- import de relevés spécifiques aux formats de chaque fournisseur.

## Phase 4 — trésorerie et rapprochements

- `CSN Compte Tresorerie` représente les banques, caisses, comptes Mobile Money, comptes de collecte, projets, bailleurs, campagnes et transit.
- Chaque compte est lié à un compte comptable ERPNext actif et dans la même devise.
- `CSN Operation Tresorerie` conserve montant brut, frais, net, devises, taux, identifiant fournisseur et pièce justificative.
- `Payment Entry` porte le compte CSN, le canal, la source et la date du taux de change ainsi que son validateur.
- `CSN Rapprochement Tresorerie` rapproche une opération externe confirmée avec un paiement soumis.
- Un rapprochement exige une seconde personne; un écart supérieur à la tolérance exige une justification.
- L'annulation conserve la trace et remet l'opération externe au statut confirmé.
