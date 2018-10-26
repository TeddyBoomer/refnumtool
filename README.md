refnumtool
==========
:page Github: https://github.com/TeddyBoomer/refnumtool
:Téléchargement: https://github.com/TeddyBoomer/refnumtool/releases


Utilitaire pour les référents numériques d'EPLE par exemple en
rhones-alpes-auvergne.

Il permet de diffuser les informations vers les profs principaux et générer des
documents odt pour les parents:

 - dépassement de quota des élèves sur le serveur scribe
 - identifiants ENT elycee
 - identifiants Atos réseau pédagogique
 
Il s'appuie sur des extractions au format CSV:
 - listes des profs principaux + email par classe (ex: export pronote)
 - copie du listing scribe des dépassements de quota et mise en CSV
 - fichier général des identifiants ENT elycee ou fichier des nouveaux
   identifiants.
 - fichiers des identifiants générés par Atos sur réseau pédagogique
 
dépendances python:
odfpy, pyyaml

Installation
============

Les scripts sont écrits en Python3. Il vous est conseillé d'utiliser une
version de Python >=3.4. En effet, à partir de là, l'installateur pip
standardise l'installation des modules (et utilise le plus récent format
d'archive **wheel**)

le module dépend de **odfpy** et **pyyaml** pour la génération de fichiers
opendocument et l'utilisation de fichiers de configuration au format yaml
(texte lisible par les humains).

Il s'agit donc d'installer d'abord les dépendances puis l'archive wheel .whl

Pour windows::

```
py -3 -m pip install odfpy pyyaml \chemin\vers\refnumtool-xxx-py3-none-any.whl
```

Pour linux::

```
sudo pip3 install odfpy pyyaml /chemin/vers/refnumtool-xxx-py3-none-any.whl
```

Il peut y avoir des messages de warning pour l'installation de pyyaml du fait
d'une liaison possible à d'autres bibliothèques (plus rapides)… pas
d'inquiétude.

Lancement
=========

En ligne de commande depuis n'importe où::

```
run_refnumtool.bat
run_refnumtool.sh
```

dans les deux cas on lance simplement le module, ce qui correspond à::

```
python3 -m refnumtool
```

Documentation
=============

La documentation se trouve dans le dossier *data* du module (à
chercher dans le dossier de votre python par ex. C:\Python34 ou
/usr/local/lib/python3.4/dist-packages)