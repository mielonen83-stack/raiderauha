import streamlit as st
import requests
from datetime import datetime

# Sivun perusasetukset
st.set_page_config(
    page_title="Raiderauha – Etsi rauha junamatkalle", 
    page_icon="🚆", 
    layout="wide"
)

st.title("🚆 Raiderauha")
st.markdown("### Etsi rauhallinen ja sujuva matkustuskokemus suomalaisissa junissa.")

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

if st.button("🔍 Etsi junat ja rauhan paikat", type="primary"):
    # Haetaan lähtöaseman kautta kulkevat junat oikealla rajapintapolulla
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{lahto}?included_countries=FI"
    
    with st.spinner(f"Etsitään junia väliltä {valittu_lahto_nimi} – {valittu_paikka_nimi}..."):
        vastaus = requests.get(url)
    
    if vastaus.status_code == 200:
        kaikki_junat = vastaus.json()
        
        # Suodatetaan ne junat, jotka menevät myös määränpään kautta
        loytyneet_junat = []
        
        for juna in kaikki_junat:
            if juna.get('cancelled', False):
                continue
            
            aikataulu = juna.get('timeTableRows', [])
            menee_lahtoon = False
            menee_paikkaan = False
            lahto_aika = ""
            saapumis_aika = ""
            
            for rivi in aikataulu:
                asema_koodi = rivi.get('stationShortCode')
                tyyppi = rivi.get('type')
                
                # Tarkistetaan järjestys: lähtöaseman pitää olla ennen määränpäätä
                if asema_koodi == lahto and tyyppi == 'DEPARTURE':
                    menee_lahtoon = True
                    aika_str = rivi.get('scheduledTime')
                    if aika_str:
                        lahto_aika = datetime.fromisoformat(aika_str.replace('Z', '+00:00')).strftime('%H:%M')
                
                if asema_koodi == paikka and tyyppi == 'ARRIVAL' and menee_lahtoon:
                    menee_paikkaan = True
                    aika_str = rivi.get('scheduledTime')
                    if aika_str:
                        saapumis_aika = datetime.fromisoformat(aika_str.replace('Z', '+00:00')).strftime('%H:%M')
            
            if menee_lahtoon and menee_paikkaan:
                juna['lahto_aika'] = lahto_aika
                juna['saapumis_aika'] = saapumis_aika
                loytyneet_junat.append(juna)
        
        if not loytyneet_junat:
            st.warning(f"Ei löytynyt suoria junia valitsemallesi välille ({valittu_lahto_nimi} -> {valittu_paikka_nimi}) tällä hetkellä.")
        else:
            st.success(f"Löytyi {len(loytyneet_junat)} junaa!")
            
            for juna in loytyneet_junat:
                train_num = juna.get('trainNumber')
                train_type = juna.get('trainType')
                l_aika = juna.get('lahto_aika')
                s_aika = juna.get('saapumis_aika')
                
                with st.expander(f"🚆 Juna {train_type} {train_num} | Lähtö klo {l_aika} -> Perillä klo {s_aika}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Matkatiedot:**")
                        st.write(f"- Lähtö: **{valittu_lahto_nimi}** klo **{l_aika}**")
                        st.write(f"- Perillä: **{valittu_paikka_nimi}** klo **{s_aika}**")
                        st.write(f"- Junatyyppi: {train_type} {train_num}")
                    
                    with col2:
                        st.markdown("**Vinkit rauhalliseen matkaan:**")
                        st.info("💡 **Rauhavinkki:** Valitse paikka vaunun keskivaiheilta, kauempaa ovista ja vessakopeista. Ravintolavaunun läheisyydessä on vilkkaampaa, kun taas Ekstra-luokka tarjoaa hiljaisuutta.")
            
    else:
        st.error(f"Virhe tiedon haussa (koodi {vastaus.status_code}). Yritä hetken päästä uudelleen.")
