# Analyse de sécurité — helloAssoManager

**Dernière mise à jour :** 2026-03-22 (S07–S10 corrigés)
**Application :** Django 5.2 — Gestion club de plongée, données HelloAsso
**Périmètre :** Code source, configuration, API client, templates

---

## Légende

| Symbole | Signification |
|---------|--------------|
| ✅ | Corrigé |
| 🔴 | Critique — à corriger avant mise en prod |
| 🟠 | Haute — à corriger rapidement |
| 🟡 | Moyenne — à planifier |
| 🟢 | Faible — à traiter si le temps le permet |

---

## Tableau de bord

| ID | Titre | Priorité | Statut |
|----|-------|----------|--------|
| S01 | Accès aux sorties non restreint aux rôles autorisés | 🔴 Critique | ✅ Corrigé |
| S02 | SECRET_KEY avec valeur par défaut publique | 🔴 Critique | ✅ Corrigé |
| S03 | Open redirect dans la fusion de membres | 🟡 Moyenne | ✅ Corrigé |
| S04 | Cookies de session non sécurisés en production | 🟡 Moyenne | ✅ Corrigé |
| S05 | Pas de transaction sur les imports API | 🟠 Haute | ✅ Corrigé |
| S06 | Rafraîchissement API sans limite de fréquence | 🟠 Haute | ✅ Corrigé |
| S07 | Suppressions en cascade sans filet de sécurité | 🟠 Haute | ✅ Corrigé |
| S08 | Token d'invitation sans expiration | 🟠 Haute | ✅ Corrigé |
| S09 | Aucune trace des actions admin | 🟠 Haute | ✅ Corrigé |
| S10 | URL d'invitation stockée en base | 🟡 Moyenne | ✅ Corrigé |
| S11 | Race condition sur la création de membres | 🟡 Moyenne | 🔴 Ouvert |

---

## Éléments corrigés

### ✅ S01 — Accès aux sorties non restreint aux rôles autorisés
**Était :** `EventFormListView`, `EventFormDetailView`, `create_event_form` et `refresh_event_forms`
utilisaient `@login_required` — tout utilisateur connecté pouvait voir les inscriptions et déclencher des imports.

**Correction :** Nouveaux garde `ClubStaffRequiredMixin` et `@club_staff_required` dans
`userManagement/views.py`. Vérifient l'appartenance aux groupes `admin`, `instructor` ou
`dive_director`. Les simples membres (`member`) sont redirigés vers l'accueil.

---

### ✅ S02 — SECRET_KEY avec valeur par défaut publique
**Était :** `os.environ.get('SECRET_KEY', 'django-insecure-...')` — si la variable d'env était
absente, l'appli démarrait avec une clé connue publiquement (forge de session, bypass CSRF).

**Correction :** En `DEBUG=False`, l'absence de `SECRET_KEY` lève une `RuntimeError` au démarrage.
En `DEBUG=True` (dev), une clé locale est utilisée.

> **Rappel :** Le `SECRET_KEY` signe les cookies de session, les tokens CSRF et les tokens de
> réinitialisation de mot de passe. Avec une clé connue, un attaquant peut forger une session valide
> pour n'importe quel compte sans connaître son mot de passe.

---

### ✅ S03 — Open redirect dans la fusion de membres
**Était :** `url_has_allowed_host_and_scheme(next_url, allowed_hosts=None)` acceptait des URLs
comme `//evil.com` (protocole-relative).

**Correction :** `allowed_hosts={request.get_host()}` — seules les URLs relatives au même hôte
sont acceptées.

---

### ✅ S04 — Cookies de session non sécurisés en production
**Était :** `SESSION_COOKIE_SECURE` et `CSRF_COOKIE_SECURE` non configurés — cookies transmis en
clair sur HTTP en production.

**Correction :**
```python
SESSION_COOKIE_SECURE = not DEBUG   # HTTPS uniquement en prod
CSRF_COOKIE_SECURE    = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
```

---

### ✅ S05 — Pas de transaction sur les imports API
**Était :** `save_membership_form_members()` et `get_event_form_orders()` écrivaient en base sans
`transaction.atomic()` — un échec en cours d'import laissait la base dans un état partiel.

**Correction :** Les appels API (non annulables) restent hors transaction. Toutes les écritures DB
sont regroupées dans un `with transaction.atomic()`.

---

### ✅ S06 — Rafraîchissement API sans limite de fréquence
**Était :** Le bouton "Rafraîchir" pouvait être cliqué sans restriction — risque d'épuisement du
quota HelloAsso.

**Correction :** Cooldown de 60 secondes via le cache Django (`cache.set(_REFRESH_COOLDOWN_KEY,
True, 60)`). Le cooldown est annulé si l'appel API initial échoue.

---

## Éléments corrigés (suite)

### ✅ S07 — Suppressions en cascade sans filet de sécurité
**Correction (Option B) :** `EventFormAdmin` et `MemberShipFormAdmin` créés dans `helloAssoImporter/admin.py`.
- Colonne `registration_count` / `order_count` affichée en rouge dans la liste admin — visible avant toute action
- `delete_model` et `delete_queryset` surchargés : log `WARNING` avec le titre, le PK et le compte des enregistrements avant suppression
- Django affiche la liste complète des objets impactés dans la page de confirmation de suppression (comportement natif)

---

### ✅ S08 — Token d'invitation sans expiration
**Correction :** Champ `invite_expires_at = DateTimeField(null=True)` ajouté sur `CustomUser` (migration `0003`).
- `InviteView` fixe l'expiration à `now() + 7 jours`
- `AcceptInviteView.get_pending_user()` lève `Http404` si `invite_expires_at` est dépassé
- `AcceptInviteView.post()` remet `invite_expires_at = None` après acceptation
- Les invitations existantes (token présent, `invite_expires_at = NULL`) continuent de fonctionner

---

### ✅ S09 — Aucune trace des actions administratives
**Correction :** Logs `INFO` / `WARNING` ajoutés sur les actions sensibles :

| Action | Niveau | Champs loggés |
|--------|--------|---------------|
| Fusion de membres | INFO | keep pk/nom, absorbed pks, nb réassignés, auteur |
| Suppression saison | INFO | pk, label, auteur |
| Changement de rôle | INFO | username, ancien rôle, nouveau rôle, auteur |
| Suppression compte | INFO | username, email, auteur |
| Suppression EventForm (admin) | WARNING | pk, titre, nb inscriptions, auteur |
| Suppression MemberShipForm (admin) | WARNING | pk, titre, nb inscriptions, auteur |
| Invitation envoyée | INFO | email, auteur, durée validité |
| Invitation acceptée | INFO | username, email |

---

### ✅ S10 — URL d'invitation stockée en clair en base
**Correction :** Champ `invite_url` supprimé du modèle `CustomUser` (migration `0003`).
- `UserListView.get_context_data()` reconstruit dynamiquement les URLs via `request.build_absolute_uri(reverse(..., args=[u.invite_token]))`
- Passées au template sous forme de tuples `(user, invite_url|None)` — pas de filtre custom nécessaire
- La page utilisateurs affiche toujours l'URL avec bouton "Copier" pour les invitations en attente

---

## Éléments ouverts

### 🟡 S11 — Race condition sur la création de membres
**Localisation :** `common/api/helloAssoApi.py` — `save_membership_form_members()`

**Description :** `Member.objects.get_or_create(email, first_name, last_name)` peut produire un
doublon ou une `IntegrityError` si deux imports tournent simultanément sur le même formulaire
(fenêtre de temps entre le GET et le CREATE).

**Impact :** `IntegrityError` non gérée → import annulé sans message clair. En pratique, le
cooldown de 60 secondes (S06) rend ce cas très improbable.

**Correction suggérée :**
```python
from django.db import IntegrityError

try:
    member, created = Member.objects.get_or_create(
        email=email, first_name=first_name, last_name=last_name,
    )
except IntegrityError:
    member = Member.objects.get(
        email=email, first_name=first_name, last_name=last_name,
    )
    created = False
```

---

## Périmètre non couvert

Les points suivants sortent du cadre d'une application club de cette taille mais sont mentionnés
pour référence :

- **Chiffrement des données personnelles en base** (date de naissance, numéro de licence) — à
  considérer si la base est accessible à des tiers ou sauvegardée externement.
- **Rate limiting sur la page de login** — Django Axes ou similaire. Faible risque car
  l'inscription est uniquement par invitation.
- **Health check endpoint** — utile si un monitoring externe est mis en place.
- **Rotation des credentials HelloAsso** — dépend des capacités de la plateforme HelloAsso.
