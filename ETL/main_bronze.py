import pandas as pd
import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tqdm import tqdm
from db.connection import get_connection
from db.create_table import create_bronze_table
from db.fct_bronze import create_materialized_view, update_coordinate_city
from utils.fct_format_time import Fct_Arr_Es_Time_Cor, date_time_format



def main():
    start = time.time() # Début du chrono

    inserted_states = set() # Sets pour stocker les villes et états deja saisie
    inserted_cities = set()


    conn = None 
    try:
        conn = get_connection()
        print("Connexion à Postgres réussi !")
        cur = conn.cursor() # Création des tables
        create_bronze_table(conn, cur)
        

        df = pd.read_csv(os.getenv("DATASET_AIRLINES"), sep=',', header=0, engine='pyarrow') # pyright: ignore[reportArgumentType]
        
        df['CancellationCode'] = df['CancellationCode'].fillna('0') # Remplace CancellationCode par 0 lorsque le vol n'est pas annulé

        cols_int = ['DepDelayMinutes', 'ArrDelayMinutes', 'CRSElapsedTime', 'ActualElapsedTime', 'CarrierDelay', 'WeatherDelay', 'NASDelay', 'SecurityDelay', 'LateAircraftDelay', 'DepTime', 'ArrTime', 'DepDelay', 'ArrDelay']
        df[cols_int] = df[cols_int].fillna(0).astype(int) # On convertis les formats .0 en entier, en tenant compte des NaN qu'on remplace par 0


        for index, row in tqdm(df.iterrows(), total=len(df), desc="Ecriture du dataset"): # On parcours toutes les lignes du CSV - TQDM = barre de chargement
            if index % 1000 == 0: # On commit toutes les 1000 lignes
                conn.commit()
            
            if row['OriginState'] not in inserted_states:
                cur.execute("""
                    INSERT INTO State (
                    Id_State,
                    Name_State)
                        VALUES (%s, %s)
                    """, (
                    row['OriginState'],
                    row['OriginStateName']))
                inserted_states.add(row['OriginState'])

            if row['DestState'] not in inserted_states:           
                cur.execute("""
                    INSERT INTO State (
                    Id_State,
                    Name_State)
                        VALUES (%s, %s)
                    """, (
                    row['DestState'],
                    row['DestStateName']))
                inserted_states.add(row['DestState'])      

            if row['Origin'] not in inserted_cities:
                cur.execute("""
                    INSERT INTO City (
                    Id_City,
                    Name_City,
                    Id_State)
                        VALUES (%s, %s, %s)
                    """, (
                    row['Origin'],
                    row['OriginCityName'],
                    row['OriginState']))
                inserted_cities.add(row['Origin'])

            if row['Dest'] not in inserted_cities:          
                cur.execute("""
                    INSERT INTO City (
                    Id_City,
                    Name_City,
                    Id_State)
                        VALUES (%s, %s, %s)
                    """, (
                    row['Dest'],
                    row['DestCityName'],
                    row['DestState']))
                inserted_cities.add(row['Dest'])
            
            # Remplissage des champs calculés
            Arr_Es_Time_Cor = Fct_Arr_Es_Time_Cor(row['DepTime'],row['CRSElapsedTime'])
            Dep_CRS_Time_Cor, Arr_Es_Time_Cor = date_time_format(row['FlightDate'], row['CRSDepTime'], Arr_Es_Time_Cor)

            cur.execute("""
                INSERT INTO Flights (
                Flight_Number,
                Date_Flight,
                Day_of_Week,
                Day_Flight,
                Month_Flight,
                Year_Flight,
                Dep_CRS_Time,
                Dep_CRS_Time_Cor,
                Dep_Time,
                Dep_Delay,
                Arr_CRS_Time,
                Arr_Time,
                Arr_Es_Time_Cor,
                Arr_Delay,
                Estimated_Duration,
                Final_Duration,
                Carrier_Delay,
                Weather_Delay,
                NAS_Delay,
                Security_Delay,
                LateAircraft_Delay,
                Id_Origin_City,
                Id_Dest_City,
                Id_Cancel)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                row['Flight_Number_Operating_Airline'],
                row['FlightDate'],
                row['DayOfWeek'],
                row['DayofMonth'],
                row['Month'],
                row['Year'],
                row['CRSDepTime'],
                Dep_CRS_Time_Cor,
                row['DepTime'],
                row['DepDelay'],
                row['CRSArrTime'],
                row['ArrTime'],
                Arr_Es_Time_Cor,
                row['ArrDelay'],
                row['CRSElapsedTime'],
                row['ActualElapsedTime'],
                row['CarrierDelay'],
                row['WeatherDelay'],
                row['NASDelay'],
                row['SecurityDelay'],
                row['LateAircraftDelay'],
                row['Origin'],
                row['Dest'],
                row['CancellationCode']))
        
        conn.commit()
        update_coordinate_city(cur, conn)

        print("Création des vues matérialisées ...")
        create_materialized_view(conn)
        conn.close()

        end = time.time() # Fin du chrono
        elapsed = end - start
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        print("Script exécuté avec succès !")
        print(f"Nombre de lignes traitées : {len(df)}")
        print(f"Temps total d'exécution : {minutes} minutes et {seconds} secondes\n")


    except Exception as e:
        if conn is not None:    # vérifie avant rollback
            conn.rollback()
        print(f"Erreur globale : {e}")
        raise
    finally:
        if conn is not None:    # vérifie avant close
            conn.close()


if __name__ == "__main__":
    main()



