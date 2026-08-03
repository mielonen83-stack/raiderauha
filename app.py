import streamlit as st
import requests
from datetime import datetime
from openai import OpenAI

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

# Haetaan asemat Digitrafficin rajapinnasta
@st.cache_data
def hae_asemat():
    url = "https://rata.digitraffic.fi/api/v1/metadata/stations"
    try:
        vastaus = requests.get(url)
        if vastaus.status_code == 200:
            asemat = vastaus.json()
            matkustajasektori = [a for a in asemat if a.get('passengerTraffic') == True]
            asema_lista = {f"{a['stationName']} ({a['stationShortCode']})": a['stationShortCode'] for a in matkustajasektori}
            return asema_lista
    except:
        pass
    return {"Helsinki (HKI)": "HKI", "Tampere (TPE)": "TPE", "Turku (TKU)": "TKU", "Oulu (OULU)": "OULU"}

asema_dict = hae_asemat()
asema_nimet = list(asema_dict.keys())

# Sivupalkin hakuehdot
st.sidebar.header("🎛️ Matkan tiedot")
oletus_lahto_idx = asema_nimet.index("Helsinki (HKI)") if "Helsinki (HKI)" in asema_nimet else 0
oletus_paikka_idx = asema_nimet.index("Tampere (TPE)") if "Tampere (TPE)" in asema_nimet else 1

valittu_lahto_nimi = st.sidebar.selectbox("Lähtöasema", asema_nimet, index=oletus_lahto_idx)
valittu_paikka_nimi = st.sidebar.selectbox("Määränpää", asema_nimet, index=oletus_paikka_idx)

lahto = asema_dict[valittu_lahto_nimi]
paikka = asema_dict[valittu_paikka_nimi]

if st.sidebar.button("🔍 Etsi junat ja rauha-alueet", type="primary"):
    
    # Siisti matkatieto-otsikko ilman karttasekoiluja
    st.markdown(f"### 🗺️ Reitti: **{valittu_lahto_nimi}** ➔ **{valittu_paikka_nimi}**")
    st.info("💡 Haetaan reaaliaikaisia junatietoja ja vaunukokoonpanoja Digitrafficista...")
    st.divider()
    
    # Haetaan junat
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{lahto}/{paikka}"
    
    with st.spinner("Haetaan junavuoroja ja tekoälyn analyysiä..."):
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
                                    {"wagonType": "Vaunu", "salesNumber": "2"},
                                    {"wagonType": "Vaunu", "salesNumber": "3"}
                                ]
                        
                        cols = st.columns(len(vaunut) if len(vaunut) <= 8 else 8)
                        for idx, v in enumerate(vaunut[:8]):
                            v_nimi = v.get('wagonType', 'Vaunu')
                            v_nro = v.get('salesNumber', str(idx+1))
                            with cols[idx]:
                                st.metric(label=f"Vaunu {v_nro}", value=v_nimi)
                        
                        # Vaunun sisäinen rauha-aluekartta
                        st.markdown("---")
                        st.markdown("#### 💺 Vaunun sisäinen rauha-kartta (Mistä löydät hiljaisuuden?)")
                        st.write("Tältä näyttää tyypillisen vaunun sisäinen dynamiikka päädystä päätyyn:")
                        
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
