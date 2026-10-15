import os
import json
import re
import urllib.parse
import requests
import unicodedata
import time
from datetime import datetime, timedelta

# Configuración de URLs y archivos locales
AGENDA_URL = "https://streamxhd.com/eventos.json?"
LOCAL_CHANNELS_JSON = "04.json"
OUTPUT_JSON = "agenda.json"
BASE_IMG_URL = "https://raw.githubusercontent.com/Configuracao/Vix/main/assets/equipos_fm"

# Clase para hacer un diccionario insensible a mayúsculas, minúsculas y acentos
class CaseInsensitiveDict(dict):
    def __init__(self, data=None, **kwargs):
        super().__init__()
        if data:
            self.update(data)
        if kwargs:
            self.update(kwargs)

    def _normalize(self, key):
        if not isinstance(key, str):
            return key
        texto = unicodedata.normalize('NFD', key)
        texto = texto.encode('ascii', 'ignore').decode('utf-8')
        return texto.strip().lower()

    def __setitem__(self, key, value):
        super().__setitem__(self._normalize(key), value)

    def __getitem__(self, key):
        return super().__getitem__(self._normalize(key))

    def __contains__(self, key):
        return super().__contains__(self._normalize(key))

    def get(self, key, default=None):
        return super().get(self._normalize(key), default)
        
    def update(self, E=None, **F):
        if E is not None:
            if hasattr(E, 'keys'):
                for k in E:
                    super().__setitem__(self._normalize(k), E[k])
            else:
                for k, v in E:
                    super().__setitem__(self._normalize(k), v)
            for k in F:
                super().__setitem__(self._normalize(k), F[k])

# Diccionario para reemplazar nombres de equipos automáticamente
MAPEO_REEMPLAZO_NOMBRES = CaseInsensitiveDict({
    "AFC Bournemouth": "Bournemouth",
    "Athletic Club": "Athletic Bilbao",
    "Inter": "Inter Milan",
    "Bayern München": "Bayern Munich",
    "Hamburger SV": "Hamburg",
    "Mainz 05": "Mainz",
    "Univ. Concepción": "Universidad de Concepción",
    "Wanderers": "Montevideo Wanderers",
    "Brighton & Hove Albion": "Brighton and Hove Albion",
    "Angers SCO": "Angers",
    "PSG": "Paris Saint-Germain",
    "Cincinnati": "FC Cincinnati",
    "Orlando City SC": "Orlando City",
    "New York RB": "New York Red Bulls",
    "Charlotte": "Charlotte FC",
    "Dallas": "FC Dallas",
    "New England": "New England Revolution",
    "Seattle Sounders FC": "Seattle Sounders",
    "Austin": "Austin FC",
    "FC Cajamarca": "Cajamarca",
    "Al Hilal": "Al-Hilal",
    "Al Ittihad": "Al-Ittihad",
    "Central Córdoba SdE": "Central Córdoba de Santiago del Estero",
    "Estudiantes LP": "Estudiantes de La Plata",
    "Estudiantes Río Cuarto": "Estudiantes de Río Cuarto",
    "Brendan Allen": "Allen",
    "Christian Leroy Duncan": "Duncan",
    "Junior": "Atlético Junior",
    "Inter Bogotá": "Internacional de Bogotá",
    "Guadalajara": "CD Guadalajara",
    "Sporting KC": "Sporting Kansas City",
    "SJ Earthquakes": "San Jose Earthquakes",
    "Milan": "AC Milan",
    "Hertha BSC": "Hertha",
    "Celta de Vigo": "Celta Vigo",
    "Deportivo La Coruña": "Deportivo de A Coruña",
    "Racing Santander": "Racing de Santander",
    "CD Castellon": "Castellón",
    "Sporting Gijón": "Sporting de Gijón",
    "Olympique Marseille": "Marseille",
    "Borussia M'gladbach": "Borussia Mönchengladbach",
    "Juventud": "Juventud Las Piedras",
    "Racing": "Racing Montevideo",
    "Nacional": "Nacional Montevideo",
    "Saints": "New Orleans Saints",
    "Vikings": "Minnesota Vikings",
    "Bears": "Chicago Bears",
    "Packers": "Green Bay Packers",
    "Steelers": "Pittsburgh Steelers",
    "Colts": "Indianapolis Colts",
    "Broncos": "Denver Broncos",
    "Chargers": "Los Angeles Chargers",
    "Cardinals": "Arizona Cardinals",
    "Lions": "Detroit Lions",
    "49ers": "San Francisco 49ers",
    "Seahawks": "Seattle Seahawks",
    "Ravens": "Baltimore Ravens",
    "Falcons": "Atlanta Falcons",
    "Vitória Guimarães": "Vitória de Guimarães",
    "Talleres Córdoba": "Talleres de Córdoba",
    "UTC Cajamarca": "Universidad Técnica de Cajamarca",
    "Olympiakos Piraeus": "Olympiacos",
    "Santa Fe": "Independiente Santa Fe",
    "Fortaleza CEIF": "Fortaleza FC",
    "Medellín": "Independiente Medellín",
    "Atlético San Luis": "Atlético de San Luis",
    "St. Louis City": "St. Louis City SC",
    "La Serena": "Deportes La Serena",
    "Carrera": "Singapore Grand Prix",
    "Athletico-PR": "Athletico Paranaense",
    "RB Bragantino": "Bragantino",
    "Universidad Chile": "Universidad de Chile",
    "Rams": "Los Angeles Rams",
    "Bills": "Buffalo Bills",
    "Gimnasia Mendoza": "Gimnasia y Esgrima de Mendoza",
    "Al Nassr": "Al-Nassr",
    "Neftchi": "Neftchi Fergana",
    "Sabah": "Sabah Baku",
    "Slavia Praha": "Slavia Prague",
    "Internazionale": "Inter Milan",
    "Al Sadd": "Al-Sadd",
    "Shabab Al Ahli": "Shabab Al-Ahli Dubai",
    "Akron": "Akron Tolyatti",
    "Atlético Madrid Sub-19": "Atlético Madrid Juvenil",
    "Manchester United Sub-19": "Manchester United Youth",
    "Galatasaray Sub-19": "Galatasaray Youth",
    "Barcelona Sub-19": "Barcelona Youth",
    "LASK LINZ": "LASK",
    "CSKA MOSKVA": "CSKA Moscow",
    "Fenerbahce": "Fenerbahçe",
    "Carreraa": "SingaporeGrandPrix",
    "Bodø / Glimt": "Bodø/Glimt",
    "Zenit": "Zenit Saint Petersburg",
    "Dinamo Moskva": "Dynamo Moscow",
    "Heat": "Miami Heat",
    "Nets": "Brooklyn Nets",
    "Timberwolves": "Minnesota Timberwolves",
    "Pistons": "Detroit Pistons",
    "Bucks": "Milwaukee Bucks",
    "Bulls": "Chicago Bulls",
    "Suns": "Phoenix Suns",
    "Spurs": "San Antonio Spurs",
    "Mavericks": "Dallas Mavericks",
    "Pelicans": "New Orleans Pelicans",
    "Clippers": "Los Angeles Clippers",
    "Nuggets": "Denver Nuggets",
    "Torque": "Montevideo City Torque",
    "San Diego": "San Diego FC",
    "Houston Dynamo": "Houston Dynamo",
    "Carreraa": "SingaporeGrandPrix",
    "Carreraa": "SingaporeGrandPrix",
    "Carreraa": "SingaporeGrandPrix",
    "Carreraa": "SingaporeGrandPrix",
    "Carreraa": "SingaporeGrandPrix",
    "Carreraa": "SingaporeGrandPrix",
    "Carreraa": "SingaporeGrandPrix",
    "Carreraa": "SingaporeGrandPrix",
    "Carreraa": "SingaporeGrandPrix",
    "Carreraa": "SingaporeGrandPrix",
    "Carreraa": "SingaporeGrandPrix",
})

# Diccionario de equipos (para escudos locales de respaldo)
MAPEO_EQUIPOS = CaseInsensitiveDict({
    "puebla": "7847", "club puebla": "7847", "leon": "1841", "club León": "1841",
    "tigres": "8561", "tigres uanl": "8561", "toluca": "6618", "fc juarez": "649424",
    "juarez": "649424", "tijuana": "162418", "xolos": "162418", "queretaro": "1943",
    "queretaro fc": "1943", "atlante": "1942", "atlas": "6577", "chivas": "7807",
    "chivas guadalajara": "7807", "guadalajara": "7807", "cf america": "6576",
    "america": "6576", "club america": "6576", "monterrey": "7849", "rayados": "7849",
    "atletico de san luis": "6358", "atletico san luis": "6358", "san luis": "6358",
    "santos laguna": "7857", "pachuca": "7848", "necaxa": "1842", "pumas": "1946",
    "pumas unam": "1946", "cruz azul": "6578",
    "malaga": "9864", "espanyol": "8558", "rayo vallecano": "8370", "athletic club": "8315",
    "athletic bilbao": "8315", "deportivo alaves": "9866", "alaves": "9866",
    "atletico madrid": "9906", "atletico de madrid": "9906", "barcelona": "8634",
    "fc barcelona": "8634", "getafe": "8305", "real madrid": "8633", "villarreal": "10205",
    "elche": "10268", "celta vigo": "9910", "celta de vigo": "9910", "celta": "9910",
    "real sociedad": "8560", "deportivo a coruna": "9783", "real betis": "8603",
    "betis": "8603", "osasuna": "8371", "mallorca": "8661", "las palmas": "8306",
    "sevilla": "8302", "levante": "8581", "racing santander": "8696", "ceuta": "357259",
    "sabadell": "4033", "eldense": "8288", "cordoba": "7869", "girona": "7732",
    "arsenal": "9825", "leeds united": "8463", "aston villa": "10252", "brentford": "9937",
    "sunderland": "8472", "brighton & hove albion": "10204", "chelsea": "8455",
    "ipswich town": "9902", "fulham": "9879", "manchester united": "10260",
    "tottenham hotspur": "8586", "tottenham": "8586", "crystal palace": "9826",
    "nottingham forest": "10203", "hull city": "8667", "everton": "8668",
    "liverpool": "8650", "manchester city": "8456", "afc bournemouth": "8678",
    "bournemouth": "8678", "newcastle united": "10261",
    "borussia dortmund": "9789", "werder bremen": "8697", "paderborn": "8460",
    "stuttgart": "10269", "hoffenheim": "8226", "hamburger sv": "9790",
    "augsburg": "8406", "bayern munchen": "9823", "mainz 05": "9905",
    "bayer leverkusen": "8178", "union berlin": "8149", "elversberg": "8232",
    "rb leipzig": "178475", "eintracht frankfurt": "9810",
    "lens": "8588", "olympique lyonnais": "9748", "lille": "8639", "le havre": "9746",
    "lorient": "8689", "paris": "6379", "brest": "8521", "angers sco": "8121",
    "psg": "9847", "le mans": "8682", "monaco": "9829", "toulouse": "9941",
    "genoa": "10233", "fiorentina": "8535", "inter": "8636", "inter de milan": "8636", "parma": "10167",
    "napoli": "9875", "frosinone": "9891",
    "vasco da gama": "10276", "remo": "1626", "são paulo": "10277", "vitória": "7733",
    "boca juniors": "90006", "river plate": "90015",
})

def limpiar_nombre_equipo(nombre, liga_nombre=""):
    if not nombre:
        return ""
    nombre_limpio = nombre.strip()
    if nombre_limpio.lower() == "everton":
        liga_lower = liga_nombre.lower()
        if any(k in liga_lower for k in ["primera división", "chile", "tntsports"]):
            return "Everton de Viña del Mar"
        return "Everton"
    if nombre_limpio in MAPEO_REEMPLAZO_NOMBRES:
        return MAPEO_REEMPLAZO_NOMBRES[nombre_limpio]
    return nombre_limpio

def buscar_imagen(equipo_val):
    if not equipo_val:
        return ""
    if equipo_val in MAPEO_EQUIPOS:
        return f"{BASE_IMG_URL}/{MAPEO_EQUIPOS[equipo_val]}.png"
    return ""

def consultar_thesportsdb(home_team, away_team, fecha):
    combinaciones = []
    if away_team:
        combinaciones.append((home_team, away_team))
        combinaciones.append((away_team, home_team))
    else:
        combinaciones.append((home_team, ""))

    fechas_a_probar = [fecha]
    try:
        dt_obj = datetime.strptime(fecha, "%Y-%m-%d")
        fecha_siguiente = (dt_obj + timedelta(days=1)).strftime("%Y-%m-%d")
        fechas_a_probar.append(fecha_siguiente)
    except ValueError:
        pass

    for f_busqueda in fechas_a_probar:
        for h, a in combinaciones:
            if a:
                query_variants = [
                    f"{h} vs {a}",
                    f"{h}-vs-{a}",
                    f"{h.lower()} vs {a.lower()}",
                    f"{h.lower()}-vs-{a.lower()}",
                    f"{h} - {a}"
                ]
            else:
                query_variants = [h, h.lower()]

            for q in query_variants:
                encoded_q = urllib.parse.quote(q)
                url = f"https://www.thesportsdb.com/api/v1/json/123/searchevents.php?e={encoded_q}&d={f_busqueda}"
                try:
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    response = requests.get(url, headers=headers, timeout=5)
                    time.sleep(3.0) 
                    if response.status_code == 200:
                        data = response.json()
                        if data and "event" in data and data["event"]:
                            evento = data["event"][0]
                            return {
                                "homeLogo": evento.get("strHomeTeamBadge", ""),
                                "awayLogo": evento.get("strAwayTeamBadge", ""),
                                "thumb": evento.get("strThumb", "")
                            }
                except Exception:
                    continue
                    
    return {"homeLogo": "", "awayLogo": "", "thumb": ""}

def procesar_agenda():
    canales_04_dict = {}
    if os.path.exists(LOCAL_CHANNELS_JSON):
        try:
            with open(LOCAL_CHANNELS_JSON, "r", encoding="utf-8") as f:
                contenido_04 = json.load(f)
                if isinstance(contenido_04, list) and len(contenido_04) > 0:
                    for c in contenido_04:
                        ch_key = c.get("channel", "").strip().lower()
                        if ch_key:
                            canales_04_dict[ch_key] = c
                    print(f"Se cargaron e indexaron {len(canales_04_dict)} canales desde {LOCAL_CHANNELS_JSON}.")
        except Exception as e:
            print(f"Error al leer {LOCAL_CHANNELS_JSON}: {e}")

    print(f"Descargando JSON manual desde {AGENDA_URL}...")
    try:
        response = requests.get(AGENDA_URL, timeout=10)
        if response.status_code != 200:
            print(f"Error al descargar la agenda manual: Status {response.status_code}")
            return
        agenda_data = response.json()
    except Exception as e:
        print(f"Error al obtener datos de la agenda manual: {e}")
        return

    print("Procesando eventos, consultando TheSportsDB y aplicando reemplazos...")

    if "sports" in agenda_data:
        for sport in agenda_data["sports"]:
            for league in sport.get("leagues", []):
                league_name = league.get("name", "")
                for event in league.get("events", []):
                    home_raw = event.get("homeTeam", "")
                    away_raw = event.get("awayTeam", "")
                    
                    home_team = limpiar_nombre_equipo(home_raw, league_name)
                    away_team = limpiar_nombre_equipo(away_raw, league_name)

                    event["homeTeam"] = home_team
                    event["awayTeam"] = away_team

                    if away_team:
                        event["title"] = f"{home_team} vs {away_team}"
                    else:
                        event["title"] = home_team

                    # Obtener fecha base del evento (YYYY-MM-DD)
                    time_str = event.get("time", "")
                    fecha = time_str[:10] if len(time_str) >= 10 else datetime.now().strftime("%Y-%m-%d")

                    # Consultar TheSportsDB para imágenes y logos si faltan
                    api_images = consultar_thesportsdb(home_team, away_team, fecha)

                    home_logo = event.get("homeLogo") or api_images.get("homeLogo", "") or buscar_imagen(home_team)
                    away_logo = event.get("awayLogo") or api_images.get("awayLogo", "") or buscar_imagen(away_team)
                    event_thumb = event.get("image") or api_images.get("thumb", "")

                    event["homeLogo"] = home_logo
                    event["awayLogo"] = away_logo
                    event["image"] = event_thumb

                    if event_thumb:
                        event["imageMode"] = "banner"
                    elif home_logo or away_logo:
                        event["imageMode"] = "teams"

                    # Procesar servidores y buscar coincidencias en 04.json
                    nuevos_servidores = []
                    for server in event.get("servers", []):
                        server_url = server.get("url", "")
                        parsed_url = urllib.parse.urlparse(server_url)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        
                        channel_param = query_params.get("channel", [""])[0].strip().lower()
                        if not channel_param:
                            channel_param = query_params.get("stream", [""])[0].strip().lower()

                        if channel_param and channel_param in canales_04_dict:
                            canal_info = canales_04_dict[channel_param]
                            nuevos_servidores.append({
                                "name": canal_info.get("canal", server.get("name", channel_param.upper())),
                                "url": canal_info.get("url", ""),
                                "type": canal_info.get("tipo", "clearkey"),
                                "quality": server.get("quality", ""),
                                "active": True,
                                "languages": server.get("languages", []),
                                "customLanguages": server.get("customLanguages", ""),
                                "channelLogo": canal_info.get("logo", server.get("channelLogo", "")),
                                "clearkey": canal_info.get("clearkey", None),
                                "referer": canal_info.get("referer", ""),
                                "origin": canal_info.get("origin", "")
                            })
                        else:
                            # Si no se encuentra en 04.json, envolvemos la URL en el enlace iframe embed
                            iframe_url = f"https://pruevon.blogspot.com/2026/04/embedc.html?r={urllib.parse.quote(server_url, safe='')}"
                            
                            server_copy = dict(server)
                            server_copy["url"] = iframe_url
                            server_copy["type"] = "iframe"
                            nuevos_servidores.append(server_copy)

                    event["servers"] = nuevos_servidores

    if "updated" not in agenda_data or not agenda_data["updated"]:
        agenda_data["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(agenda_data, f, ensure_ascii=False, indent=4)

    print(f"Agenda manual procesada y guardada correctamente en {OUTPUT_JSON}.")

if __name__ == "__main__":
    procesar_agenda()