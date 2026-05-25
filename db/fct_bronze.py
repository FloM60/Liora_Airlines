import asyncio
import httpx
from tqdm import tqdm # type: ignore
from utils.api_geoloc import get_geoloc_from_code # type: ignore


def create_materialized_view(conn):
    try:
        cur = conn.cursor()

        # Supprime si elle existe déjà
        cur.execute("DROP MATERIALIZED VIEW IF EXISTS view_flight_dates;")

        # Création de la vue
        cur.execute("""
            CREATE MATERIALIZED VIEW view_flight_dates AS 
            WITH all_cities AS (
                SELECT Id_Origin_City AS Id_City, Date_Flight FROM Flights
                UNION ALL
                SELECT Id_Dest_City AS Id_City, Date_Flight FROM Flights
            )
            SELECT 
                Id_City, 
                MIN(Date_Flight) AS min_date, 
                MAX(Date_Flight) AS max_date
            FROM all_cities
            GROUP BY Id_City;
        """)

        conn.commit()  # ✅ commit obligatoire ici car c'est une écriture

    except Exception as e:
        conn.rollback()  # annule si erreur
        print(f"Erreur lors de la création de la vue : {e}")


def update_coordinate_city(cur, conn):
    # 1. Récupère toutes les villes en une seule requête
    cur.execute("SELECT Id_City, Name_City FROM City")
    cities = cur.fetchall()

    #Prépare un batch de coords
    coords_batch = []
    for city_id, _ in tqdm(cities, desc="Villes géolocalisées"):
        try:
            
            result = get_geoloc_from_code(city_id)
            if result is not None:
                lat = result["lat"]
                lon = result["lng"]
                coords_batch.append((lat, lon, city_id))
            
        except Exception as e:
            print(f"Erreur pour {city_id}: {e}")
            coords_batch.append((None, None, city_id))  # On skippe sans bloquer

    #3. UPDATE en une seule fois avec executemany
    cur.executemany("""
        UPDATE City SET Latitude_City = %s, Longitude_City = %s
        WHERE Id_City = %s
    """, coords_batch)
    conn.commit()




# ==============================================================================
#                 PARTIE ASYNCHRONE : GÉOLOCALISATION DES VILLES
# ==============================================================================


async def get_geoloc_async(client: httpx.AsyncClient, city_id: str, sem: asyncio.Semaphore):
    """
    Fonction asynchrone qui effectue l'appel API vers Open-Meteo pour récupérer
    la latitude et longitude d'une ville (city_id).
    L'utilisation de 'await' permet au programme de faire autre chose sans bloquer
    l'exécution, de la même manière que plusieurs serveurs servent des clients
    simultanément en restauration.
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        'name': city_id,
        'language': 'fr',
        'format': 'json',
        'count': 1
    }
    try:
        async with sem:                  # ✅ Max 9 requêtes simultanées
            await asyncio.sleep(0.11)
            response = await client.get(url, params=params, timeout=10)
            response.raise_for_status()
            results = response.json().get("results", [])
            
            if not results:
                return None, None, city_id
                
            return results[0]["latitude"], results[0]["longitude"], city_id

    except httpx.RequestError as exc:
        print(f"Erreur requête pour {city_id}: {exc}")
        return None, None, city_id


async def update_coordinate_city_async(cur, conn):
    """
    Au lieu de demander la géolocalisation pour chaque ville les unes à la 
    suite des autres, on lance toutes les requêtes en même temps (concurrent),
    ce qui accélère prodigieusement le temps d'exécution.
    """
    # 1. On récupère les villes existantes dans la DB
    cur.execute("SELECT Id_City, Name_City FROM City")
    cities = cur.fetchall()

    coords_batch = []
    
    print("Démarrage de la récupération asynchrone des coordonnées API...")
    
    # 2. On ouvre la connexion aux API
    async with httpx.AsyncClient() as client:
        sem = asyncio.Semaphore(9)
        tasks = [get_geoloc_async(client, city_id, sem) for city_id, _ in cities]
        
        # 3. On traite les requêtes au fur et à mesure qu'elles se terminent
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Villes géolocalisées"):
            lat, lon, city_id = await task
            if lat is not None and lon is not None:
                coords_batch.append((lat, lon, city_id))
            else:
                coords_batch.append((None, None, city_id))

    # 4. On enregistre en masse dans la DB (de manière classique)
    print("\nMise à jour en base des coordonnées...")
    cur.executemany("""
        UPDATE City SET Latitude_City = %s, Longitude_City = %s
        WHERE Id_City = %s
    """, coords_batch)
    conn.commit()


