# Workflows financiers CSN-GHC

## Dépense

`Brouillon → Soumise → Approuvée → Engagée → Liquidée → Payée → Clôturée`

- Demandeur : prépare la demande et les pièces.
- Gestionnaire budgétaire : contrôle la ligne PTBA et le crédit.
- Responsable achats : contrôle et valide le fournisseur.
- Contrôleur interne / Directeur financier : approuve l'engagement.
- Comptable : contrôle la facture et la liquidation.
- Trésorier : prépare le paiement.
- Validateur habilité : soumet le paiement selon les permissions ERPNext.
- Auditeur : lecture et export sans modification.

L'initiateur d'une demande ne peut pas l'approuver seul. Chaque facture et paiement reste relié à l'engagement et à la ligne PTBA par `csn_engagement`.

## Correction comptable

Une écriture soumise est immuable. L'utilisateur demande une contre-passation avec date, période, journal d'extourne et justification. Le système copie les dimensions et inverse débit/crédit dans une nouvelle écriture en brouillon. Une autre personne doit la valider.
