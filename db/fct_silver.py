import asyncio
import httpx
from tqdm import tqdm
from utils.api_weather import get_weather_async



def list_date_cities(cur):
    cur.execute("""          
    SELECT id_flight, dep_crs_time_cor, arr_es_time_cor, co.id_city as origin, cd.id_city as dest
    from flights f
    join city co on co.id_city = f.id_origin_city
    join city cd on cd.id_city = f.id_dest_city
    """)
    colonnes = [desc[0] for desc in cur.description]
    return colonnes, cur.fetchall()



def cities_min_max(cur):
    cur.execute("""
    SELECT c.id_city, c.latitude_city, c.Longitude_city, v.min_date, v.max_date
    FROM city c
    JOIN view_flight_dates v ON c.id_City = v.id_City
    GROUP BY c.Id_City, v.min_date, v.max_date;
    """)
    return cur.fetchall()



# ==============================================================================
#                 PARTIE ASYNCHRONE : CHARGEMENT DE LA MÉTÉO
# ==============================================================================

async def fetch_weather_task(id_city, lat, lon, min_date, max_date, session, sem):
    """
    Exécute la fonction 'get_weather' originale dans un thread séparé de 
    manière asynchrone afin de la paralléliser sans la réécrire.
    """
    df = await get_weather_async(session, sem, lat, lon, str(min_date), str(max_date))
    return id_city, df


async def build_weather_cache_async(cities: list) -> dict:
    """
    Crée le cache météo en récupérant les données asynchrones sans dépasser
    la limite stricte de 600 appels / minute (10 appels / seconde max).
    """
    cache = {}
    tasks = []
    sem = asyncio.Semaphore(5)
    
    print("Préparation de la file d'attente ...")
    async with httpx.AsyncClient() as session:
        for city in cities:
            id_city, lat, lon, min_date, max_date = city
            task = asyncio.create_task(fetch_weather_task(id_city, lat, lon, min_date, max_date, session, sem))
            tasks.append(task)
        
        print("Lancement et attente des requêtes météo...")
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Chargement météo asynchrone"):
            id_city, result_df = await task
            if result_df is not None:
                cache[id_city] = result_df
                
    print(f"Cache météo terminé : {len(cache)} villes chargées.")
    return cache
