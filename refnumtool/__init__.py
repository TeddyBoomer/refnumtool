import tkinter as tk
import os
from functools import reduce
from os.path import basename, dirname, join, isdir, exists, expanduser
from yaml import load, dump
from shutil import copyfile

try:
    from yaml import CLoader as Loader
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Loader
    from yaml import Dumper

import refnumtool.parametre as param
from refnumtool.mailing import Mailing
from refnumtool.id2odt import *

class refnumTool(tk.Frame):
    """classe principale de gestion pour référent numérique
    interface en ligne de commande par choix simple
    Vous devez avoir:

    * un csv des profs principaux
    * un csv des overquotas
    * un csv des identifiants ENT (général ou juste une màj)
    * un csv des identifiants réseau péda. (export ATOS dans PASSWORDS)
    
    1. envoi de messages aux profs principaux pour les dépassements de quota (scribe)
    2. génération d'un document .odt par classe des identifiants ENT pour les
       tuteurs sur une mise à jour, envoi des identifiants élèves aux PP (elycee)
    3. génération globale des identifiants ENT tuteurs et élèves par classe
       les comptes tuteurs déjà utilisés sont expurgés (elycee)
    4. envoi général des id élèves aux PP (elycee)
    5. envoi général des id tuteurs aux PP (elycee)
    6. envoi des nouveaux identifiants réseau élèves aux PP (atos)
    7. quitter

    """
    global Dumper
    global Loader

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.grid()         
        # paramètres généraux
        home = expanduser("~/.refnumtool.d")
        #creation des fichiers de config si ils n'existent pas.
        ConfFiles=[("config.yaml",param.config),
                   ("text_extract_tuteur.yaml",param.extract_tuteur),
                   ("textquota.yaml",param.txtquota),
                   ("textidnew.yaml",param.txtidnew),
                   ("textidrezonew.yaml",param.txtidrezonew),
                   ("textidgen.yaml",param.txtidgen)]
        for e in ConfFiles:
            PATH = join(home,e[0]) # chemin complet vers fichier de conf
            if not(exists(PATH)):
                print("création "+PATH)
                self.init_config(e[1], PATH)
                
        # chargement des paramètres généraux
        confpath = join(home,"config.yaml")
        with open(confpath,"r") as conf_file:
            self.config = load(conf_file, Loader=Loader)
        print("chargement du fichier des professeurs principaux")    
        self.mailing  = Mailing(self.config)
        self.options = {'1': self._quota, '2': self._idnew,
                        '3': self.mailing.admin_idgen,
                        '4': self.mailing.admin_idrezogen,
                        '5': self._idgen,
                        '6': self._idgentu, '7': self._idrezonew,
                        '8': lambda: self._idgen(filtre_entrants=True),
                        '9': self._exit}

        self.__call__()
        
    def __call__(self):
        choix = ["1: envoi des overquotas aux pp (scribe)",
                 "2: génération d'un .odt tuteurs, envoi des nouveaux id aux pp (elycee)",
                 "3: génération de tous les id ENT par classe (elycee)",
                 "4: génération de tous les id réseau par classe (Atos)",
                 "5: envoi des id élèves globaux aux PP (elycee)",
                 "6: envoi des id tuteurs globaux aux PP (elycee)",
                 "7: envoi des nouveaux id réseau péda. aux pp (atos)",
                 "8: envoi des id élèves globaux aux PP + filtre no_entrants (elycee)",
                 "9: quitter"]
        
        print(*choix, sep='\n')
        IN = input("choisir 1,2,3,4,5,6,7,8,9 :")
        while IN not in "123456789":
            IN = input("choisir 1,2,3,4,5,6,7,8,9 :")
        self.options[IN]()

    def init_config(self, val, path):
        """créer ou réinitialiser un fichier yaml de config

        :param val: valeurs à enregistrer
        :type val: dict list ou autre
        :param path: chemin d'enregistrement
        :type path: str
        """
        with open(path, "w") as f:
            dump(val, f, Dumper=Dumper,default_flow_style=False)
            # False permet d'avoir la syntaxe basique de yaml

    def _quota(self):
        self.mailing.admin_quota()
        pp = [v for v in self.mailing.PP.values() if "over" in v]
        print(len(pp), " profs à contacter")
        a = input("poursuivre?(o/n) ")
        if a == 'o':
            self.mailing.mailing("quota")
        else:
            self.mailing._save_config()
            self.__call__()
            
    def _idnew(self):
        self.mailing.admin_idnew()
        #générer un .odt des identifiants Tuteur.    
        pp = [e for e in self.mailing.PP.values() if "Eleve" in e]
        pptu = [e for e in self.mailing.PP.values() if "Tuteur" in e]
        
        for prof in pptu:
            tuteurs = parentId(self.mailing.pathid, maj=True, data=prof)
        print("fichiers des nouveaux identifiants généré pour "+str(self.mailing.nbtu)+" tuteurs")

        print(len(pp), " profs à contacter pour élèves")
        print(len(pptu), " profs à contacter pour tuteurs")
        a = input("poursuivre?(o/n) ")
        if a == 'o':
            self.mailing.mailing("idnew")
        else:
            self.mailing._save_config()
            self.__call__()

    def _idrezonew(self):
        self.mailing.admin_idrezonew()
        # réduire la liste de liste des pp
        pp = reduce(lambda x,y: x+y,
                    [[prof for prof in self.mailing.PP[classe] if "Eleve" in prof] for classe in self.mailing.PP])
        print(len(pp), " profs à contacter pour élèves - nv id réseau péda.")
        a = input("poursuivre?(o/n) ")
        if a == 'o':
            self.mailing.mailing("idrezonew")
        else:
            self.mailing._save_config()
            self.__call__()
            
    def _idgen(self, filtre_entrants=False):
        self.mailing._set_iddirectory("dossier des identifiants")
        self.mailing._set_prof("elycee")
        if not(filtre_entrants):
            a = input("envoyer les id élèves à tous les PP?(o/n) ")
        else:
            a = input("envoyer les id élèves à tous les PP des non entrants?(o/n) ")
        if a == 'o':
            self.mailing.mailing("idgen", filtre_entrants=filtre_entrants)
        else:
            self.mailing._save_config()
            self.__call__()

    def _idgentu(self):
        self.mailing._set_iddirectory("dossier des identifiants")
        self.mailing._set_prof("elycee")
        a = input("envoyer les id tuteurs à tous les PP?(o/n) ")
        if a == 'o':
            self.mailing.mailing("idgentu")
        else:
            self.mailing._save_config()
            self.__call__()

    def _exit(self):
        exit()
