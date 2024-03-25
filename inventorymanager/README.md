To initialize the database for this application, run the following commands from the root directory of the project

```
flask --app inventorymanager init-db
flask --app inventorymanager populate-db
flask --app inventorymanager catalogue-key
```
To check the contents of the database, run the flask shell using the following command from the root directory of the project

```
flask --app inventorymanager shell
```

This will open an interactive flask-shell in which we can query the database. For a quick overview of each model, run any of the following commands in the shell:

```
Location.query.all()
Warehouse.query.all()
Item.query.all()
Stock.query.all()
Catalogue.query.all()
```
To test the app, type the following commands in cmd:

```
set FLASK_APP=inventorymanager
set FLASK_ENV=developement
flask run
```