def create_bronze_table(conn, cur):
    cur.execute(""" 
        DROP TABLE IF EXISTS Flights CASCADE;
        DROP TABLE IF EXISTS Weather CASCADE;
        DROP TABLE IF EXISTS WeatherDesc CASCADE;      
        DROP TABLE IF EXISTS Cancel CASCADE;
        DROP TABLE IF EXISTS City CASCADE;
        DROP TABLE IF EXISTS State CASCADE;


        CREATE TABLE State (
            Id_State varchar(5) PRIMARY KEY,
            Name_State varchar(50) NOT NULL
        );


        CREATE TABLE City (
            Id_City varchar(5) PRIMARY KEY,
            Name_City varchar(100) NOT NULL,
            Latitude_City DECIMAL(9,6),
            Longitude_City DECIMAL(9,6), 
            Id_State varchar(5) NOT NULL,
            FOREIGN KEY (Id_State) REFERENCES State(Id_State)
        );


        CREATE TABLE Cancel (
            Id_Cancel varchar(1) PRIMARY KEY,
            Name_Cancel varchar(250)
        );
                
        
        CREATE TABLE WeatherDesc (
            Weather_Code int PRIMARY KEY,
            Weather_Description varchar(100)
        );

            
        CREATE TABLE Weather (
            Id_Weather int PRIMARY KEY,
            Temperature decimal(6,2),
            Relative_Humidity int,
            Dewpoint decimal(6,2),
            Apparent_Temperature decimal(6,2),
            Precipitation decimal(6,2),
            Rain decimal(6,2),
            Snowfall decimal(6,2),
            Snow_deph decimal(6,2),
            Vapour_Press_Deficit decimal(6,2),
            Wind_Speed_10 decimal(6,2),
            Wind_Speed_100 decimal(6,2),
            Wind_Gusts_10 decimal(6,2),
            Weather_code int,
            FOREIGN KEY (Weather_Code) REFERENCES WeatherDesc(Weather_Code)
        );

                    
        CREATE TABLE Flights (
            Id_Flight serial PRIMARY KEY,
            Flight_Number int NOT NULL,
            Date_Flight date NOT NULL,
            Day_of_Week int NOT NULL,
            Day_Flight int NOT NULL,
            Month_Flight int NOT NULL,
            Year_Flight int NOT NULL,
            Dep_CRS_Time int NOT NULL,
            Dep_CRS_Time_Cor varchar(16),
            Dep_Time int NOT NULL,   
            Dep_Delay int NOT NULL,
            Arr_CRS_Time int NOT NULL,
            Arr_Time int NOT NULL,
            Arr_Es_Time_Cor varchar(16),        
            Arr_Delay int NOT NULL,
            Estimated_Duration int NOT NULL,
            Final_Duration int NOT NULL,
            Carrier_Delay int NOT NULL,
            Weather_Delay int NOT NULL,
            NAS_Delay int NOT NULL,
            Security_Delay int NOT NULL,
            LateAircraft_Delay int NOT NULL,
            Id_Origin_City varchar(5) NOT NULL,
            Id_Dest_City varchar(5) NOT NULL,
            Id_Origin_Weather int,
            Id_Dest_Weather int,
            Id_Cancel varchar(1) NOT NULL,
            FOREIGN KEY (Id_Origin_City) REFERENCES City(Id_City),
            FOREIGN KEY (Id_Dest_City) REFERENCES City(Id_City),
            FOREIGN KEY (Id_Origin_Weather) REFERENCES Weather(Id_Weather),
            FOREIGN KEY (Id_Dest_Weather) REFERENCES Weather(Id_Weather),
            FOREIGN KEY (Id_Cancel) REFERENCES Cancel(Id_Cancel)
        );

            
        INSERT INTO Cancel (Id_Cancel, Name_Cancel) VALUES
            ('0', 'Le vol n''a pas été annulé.'),
            ('A', 'Conditions météorologiques imprévues (ex. : tempête violente).'),
            ('B', 'Problèmes de sécurité imprévus (ex. : menace sécuritaire).'),
            ('C', 'Grèves du personnel de l''aéroport ou d''un prestataire tiers (hors grève interne à la compagnie).');
        

        INSERT INTO WeatherDesc (
            Weather_Code, 
            Weather_Description)
            VALUES
            ('0', 'Ciel clair'),
            ('1', 'Ciel généralement clair'),
            ('2', 'Ciel partiellement nuageux'),
            ('3', 'Ciel couvert'),
            ('45', 'Brouillard'),
            ('48', 'Brouillard givrant'),
            ('51', 'Bruine : Légère'),
            ('53', 'Bruine : Modérée'),
            ('55', 'Bruine : Intensité intense'),
            ('56', 'Bruine verglaçante : légère'),
            ('57', 'Bruine verglaçante : Intensité intense'),
            ('61', 'Pluie : légère'),
            ('63', 'Pluie : modérée'),
            ('65', 'Pluie : Forte intensité'),
            ('66', 'Pluie verglaçante : légère'),
            ('67', 'Pluie verglaçante : forte intensité'),
            ('71', 'Chutes de neige : légères'),
            ('73', 'Chutes de neige : modérées'),
            ('75', 'Chutes de neige : fortes intensités'),
            ('77', 'Cristaux de neige'),
            ('80', 'Averses : légères'),
            ('81', 'Averses : modérées'),
            ('82', 'Averses : Violentes'),
            ('85', 'Averses de neige : légères'),
            ('86', 'Averses de neige : fortes'),
            ('95', 'Orages : faibles ou modérés'),
            ('96', 'Orage avec un peu de grêle'),
            ('99', 'Orage avec forte grêle');


        --Création d'index pour déterminer le min/max des dates par aéroport
        CREATE INDEX idx_flights_dep_date           
        ON Flights (Id_Origin_City, Date_Flight);

        CREATE INDEX idx_flights_arr_date
        ON Flights (Id_Dest_City, Date_Flight);
    """)   
    conn.commit()
    print("Tables créées avec succès !")