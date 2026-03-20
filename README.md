## Rôles utilisateurs

| Rôle | Gestion des utilisateurs | Inscriptions |
|------|--------------------------|--------------|
| **admin** | Oui (inviter, changer les rôles, supprimer) | Oui |
| **manager** | Non | Oui |
| **viewer** | Non | Oui |

> `manager` et `viewer` ont les mêmes droits dans l'implémentation actuelle. La distinction est réservée à un usage futur.

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
