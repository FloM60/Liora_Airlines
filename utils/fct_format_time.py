from datetime import time, timedelta

def Fct_Arr_Es_Time_Cor(Dep_Time,Estimated_Duration):
    """
    Calcul de la colonne Arr_Es_Time_Cor dans la table Flights
    """
    arr_crs_minutes = (Dep_Time // 100) * 60 + (Dep_Time % 100)
    arr_es_minutes = arr_crs_minutes + Estimated_Duration
   
    # Gestion du basculement sur le jour suivant
    if arr_es_minutes >= 24*60: 
        arr_es_minutes %= 24*60
    # Gestion du basculement sur le jour précédent
    elif arr_es_minutes < 0: 
        arr_es_minutes = arr_es_minutes % (24*60)
    # Reconversion en format HHMM
    Arr_Es_Time_Cor = (arr_es_minutes // 60) * 100 + (arr_es_minutes % 60) 
    return Arr_Es_Time_Cor


def hour_round(time_flight: int):
    """
    Cette fonction sépare une heure stockée sous forme d'entier en heure et minutes 
    pour aller récupérer l'heure une heure ronde inférieure ou supérieure.
    En effet, l'API History Weather ne donne la météo que sur des heures rondes.

    """
    try:

        hours = time_flight // 100
        minutes = time_flight % 100

        if minutes >= 30:
            hours += 1
        minutes = 0

        if hours == 24:
            hours = 0
        
        return time(hour = hours, minute = minutes).strftime('%H:%M')

    except (ValueError, TypeError) as error:
        
        print(f"Erreur dans le format de l'heure: {error}")

        return None
        

def date_time_format(Date_Flight, Dep_CRS_Time, Arr_Es_Time_Cor):
    """
    Cette fonction prend une heure au format HHMM et une date, arrondit à l'heure ronde la plus proche et retourne
    un timestamp au format 'YYYY-MM-DDTHH:00'.
    Si dep_heure est fourni, gère le cas où l'arrivée est le lendemain.
    En effet, l'API History Weather ne donne la météo que sur des heures rondes.
    """

    # Construction du timestamp de départ prévu

    hour = hour_round(Dep_CRS_Time)
    dep_crs_time_cor = str(Date_Flight) + "T" + str(hour)

    # Construction du timestamp de l'arrivée estimée

    hour = hour_round(Arr_Es_Time_Cor)
    if Arr_Es_Time_Cor < Dep_CRS_Time:
        arr_es = Date_Flight + timedelta(days=1)
    else:
        arr_es = Date_Flight

    arr_es_time_cor = str(arr_es) + "T" + str(hour)

    return dep_crs_time_cor, arr_es_time_cor


