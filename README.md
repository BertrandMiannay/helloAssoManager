## Importer une formation (JSON)

L'onglet **Importer formation** (section Gestion du club) permet de créer un cursus complet en collant du JSON.

```json
{
  "name": "Cursus Niveau 2",
  "date": "2024-09-01",
  "categories": [
    {
      "name": "Équipement",
      "skills": [
        {"name": "Montage du détendeur"},
        {"name": "Gréement du gilet"}
      ]
    },
    {
      "name": "Techniques subaquatiques",
      "skills": [
        {"name": "Équilibrage"},
        {"name": "Palmage en surface"}
      ]
    }
  ]
}
```

Champs :
- `name` *(requis)* — nom du cursus
- `date` *(requis)* — date de version, format `AAAA-MM-JJ`
- `categories` — liste de catégories, chacune avec un `name` et une liste `skills` (objets `{"name": "..."}`)

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
