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

# Sivupalkin hakuehdot
st.sidebar.header("🎛️ Hakuehdot")

# Suositut asemat helpottamaan valintaa
asemat_valinta = st.sidebar.selectbox(
    "Valitse suosittu reitti tai syötä omat lyhenteet:",
    ["Helsinki – Tampere (HKI - TPE)", "Helsinki – Turku (HKI - TKU)", "Helsinki – Oulu (HKI - OULU)", "Muu (kirjoita itse)"]
)

if "Helsinki – Tampere" in asemat_valinta:
    oletus_lahto = "HKI"
    oletus_paikka = "TPE"
elif "Helsinki – Turku" in asemat_valinta:
    oletus_lahto = "HKI"
    oletus_paikka = "TKU"
elif "Helsinki – Oulu" in asemat_valinta:
    oletus_lahto = "HKI"
    oletus_paikka = "OULU"
else:
    oletus_lahto = "HKI"
    oletus_paikka = "TPE"

lahtoasema = st.sidebar.text_input("Lähtöasema (lyhenne)", value=oletus_lahto)
maaranpaa = st.sidebar.text_input("Määränpää (lyhenne)", value=oletus_paikka)

lahto = lahtoasema.upper().strip()
paikka = maaranpaa.upper().strip()

# Hakunappi
if st.button("🔍 Etsi junat ja rauhan paikat", type="primary"):
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/{lahto}/{paikka}"
    
    with st.spinner(f"Etsitään junia välille {lahto} – {paikka}..."):
        vastaus = requests.get(url)
    
    if vastaus.status_code == 200:
        junat = vastaus.json()
        
        if not junat:
            st.warning(f"Ei löytynyt junia välille {lahto} – {paikka}. Tarkista asemalyhenteet.")
        else:
            st.success(f"Löytyi {len(junat)} junaa tälle välille!")
            
            # Käydään junia läpi
            for juna in junat:
                train_num = juna.get('trainNumber')
                train_type = juna.get('trainType')
                cancelled = juna.get('cancelled', False)
                
                # Jos juna on peruttu, ohitetaan se
                if cancelled:
                    continue
                
                # Etsitään lähtö- ja saapumisajat kyseisille asemille
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

                # Korttimainen esitys jokaiselle junalle
                with st.expander(f"🚆 Juna {train_type} {train_num} | Lähtö klo {lahto_aika} -> Perillä klo {saapumis_aika}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Matkatiedot:**")
                        st.write(f"- Lähtöasema: **{lahto}** klo **{lahto_aika}**")
                        st.write(f"- Määränpää: **{paikka}** klo **{saapumis_aika}**")
                        st.write(f"- Junatyyppi: {train_type}")
                    
                    with col2:
                        st.markdown("**Vinkit rauhalliseen matkaan:**")
                        st.info("💡 Vinkki: Ravintolavaunun läheisyydessä voi olla vilkkaampaa. Etsi paikka mahdollisimman kaukaa vaunujen päistä tai valitse Ekstra-luokka, jos kaipaat täydellistä hiljaisuutta.")
            
    else:
        st.error(f"Virhe tiedon haussa (koodi {vastaus.status_code}). Tarkista asemalyhenteet.")
