

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

## TO DO 
Import HelloAsso :
- Optimiser l'import avec le last updated_at
- Ajouter un check en amont sur le format de la sortie -> Import possible ?
- Ajout import des membres
- - Choix du form
- - Mapping avec sorties
- - Gestion des groupes de formations
- - - alertes si pb (pas de groupe, plusieurs groupes en même temps, etc.)
- Envoi de mails
- - serveur smtp
- Gestion CACI
- - océrisation CACI -> extraction date fin validité
- ChatTP