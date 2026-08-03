import streamlit as st
import requests
from datetime import datetime

# Sivun perusasetukset
st.set_page_config(
    page_title="Raiderauha – Visuaalinen vaunukartta", 
    page_icon="🚆", 
    layout="wide"
)

st.title("🚆 Raiderauha")
st.markdown("##### *Visuaalinen junatutka ja graafinen vaunukartta*")
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
oletus_lahto_idx = asema_nimet.index("Helsinki (HKI)") if "Helsinki (HKI)" in asemat_nimet else 0
oletus_paikka_idx = asema_nimet.index("Tampere (TPE)") if "Tampere (TPE)" in asemat_nimet else 1

valittu_lahto_nimi = st.sidebar.selectbox("Lähtöasema", asema_nimet, index=oletus_lahto_idx)
valittu_paikka_nimi = st.sidebar.selectbox("Määränpää", asema_nimet, index=oletus_paikka_idx)

lahto = asema_dict[valittu_lahto_nimi]
paikka = asema_dict[valittu_paikka_nimi]

if st.sidebar.button("🔍 Etsi junat ja vaunukartta", type="primary"):
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{lahto}/{paikka}"
    
    with st.spinner("Haetaan junia ja luodaan vaunukarttaa..."):
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
                if rivi.get('stationShortCode') == lahto and rivi.get('type'] == 'DEPARTURE':
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
                    st.markdown("#### 🗺️ Visuaalinen vaunukartta")
                    st.write("Junan kokoonpano veturista alkaen (⬅️ Etuosa / Veturi | Takaosa ➡️):")
                    
                    # Haetaan vaunut
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
                        # Varakartta hienolla esityksellä
                        if t_tyyppi == "IC":
                            vaunut = [
                                {"wagonType": "Edb (Ekstra)", "salesNumber": "1", "tyyppi": "ekstra"},
                                {"wagonType": "Ravintola", "salesNumber": "2", "tyyppi": "ravintola"},
                                {"wagonType": "InterCity", "salesNumber": "3", "tyyppi": "normaali"},
                                {"wagonType": "InterCity", "salesNumber": "4", "tyyppi": "normaali"},
                                {"wagonType": "InterCity", "salesNumber": "5", "tyyppi": "normaali"},
                                {"wagonType": "InterCity", "salesNumber": "6", "tyyppi": "normaali"},
                                {"wagonType": "InterCity", "salesNumber": "7", "tyyppi": "normaali"}
                            ]
                        else:
                            vaunut = [
                                {"wagonType": "Ravintola", "salesNumber": "1", "tyyppi": "ravintola"},
                                {"wagonType": "Vaunu", "salesNumber": "2", "tyyppi": "normaali"},
                                {"wagonType": "Vaunu", "salesNumber": "3", "tyyppi": "normaali"}
                            ]
                    
                    # Rakennetaan HTML-vaunujono
                    html_vaunut = "<div style='display: flex; gap: 8px; overflow-x: auto; padding: 10px 0; align-items: center;'>"
                    
                    # Lisätään veturi alkuun
                    html_vaunut += "<div style='background-color: #333; color: white; padding: 12px 10px; border-radius: 8px; text-align: center; min-width: 70px; font-weight: bold; font-size: 12px;'> locomotives 🚂<br><span style='font-size: 10px;'>Veturi</span></div>"
                    
                    for idx, v in enumerate(vaunut):
                        v_nimi = v.get('wagonType', 'Vaunu')
                        v_nro = v.get('salesNumber', str(idx+1))
                        
                        # Värikoodataan tyypin mukaan
                        bg_color = "#1f77b4" # Sininen oletus
                        v_lower = str(v_nimi).lower()
                        if "ekstra" in v_lower or "edb" in v_lower:
                            bg_color = "#2ca02c" # Vihreä ekstra-luokalle
                        elif "ravintola" in v_lower or "eart" in v_lower or "rk" in v_lower:
                            bg_color = "#ff7f0e" # Oranssi ravintolalle
                            
                        html_vaunut += f"""
                        <div style='background-color: {bg_color}; color: white; padding: 10px 8px; border-radius: 6px; text-align: center; min-width: 80px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                            <div style='font-size: 11px; font-weight: bold;'>Vaunu {v_nro}</div>
                            <div style='font-size: 10px; margin-top: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{v_nimi}</div>
                        </div>
                        """
                    
                    html_vaunut += "</div>"
                    
                    # Näytetään HTML Streamlitissa
                    st.markdown(html_vaunut, unsafe_allow_html=True)
                    
                    st.markdown("---")
                    st.markdown("**Värikoodien selitykset:** 🟩 Vihreä = Ekstra-luokka (hiljainen), 🟧 Oranssi = Ravintolavaunu (vilkas), 🟦 Sininen = Normaalivaunu.")
                    st.info("💡 **Rauhavinkki:** Valitse paikka keskimmäisistä sinisistä vaunuista. Vältä ravintolavaunun viereisiä vaunuja, jos haluat täydellisen levon.")

    else:
        st.error("Virhe haettaessa junatietoja.")
else:
    st.info("👈 Valitse asemat sivupalkista ja klikkaa **Etsi junat ja vaunukartta**.")
