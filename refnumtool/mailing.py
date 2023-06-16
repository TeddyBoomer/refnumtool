#/bin/env python3
# -*- coding: utf-8 -*-

import csv
import time
import re
import tkinter as tk
from functools import reduce
from tkinter.filedialog import askopenfilename, askdirectory
from os.path import basename, dirname, join, isdir, exists, expanduser
from os import mkdir, sep
from yaml import load, dump
from shutil import copyfile
from getpass import getpass

from refnumtool.id_extractor import Extractor, ExtractorAtos
import refnumtool.parametre as param

import ssl
import smtplib
import mimetypes
from email import encoders
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

class Mailing():
    """Objet pour diffusion aux profs principaux.
    L'initialisation demande de choisir un fichier csv des PP.

    self.PP: dict des données prof, clé: nom de classe elycee, valeur: dictionnaire des champs profs
    chaque dictionnaire valeur acquiert une clé supplémentaire "Eleve" ou "Tuteur" contentant la liste
    des dico des nouveaux élèves ou tuteurs.

    """
    def __init__(self, param=dict()):
        try:
            from yaml import CLoader as Loader
        except ImportError:
            from yaml import Loader

        self.config = param
        initdir = (self.config["initialdir"] if "initialdir" \
                   in self.config else "")
        self._update_config(("initialdir", initdir))

        home = expanduser("~/.refnumtool.d")
        ATTRIB = {'textquota': join(home,"textquota.yaml"),
                  'textidnew': join(home,"textidnew.yaml"),
                  'textidrezonew': join(home,"textidrezonew.yaml") ,
                  'textidgen': join(home,"textidgen.yaml")}
        for k,v in ATTRIB.items():
            with open(v,"r") as conf_file:
                setattr(self, k, load(conf_file, Loader=Loader))
            
        self.pathprof = askopenfilename(initialdir=self.config["initialdir"],\
                                        defaultextension=".csv",\
                                        title="Fichier des profs principaux",\
                                        filetypes=[("CSV", "*.csv")])
        self._update_config(("initialdir", dirname(self.pathprof)))
        self.logfile = join(dirname(self.pathprof), "log_refnumtool"+\
                            time.strftime("%d%m%Y-%H-%M-%S")+".log")
        self.PP = dict()

    def _update_config(self, pair):
        self.config.update(dict([pair]))

    def _save_config(self):
        try:
            from yaml import CDumper as Dumper
        except ImportError:
            from yaml import Dumper
        #out = dump(self.config, Dumper=Dumper)
        home = expanduser("~/.refnumtool.d")
        with open(join(home,"config.yaml"), "w") as f:
            dump(self.config, f, Dumper=Dumper,default_flow_style=False )

    def _switch_test(self):
         self.config["test"]=not(self.config["test"])

    def _set_prof(self, choix):
        """charge les données prof

        :param choix: in ["elycee", "quota", "atos"]

        désormais les values de self.PP sont des lists
        """
        #nom de l'entrée csv
        ext = (choix if choix in ["elycee", "atos"] else "scribe")
        # remplissage profs
        fprof = open(self.pathprof, encoding="utf8")
        dialect = csv.Sniffer().sniff(fprof.readline())
        fprof.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(fprof, dialect=dialect)
        for e in reader:
            if e[ext]:
                if e[ext] not in self.PP:
                    self.PP[e[ext]] = [e]
                else: # déjà un pp renseigné pour cette classe
                    self.PP[e[ext]].append(e)
        fprof.close()

    def admin_quota(self):
        """lancer l'analyse des quotas: rempli les dictionnaires self.PP avec une
        clé 'over' contenant la liste des élèves en overquota.

        file: str chemin du fichier de quota
        (copie/colle de la sortie web scribe)
        """
        self.pathquotas = askopenfilename(initialdir=self.config["initialdir"],\
                                          defaultextension=".csv",\
                                          title="Fichier des quotas",\
                                          filetypes=[("CSV", "*.csv")])
        self._set_prof("quota")
        # remplissage élèves csv file
        #analyse de la colonne "Utilisateur"
        GET_ELEVE = re.compile("(\w+\.\w+) \(élève de ([^)]+)")
        quota = open(self.pathquotas, "r") #, encoding="latin1"
        dialect=csv.Sniffer().sniff(quota.readline())
        quota.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(quota, dialect=dialect)
        self.nbel = 0 #nb élèves
        for e in reader:
            a = GET_ELEVE.search(e["Utilisateur"])
            if a and "over" in self.PP[a.group(2)]:
                (self.PP[a.group(2)]["over"]).append(a.group(1))
                self.nbel += 1 #nb élèves
            elif a:
                self.PP[a.group(2)]["over"] = [a.group(1)]
                self.nbel += 1 #nb élèves
        quota.close()

    def admin_idnew(self):
        """lancer l'analyse des nouveaux identifiants: rempli les dictionnaires
        self.PP avec une clé 'Eleve' et ou 'Tuteur' contenant la liste
        des nouveaux élèves et tuteurs.
        """
        self._set_pathid(invite="Fichier des *nouveaux identifiants*")
        self._set_prof("elycee")

        # remplissage élèves et tuteurs
        fid = open(self.pathid, "r", encoding="latin1")
        dialect=csv.Sniffer().sniff(fid.readline())
        fid.seek(0) # se remettre en début de fichier, le sniff a lu 1 ligne
        reader = csv.DictReader(fid, dialect=dialect)
        self.nbel = 0 #nb élèves
        self.nbtu = 0 #nb tuteurs
        for e in reader:
            if e["profil"] in ["Eleve", "Tuteur"]:
                p = e["profil"]
                self.nbel +=(1 if p=="Eleve" else 0)
                self.nbtu +=(1 if p== "Tuteur" else 0)
                if p not in self.PP[e["classe"]]:
                    self.PP[e["classe"]][p] =[e]
                else:
                   self.PP[e["classe"]][p].append(e)
        fid.close()

    def admin_idrezonew(self):
        """lancer l'analyse des nouveaux identifiants réseau péda (atos): rempli les
        dictionnaires self.PP avec une clé 'Eleve' liste des nouveaux élèves.

        """
        self._set_pathid(invite="Fichier des *nv identifiants - réseau péda.*")
        self._set_prof("atos")

        # remplissage élèves
        fid = open(self.pathid, "r", encoding="utf-16")
        self.nbel = 0 #nb élèves
        LIGNE = fid.readline()
        # issu de id_extractor.py: choix de séparateur de champ
        sep = (";" if ";" in LIGNE else ",")
        while LIGNE:
            TYPE, prenom, nom, login,classe, mdp = LIGNE.split(sep)
            mdp = mdp[:-1] #enlever le \n final
            if TYPE == "Eleve": # il peut aussi être PersEducNat
                self.nbel +=1
                # parcourir la liste du/des PP de la classe
                for prof in self.PP[classe]:
                    if TYPE not in prof: # self.PP[classe]
                        prof[TYPE] =[{'prenom':prenom, 'nom': nom,\
                                                  'login':login, 'mdp':mdp}]
                    else:
                        prof[TYPE].append({'prenom':prenom,\
                                                      'nom': nom,\
                                                      'login':login,\
                                                      'mdp':mdp})
            LIGNE = fid.readline()
        fid.close()

        
    def admin_idgen(self):
        """génération des fichiers d'identifiants ENT par classe.
        """
        self._set_pathid("Fichier général des identifiants ENT")
        self._set_prof("elycee")
        I = Extractor(self.pathid)
        # rediriger le chemin vers le dossier des id.
        self.pathid = join(dirname(self.pathid), "identifiantsENT")

    def admin_idrezogen(self):
        """génération des fichiers d'identifiants réseau par classe.
        (fichier csv Atos)
        """
        self._set_pathid("Fichier général des identifiants Atos")
        self._set_prof("elycee")
        I = ExtractorAtos(self.pathid)
        # rediriger le chemin vers le dossier des id.
        # self.pathid = join(dirname(self.pathid), "identifiantsAtos")

    def _set_pathid(self, invite=""):
        self.pathid = askopenfilename(initialdir=self.config["initialdir"],\
                                      defaultextension=".csv",\
                                      title=invite,\
                                      filetypes=[("CSV", "*.csv")])
        self.config["initialdir"] = dirname(self.pathid)

    def _set_iddirectory(self, invite):
        self.pathid = askdirectory(title=invite,\
                                   initialdir=self.config["initialdir"],)
        
    def mailing(self, cible, filtre_entrants=False):
        """fonction de mailing aux profs principaux
        les paramètres sont lus dans self.config importé de refnumtool.

        :param cible: in ["quota", "idgen", "idnew", "idgentu", "idrezonew]
        :type cible: str
        :param test: indique si on simule le mailing auquel cas, l'adresse de\
        sortie est default_to
        :type test: boolean
        :param dir: directory where to look for message attachments
        :type dir: str
        :param default_to: default target mail adr in case of test
        :type default_to: str
        :param default_from: who is sending
        :type default_from: str
        :param smtp: smtp relay name
        :type smtp: str
        :param port: port value for the relay 587 for secured transaction.
        :type port: int

        ajout d'un filtre des entrants (qui seront dans educonnect) pour idnew idgen et idgentu
        """

        cfg = self.config
        smtprelay = ('localhost' if cfg["test"] else cfg["smtp"])
        s = (smtplib.SMTP(smtprelay) if (cfg["test"] or (cfg["port"] not in [465, 587]))\
             else smtplib.SMTP(smtprelay, port=cfg["port"]))
        # s = smtplib.SMTP(smtprelay, port=cfg["port"])
        #smtplib.SMTP_SSL(smtprelay, port=cfg["port"]))
        #login et mdp
        #en clair mais que pour qq secondes sur un écran et pas sur le réseau.
        if not(cfg["test"]) and cfg["port"] in [465, 587]:
            if "login" not in cfg:
                cfg["loging"] = input("Entrez votre login sur le serveur "+\
                              cfg["smtp"]+": ")
            # pwd = input("pwd (en clair, dsl) :")
            pwd = getpass("pwd (valider avec Enter)")
            context = ssl.create_default_context()
            s.starttls(context=context)
            s.login(cfg["login"], pwd)

        LOG = open(self.logfile, "w")
        if cible == "quota":
            pp = [self.PP[e] for e in self.PP if "over" in self.PP[e]]
            COUNT = 0
            for E in pp:
                n = len(E["over"]) # nb d'overquotas
                msg = self.textquota[0]+E["scribe"]+".\n"
                msg += self.textquota[1]
                for x in E["over"]:
                    msg+= x+"\n"
                msg += self.textquota[2]
                msg += cfg["sig"]
                M = MIMEText(msg, _charset='utf-8')
                M['Subject'] = str(n)+' dépassement'+("s" if n>=2 else "") +\
                               " de quota en "+E["scribe"]
                M['From'] = cfg["sender"]
                M['To'] = (cfg["default_to"] if cfg["test"] else E["E-mail"])
                try:
                    COUNT += 1
                    s.send_message(M)
                    print("1 msg à "+E["Nom"]+" " +E["Prénom"]+ " - " + M['To'],
                          file=LOG)
                except: # catch all exceptions
                    print("Erreur: "+E["Nom"]+" " +E["Prénom"]+ " - " +\
                          M['To'], file=LOG)
            print(self.nbel, " élèves détectés", file=LOG)
            print(str(COUNT)+" profs contactés", file=LOG)
            print(self.nbel, " élèves détectés")
            print(str(COUNT)+" profs contactés")
        elif cible == "idnew":
            pathid = dirname(self.pathid)
            # filtrer seulement les élèves pour les pp?
            if filtre_entrants:
                pp = reduce(lambda x,y: x+y, [self.PP[e] for e in self.PP if (e not in cfg["entrants"]) and ("Eleve" in self.PP[e])]) # ajout filtre entrants
            else:
                pp = reduce(lambda x,y: x+y,  [v for v in self.PP.values() if ("Eleve" in v)]) # ajout filtre entrants
                # [self.PP[e] for e in self.PP if "Eleve" in self.PP[e]]
            # pp = [v for v in self.PP.values() if ("Eleve" in v)]
            COUNT = 0
            COUNTPP = 0
            for E in pp:
                n = len(E["Eleve"]) # nb nv élèves
                COUNT += n
                msg = self.textidnew[0]+E["elycee"]+".\n"
                msg += self.textidnew[1]
                for x in E["Eleve"]:
                    msg+= x["nom"]+ " " +x["prenom"]+ " : "+x["login"] +" -- "+x["mot de passe"]+"\n"
                msg += self.textidnew[2]
                msg += cfg["sig"]

                M = MIMEText(msg, _charset='utf-8')
                M['Subject'] = str(n)+' élève'+("s" if n>=2 else "") +\
                               " en "+E["elycee"]+" - identifiants ENT"
                M['From'] = cfg["sender"]
                M['To'] = (cfg["default_to"] if cfg["test"] else E["E-mail"])
                try:
                    COUNTPP += 1
                    s.send_message(M)
                    print("1 msg (élèves-ENT) à "+E["Nom"]+" " +E["Prénom"]+ " - " + M['To'],
                          file=LOG)
                except: # catch all exceptions
                    print("Erreur: "+E["Nom"]+" " +E["Prénom"]+ " - " +\
                          M['To'], file=LOG)
            print(COUNT, "nouveaux élèves", file=LOG)
            print(str(COUNTPP)+" profs contactés (élèves-ENT)", file=LOG)
            print(COUNT, "nouveaux élèves")
            print(str(COUNTPP)+" profs contactés (élèves-ENT)")

            pptu = [v for v in self.PP.values() if "Tuteur" in v]
            COUNT = 0
            COUNTPP = 0
            for E in pptu:
                # fichier odt
                F = join(pathid, "ENT_id_Tuteur_"+E["elycee"]+"_"+time.strftime("%d%m%Y")+".odt")
                n = len(E["Tuteur"]) # nb nv tuteurs
                COUNT += n # ne marche pas, double triple si plusieurs pp
                msg = self.textidnew[0]+E["elycee"]+".\n"
                msg += self.textidnew[3]
                msg += "\n"+cfg["sig"]
                M = MIMEMultipart()
                M['Subject'] = str(n)+' tuteur'+("s" if n>=2 else "") +\
                               " en "+E["elycee"]+" - identifiants ENT"
                M['From'] = cfg["sender"]
                M['To'] = (cfg["default_to"] if cfg["test"] else E["E-mail"])
                M.attach(MIMEText(msg, 'plain', _charset='utf-8'))                
                #open and join a file
                ctype = (mimetypes.guess_type(basename(F)))[0]
                maintype, subtype = ctype.split('/', 1)
                with open(F, 'rb') as f:
                    p = MIMEBase(maintype, subtype)
                    p.set_payload(f.read())
                    encoders.encode_base64(p)
                    p.add_header('Content-Disposition', 'attachment',
                                 filename=basename(F))
                    M.attach(p)
                try:
                    COUNTPP += 1
                    s.send_message(M)
                    print("1 msg (tuteurs) à "+E["Nom"]+" " +E["Prénom"]+ " - " + M['To'],
                          file=LOG)
                except: # catch all exceptions
                    print("Erreur (tuteurs): "+E["Nom"]+" " +E["Prénom"]+ " - " +\
                          M['To'], file=LOG)
            print(COUNT, "nouveaux tuteurs", file=LOG)
            print(str(COUNTPP)+" profs contactés (tuteurs-ENT)", file=LOG)
            print(COUNT, "nouveaux tuteurs")
            print(str(COUNTPP)+" profs contactés (tuteurs-ENT)")

        elif cible == "idrezonew":
            pathid = dirname(self.pathid)
            # filtrer seulement les élèves pour les pp?
            # pp = [v for v in self.PP.values() if "Eleve" in v]
            pp = reduce(lambda x,y: x+y,
                        [[prof for prof in self.PP[classe] if "Eleve" in prof]
                         for classe in self.PP])
            #COUNT = 0
            COUNTPP = 0
            for E in pp:
                n = len(E["Eleve"]) # nb nv élèves
                #COUNT += n
                msg = self.textidrezonew[0]+E["atos"]+".\n"
                msg += self.textidrezonew[1]
                for x in E["Eleve"]:
                    msg+= x["nom"]+ " " +x["prenom"]+ " : "+x["login"] +" -- "+x["mdp"]+"\n\n"
                msg += self.textidrezonew[2]
                msg += cfg["sig"]

                M = MIMEText(msg, _charset='utf-8')
                M['Subject'] = str(n)+' élève'+("s" if n>=2 else "") +\
                               " en "+E["atos"] + " - identifiants réseau lycée"
                M['From'] = cfg["sender"]
                M['To'] = (cfg["default_to"] if cfg["test"] else E["E-mail"])
                try:
                    COUNTPP += 1
                    s.send_message(M)
                    print("1 msg (élèves-r.péda) à "+E["Nom"]+" " +E["Prénom"]+ " - " + M['To'],
                          file=LOG)
                except: # catch all exceptions
                    print("Erreur: "+E["Nom"]+" " +E["Prénom"]+ " - " +\
                          M['To'], file=LOG)
            print(self.nbel, "nouveaux élèves", file=LOG)
            print(str(COUNTPP)+" profs contactés (élèves-réseau péda)", file=LOG)
            print(self.nbel, "nouveaux élèves")
            print(str(COUNTPP)+" profs contactés (élèves-réseau péda)")

        elif cible == "idgen":
            pathid = self.pathid
            if filtre_entrants:
                pp = reduce(lambda x,y: x+y, [self.PP[e] for e in self.PP if e not in cfg["entrants"]]) # ajout filtre entrants
            else:
                pp = reduce(lambda x,y: x+y, [self.PP[e] for e in self.PP]) # ajout filtre entrants
            COUNT = 0
            for E in pp:
                msg=self.textidgen[0]+E["elycee"]+".\n"
                msg += self.textidgen[1]
                msg += cfg["sig"]
                M = MIMEMultipart()
                M['Subject'] = "liste des comptes élève en "+E["elycee"]
                M['From'] = cfg["sender"]
                M['To'] = (cfg["default_to"] if cfg["test"] else E["E-mail"])
                M.attach(MIMEText(msg, 'plain', _charset='utf-8'))
                #ajouter la pj liée au pp, le nom du fichier doit être:
                F = join(pathid, "ENT_id_Eleve_"+E["elycee"]+".odt")
                F2 = join(pathid, "ENT_id_Eleve_"+E["elycee"]+".csv")
                #open and join a file
                ctype = (mimetypes.guess_type(basename(F)))[0]
                maintype, subtype = ctype.split('/', 1)
                ctype2 = (mimetypes.guess_type(basename(F)))[0]
                maintype2, subtype2 = ctype2.split('/', 1)
                try:
                    with open(F, 'rb') as f:
                        # creation du message
                        p = MIMEBase(maintype, subtype)
                        p.set_payload(f.read())
                        encoders.encode_base64(p)
                        p.add_header('Content-Disposition', 'attachment',
                                     filename=basename(F))
                        M.attach(p)
                    with open(F2, 'rb') as f2:
                        p2 = MIMEBase(maintype2, subtype2)
                        p2.set_payload(f2.read())
                        encoders.encode_base64(p2)
                        p2.add_header('Content-Disposition', 'attachment',
                                     filename=basename(F2))
                        M.attach(p2)
                    COUNT += 1
                    s.send_message(M)
                    print("1 msg+pj à "+E["Nom"]+" " +E["Prénom"]+ " - " +E["elycee"]+" - "+ M['To'],
                          file=LOG)
                except: # catch all exceptions
                    print("Erreur: "+E["Nom"]+" " +E["Prénom"]+ " - " +E["elycee"]+ " - " +\
                          M['To'], file=LOG)
            print(str(COUNT)+" profs contactés (id élèves)", file=LOG)
            print(str(COUNT)+" profs contactés (id élèves)")

        elif cible == "idgentu":
            pathid = self.pathid
            if filtre_entrants:
                pp = reduce(lambda x,y: x+y, [self.PP[e] for e in self.PP if e not in cfg["entrants"]]) # ajout filtre entrants
            else:
                pp = reduce(lambda x,y: x+y, [self.PP[e] for e in self.PP]) # ajout filtre entrants
            # pp = [self.PP[e] for e in self.PP]
            COUNT = 0
            for E in pp:
                msg=self.textidgen[0]+E["elycee"]+".\n"
                msg += self.textidgen[2]
                msg += cfg["sig"]
                M = MIMEMultipart()
                M['Subject'] = "fichier des comptes tuteurs en "+E["elycee"]
                M['From'] = cfg["sender"]
                M['To'] = (cfg["default_to"] if cfg["test"] else E["E-mail"])
                M.attach(MIMEText(msg, 'plain', _charset='utf-8'))
                #ajouter la pj liée au pp, le nom du fichier doit être:
                # F = join(pathid, "ENT_id_Tuteur_"+E["elycee"]+".odt")
                # essai en .pdf; 
                # appliquer le script d'impression vers PDF d'abord
                F = join(pathid, "ENT_id_Tuteur_"+E["elycee"]+".pdf")
                #open and join a file
                ctype = (mimetypes.guess_type(basename(F)))[0]
                maintype, subtype = ctype.split('/', 1)
            
                with open(F, 'rb') as f:
                    p = MIMEBase(maintype, subtype)
                    p.set_payload(f.read())
                    encoders.encode_base64(p)
                    p.add_header('Content-Disposition', 'attachment',
                                 filename=basename(F))
                    M.attach(p)
                try:
                    COUNT += 1
                    s.send_message(M)
                    print("1 msg+pj à "+E["Nom"]+" " +E["Prénom"]+ " - " + M['To'],
                          file=LOG)
                except: # catch all exceptions
                    print("Erreur: "+E["Nom"]+" " +E["Prénom"]+ " - " +\
                          M['To'], file=LOG)
            print(str(COUNT)+" profs contactés (id tuteurs)", file=LOG)
            print(str(COUNT)+" profs contactés (id tuteurs)")

        LOG.close()
        self.config = cfg
        s.quit()
        self._save_config()
