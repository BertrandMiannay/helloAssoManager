# Conformité RGPD — TP Manager

## Contexte

TP Manager est une application web utilisée par un club de plongée pour gérer les adhésions et les inscriptions aux sorties, en important les données depuis la plateforme [HelloAsso](https://www.helloasso.com/). Elle traite des données personnelles de membres et d'utilisateurs internes au club.

**Responsable de traitement :** Le club de plongée (à compléter : nom, adresse, contact DPO si applicable).

---

## 1. Inventaire des données personnelles traitées

### 1.1 Comptes utilisateurs internes (`CustomUser`)

| Champ | Nature | Obligatoire |
|---|---|---|
| `username` | Identifiant de connexion | Oui |
| `email` | Adresse e-mail | Oui |
| `first_name` / `last_name` | Nom et prénom | Non |
| `password` | Mot de passe (hashé PBKDF2) | Oui |
| `date_joined` | Date de création du compte | Auto |
| `last_login` | Date de dernière connexion | Auto |
| `invite_token` | Jeton d'invitation (UUID) | Temporaire |
| `invite_expires_at` | Expiration du jeton | Temporaire |
| `groups` | Rôle dans le club (admin, instructor, dive_director, member) | Oui |

**Source :** Invitation manuelle par un administrateur.  
**Accès :** Administrateurs uniquement via `/users/` et l'interface Django admin.

---

### 1.2 Membres (`Member`)

| Champ | Nature | Obligatoire |
|---|---|---|
| `email` | Adresse e-mail | Oui |
| `first_name` / `last_name` | Nom et prénom | Oui |
| `birthdate` | Date de naissance | Non |
| `medical_certificate_date` | Date du certificat médical | Non |

**Source :** Import depuis HelloAsso (formulaires d'adhésion).  
**Accès :** Administrateurs (liste complète) ; encadrants et directeurs de plongée (lecture seule via `/inscriptions/adherent/`).

---

### 1.3 Commandes d'adhésion (`MemberShipFormOrder`)

| Champ | Nature | Obligatoire |
|---|---|---|
| `payer_email` | E-mail du payeur | Non |
| `payer_first_name` / `payer_last_name` | Nom et prénom du payeur | Non |
| `birthdate` | Date de naissance | Non |
| `sex` | Sexe | Non |
| `licence_number` | Numéro de licence fédérale | Non |
| `emergency_contact_name` | Contact d'urgence (nom) | Non |
| `emergency_contact_phone` | Contact d'urgence (téléphone) | Non |
| `dive_level` / `apnea_level` / `underwater_shooting_level` | Niveaux de pratique | Non |
| `dive_teaching_level` / `apnea_teaching_level` / `underwater_shooting_teaching_level` | Niveaux d'encadrement | Non |
| `caci_expiration` | Date d'expiration du CACI | Non |
| `category` | Catégorie d'adhésion | Non |

**Source :** Import depuis HelloAsso (champs personnalisés des formulaires).  
**Accès :** Administrateurs uniquement via `/formulaires/`.

> **Donnée sensible :** Le certificat médical (`medical_certificate_date`) et le CACI (`caci_expiration`) sont liés à la santé. Leur traitement requiert une base légale spécifique (voir section 3).

---

### 1.4 Commandes de sorties (`EventFormOrder`)

| Champ | Nature |
|---|---|
| `payer_email` | E-mail du payeur |
| `payer_first_name` / `payer_last_name` | Nom et prénom du payeur |

**Source :** Import depuis HelloAsso (inscriptions aux sorties).  
**Accès :** Encadrants, directeurs de plongée et administrateurs via `/inscriptions/`.

---

### 1.5 Inscriptions aux sorties (`EventRegistration`)

| Champ | Nature |
|---|---|
| `first_name` / `last_name` | Nom et prénom du participant |
| `name` | Libellé libre (peut contenir un nom) |
| `state` | Statut de l'inscription |

**Source :** Import depuis HelloAsso.  
**Accès :** Encadrants, directeurs de plongée et administrateurs.

---

### 1.6 Évaluations de compétences (`SkillEvaluation`)

| Champ | Nature |
|---|---|
| `member` | Lien vers le membre évalué |
| `date` | Date de l'évaluation |
| `status` | Statut de la compétence |
| `comment` | Commentaire libre de l'évaluateur |

**Source :** Saisie manuelle par l'encadrement.  
**Accès :** Encadrants, directeurs de plongée et administrateurs.

---

## 2. Finalités du traitement

| Finalité | Données concernées | Base légale (RGPD art. 6) |
|---|---|---|
| Gestion des adhésions au club | Member, MemberShipFormOrder | Exécution du contrat (6.1.b) |
| Organisation et suivi des sorties plongée | EventFormOrder, EventRegistration | Exécution du contrat (6.1.b) |
| Vérification des aptitudes médicales et niveaux | `medical_certificate_date`, `caci_expiration`, niveaux | Obligation légale (6.1.c) — réglementation fédérale plongée |
| Gestion des accès à l'application | CustomUser | Intérêt légitime du club (6.1.f) |
| Suivi pédagogique des membres | MemberSkill, SkillEvaluation | Intérêt légitime du club (6.1.f) |
| Contact d'urgence | `emergency_contact_name`, `emergency_contact_phone` | Intérêt vital (6.1.d) |

> **Données de santé (art. 9 RGPD) :** La date de certificat médical et l'expiration du CACI constituent des données de santé au sens de l'article 9. Leur traitement doit reposer sur une dérogation explicite, typiquement : consentement explicite (9.2.a) ou nécessité pour des activités sportives d'une association (9.2.d). **Action requise :** Documenter formellement la base légale retenue et l'inscrire au registre des traitements.

---

## 3. Sous-traitant : HelloAsso

HelloAsso collecte les données en amont (paiements, inscriptions, adhésions) et les met à disposition via son API. Le club agit comme **responsable de traitement** et HelloAsso comme **sous-traitant**.

- HelloAsso publie sa politique de confidentialité et son DPA sur son site.
- **Action requise :** Vérifier qu'un contrat de sous-traitance (DPA) conforme à l'article 28 RGPD est bien signé avec HelloAsso, ou que les CGU d'HelloAsso couvrent cette exigence.

---

## 4. Durées de conservation

Aucune politique de suppression automatique n'est actuellement implémentée. Les données sont conservées indéfiniment.

| Catégorie | Durée recommandée | Référence |
|---|---|---|
| Comptes utilisateurs inactifs | 3 ans après la dernière connexion | Recommandation CNIL |
| Données d'adhésion (membres) | Durée de l'adhésion + 5 ans | Prescription légale associations |
| Données de commandes (HelloAsso) | 5 ans après la commande | Obligation comptable |
| Évaluations de compétences | Durée de la relation + 3 ans | À définir par le club |
| Jetons d'invitation | 7 jours (déjà implémenté) | ✅ Conforme |
| Données de santé (certificats, CACI) | Durée de validité + 1 saison | Recommandation fédérale |

---

## 5. Droits des personnes concernées

Les membres et utilisateurs disposent des droits suivants (RGPD art. 15 à 22) :

- **Droit d'accès** : obtenir une copie de leurs données.
- **Droit de rectification** : corriger des données inexactes.
- **Droit à l'effacement** : demander la suppression de leurs données.
- **Droit à la limitation** : geler le traitement en cas de litige.
- **Droit à la portabilité** : recevoir leurs données dans un format structuré.
- **Droit d'opposition** : s'opposer aux traitements fondés sur l'intérêt légitime.

**Contact pour exercer ces droits :** (à compléter — e-mail ou formulaire du club).

---

## 6. Sécurité des données

### Mesures déjà en place

| Mesure | Statut |
|---|---|
| Mots de passe hashés (PBKDF2-SHA256) | ✅ |
| Cookies sécurisés (HTTPS-only en production) | ✅ |
| Protection CSRF | ✅ |
| Contrôle d'accès par rôle (AdminRequired, ClubStaffRequired) | ✅ |
| Inscriptions par invitation uniquement | ✅ |
| Jetons d'invitation à durée limitée (7 jours) | ✅ |
| Journalisation des actions admin (invitation, suppression, changement de rôle, merge membre) | ✅ |
| Transactions atomiques lors des imports | ✅ |
| Rate-limiting de l'import (cooldown 60 s) | ✅ |
| SECRET_KEY obligatoire en production (lève RuntimeError si absente) | ✅ |

### Mesures à renforcer

| Mesure | Priorité |
|---|---|
| Politique de mots de passe (longueur, complexité) | Haute |
| Rotation de SECRET_KEY et des credentials HelloAsso | Haute |
| Journalisation des connexions (succès et échecs) | Moyenne |
| Chiffrement au repos pour les données sensibles (certificats médicaux) | Moyenne |
| Journalisation des accès aux données personnelles (pas seulement les modifications) | Basse |

---

## 7. Actions à mener pour la mise en conformité

### Priorité haute

- [ ] **Registre des traitements (art. 30)** : Créer et maintenir un registre des activités de traitement, en s'appuyant sur l'inventaire ci-dessus.
- [ ] **Base légale pour les données de santé** : Documenter formellement la dérogation retenue pour le traitement de `medical_certificate_date` et `caci_expiration` (consentement explicite ou art. 9.2.d pour association sportive).
- [ ] **Information des personnes (art. 13/14)** : Rédiger et diffuser une notice d'information (mention RGPD) présentée aux membres lors de l'adhésion sur HelloAsso ou lors du premier contact.
- [ ] **DPA HelloAsso** : Vérifier l'existence d'un contrat de sous-traitance conforme à l'art. 28 avec HelloAsso.

### Priorité moyenne

- [ ] **Purge automatique des données** : Implémenter une commande de gestion Django (`manage.py purge_old_data`) supprimant ou anonymisant les données dépassant la durée de conservation définie.
- [ ] **Procédure d'exercice des droits** : Définir et documenter le processus interne pour répondre aux demandes de droits (accès, rectification, effacement) dans le délai d'un mois.
- [ ] **Politique de mots de passe** : Activer les validateurs Django (`AUTH_PASSWORD_VALIDATORS`) pour imposer une complexité minimale.
- [ ] **Journalisation des connexions** : Logger les tentatives de connexion (succès et échecs) pour détecter des accès non autorisés.

### Priorité basse

- [ ] **DPO ou référent RGPD** : Désigner un référent RGPD au sein du club (obligatoire uniquement si traitement à grande échelle de données sensibles, optionnel mais recommandé sinon).
- [ ] **Revue des accès** : Audit annuel des comptes utilisateurs actifs et des rôles attribués.
- [ ] **Chiffrement des sauvegardes** : S'assurer que les sauvegardes de la base de données sont chiffrées.
- [ ] **Clause RGPD dans les statuts ou règlement intérieur** : Mentionner le traitement des données personnelles dans les documents officiels du club.

---

## 8. Points de contact et références

- **CNIL (France)** : [cnil.fr](https://www.cnil.fr) — guides pour associations, registre des traitements, formulaires.
- **Référentiel CNIL pour les associations sportives** : [cnil.fr/fr/associations](https://www.cnil.fr/fr/les-associations-et-le-rgpd)
- **HelloAsso — RGPD** : documentation disponible dans leur espace partenaire.

---

*Document généré le 2026-05-05. À réviser lors de toute évolution significative du traitement des données.*
