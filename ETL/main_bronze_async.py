import os
import sys
import time
import asyncio
import pandas as pd
import psycopg2.extras
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tqdm import tqdm
from db.connection import get_connection
from db.create_table import create_bronze_table
from db.fct_bronze import create_materialized_view, get_geoloc_async, update_coordinate_city_async
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
        
        print("Lecture du fichier CSV...")
        df = pd.read_csv(os.getenv("DATASET_AIRLINES"), sep=',', header=0, engine='pyarrow') # pyright: ignore[reportArgumentType] 
        
        df['CancellationCode'] = df['CancellationCode'].fillna('0') # Remplace CancellationCode par 0 lorsque le vol n'est pas annulé

        cols_int = ['DepDelayMinutes', 'ArrDelayMinutes', 'CRSElapsedTime', 'ActualElapsedTime', 'CarrierDelay', 'WeatherDelay', 'NASDelay', 'SecurityDelay', 'LateAircraftDelay', 'DepTime', 'ArrTime', 'DepDelay', 'ArrDelay']
        df[cols_int] = df[cols_int].fillna(0).astype(int) 

        print("Chargement en mémoire des données des vols ...")
        state_records = {} 
        city_records = {} 
        flights_records = []

        for row in tqdm(df.itertuples(index=False), total=len(df), desc="Préparation Lignes CSV"):
            if row.OriginState not in state_records:
                state_records[row.OriginState] = (row.OriginState, row.OriginStateName)
            if row.DestState not in state_records:
                state_records[row.DestState] = (row.DestState, row.DestStateName)

            if row.Origin not in city_records:
                city_records[row.Origin] = (row.Origin, row.OriginCityName, row.OriginState)
            if row.Dest not in city_records:
                city_records[row.Dest] = (row.Dest, row.DestCityName, row.DestState)
            
            # Remplissage des champs calculés
            Arr_Es_Time_Cor = Fct_Arr_Es_Time_Cor(row.DepTime, row.CRSElapsedTime)
            Dep_CRS_Time_Cor, Arr_Es_Time_Cor = date_time_format(row.FlightDate, row.CRSDepTime, Arr_Es_Time_Cor)

            flights_records.append((
                row.Flight_Number_Operating_Airline,
                row.FlightDate,
                row.DayOfWeek,
                row.DayofMonth,
                row.Month,
                row.Year,
                row.CRSDepTime,
                Dep_CRS_Time_Cor,
                row.DepTime,
                row.DepDelay,
                row.CRSArrTime,
                row.ArrTime,
                Arr_Es_Time_Cor,
                row.ArrDelay,
                row.CRSElapsedTime,
                row.ActualElapsedTime,
                row.CarrierDelay,
                row.WeatherDelay,
                row.NASDelay,
                row.SecurityDelay,
                row.LateAircraftDelay,
                row.Origin,
                row.Dest,
                row.CancellationCode
            ))


        async def async_main_orchestrator():
            def _insert_db():
                psycopg2.extras.execute_values(cur, "INSERT INTO State (Id_State, Name_State) VALUES %s ON CONFLICT (Id_State) DO NOTHING", list(state_records.values()))
                psycopg2.extras.execute_values(cur, "INSERT INTO City (Id_City, Name_City, Id_State) VALUES %s ON CONFLICT (Id_City) DO NOTHING", list(city_records.values()))
                
                insert_flights_query = """
                    INSERT INTO Flights (
                    Flight_Number, Date_Flight, Day_of_Week, Day_Flight, Month_Flight, Year_Flight,
                    Dep_CRS_Time, Dep_CRS_Time_Cor, Dep_Time, Dep_Delay,
                    Arr_CRS_Time, Arr_Time, Arr_Es_Time_Cor, Arr_Delay,
                    Estimated_Duration, Final_Duration, Carrier_Delay, Weather_Delay,
                    NAS_Delay, Security_Delay, LateAircraft_Delay,
                    Id_Origin_City, Id_Dest_City, Id_Cancel)
                    VALUES %s
                """

                chunk_size = 10000
                chunks = [flights_records[i:i+chunk_size] for i in range(0, len(flights_records), chunk_size)]

                for chunk in tqdm(chunks, desc="Insertion des vols", unit="batch"):
                    psycopg2.extras.execute_values(cur, insert_flights_query, chunk, page_size=chunk_size)
                conn.commit()

            print("Insertion en masse et asynchrone dans la DB ...")
            await asyncio.to_thread(_insert_db)
            
            # Appel asynchrone pour la géolocalisation
            await update_coordinate_city_async(cur, conn)

        # ==================== LANCEMENT ORCHESTRATEUR ASYNCHRONE ====================
        asyncio.run(async_main_orchestrator())
        # ============================================================================


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
