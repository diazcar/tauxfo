# -*- coding: utf-8 -*-
"""
Created on Thu Jan  4 11:14:26 2024

@author: ibrahima.coly
"""


#---------------------------------------   INFO  ---------------------------------------------------------------------------------#
#                                                                                                                                 #
#-   Ce script trace des graphiques représentants les niveaux horaires (mesure Atmosud) des métaux (composition chimique du PM1) sur la station Fos les carabins
# Le script tabe sur la base de données Xr via l'API                         
#                                                                                                                                 #
#---------------------------------------------------------------------------------------------------------------------------------#        



############################### Importation des bibliothéques ###################################################################
### Modules python
import os, sys, datetime, glob, urllib
import argparse # prise en compte des arguments
import logging # affiche log 
import numpy as np # fct math sur tableau vecteur... 
import pandas # traitement de csv
import matplotlib.pyplot as plt # affichage plot
import time 
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import webbrowser
#from plotly.graph_objs import parcats
from plotly.graph_objs.parcats import Line
import math 
import matplotlib.quiver as qr
import mpld3
import scp
#from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient
import netCDF4
#import libmto
#from libmto import Commune
from liblog import log
import markdown
from flask import Flask, Markup, render_template, make_response, request
import matplotlib.dates as mpld
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import matplotlib.dates as mdates
import seaborn as sns
sns.set(style='whitegrid')
sns.set(font_scale=1.5)



##################################################################################################
### Initialisation du script Argument et log des bugs

# Fonction en une ligne "lambda" pour transforme le string en date 
parse_date = lambda val: datetime.strptime(val, "%Y%m%d") #"%Y%m%d%H")


        
# Argument Parser : definition et presentation des arguments dans l'aide -h
parser = argparse.ArgumentParser(description="Analyse episode PM")
parser.add_argument("-v", "--verbose", default=0, action="count",
					help="Increase verbosity level")
parser.add_argument("date", type=parse_date, default=datetime.now(),
					nargs="?", # si absent prendre valeur "default"
					help="date jour de fin de l'analyse au format YYYYMMDD")
parser.add_argument("nbj_analyse", type=int, default=15,
					nargs="?", # si absent prendre valeur "default"
					help="nbr de jour pour l'analyse, par défaut nbj=15")
parser.add_argument("-o", "--output", type=str, default="output", help="dossier de sortie des graphiques") 


args = parser.parse_args()

LEVELS = [logging.WARNING, logging.INFO, logging.DEBUG]
if args.verbose < len(LEVELS):
	level = LEVELS[args.verbose]
else:
	level = logging.DEBUG
logging.basicConfig(level=level, format="%(asctime)s %(levelname)s : %(message)s")



########################### Configuration des dates et nombres de jour d'analyse #######################################################################

#level=30
date=datetime.now()
print(date.strftime("%Y%m%d"))
nbj_analyse=180
datej_debut = datetime.strptime(date.strftime("%Y%m%d"), "%Y%m%d") - timedelta(nbj_analyse)
datej_fin = datetime.strptime(date.strftime("%Y%m%d"), "%Y%m%d") + timedelta(-1)
#datej_debut = datetime.strptime(args.date.strftime("%Y%m%d"), "%Y%m%d") - timedelta(args.nbj_analyse)
#datej_fin = datetime.strptime(args.date.strftime("%Y%m%d"), "%Y%m%d") + timedelta(1)

str_datej_debut = datej_debut.strftime("%Y-%m-%d")        # mise sous format AAAA-MM-JJ
str_datej_fin = datej_fin.strftime("%Y-%m-%d")            # mise sous format AAAA-MM-JJ

logging.debug(" datej prise en comtpe : %s " % args.date)
logging.debug(" nbj_analyse pris en comtpe : %s " % args.nbj_analyse)

logging.info(" Période prise en compte pour l'analyse : %s " % str(str_datej_debut + ' au ' + str_datej_fin))



##################################################################################################
### Définition du répertoire de travail
#
#N:/MOD_SERVER/ADMS_URBAN/maj_admsurban_v5/graphique_AE33_PACA/output_graphique
os.chdir("Z:/icoly/doc_mesure_Xact_metaux_en_ligne") 
cwd = os.getcwd()
logging.info("Dossier de travail : % s \n" % cwd)


##################################################################################################
### Debut programme
pio.renderers.default="browser"              #pour afficher les plots dans le navigateur par défaut



#---------------------------------------- PARAMETRASE DES VARIABLES ---------------------------------------------------------
#                                                                                                                           |
################################### Les variables: codes iso des polluants  ################################################|
#                                                                                                                           |
# Vous pouvez changer le code iso selon le polluant 
# respectivement Aluminium dans le PM1,, silicium dans le PM1, souffre dans le PM1, Chlore dans le PM1, Potassium dans le PM1, 
# Vanadium dans le PM1, Chrome dans le PM1, Nickel dans le PM1, Zinc dans le PM1, Arsenic dans le PM1                                                                       
code_iso_polluant = '9G, 9q, 9h, 9U, 9c, 9u, 9W, 9e, 9v, 9I'#, 80, 83, 87, 88, 92'      
                                                                                                                           
#                                                                                                                           |
#                                                                                                                           |
################################### Références des stations météo France ###################################################|
#------------------- Pour les mesures de directions et de vitesses du vent ------------------------------------------------#|
# Vous pouvez égualement changer de références selon les sites    
                                                          
#Aref_MetFra = '83969'  #                                                                                                     |
                                                                                                                           
#                                                                                                                           |
#                                                                                                                           |
################################## Référence des sites de mesures AtmoSud ##################################################|
#--------------------- Pour les mesures de polluants dans les sites de références ci-dessous ------------------------------#|
# Pensez à chaanger de référence pour des mesures dans d'autre sites      
                                                  
ref_sites_AtmoSud = '83013' #   Fos les Carabins                                                                                            |
                                                                                                                           
#---------------------------------------------  FIN  ------------------------------------------------------------------------



#############################################################################################################################
#-------------------------------------- liste de paramètres dans XR --------------------------------------------------------#
urlcompose = "https://172.16.13.224:8443/dms-api/public/v1/physicals"
response = requests.get(urlcompose, verify = False).json()
df_parametre = pandas.DataFrame(response['physicals'])

# ---------------------- liste de sites valides du groupe DIDON dans XR ----------------------------------------------------#
#ref_site = '83926, 83927'
#url_sites_metfra = "https://172.16.13.224:8443/dms-api/public/v1/sites?&groups=MetFra"

#url_sites_metfra = "https://172.16.13.224:8443/dms-api/public/v1/sites?refSites="+ref_MetFra
#response = requests.get(url_sites_metfra, verify = False).json()
#df_sites_MetFra = pandas.DataFrame(response['sites'])


# ---------------------- liste de sites valides du groupe DIDON dans XR ----------------------------------------------------#
url_sites_atmosud = "https://172.16.13.224:8443/dms-api/public/v1/sites?&validOnly=true&groups=DIDON"
response = requests.get(url_sites_atmosud, verify = False).json()
df_sites_AtmoSud = pandas.DataFrame(response['sites'])





############################################ Pour le(s) polluant(s) ##########################################################

codes_iso = code_iso_polluant.split(', ')

# -------------------- liste des mesures valides Xr du groupe DIDON pour un ou plusieurs code ISO ---------------------------#
df_mesure_metaux = pandas.DataFrame()

for code_iso in codes_iso:
    url_measures = "https://172.16.13.224:8443/dms-api/public/v1/measures?refSites=" + ref_sites_AtmoSud + "&physicals=" + code_iso
    #print(url_measures)

    response = requests.get(url_measures, verify=False).json()
    df_mesure_code_iso = pandas.DataFrame(response['measures'])

    # pour ajouter les mesures du code ISO actuel au DataFrame total
    df_mesure_metaux = pandas.concat([df_mesure_metaux, df_mesure_code_iso], ignore_index=True)



#---------------------------- Données horaires -------------------------------------------------------------#
#df_mesure_SO2['nom_court_site_mesure'] = df_mesure_SO2['label'].apply(lambda x: x.split('2')[1])

dico_Fig={}
# boucle sur les id site unique pour récupérer l'id pour la mesure
for s in df_mesure_metaux['id_site']:
    print("Nom du site : "+ s)
    #print(df_mesure_site[df_mesure_site['id_site']==i]['id'])
    
    # Definition d'un dataframe vide pour mettre les mesures pour faire les graphiques
    DF_graphique_metaux = pandas.DataFrame([])
    dicoDF_graphique={}
    # Boucle sur les id mesures obtenues pour récupérer les données
    for j in sorted(list(df_mesure_metaux[df_mesure_metaux['id_site']==s]['id'])):
        print("Nom de la mesure : " + j)
        #"url_data="https://172.16.13.224:8443/dms-api/public/v1/data?from=2023-04-011T00:00:00Z&to=2023-04-023T00:00:00Z&validOnly=TRUE&dataTypes=hourly&measures="+j
        url_data="https://172.16.13.224:8443/dms-api/public/v1/data?from="+str_datej_debut+"T00:00:00Z&to="+str_datej_fin+"T00:00:00Z&validOnly=TRUE&dataTypes=hourly&measures="+j
        response = requests.get(url_data, verify = False).json()
        df_out_metaux = pandas.DataFrame([])
        for i in response["data"][0]['hourly']:
            #print(i)
            df_temp = pandas.DataFrame([])
            date = pandas.DataFrame([i["date"]])
            valeur = pandas.DataFrame([i["value"]])
            code_qa = pandas.DataFrame([i["state"]])
            niv_valid = pandas.DataFrame([i["validated"]])
            df_temp = pandas.concat([df_temp, date, valeur,code_qa,niv_valid], axis = 1)
            # On nomme les colonnes du tableau avec le nom de la mesure 
            # print("Nom des colonnes avec "+j)
            df_temp.columns = ['date' , str('valeur_'+j), str('code_qa_'+j), str('niv_valid_'+j)]
            df_out_metaux = pandas.concat([df_out_metaux, df_temp])
            
        # Fin boucle sur les concentrations du json
        # print(df_out)
        dicoDF_graphique[str('df_'+j)]=df_out_metaux
        df_out_metaux = df_out_metaux.reset_index(drop=True).set_index(pandas.RangeIndex(start=1, stop=len(df_out_metaux)+1))
        DF_graphique_metaux = DF_graphique_metaux.reset_index(drop=True).set_index(pandas.RangeIndex(start=1, stop=len(DF_graphique_metaux)+1))
        index_communs = list(set(df_out_metaux.index) & set(DF_graphique_metaux.index))
       
        # Réindexer les deux dataframes avec l'index commun 
        DF_graphique_metaux= pandas.concat([DF_graphique_metaux, df_out_metaux], axis = 1)
        
# respectivement Aluminium dans le PM1,, silicium dans le PM1, souffre dans le PM1, Chlore dans le PM1, Potassium dans le PM1, Vanadium dans le PM1, Chrome dans le PM1, Nickel dans le PM1, Zinc dans le PM1, Arsenic dans le PM1                                                                         
df_mesures = DF_graphique_metaux.iloc[:, [0, 1, 5, 9, 13, 17, 21, 25, 29, 33, 37]]  
df_mesures.columns = ["Date","Aluminium(Al)", "Arsenic(As)", "Chlore(Cl)", "Chrome(Cr)", "Potassium(K)", "Nickel(Ni)", "Souffre(S)", "Silicium(Si)", "Vanadium(V)", "Zinc(Zn)"]
dates_column = df_mesures.iloc[:, 0]
# je convertie les valeur ng/m³ à µg/m³ (à partir de la deuxième colonne)
df_mesures.iloc[:, 1:] = df_mesures.iloc[:, 1:] * 0.001
df_mesures.iloc[:, 0] = dates_column

Date = list(df_mesures["Date"])
Aluminium = list(df_mesures["Aluminium(Al)"])
Arsenic = list(df_mesures["Arsenic(As)"])
Chlore = list(df_mesures["Chlore(Cl)"])
Chrome = list(df_mesures["Chrome(Cr)"])
Potassium = list(df_mesures["Potassium(K)"])
Nickel = list(df_mesures["Nickel(Ni)"])
Souffre = list(df_mesures["Souffre(S)"])
Silicium = list(df_mesures["Silicium(Si)"])
Vanadium = list(df_mesures["Vanadium(V)"])
Zinc = list(df_mesures["Zinc(Zn)"])

figMetauxFosCarabins = go.Figure()
figMetauxFosCarabins.add_trace(go.Scatter(x=Date, y=Aluminium, fill="tonexty", name = "Aluminium(Al)")) # fill down to xaxis
figMetauxFosCarabins.add_trace(go.Scatter(x=Date, y=Arsenic, fill="tozeroy", name = "Arsenic(As)")) 
figMetauxFosCarabins.add_trace(go.Scatter(x=Date, y=Chlore, fill="tozeroy", name = "Chlore(Cl)")) 
figMetauxFosCarabins.add_trace(go.Scatter(x=Date, y=Chrome, fill="tozeroy", name = "Chrome(Cr)")) 
figMetauxFosCarabins.add_trace(go.Scatter(x=Date, y=Potassium, fill="tozeroy", name = "Potassium(K)")) 
figMetauxFosCarabins.add_trace(go.Scatter(x=Date, y=Nickel, fill="tozeroy", name = "Nickel(Ni)")) 
figMetauxFosCarabins.add_trace(go.Scatter(x=Date, y=Souffre, fill = "tozeroy", name = "Souffre(S)"))
figMetauxFosCarabins.add_trace(go.Scatter(x=Date, y=Silicium, fill="tozeroy", name = "Silicium(Si)"))
figMetauxFosCarabins.add_trace(go.Scatter(x=Date, y=Vanadium, fill="tozeroy", name = "Vanadium(V)")) 
figMetauxFosCarabins.add_trace(go.Scatter(x=Date, y=Zinc, fill="tozeroy", name = "Zinc(Zn)")) 
figMetauxFosCarabins.update_layout(title="Evolution des niveaux horaires des espèces chimiques PM1 sur Fos les Carabins", xaxis_title="Date",yaxis_title="Concentration moyenne horaire en µg/m3",legend_title="Metaux dans PM1",font=dict(family="Courier New, monospace",size=18,color="RebeccaPurple"))
figMetauxFosCarabins.show()



#---------------------------- Données journalières -------------------------------------------------------------#
#df_mesure_SO2['nom_court_site_mesure'] = df_mesure_SO2['label'].apply(lambda x: x.split('2')[1])
type_de_donnees = 'daily' 

dico_Fig={}
# boucle sur les id site unique pour récupérer l'id pour la mesure
for s in df_mesure_metaux['id_site']:
    print("Nom du site : "+ s)
    #print(df_mesure_site[df_mesure_site['id_site']==i]['id'])
    
    # Definition d'un dataframe vide pour mettre les mesures pour faire les graphiques
    DF_graphique_metaux = pandas.DataFrame([])
    dicoDF_graphique={}
    # Boucle sur les id mesures obtenues pour récupérer les données
    for j in sorted(list(df_mesure_metaux[df_mesure_metaux['id_site']==s]['id'])):
        print("Nom de la mesure : " + j)
        #"url_data="https://172.16.13.224:8443/dms-api/public/v1/data?from=2023-04-011T00:00:00Z&to=2023-04-023T00:00:00Z&validOnly=TRUE&dataTypes=hourly&measures="+j
        url_data="https://172.16.13.224:8443/dms-api/public/v1/data?from="+str_datej_debut+"T00:00:00Z&to="+str_datej_fin+"T00:00:00Z&validOnly=TRUE&dataTypes="+type_de_donnees+"&measures="+j
        response = requests.get(url_data, verify = False).json()
        df_out_metaux = pandas.DataFrame([])
        for i in response["data"][0][type_de_donnees]:
            #print(i)
            df_temp = pandas.DataFrame([])
            date = pandas.DataFrame([i["date"]])
            valeur = pandas.DataFrame([i["value"]])
            code_qa = pandas.DataFrame([i["state"]])
            niv_valid = pandas.DataFrame([i["validated"]])
            df_temp = pandas.concat([df_temp, date, valeur,code_qa,niv_valid], axis = 1)
            # On nomme les colonnes du tableau avec le nom de la mesure 
            # print("Nom des colonnes avec "+j)
            df_temp.columns = ['date' , str('valeur_'+j), str('code_qa_'+j), str('niv_valid_'+j)]
            df_out_metaux = pandas.concat([df_out_metaux, df_temp])
            
        # Fin boucle sur les concentrations du json
        # print(df_out)
        dicoDF_graphique[str('df_'+j)]=df_out_metaux
        df_out_metaux = df_out_metaux.reset_index(drop=True).set_index(pandas.RangeIndex(start=1, stop=len(df_out_metaux)+1))
        DF_graphique_metaux = DF_graphique_metaux.reset_index(drop=True).set_index(pandas.RangeIndex(start=1, stop=len(DF_graphique_metaux)+1))
        index_communs = list(set(df_out_metaux.index) & set(DF_graphique_metaux.index))
       
        # Réindexer les deux dataframes avec l'index commun 
        DF_graphique_metaux= pandas.concat([DF_graphique_metaux, df_out_metaux], axis = 1)

df_mesures = DF_graphique_metaux.iloc[:, [0, 1, 5, 9, 13, 17, 21, 25, 29, 33, 37]]  
df_mesures.columns = ["Date","Aluminium(Al)", "Arsenic(As)", "Chlore(Cl)", "Chrome(Cr)", "Potassium(K)", "Nickel(Ni)", "Souffre(S)", "Silicium(Si)", "Vanadium(V)", "Zinc(Zn)"]
dates_column = df_mesures.iloc[:, 0]
# je convertie les valeur ng/m³ à µg/m³ (à partir de la deuxième colonne)
df_mesures.iloc[:, 1:] = df_mesures.iloc[:, 1:] * 0.001
df_mesures.iloc[:, 0] = dates_column

#histogrammes
figMetauxFosCarabins_journaliers = go.Figure()
figMetauxFosCarabins_journaliers = px.bar(df_mesures, x="Date", y=["Aluminium(Al)", "Arsenic(As)", "Chlore(Cl)", "Chrome(Cr)", "Potassium(K)", "Nickel(Ni)", "Souffre(S)", "Silicium(Si)", "Vanadium(V)", "Zinc(Zn)"], title="Wide-Form Input")
figMetauxFosCarabins_journaliers.update_layout(title="Contributions journalières des espèces chimiques PM1 sur Fos Carabins", bargap=0.2 , xaxis_title="Date",yaxis_title="Concentration moyenne journalière, en µg/m3",legend_title="Métaux dans PM1",font=dict(family="Courier New, monospace",size=18,color="RebeccaPurple"))
figMetauxFosCarabins_journaliers.update_layout(barmode="overlay")
figMetauxFosCarabins_journaliers.show()         




################################################    Pour DV et VV    ######################################################################
code_iso_DV_VV = '51,52' # Pour les direction et vitesse du vent

# -------------------- liste des mesures valides Xr du groupe DIDON pour un ou plusieurs code ISO ----------------------------------------#
url_measures = "https://172.16.13.224:8443/dms-api/public/v1/measures?refSites="+ref_sites_AtmoSud+"&physicals="+code_iso_DV_VV
print(url_measures)
response = requests.get(url_measures, verify = False).json()
df_mesure_vv = pandas.DataFrame(response['measures'])
print(df_mesure_vv)


dico_Fig={}
# boucle sur les id site unique pour récupérer l'id pour la mesure
for k in df_mesure_vv['id_site'].drop_duplicates():
    #k='ISTRES' 
    print("Nom du site : "+ k)
    #print(df_mesure_site[df_mesure_site['id_site']==i]['id'])
    
    # Definition d'un dataframe vide pour mettre les mesures pour faire les graphiques
    DF_graphique_DV_VV = pandas.DataFrame([])
    dicoDF_graphique={}
    # Boucle sur les id mesures obtenues pour récupérer les données
    for j in sorted(list(df_mesure_vv[df_mesure_vv['id_site']==k]['id'])):
        print("Nom de la mesure : " + j)
        #"url_data="https://172.16.13.224:8443/dms-api/public/v1/data?from=2023-04-011T00:00:00Z&to=2023-04-023T00:00:00Z&validOnly=TRUE&dataTypes=hourly&measures="+j
        url_data="https://172.16.13.224:8443/dms-api/public/v1/data?from="+str_datej_debut+"T00:00:00Z&to="+str_datej_fin+"T00:00:00Z&validOnly=TRUE&dataTypes="+ type_de_donnees+"&measures="+j
        response = requests.get(url_data, verify = False).json()
        df_out_DV_VV = pandas.DataFrame([])
        for i in response["data"][0][type_de_donnees]:
            #print(i)
            df_temp = pandas.DataFrame([])
            date = pandas.DataFrame([i["date"]])
            vitesse = pandas.DataFrame([i["value"]])
            code_qa = pandas.DataFrame([i["state"]])
            niv_valid = pandas.DataFrame([i["validated"]])
            df_temp = pandas.concat([df_temp, date, vitesse,code_qa,niv_valid], axis = 1)
            # On nomme les colonnes du tableau avec le nom de la mesure 
            # print("Nom des colonnes avec "+j)
            df_temp.columns = ['date' , str('vitesse_'+j), str('code_qa_'+j), str('niv_valid_'+j)]
            df_out_DV_VV = pandas.concat([df_out_DV_VV, df_temp])
            
        # Fin boucle sur les concentrations du json
        # print(df_out)
        dicoDF_graphique[str('df_'+j)]=df_out_DV_VV
        DF_graphique_DV_VV= pandas.concat([DF_graphique_DV_VV, df_out_DV_VV], axis = 1)
   
#------------------------------------------------ FIN DU PROGRAMME ---------------------------------------------------#

#---------------- Quelques réglages sur les paramètres d'affichages: nom du sites de mesure, de station et du poluant ------------#
    
    # Sélectionner la valeur de l'id_site correspondant à k
    id_site_info = df_mesure_metaux[df_mesure_metaux['id_site'] == s].iloc[0]
#    print(id_site_info)
    id_site = id_site_info['id']
#    print(id_site)
    code_iso_souffre_dans_PM1 = '9h'
    polluant_code = id_site_info['phy_name'] #pour extraire le code du polluant
    polluant = df_parametre[df_parametre['id'] == code_iso_souffre_dans_PM1]['label'] # pour extraire le label du polluant
    polluant_str = polluant.to_string(index=False, header=False) # Convertir le label en caractère
    polluant_str = polluant_str.strip()            
    
    #Pour l'affichage du nom du site de mesure AtmoSud
    id_sites_AtmoSud_info = df_sites_AtmoSud[df_sites_AtmoSud['id'] == s]['label']
    sites_AtmoSud = id_sites_AtmoSud_info.to_string(index=False, header=False)  
    sites_AtmoSud = sites_AtmoSud.strip()
    
    
#--------------------------------- Configuration graphiques ----------------------------------------------------------------------#    
    
    # Créer une liste d'index communs pour pouvoir mieux les filtrer par la suite
    DF_graphique_DV_VV = DF_graphique_DV_VV.reset_index(drop=True).set_index(pandas.RangeIndex(start=1, stop=len(DF_graphique_DV_VV)+1))
    DF_graphique_metaux = DF_graphique_metaux.reset_index(drop=True).set_index(pandas.RangeIndex(start=1, stop=len(DF_graphique_metaux)+1))
    index_communs = list(set(DF_graphique_DV_VV.index) & set(DF_graphique_metaux.index))

# Réindexer les deux dataframes avec l'index commun
    DF_graphique_DV_VV = DF_graphique_DV_VV.reindex(index_communs)
    DF_graphique_metaux = DF_graphique_metaux.reindex(index_communs)
    
    # Je défini mes variables graphiques qui seront representées
    Date = pandas.to_datetime(DF_graphique_DV_VV.iloc[:, 0])
    vitess = DF_graphique_DV_VV.iloc[:, 5].values
    Souffre = DF_graphique_metaux.iloc[:, 25] * 0.001
    Aluminium = DF_graphique_metaux.iloc[:, 1] * 0.001
    Potassium = DF_graphique_metaux.iloc[:, 17] * 0.001
    directions = DF_graphique_DV_VV.iloc[:, 1]
    max_souffre = max(DF_graphique_metaux.iloc[:, 25] * 0.001) # je récupère la valeur maximale de la colonne de PM10
    
    #Pour le format de la date actuelle (facultatif)
    now = datetime.now()
    now_str = now.strftime("%d/%m/%Y %H:%M:%S")  # Format de la date et de l'heure
    
# Créer la figure et les sous-figures
    figSouffre = plt.Figure()
    figSouffre, ax = plt.subplots(figsize=(15,6))
    figSouffre.patch.set_facecolor('white')
   
     
 # Tracer la concentration du polluant en série temporelle
    ax.plot(Date, Souffre, '-', linewidth=2, color='red', alpha=.65, label='Souffre')
    ax.plot(Date, Aluminium, '-', linewidth=2, color='blue', alpha=.65, label='Aluminium')
    ax.plot(Date, Potassium, '-', linewidth=2, color='orange', alpha=.65, label='Potassium')
    ax.set_xlabel('Date', color = 'RebeccaPurple', fontsize=18)
    ax.set_ylabel('Souffre, Aluminium, Potassium (µg/m3)', color='b', fontsize=19)
    ax.tick_params('y', colors='b')

    
 # Tracer la direction du vent sous forme de flèche
    x = list(Date)
    y = DF_graphique_DV_VV.iloc[:, 1]
    # je récupère les limites actuelles des axes du graphique.
    x1, x2, y1, y2 = plt.axis()
    
    # Calcule de la direction du vent en degrés par rapport au nord en soustrayant la direction en degrés par rapport à l’est de 90°.
    direction_bis = 90 - directions
    
    # Convertit les degrés en radians 
    direction_bis = np.radians(direction_bis.values)
   
    #Crée un tableau de zéros de même taille que direction_bis et le multiplie par la moitié de la valeur de y2.
    b = np.zeros(direction_bis.shape, dtype=np.int8)+ int(y2 * 0.50)
    
    #Calcule la composante verticale des flèches de vent en utilisant la vitesse du vent et la direction en radians.
    composante_verticale_y = -vitess*np.sin(direction_bis)
    
    #Calcule la composante horizontale des flèches de vent en utilisant la vitesse du vent et la direction en radians.
    composante_horizontel_x = -vitess*np.cos(direction_bis)
    
    # Calculer la longueur des flèches en utilisant les composantes horizontale et verticale de chaque fleche
    longueur_fleches = np.sqrt(composante_horizontel_x**2 + composante_verticale_y**2)
    
    # Créer une carte de couleurs avec des couleurs correspondant à différentes longueurs de flèches precedement définies
    cmap = plt.cm.coolwarm
    norm = plt.Normalize(vmin=vitess.min(), vmax=vitess.max())
    
    # Je trace le méteogramme en utilisant la carte de couleurs pour la couleur des fleches
    ax.quiver(x, b + 1.7, composante_horizontel_x,  composante_verticale_y, longueur_fleches, width=0.005, edgecolor='black')
    ax.set_ylim([-2, 2]) # Définir la plage de valeurs pour l'axe supérieur
   
    # j'ajoute une barre de couleurs verticals pour la carte de couleurs
    cbar = plt.colorbar(ax.collections[0], ax=ax, orientation='vertical', pad=0.05)
    cbar.set_label('Vitesse du Vent (m/s)', fontsize=16)
    
    
    # Réglages des limites d'axes pour éviter que la courbe de vitesse ne touche les flèches
    ax.set_ylim(0, max_souffre + 1)
    
    # pour régler la rotation des dates à 45 degré
    plt.xticks(rotation=45, ha='right')

    #Pour mettre des grilles dans le graphe
    ax.grid(True, linewidth=0.5, alpha=0.3, linestyle='--')

    #Le titre de chague graphe selon le polluant, le site AtmoSud et la station météo France
    #ax.set_title(f'Concentration du {polluant_str} et la direction du vent de la station du site {sites_AtmoSud}',  color = 'RebeccaPurple', fontsize=15)
    
    # Pour que la légende soit horizontale (nombre de colonnes (ncol) à régler en fonction du nombre de paramètres à afficher)
    ax.legend(ncol = 3, loc='upper left', bbox_to_anchor=(0, 1))
    
    #dictionnaire qui contient toute les figures
    dico_Fig[str('Figure_'+k)]=figSouffre
        
    plt.show()  
    
    
         
# --------- Partie facultative -------------#      
# Chemin complet du répertoire de destination
output_directory = r'Z:\icoly\doc_mesure_Xact_metaux_en_ligne'
#Enregistrement des données dans un fichier CSV avec le chemin complet du répertoire
DF_graphique_DV_VV.to_csv(os.path.join(output_directory, 'Direction_vitesse_vent_Fos_Carabins.csv'), sep=";")
# ------ fin de la partie facultative -----#      


#-------------------------------------- Création d'un html avec toutes les figures ---------------------------------
def figures_to_html(figs, filename="Metaux_en_ligne_Fos-sur-Mer.HTML"):
	with open(filename, 'w') as dashboard:
		dashboard.write("<html><head></head><body>" + "\n")
		for fig in figs:
			inner_html = fig.to_html().split('<body>')[1].split('</body>')[0]
			dashboard.write(inner_html)
		dashboard.write("</body></html>" + "\n")

figures_to_html([figMetauxFosCarabins, figMetauxFosCarabins_journaliers])#, figSouffre])


    
    







