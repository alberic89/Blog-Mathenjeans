# Blog-Mathenjeans
Un petit blog sympatoche propulsé par Python et Flask.

Ce blog est prévu pour quatre sujets précis, mais est facilement adaptable à d'autres sujets, quel que soit leur nombre.

Vous pouvez le voir en action [ici](https://mathenjeans.alwaysdata.net/).
## Installation

Installez toutes les dépendances nécessaires. (Voir le fichier requirement.txt)

Copiez le code source dans un dossier sans y entrer.

Définnissez la variable d'environnement `FLASK_APP=<nom_du_dossier>`

Ensuite, lancez la commande pour initaliser la base de données :
```
flask init-db
```
L'application est prête ! Vous pouvez la tester en local avec :
```
flask run
```
Pour un serveur de production, préférez waitress ou assimilié.

## Merci à

Toute l'équipe de developpement Flask. Ce blog est directement inspiré du blog [ici](https://github.com/pallets/flask/tree/main/examples/tutorial).
