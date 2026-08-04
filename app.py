from datetime import datetime
import requests
import streamlit as st

# --- SIVUSTON ASETUKSET ---
st.set_page_config(
    page_title="Raidetutka", page_icon="🚆", layout="wide"
)

# --- KÄVIJÄLASKURI (Toimii aina, ohittaa adblockerit) ---


def track_visitor():
  if "visitor_counted" not in st.session_state:
    try:
      response = requests.get(
          "https://api.countapi.xyz/hit/raidetutka-sovellus/kavijat", timeout=2
      )
      if response.status_code == 200:
        st.session_state["visitor_count"] = response.json().get("value", "–")
      else:
        st.session_state["visitor_count"] = "–"
    except Exception:
      st.session_state["visitor_count"] = "–"
    st.session_state["visitor_counted"] = True


track_visitor()

# --- SIVUPALKKI (Sidebar) ---
st.sidebar.title("🚆 Raidetutka")
st.sidebar.markdown("Reaaliaikainen junaseuranta Suomessa.")

st.sidebar.markdown("---")
st.sidebar.subheader("📈 Tilastot")
st.sidebar.metric(
    label="Kävijät yhteensä",
    value=st.session_state.get("visitor_count", "–"),
)

st.sidebar.markdown("---")
st.sidebar.subheader("💡 Mainokset / Yhteistyö")
st.sidebar.write("Suunnitteletko matkaa? Löydä parhaat yhteydet ja liput alta:")

# Affiliate-linkkinappi (Vaihda Omiosta saamasi seurantalinkki tähän)
st.sidebar.link_button(
    "🎟️ Siirry lipunmyyntiin ja varauksiin",
    "https://www.omio.com",  # <-- VAIHDA TÄHÄN OMA AFFILIATE-LINKKISI
)

# --- PÄÄSIVU ---
st.title("🚆 Raidetutka - Junien seuranta")
st.write(
    "Tervetuloa seurantaan! Valitse alta lähtö- ja määräasema nähdäksesi"
    " aikataulut ja reaaliaikaiset myöhästymiset."
)

# Asemavalinnat
col1, col2 = st.columns(2)
with col1:
  lahtoasema = st.selectbox(
      "Lähtöasema", ["Helsinki", "Tampere", "Turku", "Oulu", "Joensuu"]
  )
with col2:
  saapumisasema = st.selectbox(
      "Määräasema", ["Tampere", "Helsinki", "Oulu", "Turku", "Joensuu"]
  )

paiva = st.date_input("Valitse päivä", datetime.now())

if st.button("Hae junat"):
  st.info(
      f"Haetaan junia välille {lahtoasema} – {saapumisasema}"
      f" ({paiva.strftime('%d.%m.%Y')})..."
  )

  # Esimerkkidatassa kellonajat ovat 24 tunnin muodossa (%H:%M)
  Esimerkki_junat = [
      {
          "nimi": "IC 8",
          "lahto": "09:00",
          "perille": "13:44",
          "tila": "Myöhässä +1 min ⚠️",
      },
      {
          "nimi": "IC 10",
          "lahto": "12:10",
          "perille": "16:44",
          "tila": "Myöhässä +1 min ⚠️",
      },
      {
          "nimi": "IC 12",
          "lahto": "15:10",
          "perille": "19:45",
          "tila": "Myöhässä +1 min ⚠️",
      },
      {
          "nimi": "IC 104",
          "lahto": "16:00",
          "perille": "20:40",
          "tila": "Aikataulussa ✅",
      },
  ]

  st.markdown("### Löytyneet vuorot:")
  for juna in Esimerkki_junat:
    st.markdown(
        f"**🚆 {juna['nimi']}**\n\nLähtö: {juna['lahto']} ➔ Perille:"
        f" {juna['perille']}\nTila: {juna['tila']}\n"
    )
    st.markdown("---")
