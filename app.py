import streamlit as st
import requests
from datetime import datetime

# Sivun perusasetukset
st.set_page_config(
    page_title="Raiderauha – Etsi rauha junamatkalle", 
    page_icon="🚆", 
    layout="wide"
)

# Pääotsikko ja kuvaus
st.title("🚆 Raiderauha")
st.markdown("### Etsi rauhallinen ja sujuva matkustuskokemus suomalaisissa junissa.")

# Haetaan asemat Digitrafficin rajapinnasta, jotta saadaan oikeat nimet ja lyhenneteet
@st.cache_data
def hae_asemat():
    url = "https://rata.digitraffic.fi/api/v1/metadata/stations"
    try:
        vastaus = requests.get(url)
        if vastaus.status_code == 200:
            asemat = vastaus.json()
            # Suodatetaan vain matkustajaliikenteen asemat, joilla on nimi
            matkustajasektori = [a for a in asemat if a.get('passengerTraffic') == True]
            # Tehdään sanakirja: "Helsinki (HKI)" -> "HKI"
            asema_lista = {f"{a['stationName']} ({a['stationShortCode']})": a['stationShortCode'] for a in matkustajasektori}
            return asema_lista
    except:
        pass
    # Varakartta jos rajapinnassa häiriö
    return {"Helsinki (HKI)": "HKI", "Tampere (TPE)": "TPE", "Turku (TKU)": "TKU", "Oulu (OULU)": "OULU"}

asema_dict = hae_asemat()
asema_nimet = list(asema_dict.keys())

# Sivupalkin hakuehdot
st.sidebar.header("🎛️ Matkan tiedot")

# Valitaan lähtö- ja määränpääasema pudotusvalikoista
oletus_lahto_idx = asema_nimet.index("Helsinki (HKI)") if "Helsinki (HKI)" in asema_nimet else 0
oletus_paikka_idx = asema_nimet.index("Tampere (TPE)") if "Tampere (TPE)" in asema_nimet else 1

valittu_lahto_nimi = st.sidebar.selectbox("Lähtöasema", asema_nimet, index=oletus_lahto_idx)
valittu_paikka_nimi = st.sidebar.selectbox("Määränpää", asema_nimet, index=oletus_paikka_idx)

lahto = asema_dict[valittu_lahto_nimi]
paikka = asema_dict[valittu_paikka_nimi]

# Hakunappi
if st.button("🔍 Etsi junat ja rauhan paikat", type="primary"):
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/{lahto}/{paikka}"
    
    with st.spinner(f"Etsitään junia väliltä {valittu_lahto_nimi} – {valittu_paikka_nimi}..."):
        vastaus = requests.get(url)
    
    if vastaus.status_code == 200:
        junat = vastaus.json()
        
        if not junat:
            st.warning(f"Ei löytynyt suoria junia valitsemallesi välille. Kokeile toisia asemia.")
        else:
            st.success(f"Löytyi {len(junat)} junaa!")
            
            # Käydään junia läpi
            for juna in junat:
                train_num = juna.get('trainNumber')
                train_type = juna.get('trainType')
                cancelled = juna.get('cancelled', False)
                
                if cancelled:
                    continue
                
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

                # Korttimainen esitys
                with st.expander(f"🚆 Juna {train_type} {train_num} | Lähtö klo {lahto_aika} -> Perillä klo {saapumis_aika}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Matkatiedot:**")
                        st.write(f"- Lähtö: **{valittu_lahto_nimi}** klo **{lahto_aika}**")
                        st.write(f"- Perillä: **{valittu_paikka_nimi}** klo **{saapumis_aika}**")
                        st.write(f"- Junatyyppi: {train_type} {train_num}")
                    
                    with col2:
                        st.markdown("**Vinkit rauhalliseen matkaan:**")
                        st.info("💡 **Rauhavinkki:** Valitse paikka vaunun keskivaiheilta, kauempaa ovista ja vessakopeista. Ravintolavaunun läheisyydessä on usein enemmän liikehdintää, kun taas Ekstra-luokka tarjoaa maksimaalista hiljaisuutta.")
            
    else:
        st.error(f"Virhe tiedon haussa (koodi {vastaus.status_code}). Yritä hetken päästä uudelleen.")
