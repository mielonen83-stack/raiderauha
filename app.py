import streamlit as st
import requests

st.title("🚆 Raiderauha")
st.write("Etsi rauhallinen istumapaikka suomalaisista junista.")

if st.button("Hae junat (Helsinki - Tampere)"):
    url = "https://rata.digitraffic.fi/api/v1/live-trains/hki/tpe"
    
    with st.spinner("Haetaan tietoja Digitrafficista..."):
        vastaus = requests.get(url)
    
    if vastaus.status_code == 200:
        junat = vastaus.json()
        st.success(f"Yhteys toimii! Löytyi {len(junat)} junaa.")
        
        # Näytetään muutama ensimmäinen juna
        for juna in junat[:3]:
            train_num = juna.get('trainNumber')
            train_type = juna.get('trainType')
            st.write(f"🔹 **Juna {train_num}** ({train_type})")
    else:
        st.error(f"Virhe tiedon haussa: {vastaus.status_code}")
