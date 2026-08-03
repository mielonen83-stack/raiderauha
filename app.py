import streamlit as st
import requests
from datetime import datetime

# Sivun perusasetukset
st.set_page_config(
    page_title="Raiderauha – Älykäs vaunukartta", 
    page_icon="🚆", 
    layout="wide"
)

st.title("🚆 Raiderauha")
st.markdown("##### *Älykäs junatutka vaunukartoilla varustettuna*")
st.divider()

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

if st.sidebar.button("🔍 Etsi junat ja vaunukartat", type="primary"):
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{lahto}/{paikka}"
    
    with st.spinner("Haetaan junia ja kokoonpanoja..."):
        vastaus = requests.get(url)
    
    if vastaus.status_code == 200:
        junat = vastaus.json()
        
        aktiiviset_junat = []
        for juna in junat:
            if juna.get('cancelled', False):
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
                aktiiviset_junat.append({
                    "numero": train_num,
                    "tyyppi": train_type,
                    "lahto": lahto_aika,
                    "saapuminen": saapumis_aika
                })
        
        if not aktiiviset_junat:
            st.warning("Ei löytynyt suoria junia valitsemallesi välille.")
        else:
            st.success(f"Löytyi {len(aktiiviset_junat)} junaa!")
            
            for juna in aktiiviset_junat:
                t_num = juna["numero"]
                t_tyyppi = juna["tyyppi"]
                
                with st.expander(f"🚆 {t_tyyppi} {t_num} | Lähtö klo {juna['lahto']} ➔ Perillä klo {juna['saapuminen']}"):
                    st.markdown("#### 🗺️ Junan vaunukartta ja rauhallisuus")
                    st.write("Vaunujärjestys veturista alkaen (Etuosa ➔ Takaosa):")
                    
                    vaunut = []
                    # Yritetään hakea reaaliaikainen kokoonpano
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
                    
                    # Jos reaaliaikaisia vaunuja ei löydy, käytetään tyypillistä InterCityn/Pendolinon mallipohjaa
                    if not vaunut:
                        if t_tyyppi == "IC":
                            vaunut = [
                                {"wagonType": "Edb (Ekstra)", "salesNumber": 1},
                                {"wagonType": "Eart (Ravintola)", "salesNumber": 2},
                                {"wagonType": "In", "salesNumber": 3},
                                {"wagonType": "EFi", "salesNumber": 4},
                                {"wagonType": "Ce", "salesNumber": 5},
                                {"wagonType": "Ce", "salesNumber": 6},
                                {"wagonType": "Ce", "salesNumber": 7}
                            ]
                        else:
                            vaunut = [
                                {"wagonType": "Rk (Ravintola)", "salesNumber": 1},
                                {"wagonType": "Eo", "salesNumber": 2},
                                {"wagonType": "Eed", "salesNumber": 3},
                                {"wagonType": "Eed", "salesNumber": 4}
                            ]
                        st.caption("ℹ️ *Näytetään tyypillinen vaunumalli (reaaliaikainen kokoonpano päivittyy lähempänä lähtöä).*")
                    
                    # Piirretään vaunut visuaalisesti pylväinä
                    cols = st.columns(len(vaunut) if len(vaunut) <= 7 else 7)
                    for idx, vaunu in enumerate(vaunut[:7]):
                        v_tyyppi = vaunu.get('wagonType', 'Vaunu')
                        v_nro = vaunu.get('salesNumber', idx+1)
                        with cols[idx]:
                            st.metric(label=f"Vaunu {v_nro}", value=v_tyyppi)
                            
                    st.markdown("---")
                    st.info("💡 **Rauhavinkki:** Valitse paikka mahdollisimman kaukaa ravintolavaunusta tai leikkipaikasta. Ekstra-luokan vaunu (Edb) tarjoaa täydellisen hiljaisuuden.")

    else:
        st.error("Virhe haettaessa junatietoja.")
else:
    st.info("👈 Valitse asemat sivupalkista ja klikkaa **Etsi junat ja vaunukartat**.")
