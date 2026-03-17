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
sudo nano /etc/helloasso/env  # remplir SECRET_KEY, ALLOWED_HOSTS=<IP du VPS>, etc.
sudo chmod 600 /etc/helloasso/env
```

## 3. Préparer l'app

```bash
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

## 5. Nginx (HTTP, sans domaine)

```bash
sudo nano /etc/nginx/sites-available/helloasso
```

Contenu :

```nginx
server {
    listen 80;
    server_name _;

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

L'app est accessible sur `http://<IP du VPS>`.

## Mise à jour

```bash
cd ~/helloAssoManager
git pull
.venv/bin/poetry install --only main
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --no-input
sudo systemctl restart helloasso
```

## Commandes utiles

```bash
sudo journalctl -u helloasso -f   # logs en temps réel
sudo systemctl restart helloasso  # redémarrer le serveur
sudo systemctl status helloasso   # état du service
sudo nginx -t                     # vérifier la config Nginx
```
