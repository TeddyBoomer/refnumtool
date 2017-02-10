Installation et fichiers de configuration
=========================================

Python
^^^^^^

Les scripts sont écrits en Python3. Il vous est conseillé d'utiliser une
version de Python >=3.4. En effet, à partir de là, l'installateur pip
standardise l'installation des modules (et utilise le plus récent format
d'archive **wheel**)

le module dépend de **odfpy** et **pyyaml** pour la génération de fichiers
opendocument et l'utilisation de fichiers de configuration au format yaml
(texte lisible par les humains).

Il s'agit donc d'installer d'abord les dépendances puis l'archive wheel .whl

Pour windows::

  py -3 -m pip install odfpy pyyaml \chemin\vers\refnumtool-xxx-py3-none-any.whl

Pour linux::

  sudo pip3 install odfpy pyyaml /chemin/vers/refnumtool-xxx-py3-none-any.whl

Il peut y avoir des messages de warning pour l'installation de pyyaml du fait
d'une liaison possible à d'autres bibliothèques (plus rapides)… pas
d'inquiétude.

Documentation
^^^^^^^^^^^^^

Cette documentation se trouve dans le dossier *data* du module (à
chercher dans le dossier de votre python par ex. C:\Python34 ou
/usr/local/lib/python3.4/dist-packages)

Config et 1er lancement
^^^^^^^^^^^^^^^^^^^^^^^

Au premier lancement, des fichiers de paramétrage vont être générés.
Soit *HOME* la racine du dossier de l'utilisateur. Alors ils seront copiés dans 
*HOME/.refnumtool.d/*

Fichier *config.yaml*: Après un premier lancement de l'outil, le chemin de
recherche des fichiers csv est conservé dans ce fichier de configuration; c'est
bien pratique! Il contient aussi l'expéditeur par défaut, le port et le nom du
relais smtp (par défaut smtps.ac-lyon.fr en 587, connexion sécurisée)

.. important:: Par défaut, le fichier *config.yaml* contient un paramètre test:
             true pour des raisons de sécurité et de développement. Ainsi on
             peut lancer l'application sans crainte de publiposter n'importe
             quoi. Les mails sont alors envoyé au *default_to* (avec
             smtp=localhost, cela fonctionne sous linux avec un serveur mail
             opérationnel). 
	     Pour activer le publipostage, vous **devez** modifier ce paramètre à ::

	       test: false

Fichier *textquotas.yaml*: les principales lignes du message envoyé pour les
dépassements de quota. Les champs d'identifiant ou de classe sont ajoutés
on-the-fly au moment de générer les messages. La syntaxe avec - correspond à
une liste de str chargée dans python.

Fichier *textidnew.yaml*: les principales lignes du message envoyé pour les
identifiants et mot de passe provisoire de nouveaux élèves.

Fichier *text_extract_tuteur.yaml*: les principales lignes du fichier ODT des
tuteurs.

Fichiers CSV
^^^^^^^^^^^^

Le logiciel est conçu pour manipuler des données au format CSV (peu importe les séparateurs et autres options).

* Fichiers des profs principaux: Le plus simple est d'extraire un csv à partir
  d'un logiciel de gestion de vie scolaire (par ex. pronote). Il doit à minima
  contenir les champs suivants dans un ordre quelconque:

  +-----+--------+--------+--------+-------+
  | Nom | Prénom | E-Mail | elycee |scribe |
  +-----+--------+--------+--------+-------+
  
  Les champs *elycee* et *scribe* sont les noms des classes dans ces deux types
  de bases; en effet, si vous n'avez pas de chance, pronote, sts, elycee et
  scribe ne vont pas avoir le même nommage des classes.

  Si votre établissement est passé en mise à niveau Atos, vous n'avez plus de
  serveur scribe; les identifiants réseau pédagogique sont synchronisés de
  façon hebdomadaire avec la base SIECLE rectorale. Vous pouvez récupérer le
  csv des nouveaux identifiants dans le partage réseau des Référents. Mais à
  nouveau, les noms de classe peuvent être différents de ceux de elycee; il
  faut placer un champs atos:

  +-----+--------+--------+--------+------+
  | Nom | Prénom | E-Mail | elycee | atos |
  +-----+--------+--------+--------+------+

  On ajuste les noms de classe exacts dans cette colonne.
  
* [elycee] Fichiers des identifiants: export complet depuis elycee pour génération
  globale par classe (tuteurs et élèves), export d'un fichier de mise à jour
  des nouveaux identifiants sinon.

* [scribe] Fichier des quotas: à partir de la page web de l'EAD scribe, on copie/colle
  le tableau dans un tableur et on sauve en .csv.  Attention, c'est le champ
  *Utilisateur* qui est analysé.

* [atos] Fichier des identifiants. Pas de ligne d'entête. Séparateur de champs ";"

Log
^^^

un fichier de log des mails envoyés est créé dans le même dossier que le
fichier des profs. La date et l'heure du publipostage apparaissent dans le
nom du fichier du type *nom_%d%m%Y-%H-%M-%S.log*
