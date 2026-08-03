import streamlit as st
import requests

# Sivun asetukset
st.set_page_title_config = st.set_page_config(page_title="Raiderauha", page_icon="🚆", layout="wide")

st.title("🚆 Raiderauha")
st.write("Etsi rauhallinen ja sujuva matkustuskokemus suomalaisissa junissa.")

# Hakuehdot käyttäjälle
st.sidebar.header("Hakuehdot")
lahtoasema = st.sidebar.text_input("Lähtöasema (lyhenne)", value="HKI")
maaranpaa = st.sidebar.text_input("Määränpää (lyhenne)", value="TPE")

# Muutetaan isot kirjaimet varmuudeksi
lahto = lahtoasema.upper().strip()
paikka = maaranpaa.upper().strip()

if st.button("Hae junat", type="primary"):
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/{lahto}/{paikka}"
    
    with st.spinner(painava_viesti := f"Haetaan junia välille {lahto} – {paikka}..."):
        vastaus = requests.get(url)
    
    if vastaus.status_code == 200:
        junat = vastaus.json()
        
        if not junat:
            st.warning(f"Ei löytynyt junia välille {lahto} – {paikka}. Tarkista asemalyhenteet (esim. HKI, TPE, OULU, KUO).")
        else:
            st.success(f"Löytyi {len(junat)} junaa!")
            
            # Kerätään tiedot listaan, jotta saadaan siisti taulukko
            taulukko_data = []
            for juna in junat:
                train_num = juna.get('trainNumber')
                train_type = juna.get('trainType')
                dep_date = juna.get('departureDate')
                
                taulukko_data.append({
                    "Junanumero": train_num,
                    "Tyyppi": train_type,
                    "Lähtöpäivä": dep_date
                })
            
            # Näytetään tiedot Streamlitin hienona taulukkona
            st.dataframe(taulukko_data, use_container_width=True)
            
    else:
        st.error(f"Virhe tiedon haussa (koodi {vastaus.status_code}). Tarkista asemalyhenteet.")
