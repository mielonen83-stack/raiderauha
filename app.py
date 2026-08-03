import streamlit as st
import requests
from datetime import datetime
from openai import OpenAI
import folium
from streamlit_folium import st_folium

# Sivun perusasetukset
st.set_page_config(
    page_title="Raiderauha – Älykäs vaunukartta", 
    page_icon="🚆", 
    layout="wide"
)

st.title("🚆 Raiderauha")
st.markdown("##### *Älykäs junatutka, tekoäly ja vaunujen sisäiset rauha-alueet*")
st.divider()

# Alustetaan OpenAI turvallisesti Streamlitin secrets-asetuksesta
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    ai_kaytossa = True
except:
    ai_kaytossa = False

# Haetaan asemat koordinaatteineen Digitrafficin rajapinnasta
@st.cache_data
def hae_asemat():
    url = "https://rata.digitraffic.fi/api/v1/metadata/stations"
    try:
        vastaus = requests.get(url)
        if vastaus.status_code == 200:
            asemat = vastaus.json()
            matkustajasektori = [a for a in asemat if a.get('passengerTraffic') == True]
            asema_lista = {}
            for a in matkustajasektori:
                nimi = f"{a['stationName']} ({a['stationShortCode']})"
                asema_lista[nimi] = {
                    "koodi": a['stationShortCode'],
                    "lat": a.get('latitude'),
                    "lon": a.get('longitude')
                }
            return asema_lista
    except:
        pass
    return {
        "Helsinki (HKI)": {"koodi": "HKI", "lat": 60.1719, "lon": 24.9414},
        "Tampere (TPE)": {"koodi": "TPE", "lat": 61.5033, "lon": 23.7753},
        "Oulu (OULU)": {"koodi": "OULU", "lat": 65.0124, "lon": 25.4682}
    }

asema_dict = hae_asemat()
asema_nimet = list(asema_dict.keys())

# Sivupalkin hakuehdot
st.sidebar.header("🎛️ Matkan tiedot")
oletus_lahto_idx = asemat_nimet.index("Helsinki (HKI)") if "Helsinki (HKI)" in asema_nimet else 0
oletus_paikka_idx = asemat_nimet.index("Tampere (TPE)") if "Tampere (TPE)" in asema_nimet else 1

valittu_lahto_nimi = st.sidebar.selectbox("Lähtöasema", asema_nimet, index=oletus_lahto_idx)
valittu_paikka_nimi = st.sidebar.selectbox("Määränpää", asema_nimet, index=oletus_paikka_idx)

lahto_info = asema_dict[valittu_lahto_nimi]
paikka_info = asema_dict[valittu_paikka_nimi]

lahto = lahto_info["koodi"]
paikka = paikka_info["koodi"]

if st.sidebar.button("🔍 Etsi junat ja rauha-alueet", type="primary"):
    
    # 1. Kartta
    st.markdown("### 🗺️ Reittikartta")
    if lahto_info["lat"] and paikka_info["lat"]:
        keski_lat = (lahto_info["lat"] + paikka_info["lat"]) / 2
        keski_lon = (lahto_info["lon"] + paikka_info["lon"]) / 2
        
        m = folium.Map(location=[keski_lat, keski_lon], zoom_start=7, tiles="CartoDB positron")
        folium.Marker([lahto_info["lat"], lahto_info["lon"]], popup=valittu_lahto_nimi, icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker([paikka_info["lat"], paikka_info["lon"]], popup=valittu_paikka_nimi, icon=folium.Icon(color="red", icon="stop")).add_to(m)
        folium.PolyLine(locations=[[lahto_info["lat"], lahto_info["lon"]], [paikka_info["lat"], paikka_info["lon"]]], color="#1f77b4", weight=4, opacity=0.8).add_to(m)
        st_folium(m, width="100%", height=350)
    
    st.divider()
    
    # 2. Junat
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{lahto}/{paikka}"
    
    with st.spinner("Haetaan junavuoroja..."):
        vastaus = requests.get(url)
    
    if vastaus.status_code == 200:
        junat = vastaus.json()
        
        if not isinstance(junat, list):
            st.warning("Ei löytynyt suoria junia valitsemallesi välille.")
        else:
            aktiiviset_junat = []
            for juna in junat:
                if not isinstance(juna, dict) or juna.get('cancelled', False):
                    continue
                
                train_num = juna.get('trainNumber')
                train_type = juna.get('trainType')
                
                timeTable = juna.get('timeTableRows', [])
                lahto_aika = ""
                saapumis_aika = ""
                
                for rivi in timeTable:
                    if rivi.get('stationShortCode') == lahto and rivi.get('type') == 'DEPARTURE':
                        aika_str = rivi.get('scheduledTime')
                        if aika_str:
                            lahto_aika = datetime.fromisoformat(aika_str.replace('Z', '+00:00')).strftime('%H:%M')
                    if rivi.get('stationShortCode') == paikka and rivi.get('type') == 'ARRIVAL':
                        aika_str = rivi.get('scheduledTime')
                        if aika_str:
                            saapumis_aika = datetime.fromisoformat(aika_str.replace('Z', '+00:00')).strftime('%H:%M')
                
                if lahto_aika and saapumis_aika:
                    aktiiviset_junat.append({"numero": train_num, "tyyppi": train_type, "lahto": lahto_aika, "saapuminen": saapumis_aika})
            
            if not aktiiviset_junat:
                st.warning("Ei löytynyt suoria junia valitsemallesi välille.")
            else:
                st.success(f"Löytyi {len(aktiiviset_junat)} junaa!")
                
                for juna in aktiiviset_junat:
                    t_num = juna["numero"]
                    t_tyyppi = juna["tyyppi"]
                    
                    with st.expander(f"🚆 {t_tyyppi} {t_num} | Lähtö klo {juna['lahto']} ➔ Perillä klo {juna['saapuminen']}"):
                        
                        if ai_kaytossa:
                            with st.spinner("🤖 Tekoäly analysoi junaa..."):
                                try:
                                    prompt = f"Olet VR:n matkaoppaan assistentti. Anna lyhyt ja oivaltava rauhallisuussuositus junalle {t_tyyppi} {t_num} reitillä {valittu_lahto_nimi} - {valittu_paikka_nimi}."
                                    completion = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], max_tokens=150)
                                    st.info(f"🤖 **Tekoälyn rauharaportti:**\n\n{completion.choices[0].message.content}")
                                except:
                                    pass
                        
                        st.markdown("#### 🗺️ Junan vaunukartta")
                        st.write("Junan kokoonpano veturista alkaen (⬅️ Veturi | Takaosa ➡️):")
                        
                        vaunut = []
                        komp_url = f"https://rata.digitraffic.fi/api/v1/compositions/{t_num}"
                        try:
                            komp_vastaus = requests.get(komp_url)
                            if komp_vastaus.status_code == 200:
                                komp_data = komp_vastaus.json()
                                sections = komp_data.get('journeySections', [])
                                if sections:
                                    vaunut = sections[0].get('wagons', [])
                        except:
                            pass
                        
                        if not vaunut:
                            if t_tyyppi == "IC":
                                vaunut = [
                                    {"wagonType": "Edb (Ekstra)", "salesNumber": "1"},
                                    {"wagonType": "Ravintola", "salesNumber": "2"},
                                    {"wagonType": "InterCity", "salesNumber": "3"},
                                    {"wagonType": "InterCity", "salesNumber": "4"},
                                    {"wagonType": "InterCity", "salesNumber": "5"},
                                    {"wagonType": "InterCity", "salesNumber": "6"},
                                    {"wagonType": "InterCity", "salesNumber": "7"}
                                ]
                            else:
                                vaunut = [
                                    {"wagonType": "Ravintola", "salesNumber": "1"},
                                    {"wagonType": "Vaunun", "salesNumber": "2"},
                                    {"wagonType": "Vaunu", "salesNumber": "3"}
                                ]
                        
                        cols = st.columns(len(vaunut) if len(vaunut) <= 8 else 8)
                        for idx, v in enumerate(vaunut[:8]):
                            v_nimi = v.get('wagonType', 'Vaunu')
                            v_nro = v.get('salesNumber', str(idx+1))
                            with cols[idx]:
                                st.metric(label=f"Vaunu {v_nro}", value=v_nimi)
                        
                        # --- UUSI: YKSITTÄISEN VAUNUN SISÄINEN RAUHA-ALUEKARTTA ---
                        st.markdown("---")
                        st.markdown("#### 💺 Vaunun sisäinen rauha-kartta (Mistä löydät hiljaisuuden?)")
                        st.write("Tältä näyttää tyypillisen vaunun sisäinen dynamiikka päädystä päätyyn:")
                        
                        # Piirretään graafinen vaunun sisäosa sarakkeilla
                        v_col1, v_col2, v_col3, v_col4, v_col5 = st.columns(5)
                        
                        with v_col1:
                            st.error("🔴 **Väliovi / Vessa**\n\n*Vilkas*\n(Paljon kulkua ja oven aukaisua)")
                        with v_col2:
                            st.warning("🟠 **Vaunun päätypaikat**\n\n*Melko vilkas*\n(Lähellä eteistä)")
                        with v_col3:
                            st.success("🟢 **Vaunun keskiosa**\n\n*Erittäin rauhallinen*\n⭐ **Paras paikka**")
                        with v_col4:
                            st.warning("🟠 **Vaunun päätypaikat**\n\n*Melko vilkas*\n(Lähellä eteistä)")
                        with v_col5:
                            st.error("🔴 **Väliovi / Vessa**\n\n*Vilkas*\n(Paljon kulkua ja oven aukaisua)")

    else:
        st.error("Virhe haettaessa junatietoja.")
else:
    st.info("👈 Valitse asemat sivupalkista ja klikkaa **Etsi junat ja rauha-alueet**.")
