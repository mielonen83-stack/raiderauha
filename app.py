import streamlit as st
import requests
from datetime import datetime

# Sivun perusasetukset
st.set_page_config(
    page_title="Raiderauha – Visuaalinen junatutka", 
    page_icon="🚆", 
    layout="wide"
)

# Tyylikäs yläpalkki / otsikko
st.title("🚆 Raiderauha")
st.markdown("##### *Visuaalinen työkalu rauhallisen ja sujuvan junamatkan suunnitteluun*")
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
st.sidebar.markdown("Valitse reitti, jolle haluat etsiä rauhallisen junapaikan.")

# Korjattu muuttujan nimi (asema_nimet)
oletus_lahto_idx = asema_nimet.index("Helsinki (HKI)") if "Helsinki (HKI)" in asema_nimet else 0
oletus_paikka_idx = asema_nimet.index("Tampere (TPE)") if "Tampere (TPE)" in asema_nimet else 1

valittu_lahto_nimi = st.sidebar.selectbox("Lähtöasema", asema_nimet, index=oletus_lahto_idx)
valittu_paikka_nimi = st.sidebar.selectbox("Määränpää", asema_nimet, index=oletus_paikka_idx)

lahto = asema_dict[valittu_lahto_nimi]
paikka = asema_dict[valittu_paikka_nimi]

# Hakunappi
if st.sidebar.button("🔍 Hae junat ja tilastot", type="primary"):
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{lahto}/{paikka}"
    
    with st.spinner(f"Haetaan grafiikoita ja junatietoja välille {valittu_lahto_nimi} – {valittu_paikka_nimi}..."):
        vastaus = requests.get(url)
    
    if vastaus.status_code == 200:
        junat = vastaus.json()
        
        # Suodatetaan perutut pois
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
                    "numero": f"{train_type} {train_num}",
                    "lahto": lahto_aika,
                    "saapuminen": saapumis_aika,
                    "tyyppi": train_type
                })
        
        if not aktiiviset_junat:
            st.warning(f"Ei löytynyt suoria junia välille {valittu_lahto_nimi} -> {valittu_paikka_nimi} tällä hetkellä.")
        else:
            # Visuaaliset mittarit (Metrics) yläosaan
            st.markdown("### 📊 Reitin yleiskatsaus")
            m1, m2, m3 = st.columns(3)
            m1.metric(label="Löytyneet vuorot", value=f"{len(aktiiviset_junat)} kpl")
            m2.metric(label="Ensimmäinen lähtö", value=aktiiviset_junat[0]["lahto"])
            m3.metric(label="Viimeinen lähtö", value=aktiiviset_junat[-1]["lahto"])
            
            st.divider()
            st.markdown("### 🚆 Junavuorot ja rauhallisuuden arviot")
            
            # Käydään vuorot läpi grafiikoiden kanssa
            for juna in aktiiviset_junat:
                with st.expander(f"🚆 {juna['numero']} | Lähtö klo {juna['lahto']} ➔ Perillä klo {juna['saapuminen']}"):
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                        st.markdown("**Matkan tiedot:**")
                        st.write(f"• Lähtö: **{valittu_lahto_nimi}** klo **{juna['lahto']}**")
                        st.write(f"• Perillä: **{valittu_paikka_nimi}** klo **{juna['saapuminen']}**")
                    
                    with col2:
                        st.markdown("**Rauhallisuusindeksi:**")
                        st.progress(75, text="Välivaihe: Hiljainen / Mukava")
                        st.write("💡 *Vinkki: Keskivaunut tarjoavat yleensä vähiten läpikulkuliikennettä.*")
                        
                    with col3:
                        st.markdown("**Valinta:**")
                        if st.button("Valitse", key=f"btn_{juna['numero']}"):
                            st.toast(f"Valitsit junan {juna['numero']}! Hyvää matkaa rauhaan.")

    else:
        st.error(f"Virhe tiedon haussa (koodi {vastaus.status_code}). Yritä hetken päästä uudelleen.")
else:
    # Aloitusnäyttö ennen hakua
    st.info("👈 Valitse sivupalkista lähtö- ja määränpääasema, ja klikkaa **Hae junat ja tilastot**.")
