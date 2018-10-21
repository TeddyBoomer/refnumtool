extract_tuteur = {
    'annonce': [
"""Madame, Monsieur, le lycée Jacques Brel utilise désormais un ENT \
(environnement numérique de travail) commun aux lycées de l'académie.\
Cet environnement est le point d'accès unique aux ressources numériques \
du lycée : cahier de texte de l'élève, notes, messagerie vers \
les enseignants …""",
"Vous avez accès à l'ENT via le site du lycée:",
'http://lyc-jacques-brel.elycee.rhonealpes.fr/',
'Cliquer sur\xa0: se connecter en tant que «\xa0parent\xa0»',
"À l'issue de la 1ere connexion, vous devrez",
"L'accès aux notes se fait dans l'onglet «\xa0Pronote\xa0»"], 
    'actions': ["valider l'acceptation de la charte informatique de l'ENT",
                'personnaliser votre mot de passe',
                'renseigner une adresse mail de notification\
                (important en cas de perte/oubli du mot de passe)']}


config ={
"default_to": "boris@bebop",
"initialdir": "",
"port": 587,
"smtp": "smtps.ac-lyon.fr",
"sender": "adr-valide@ac-lyon.fr",
"test": True,
"sig": "Le référent numérique",
"login": "login_valide"}

# liste des phrases dans un message pour quotas
txtquota =["Bonjour, tu es prof principal de la ",
           "Les élèves suivants sont en dépassement de quota sur le réseau pédagogique:\n",
"""Merci de leur indiquer d'effacer leurs fichiers superflus, puis de bien faire
*vider la corbeille* même si elle semble vide.
Bien cordialement,"""]

# lignes de texte pour envoi d'identifiant de nouveaux élèves - ENT
txtidnew= ["Bonjour, tu es prof principal de la ",
           "Les nouveaux élèves suivants sont arrivés dans ta classe:\n",
"""Merci de leur transmettre leur identifiant + mot de passe (ENT). 
Bien cordialement,""",
           "Voici les identifiants des nouveaux tuteurs dans ta classe.\nBien cordialement,"]

# lignes de texte pour envoi d'identifiant de nouveaux élèves - réseau pédagogique
txtidrezonew= ["Bonjour, tu es prof principal de la ",
               "Les nouveaux \xE9l\xE8ves suivants sont arrivés dans ta classe:\n",
"""Merci de leur transmettre leur identifiant + mot de passe provisoire du ré-
seau pédagogique. 
Il faut mettre des lettres (dont majuscule) et des chiffres pour le nouveau
mot de passe.
Bien cordialement,"""]

# lignes de texte du message pour diffusion générale des id et mdp
txtidgen = ["Bonjour, tu es prof principal de la ",
"""Voici la liste des identifiants et mot de passe provisoire de tes élèves
en pièce jointe.
Bien cordialement,""",
"""Voici le fichier des identifiants et mot de passe provisoire des responsables
en pièce jointe.
Bien cordialement,"""]


