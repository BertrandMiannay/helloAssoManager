

## Run local server
```
python manage.py migrate
python manage.py runserver
```


## Manage migration
```
 python manage.py makemigrations helloAssoImporter
python manage.py migrate
```s

### Rever migration
```
./manage.py migrate helloAssoImporter zero
```