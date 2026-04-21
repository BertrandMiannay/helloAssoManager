# Déploiement sur VPS

## Prérequis

- VPS Ubuntu/Debian avec Python 3.13, Nginx, Git installés
- Accès SSH avec droits sudo

## 1. Cloner et installer

```bash
git clone https://github.com/BertrandMiannay/helloAssoManager.git ~/helloAssoManager
cd ~/helloAssoManager
python3 -m venv .venv
.venv/bin/pip install poetry
.venv/bin/poetry install --only main
```

## 2. Variables d'environnement

```bash
sudo mkdir /etc/helloasso
sudo cp deploy/env.example /etc/helloasso/env
sudo nano /etc/helloasso/env  # remplir SECRET_KEY, ALLOWED_HOSTS=<domaine>, etc.
sudo chmod 666 /etc/helloasso/env  
```

## 3. Préparer l'app

Les variables d'environnement de `/etc/helloasso/env` doivent être chargées avant de lancer les commandes Django :

```bash
set -a && source /etc/helloasso/env && set +a
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --no-input
.venv/bin/python manage.py init_dev_db  # crée le superuser admin/admin
```

## 4. Lancer gunicorn via systemd

Avant de copier le service, remplacer `<your-user>` par ton nom d'utilisateur dans `deploy/helloasso.service`.

```bash
sudo cp deploy/helloasso.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now helloasso
sudo systemctl status helloasso
```

## 5. Nginx + HTTPS (Let's Encrypt)

```bash
sudo nano /etc/nginx/sites-available/helloasso
```

Contenu initial (remplacer `<domaine>` par le vrai domaine, ex: `botouraineplongee.ddns.net`) :

```nginx
server {
    listen 80;
    server_name <domaine>;

    location / {
        proxy_pass http://unix:/run/helloasso/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/helloasso /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Activer HTTPS avec Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d <domaine>
```

Certbot modifie automatiquement la config Nginx pour ajouter le bloc HTTPS et la redirection HTTP→HTTPS. Le renouvellement automatique est configuré par Certbot.

### Variables d'environnement à activer après HTTPS

Dans `/etc/helloasso/env` :

```
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

```bash
sudo systemctl restart helloasso
```

L'app est accessible sur `https://<domaine>`.

## Mise à jour

```bash
cd ~/helloAssoManager
git pull
.venv/bin/poetry install --only main
set -a && source /etc/helloasso/env && set +a
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --no-input
sudo systemctl restart helloasso
```

## Commandes utiles

```bash
sudo journalctl -u helloasso -f   # logs en temps réel
sudo systemctl stop helloasso     # stoppe le serveur
sudo systemctl restart helloasso  # redémarrer le serveur
sudo systemctl status helloasso   # état du service
sudo nginx -t                     # vérifier la config Nginx
```
