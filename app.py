from datetime import date, datetime, timedelta
from math import atan2, cos, radians, sin, sqrt
from zoneinfo import ZoneInfo
from openai import OpenAI
import requests
import sqlite3
import streamlit as st
import streamlit.components.v1 as components

# Sivun perusasetukset ja SEO-otsikko
st.set_page_config(
    page_title=(
        "Raiderauha – Reaaliaikainen Junatutka, Aikataulut & Rataliikennehäiriöt"
    ),
    page_icon="🚆",
    layout="wide",
)

# --- GOOGLE ANALYTICS & SEO METATIEDOT ---
GA_MEASUREMENT_ID = "G-ET3PWNZCXH"

ga_script = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{GA_MEASUREMENT_ID}');
    </script>
    <!-- SEO Meta Tags -->
    <meta name="description" content="Raiderauha on älykäs junatutka, joka näyttää VR:n reaaliaikaiset aikataulut, rataliikennehäiriöt, sää ja matkustajien live-raportit." />
    <meta name="keywords" content="junatutka, junan myöhästyminen, VR aikataulut, rataliikennehäiriöt, live junatutka, matkabingo" />
"""
components.html(ga_script, height=0, width=0)


# --- TIETOKANNAN ALUSTUS ---
def alusta_tietokanta():
  yhteys = sqlite3.connect("rauharaportit.db")
  kursori = yhteys.cursor()
  kursori.execute("""
        CREATE TABLE IF NOT EXISTS raportit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juna_numero TEXT,
            raportti TEXT,
            aika TEXT
        )
    """)
  kursori.execute("""
        CREATE TABLE IF NOT EXISTS chat_viestit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            juna_numero TEXT,
            nimimerkki TEXT,
            viesti TEXT,
            aika TEXT
        )
    """)
  yhteys.commit()
  yhteys.close()


alusta_tietokanta()


def tallenna_raportti(juna_numero, raportti_teksti):
  yhteys = sqlite3.connect("rauharaportit.db")
  kursori = yhteys.cursor()
  aikaleima = datetime.now(ZoneInfo("Europe/Helsinki")).strftime(
      "%d.%m.%Y klo %H:%M"
  )
  kursori.execute(
      "INSERT INTO raportit (juna_numero, raportti, aika) VALUES (?, ?, ?)",
      (str(juna_numero), raportti_teksti, aikaleima),
  )
  yhteys.commit()
  yhteys.close()


def hae_raportit(juna_numero):
  yhteys = sqlite3.connect("rauharaportit.db")
  kursori = yhteys.cursor()
  kursori.execute(
      "SELECT raportti, aika FROM raportit WHERE juna_numero = ? ORDER BY id"
      " DESC",
      (str(juna_numero),),
  )
  tulokset = kursori.fetchall()
  yhteys.close()
  return tulokset


def tallenna_chat_viesti(juna_numero, nimimerkki, viesti):
  yhteys = sqlite3.connect("rauharaportit.db")
  kursori = yhteys.cursor()
  aikaleima = datetime.now(ZoneInfo("Europe/Helsinki")).strftime("%H:%M")
  kursori.execute(
      "INSERT INTO chat_viestit (juna_numero, nimimerkki, viesti, aika) VALUES"
      " (?, ?, ?, ?)",
      (str(juna_numero), nimimerkki, viesti, aikaleima),
  )
  yhteys.commit()
  yhteys.close()


def hae_chat_viestit(juna_numero):
  yhteys = sqlite3.connect("rauharaportit.db")
  kursori = yhteys.cursor()
  kursori.execute(
      "SELECT nimimerkki, viesti, aika FROM chat_viestit WHERE juna_numero = ?"
      " ORDER BY id ASC",
      (str(juna_numero),),
  )
  tulokset = kursori.fetchall()
  yhteys.close()
  return tulokset


if "suosikit" not in st.session_state:
  st.session_state.suosikit = [("Helsinki (HKI)", "Joensuu (JNS)")]

if "paivan_vitsi" not in st.session_state:
  st.session_state.paivan_vitsi = (
      "Miksi juna pysähtyi keskelle metsää? – Konduktööri unohti pyyhkiä pyyhkijät"
      " pois päältä! 🚂💨"
  )

if "haku_tehty" not in st.session_state:
  st.session_state.haku_tehty = False

# Matkabingon tilan alustus
if "bingo_ruudut" not in st.session_state:
  st.session_state.bingo_ruudut = {
      "Pahoittelemme myöhästymistä": False,
      "Kaiuttimen rätinä": False,
      "Puhelin ilman kuulokkeita": False,
      "Kahvikuppi nurin tai kaatuu": False,
      "Kadonnut matkalippu": False,
      "Lehmä ikkunasta bongattu": False,
      "Konduktöörin syvä huokaus": False,
      "Joku puhuu puheluun liian kovaa": False,
      "Vessanovi ei meinaa mennä kiinni": False,
  }

try:
  client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
  ai_kaytossa = True
except:
  ai_kaytossa = False


@st.cache_data
def hae_asemat():
  url = "https://rata.digitraffic.fi/api/v1/metadata/stations"
  try:
    vastaus = requests.get(url)
    if vastaus.status_code == 200:
      asemat = vastaus.json()
      matkustajasektori = [
          a for a in asemat if a.get("passengerTraffic") == True
      ]
      asema_lista = {}
      for a in matkustajasektori:
        nimi = f"{a['stationName']} ({a['stationShortCode']})"
        asema_lista[nimi] = {
            "koodi": a["stationShortCode"],
            "lat": a.get("latitude"),
            "lon": a.get("longitude"),
        }
      return asema_lista
  except:
    pass
  return {
      "Helsinki (HKI)": {"koodi": "HKI", "lat": 60.1719, "lon": 24.9414},
      "Joensuu (JNS)": {"koodi": "JNS", "lat": 62.5998, "lon": 29.7634},
      "Tampere (TPE)": {"koodi": "TPE", "lat": 61.5033, "lon": 23.7733},
  }


# --- FINTRAFFICIN HÄIRIÖTIEDOTTEIDEN & ASEMAVIESTIEN RAJAPINTA ---
@st.cache_data(ttl=300)
def hae_rautatie_hairiot():
  url = "https://rata.digitraffic.fi/api/v1/messages"
  try:
    vastaus = requests.get(url)
    if vastaus.status_code == 200:
      return vastaus.json()
  except:
    pass
  return []


@st.cache_data(ttl=300)
def hae_aseman_tiedotteet(asema_koodi):
  # Fintrafficin yleiset viestit, joista voidaan poimia asemaa koskevat
  url = "https://rata.digitraffic.fi/api/v1/messages"
  try:
    vastaus = requests.get(url)
    if vastaus.status_code == 200:
      viestit = vastaus.json()
      # Suodatetaan viestit, jotka koskevat kyseistä asemaa tai ovat yleisiä
      suodatetut = []
      for v in viestit:
        # Tarkistetaan, mainitaanko asema koodi tai otsikko/sisältö
        suodatetut.append(v)
      return suodatetut[:5]
  except:
    pass
  return []


asema_dict = hae_asemat()
asema_nimet = list(asema_dict.keys())

koodi_to_nimi = {}
for nimi, tiedot in asema_dict.items():
  koodi_to_nimi[tiedot["koodi"]] = nimi.split(" (")[0]


# --- TEKOÄLYn LYHYT TERVEHDYS ---
@st.cache_data(ttl=3600)
def hae_tekoaly_tervehdys():
  if ai_kaytossa:
    try:
      prompt = (
          "Kirjoita korkeintaan 1 lauseen mittainen, hauska ja sarkastinen"
          " tervehdys junamatkustajalle. Vain suora lause."
      )
      vastaus = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=[{"role": "user", "content": prompt}],
          max_tokens=40,
      )
      return vastaus.choices[0].message.content
    except:
      pass
  return (
      "Tervetuloa Raiderauhaan! Toivottavasti juna kulkee tänään edes"
      " sinnepäin. 🚆😂"
  )


tekoaly_tervehdys = hae_tekoaly_tervehdys()

# --- SIVUPALKKI & ASETUKSET ---
st.sidebar.markdown(f'🤖 *"{tekoaly_tervehdys}"*')
st.sidebar.divider()

st.sidebar.markdown("### 🚨 Viralliset rataliikennehäiriöt")
hairiot = hae_rautatie_hairiot()
if hairiot:
  for h in hairiot[:3]:
    otsikko = h.get("title", "Häiriö")
    kuvaus = h.get("ingress", "")
    st.sidebar.warning(f"**{otsikko}**\n\n{kuvaus}")
else:
  st.sidebar.success("Ei tiedossa olevia rataliikennehäiriötä.")

st.sidebar.divider()
st.sidebar.header("🎛️ Matkan tiedot & Asetukset")

if st.sidebar.button("🃏 Arvo uusi matkavitsi", use_container_width=True):
  if ai_kaytossa:
    try:
      prompt = (
          "Keksi lyhyt ja hauska vitsi junamatkustamisesta. Vain vitsi suoraan."
      )
      vastaus = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=[{"role": "user", "content": prompt}],
          max_tokens=50,
      )
      st.session_state.paivan_vitsi = vastaus.choices[0].message.content
    except:
      pass

st.sidebar.info(f'💡 **Matkavitsi:**\n\n"{st.session_state.paivan_vitsi}"')
st.sidebar.divider()

if st.session_state.suosikit:
  st.sidebar.markdown("### ⭐ Suosikkireitit")
  for idx, (s_lahto, s_paikka) in enumerate(st.session_state.suosikit):
    if st.sidebar.button(f"{s_lahto} ➔ {s_paikka}", key=f"suosikki_{idx}"):
      st.session_state.valittu_lahto = s_lahto
      st.session_state.valittu_paikka = s_paikka

oletus_lahto_idx = (
    asema_nimet.index(st.session_state.get("valittu_lahto", "Helsinki (HKI)"))
    if st.session_state.get("valittu_lahto", "Helsinki (HKI)") in asema_nimet
    else 0
)
oletus_paikka_idx = (
    asema_nimet.index(asema_nimet.index(st.session_state.get("valittu_paikka", "Joensuu (JNS)")) if st.session_state.get("valittu_paikka", "Joensuu (JNS)") in asema_nimet else 1)
    if st.session_state.get("valittu_paikka", "Joensuu (JNS)") in asema_nimet
    else 1
)

valittu_lahto_nimi = st.sidebar.selectbox(
    "Lähtöasema", asema_nimet, index=oletus_lahto_idx
)
valittu_paikka_nimi = st.sidebar.selectbox(
    "Määränpää", asema_nimet, index=oletus_paikka_idx
)

if st.sidebar.button("❤️ Tallenna suosikkireitiksi"):
  uusi_suosikki = (valittu_lahto_nimi, valittu_paikka_nimi)
  if uusi_suosikki not in st.session_state.suosikit:
    st.session_state.suosikit.append(uusi_suosikki)
    st.sidebar.success("Reitti tallennettu suosikkeihin!")

valittu_pvm = st.sidebar.date_input("Matkustuspäivä", value=date.today())

lahto = asema_dict[valittu_lahto_nimi]["koodi"]
paikka = asema_dict[valittu_paikka_nimi]["koodi"]

hakunappi = st.sidebar.button("🔍 Etsi junat ja Rauhavahti", type="primary")

if hakunappi:
  st.session_state.haku_tehty = True

st.sidebar.divider()
st.sidebar.caption(
    "Tiedot: [Fintraffic / Digitraffic"
    " (CC 4.0 BY)](https://www.digitraffic.fi) & Open-Meteo."
)

# --- PÄÄSIVU ---
st.title("🚆 Raiderauha")
st.markdown(
    "##### *Reaaliaikainen junatutka, tekoälyn rauha-alueet, sää ja matkustajien"
    " live-raportit*"
)
st.divider()

# --- MATKABINGO-OSIO AINA NÄKYVISSÄ ---
st.markdown("### 🎫 Junamatkustajan Matkabingo")
st.markdown(
    "*Bongaa klassisia junailmiöitä matkan varrelta ja rukskaa ruutuja!*"
)

b_col1, b_col2, b_col3 = st.columns(3)
bingo_sarakkeet = [b_col1, b_col2, b_col3]

for i, (tehtävä, tila) in enumerate(st.session_state.bingo_ruudut.items()):
  col = bingo_sarakkeet[i % 3]
  with col:
    uusi_tila = st.checkbox(
        tehtävä, value=tila, key=f"bingo_{i}", help="Rukskaa kun tapahtuu!"
    )
    st.session_state.bingo_ruudut[tehtävä] = uusi_tila

if all(st.session_state.bingo_ruudut.values()):
  st.balloons()
  st.success("🎉 **BINGO!** Olet kokenut täydellisen suomalaisen junamatkan!")

st.divider()

if st.session_state.haku_tehty:
  st.markdown(
      f"### 🗺️ Reitti: **{valittu_lahto_nimi}** ➔"
      f" **{valittu_paikka_nimi}** ({valittu_pvm.strftime('%d.%m.%Y')})"
  )

  # --- ASEMAN LIVE-KUULUTUKSET JA TIEDOTTEET (Laituritaulu-simulaatio) ---
  st.markdown(
      f"📢 **Lähtöaseman ({valittu_lahto_nimi.split(' ')[0]}) ajankohtaiset"
      " laituritiedotteet:**"
  )
  asema_tiedotteet = hae_aseman_tiedotteet(lahto)
  if asema_tiedotteet:
    for tiedote in asema_tiedotteet[:2]:
      t_otsikko = tiedote.get("title", "Tiedote")
      t_ingressi = tiedote.get("ingress", "")
      st.info(f"🔊 **{t_otsikko}**\n\n{t_ingressi}")
  else:
    st.caption("Ei erillisiä asemakohtaisia poikkeustiedotteita.")

  st.divider()

  # --- SÄÄ JA HIILIDIOKSIDISÄÄSTÖLASKURI ---
  l_lat = asema_dict[valittu_lahto_nimi].get("lat")
  l_lon = asema_dict[valittu_lahto_nimi].get("lon")
  p_lat = asema_dict[valittu_paikka_nimi].get("lat")
  p_lon = asema_dict[valittu_paikka_nimi].get("lon")

  if p_lat and p_lon:
    try:
      sää_url = f"https://api.open-meteo.com/v1/forecast?latitude={p_lat}&longitude={p_lon}&current=temperature_2m,weather_code"
      s_vast = requests.get(sää_url).json()
      lampo = s_vast["current"]["temperature_2m"]
      st.success(
          f"🌤️ **Sää määränpäässä ({valittu_paikka_nimi.split(' ')[0]}):**"
          f" {lampo}°C"
      )
    except:
      pass

  if l_lat and l_lon and p_lat and p_lon:
    R = 6371
    dLat = radians(p_lat - l_lat)
    dLon = radians(p_lon - l_lon)
    a = sin(dLat / 2) ** 2 + cos(radians(l_lat)) * cos(radians(p_lat)) * sin(
        dLon / 2
    ) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    etaisyys_km = R * c
    todellinen_arvio_km = etaisyys_km * 1.2
    auton_paastot_kg = (todellinen_arvio_km * 120) / 1000
    saastetty_co2 = auton_paastot_kg

    st.info(
        f"🌱 **Hiilijalanjälkilaskuri:** Valitsemalla junan auton sijaan"
        f" säästit tällä noin **{todellinen_arvio_km:.0f} km** matkalla"
        f" arviolta **{saastetty_co2:.1f} kg CO₂** -päästöjä!"
    )

  st.info("📡 Haetaan aikatauluja ja Digitrafficin tietoja...")
  st.divider()

  url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{lahto}/{paikka}?departure_date={valittu_pvm.strftime('%Y-%m-%d')}"

  with st.spinner("Etsitään sopivia junavuoroja..."):
    vastaus = requests.get(url)

  if vastaus.status_code == 200:
    junat = vastaus.json()

    if not isinstance(junat, list) or not junat:
      st.warning(
          "⚠️ Valitsemallesi päivälle ja välille ei löytynyt suoria"
          " junavuoroja."
      )
    else:
      aktiiviset_junat = []
      suomi_aika = ZoneInfo("Europe/Helsinki")
      nyt = datetime.now(suomi_aika)

      for juna in junat:
        if not isinstance(juna, dict) or juna.get("cancelled", False):
          continue

        train_num = juna.get("trainNumber")
        train_type = juna.get("trainType")
        timeTable = juna.get("timeTableRows", [])

        lahto_aika_str = ""
        saapumis_aika_str = ""
        lahto_dt = None
        saapumis_dt = None

        for rivi in timeTable:
          if (
              rivi.get("stationShortCode") == lahto
              and rivi.get("type") == "DEPARTURE"
          ):
            aika_str = rivi.get("scheduledTime")
            if aika_str:
              dt_obj = datetime.fromisoformat(
                  aika_str.replace("Z", "+00:00")
              ).astimezone(suomi_aika)
              lahto_aika_str = dt_obj.strftime("%H:%M")
              lahto_dt = dt_obj
          if (
              rivi.get("stationShortCode") == paikka
              and rivi.get("type") == "ARRIVAL"
          ):
            aika_str = rivi.get("scheduledTime")
            if aika_str:
              dt_obj = datetime.fromisoformat(
                  aika_str.replace("Z", "+00:00")
              ).astimezone(suomi_aika)
              saapumis_aika_str = dt_obj.strftime("%H:%M")
              saapumis_dt = dt_obj

        if lahto_dt and saapumis_dt:
          is_today = valittu_pvm == date.today()

          if not is_today or (
              lahto_dt >= nyt or (lahto_dt <= nyt <= saapumis_dt)
          ):
            if not is_today:
              tila = f"📅 Päivä {valittu_pvm.strftime('%d.%m.')}"
            elif nyt < lahto_dt:
              tila = "⏳ Lähtee pian"
            else:
              tila = "🟢 Juuri nyt matkalla"

            aktiiviset_junat.append({
                "numero": train_num,
                "tyyppi": train_type,
                "lahto": lahto_aika_str,
                "saapuminen": saapumis_aika_str,
                "aikataulu": timeTable,
                "tila": tila,
            })

      if not aktiiviset_junat:
        st.warning(
            "⚠️ Valitsemallesi päivälle ei löytynyt enää aktiivisia/tulevia"
            " vuoroja tällä välillä."
        )
      else:
        st.success(
            f"Löytyi {len(aktiiviset_junat)} junavuoroja!"
            if len(aktiiviset_junat) > 1
            else "Löytyi 1 junavuoro!"
        )

        for juna in aktiiviset_junat:
          t_num = juna["numero"]
          t_tyyppi = juna["tyyppi"]
          status_teksti = juna["tila"]

          with st.expander(
              f"🚆 {t_tyyppi} {t_num} | Lähtö klo {juna['lahto']} ➔ Perillä"
              f" klo {juna['saapuminen']} ({status_teksti})"
          ):

            st.markdown("#### 📍 Junan koko reitin reaaliaikainen aikataulu")

            timeTable = juna["aikataulu"]
            asemat_map = {}
            maaranpaa_myohassa = 0

            naytetaan = False
            for rivi in timeTable:
              s_koodi = rivi.get("stationShortCode")

              if s_koodi not in koodi_to_nimi:
                continue

              if s_koodi == lahto and rivi.get("type") == "DEPARTURE":
                naytetaan = True

              if naytetaan and s_koodi:
                a_aika = rivi.get("scheduledTime")
                myohassa = rivi.get("differenceInMinutes", 0)
                onko_mennyt = rivi.get("actualTime") is not None

                if s_koodi == paikka and rivi.get("type") == "ARRIVAL":
                  maaranpaa_myohassa = myohassa

                if a_aika:
                  dt_obj = datetime.fromisoformat(
                      a_aika.replace("Z", "+00:00")
                  ).astimezone(suomi_aika)
                  reaaliaika_dt = dt_obj + timedelta(minutes=myohassa)
                  klo = reaaliaika_dt.strftime("%H:%M")
                  onko_kello_mennyt_ohi = reaaliaika_dt <= nyt

                  aktiivinen_tila = onko_mennyt or onko_kello_mennyt_ohi

                  if s_koodi not in asemat_map:
                    asemat_map[s_koodi] = {
                        "asema": s_koodi,
                        "aika": klo,
                        "myohassa": myohassa,
                        "aktiivinen": aktiivinen_tila,
                    }
                  else:
                    if aktiivinen_tila:
                      asemat_map[s_koodi]["aktiivinen"] = True

                if s_koodi == paikka and rivi.get("type") == "ARRIVAL":
                  break

            asemat_matkalla = list(asemat_map.values())

            if asemat_matkalla:
              for asema_info in asemat_matkalla:
                tila_emoji = "✅" if asema_info["aktiivinen"] else "⏳"
                myoha_str = (
                    f" (+{asema_info['myohassa']} min myöhässä)"
                    if asema_info['myohassa'] > 0
                    else ""
                )

                lyhenne = asema_info["asema"]
                kokonainen_nimi = koodi_to_nimi.get(lyhenne, lyhenne)

                st.write(
                    f"{tila_emoji} **{kokonainen_nimi}** – klo"
                    f" {asema_info['aika']}{myoha_str}"
                )

            # --- JATKOYHTEYKSIEN TARKISTUS ---
            viimeinen_asema = asemat_matkalla[-1] if asemat_matkalla else None
            if viimeinen_asema and viimeinen_asema["myohassa"] > 0:
              st.warning(
                  f"⚠️ **Vaihdot vaarassa:** Juna on noin"
                  f" {viimeinen_asema['myohassa']} min myöhässä perille"
                  " saapuessa."
              )
            else:
              st.success(
                  "✅ **Vaihtoyhteydet:** Juna näyttäisi olevan aikataulussa."
              )

            st.divider()

            # --- KORVAUSHAKEMUS-GENERAATTORI ---
            if maaranpaa_myohassa >= 60:
              prosentti = 50 if maaranpaa_myohassa >= 120 else 25
              st.error(
                  f"🚨 **Myöhästymiskorvausoikeus aktivoitunut!** Juna on"
                  f" myöhässä perillä {maaranpaa_myohassa} min. Olet oikeutettu"
                  f" **{prosentti}%** hyvitykseen lipun hinnasta! (VR:n"
                  " vakiokorvaus)"
              )

              hakemus_teksti = (
                  f"Hei VR Asiakaspalvelu,\n\n"
                  f"Haen korvausta matkalipustani EU:n rautatievastuuasetuksen"
                  f" mukaisesti.\n\n"
                  f"Matkatiedot:\n"
                  f"- Junavuoro: {t_tyyppi} {t_num}\n"
                  f"- Reitti: {valittu_lahto_nimi.split(' ')[0]} ➔"
                  f" {valittu_paikka_nimi.split(' ')[0]}\n"
                  f"- Matkustuspäivä: {valittu_pvm.strftime('%d.%m.%Y')}\n"
                  f"- Myöhästyminen perillä: noin {maaranpaa_myohassa} minuuttia"
                  f" ({prosentti}% hyvitys lipun hinnasta)\n\n"
                  f"Pyydän palauttamaan korvauksen ilmoitetulle tililleni."
                  f" Kiitos!\n\n"
                  f"Ystävällisin terveisin,\n[Nimesi]"
              )

              st.markdown(
                  "📋 **Valmis korvaushakemusteksti VR:lle (kopioi alta):**"
              )
              st.code(hakemus_teksti, language="text")
              st.markdown(
                  "[Siirry täyttämään virallinen VR:n korvauslomake"
                  " täältä](https://www.vr.fi/hae-korvausta)"
              )
              st.divider()

            # --- TEKOÄLYN RAUHAVAHTI ---
            if ai_kaytossa:
              with st.spinner("🤖 Rauhavahti analysoi vaunutilannetta..."):
                try:
                  prompt = (
                      "Olet sarkastinen matkaoppaan assistentti. Anna hyvin"
                      f" lyhyt, 1-2 virkkeen pituinen vaunusuositus ja varoitus"
                      f" junalle {t_tyyppi} {t_num} reitillä"
                      f" {valittu_lahto_nimi}-{valittu_paikka_nimi}. Pidä"
                      " vastaus napakkana."
                  )
                  completion = client.chat.completions.create(
                      model="gpt-4o-mini",
                      messages=[{"role": "user", "content": prompt}],
                      max_tokens=80,
                  )
                  st.info(
                      "🤖 **Rauhavahti:**\n\n"
                      f"{completion.choices[0].message.content}"
                  )
                except:
                  pass

            # --- TIETOKANTAAN TALLENTUVAT MATKUSTAJIEN RAUHARAPORTIT ---
            st.markdown("#### 🗣️ Matkustajien live-rauharaportit")

            with st.form(key=f"form_{t_num}"):
              uusi_raportti = st.text_input(
                  f"Ilmoita tunnelma tälle junalle ({t_num}):",
                  placeholder="Esim. Vaunu 3 superhiljainen",
              )
              submit_nappi = st.form_submit_button(
                  "Lähetä raportti tietokantaan"
              )

              if submit_nappi:
                if uusi_raportti:
                  tallenna_raportti(t_num, uusi_raportti)
                  st.success("Kiitos! Raportti tallennettiin.")
                else:
                  st.warning("Kirjoita ensin jotain raporttiin.")

            tallennetut_raportit = hae_raportit(t_num)
            if tallennetut_raportit:
              for r_teksti, r_aika in tallennetut_raportit:
                st.write(
                    f"💬 *\"{r_teksti}\"* — <small"
                    f" style='color: gray;'>({r_aika})</small>",
                    unsafe_allow_html=True,
                )
            else:
              st.caption("Ei vielä raportteja tässä tietokannassa.")

            st.divider()

            # --- MATKUSTAJIEN LIVE-CHAT ---
            st.markdown("#### 💬 Matkustajien live-chat")
            st.markdown(
                f"*Keskustele muiden samassa junassa ({t_num}) matkustavien"
                " kanssa!*"
            )

            with st.form(key=f"chat_form_{t_num}", clear_on_submit=True):
              c_col1, c_col2 = st.columns([1, 2])
              with c_col1:
                nimimerkki = st.text_input(
                    "Nimimerkki", value="Matkustaja", max_chars=20
                )
              with c_col2:
                uusi_viesti = st.text_input(
                    "Viesti", placeholder="Kirjoita jotain junan tunnelmasta..."
                )

              laheta_chat_nappi = st.form_submit_button("Lähetä viesti chattiin")

              if laheta_chat_nappi:
                if uusi_viesti.strip():
                  tallenna_chat_viesti(t_num, nimimerkki, uusi_viesti)
                  st.rerun()
                else:
                  st.warning("Viesti ei voi olla tyhjä.")

            historia = hae_chat_viestit(t_num)
            if historia:
              chat_container = st.container(height=200)
              with chat_container:
                for nimiv, viestiv, aikav in historia:
                  st.markdown(
                      f"**{nimiv}** <small style='color: gray;'>({aikav})</small>:"
                      f" {viestiv}",
                      unsafe_allow_html=True,
                  )
            else:
              st.caption(
                  "Ei viestejä vielä. Ole ensimmäinen, joka aloittaa keskustelun"
                  " tällä junalla!"
              )

            st.divider()

            # --- VAUNUKARTTA ---
            st.markdown("#### 🗺️ Vaunukartta ja sisäiset rauha-alueet")

            vaunut = []
            komp_url = (
                f"https://rata.digitraffic.fi/api/v1/compositions/{t_num}"
            )
            try:
              komp_vastaus = requests.get(komp_url)
              if komp_vastaus.status_code == 200:
                komp_data = komp_vastaus.json()
                sections = komp_data.get("journeySections", [])
                if sections:
                  vaunut = sections[0].get("wagons", [])
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
                    {"wagonType": "InterCity", "salesNumber": "7"},
                ]
              else:
                vaunut = [
                    {"wagonType": "Ravintola", "salesNumber": "1"},
                    {"wagonType": "Vaunu", "salesNumber": "2"},
                    {"wagonType": "Vaunu", "salesNumber": "3"},
                ]

            v_cols = st.columns(len(vaunut) if len(vaunut) <= 8 else 8)
            for idx, v in enumerate(vaunut[:8]):
              v_nimi = v.get("wagonType", "Vaunu")
              v_nro = v.get("salesNumber", str(idx + 1))
              with v_cols[idx]:
                st.metric(label=f"Vaunu {v_nro}", value=v_nimi)

            st.markdown("---")
            st.markdown("#### 💺 Vaunun sisäinen rauha-kartta")

            v_col1, v_col2, v_col3, v_col4, v_col5 = st.columns(5)
            with v_col1:
              st.error("🔴 **Vessa / Ovi**\n\n*Vilkas*")
            with v_col2:
              st.warning("🟠 **Päätypaikat**\n\n*Melko vilkas*")
            with v_col3:
              st.success("🟢 **Keskiosa**\n\n*Hiljainen*\n⭐ **Paras**")
            with v_col4:
              st.warning("🟠 **Päätypaikat**\n\n*Melko vilkas*")
            with v_col5:
              st.error("🔴 **Vessa / Ovi**\n\n*Vilkas*")

  else:
    st.error("Virhe haettaessa junatietoja.")
else:
  st.info(
      "👈 Valitse asemat ja matkustuspäivä sivupalkista, ja klikkaa **Etsi"
      " junat ja Rauhavahti**."
  )

# --- SEO-PIILOTETTU TEKSTI ---
st.markdown("---")
with st.expander("ℹ️ Tietoa Raiderauha-palvelusta (Junatutka & Aikataulut)"):
  st.markdown("""
    **Raiderauha** on kattava ja reaaliaikainen **junatutka**, jonka avulla matkustajat voivat tarkistaa suomalaisten junien aikataulut, mahdolliset **myöhästymiset**, **rataliikennehäiriöt** sekä sääolosuhteet määränpäässä. Palvelu hyödyntää virallista Fintrafficin avointa dataa ja tarjoaa tekoälyn avustuksella vaunusuosituksia sekä hauskan matkabingon matkan ratoksi. Etsitpä sitten tietoa IC-junien kulusta, vaihtoyhteyksistä tai haluat jättää live-raportin, chat-viestin, hyödyntää myöhästymiskorvausgeneraattoria tai tarkistaa aseman live-tiedotteita, Raiderauha auttaa pitämään matkasi rauhallisena ja hallinnassa.
    """)
