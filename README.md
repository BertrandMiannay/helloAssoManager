## Rôles utilisateurs

| Rôle | Label | Gestion des utilisateurs | Sorties |
|------|-------|--------------------------|---------|
| `admin` | Administrateur | Oui (inviter, changer les rôles, supprimer) | Oui |
| `member` | Membre | Non | Oui |
| `instructor` | Formateur | Non | Oui |
| `dive_director` | Directeur de plongée | Non | Oui |

## Run local server
```
python manage.py migrate
python manage.py runserver
```


## Manage migration
```
 python manage.py makemigrations helloAssoImporter
python manage.py migrate
```

### Rever migration
```
./manage.py migrate helloAssoImporter zero
```


### Create super user
```
 python manage.py createsuperuser  
 ```

 ### Reset database
  ```
 python manage.py init_dev_db
  ```
