from datetime import date, datetime, timedelta
from math import atan2, cos, radians, sin, sqrt
from zoneinfo import ZoneInfo
import csv
import os
import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# --- KIELIKÄÄNNÖKSET (TRANSLATIONS) ---
TEKSTIT = {
    "Suomi": {
        "page_title": "Raidetutka – Reaaliaikainen Junatutka, Aikataulut & Rataliikennehäiriöt",
        "sidebar_hallinta": "🚆 Raidetutka Hallinta",
        "live_paivitys": "🔄 Automaattinen live-päivitys (15s)",
        "hairiot_otsikko": "🚨 Rataliikennehäiriöt",
        "ei_hairioita": "Ei tiedossa olevia rataliikennehäiriöitä.",
        "ratatyot_otsikko": "🚧 Ratatyöt & Nopeusrajoitukset",
        "ei_ratatoita": "Ei aktiivisia ratatöitä tai hidastuksia.",
        "reitti_seuranta": "🎛️ Reitti & Seuranta",
        "seuratut_junat": "⭐ Seuratut junat",
        "lisaa_juna_placeholder": "Esim. 67",
        "lisaa_juna_btn": "Lisää juna",
        "tyhjenna_btn": "Tyhjennä",
        "juna_lisatty": "Juna {nro} lisätty.",
        "ei_live_paikannusta": "⏳ Ei live-paikannusta",
        "myohassa_txt": "⚠️ Myöhässä: +{min} min",
        "ajallaan_txt": "✅ Ajallaan",
        "avaa_seuranta": "📡 Avaa seuranta ({nro})",
        "suosikkireitit": "⭐ Suosikkireitit",
        "tallenna_suosikki": "❤️ Tallenna suosikkireitiksi",
        "reitti_tallennettu": "Reitti tallennettu suosikkeihin.",
        "lahtoasema": "Lähtöasema",
        "maaranpaa": "Määränpää",
        "matkustuspäivä": "Matkustuspäivä",
        "hae_reitti": "🔍 Hae reitti",
        "palaute_otsikko": "💬 Palaute & Kehitysehdotukset",
        "palaute_nimi": "Nimi (valinnainen)",
        "palaute_aihe": "Aihealue",
        "palaute_vaihtoehdot": ["Kehitysehdotus", "Virheilmoitus / Bugi", "Yleinen palaute"],
        "palaute_placeholder": "Kirjoita palautteesi tähän...",
        "laheta_palaute": "Lähetä palaute",
        "palaute_kiitos": "Kiitos palautestasi.",
        "palaute_virhe": "Tallennusvirhe: {e}",
        "palaute_tyhja": "Kirjoita palauteteksti ennen lähettämistä.",
        "tietosuoja_otsikko": "🔒 Tietosuoja & Evästeet",
        "tietosuoja_linkki": "Lue tietosuojaseloste",
        "tietosuoja_teksti": """
        **Tietosuojaseloste ja evästeet:**
        - **Kerättävät tiedot:** Palautelomakkeen kautta antamasi tiedot (nimi ja palauteteksti) tallennetaan palvelimelle palvelun kehittämistä varten. Emme luovuta tietoja kolmansille osapuolille.
        - **Evästeet:** Sivusto saattaa käyttää analytiikkaevästeitä käyttökokemuksen parantamiseen. Voit hallita evästeasetuksia selaimestasi.
        """,
        "evaste_banneri": "Käytämme evästeitä ja keräämme palautelomakkeen kautta annettuja tietoja palvelun tuottamiseen ja kehittämiseen.",
        "evaste_hyvaksy": "Hyväksy evästeet",
        "footer": "Tiedot: [Fintraffic / Digitraffic (CC 4.0 BY)](https://www.digitraffic.fi) & Open-Meteo.",
        "pääotsikko": "🚆 Raidetutka",
        "pääalaotsikko": "##### *Reaaliaikainen junatutka, aikataulut ja vaunukoostumukset*",
        "palaa_reittihakuun": "⬅️ Palaa reittihakuun",
        "seuranta_otsikko": "📡 Junan **{nro}** Seuranta & Koostumus",
        "vaunut_otsikko": "🚃 Vaunukoostumus & Palvelut",
        "ei_vaunutietoja": "Ei tarkempia vaunutietoja saatavilla.",
        "ei_vaunutietoja_info": "ℹ️ Vaunukoostumustietoja ei ole saatavilla tälle junalle.",
        "gps_aktiivinen": "📍 **Sijainti:** Nopeus **{nopeus} km/h**.",
        "sulje_kartta": "Sulje kartta",
        "nayta_kartta": "🗺️ Näytä kartta",
        "gps_ei_aktiivinen": "ℹ️ GPS-paikannus ei ole aktiivinen.",
        "ajoaikataulu": "📍 Ajoaikataulu",
        "asema": "Asema",
        "tapahtuma": "Tapahtuma",
        "aika": "Aika",
        "raide": "Raide",
        "myoh_min": "Myöh (min)",
        "juna_ei_loydy": "Junan {nro} tietoja ei löytynyt.",
        "laiturinaytto_otsikko": "📺 Laiturinäyttö – {asema}",
        "laiturinaytto_sub": "Aseman reaaliaikainen aikataulunäyttö.",
        "tab_lahtevat": "🚂 Lähtevät",
        "tab_saapuvat": "📥 Saapuvat",
        "ei_lahtevia": "Ei lähteviä junia.",
        "ei_saapuvia": "Ei saapuvia junia.",
        "ladataan": "Ladataan asematietoja...",
        "peruttu": "Peruttu ❌",
        "reittihaku_otsikko": "🗺️ Reittihaku: **{lahto}** ➔ **{paikka}** ({pvm})",
        "reitti_poikkeus_varoitus": "⚠️ **Huomio!** Valitsemallesi reitille tai sen asemille on kirjattu poikkeuksia tai ratatöitä:",
        "reitti_ok": "✅ Ei tiedossa olevia poikkeuksia tai ratatöitä tällä reitillä.",
        "rataetaisyys": "📏 **Rataetäisyys-arvio:** ~{km} km (Linnuntie {linnu} km)",
        "saa_maaranpaassa": "🌤️ **Sää määränpäässä ({asema}):** {lampo}°C",
        "valitse_junavuoro": "Valitse alta haluamasi junavuoro:",
        "haetaan_junia": "Haetaan junavuoroja...",
        "ei_junia_pvm": "Valitsemallesi päivälle ei löytynyt junavuoroja rajapinnasta.",
        "reitin_junat_kartalla": "🗺️ Reitin junat kartalla",
        "aikataulussa": "Aikataulussa ✅",
        "historia_info": "📊 Viime päivinä keskimäärin +{min} min myöhässä",
        "historia_ei_tietoa": "📊 Historiatietoa ei saatavilla",
        "matka_kesto": "⏱️ Matka-aika: ~{kesto} min | Keskinopeusarvio: ~{nopeus} km/h",
        "osta_liput": "🛒 Osta liput VR:ltä",
        "seuraa_live": "📡 Seuraa live / tiedot ({nro})",
    },
    "English": {
        "page_title": "Raidetutka – Real-time Train Tracker, Schedules & Traffic Disruptions",
        "sidebar_hallinta": "🚆 Raidetutka Control",
        "live_paivitys": "🔄 Automatic live refresh (15s)",
        "hairiot_otsikko": "🚨 Railway Disruptions",
        "ei_hairioita": "No known railway traffic disruptions.",
        "ratatyot_otsikko": "🚧 Road/Track Works & Speed Limits",
        "ei_ratatoita": "No active track works or speed restrictions.",
        "reitti_seuranta": "🎛️ Route & Tracking",
        "seuratut_junat": "⭐ Tracked Trains",
        "lisaa_juna_placeholder": "E.g. 67",
        "lisaa_juna_btn": "Add train",
        "tyhjenna_btn": "Clear",
        "juna_lisatty": "Train {nro} added.",
        "ei_live_paikannusta": "⏳ No live location",
        "myohassa_txt": "⚠️ Delayed: +{min} min",
        "ajallaan_txt": "✅ On time",
        "avaa_seuranta": "📡 Open tracking ({nro})",
        "suosikkireitit": "⭐ Favorite Routes",
        "tallenna_suosikki": "❤️ Save as favorite route",
        "reitti_tallennettu": "Route saved to favorites.",
        "lahtoasema": "Departure station",
        "maaranpaa": "Destination station",
        "matkustuspäivä": "Travel date",
        "hae_reitti": "🔍 Search route",
        "palaute_otsikko": "💬 Feedback & Suggestions",
        "palaute_nimi": "Name (optional)",
        "palaute_aihe": "Category",
        "palaute_vaihtoehdot": ["Feature Suggestion", "Bug Report", "General Feedback"],
        "palaute_placeholder": "Write your feedback here...",
        "laheta_palaute": "Send feedback",
        "palaute_kiitos": "Thank you for your feedback.",
        "palaute_virhe": "Save error: {e}",
        "palaute_tyhja": "Please write feedback before sending.",
        "tietosuoja_otsikko": "🔒 Privacy & Cookies",
        "tietosuoja_linkki": "Read privacy policy",
        "tietosuoja_teksti": """
        **Privacy Policy and Cookies:**
        - **Collected Data:** Information submitted via the feedback form (name and feedback text) is stored to improve the service. We do not share data with third parties.
        - **Cookies:** The site may use analytics cookies to improve user experience. You can manage cookie settings in your browser.
        """,
        "evaste_banneri": "We use cookies and collect data provided via the feedback form to operate and improve the service.",
        "evaste_hyvaksy": "Accept cookies",
        "footer": "Data: [Fintraffic / Digitraffic (CC 4.0 BY)](https://www.digitraffic.fi) & Open-Meteo.",
        "pääotsikko": "🚆 Raidetutka",
        "pääalaotsikko": "##### *Real-time train tracker, schedules and train compositions*",
        "palaa_reittihakuun": "⬅️ Back to route search",
        "seuranta_otsikko": "📡 Train **{nro}** Tracking & Composition",
        "vaunut_otsikko": "🚃 Wagon Composition & Services",
        "ei_vaunutietoja": "No detailed wagon information available.",
        "ei_vaunutietoja_info": "ℹ️ Wagon composition data is not available for this train.",
        "gps_aktiivinen": "📍 **Location:** Speed **{nopeus} km/h**.",
        "sulje_kartta": "Close map",
        "nayta_kartta": "🗺️ Show map",
        "gps_ei_aktiivinen": "ℹ️ GPS location is not active.",
        "ajoaikataulu": "📍 Timetable",
        "asema": "Station",
        "tapahtuma": "Event",
        "aika": "Time",
        "raide": "Track",
        "myoh_min": "Delay (min)",
        "juna_ei_loydy": "Information for train {nro} not found.",
        "laiturinaytto_otsikko": "📺 Departure Board – {asema}",
        "laiturinaytto_sub": "Real-time station schedule board.",
        "tab_lahtevat": "🚂 Departures",
        "tab_saapuvat": "📥 Arrivals",
        "ei_lahtevia": "No departing trains.",
        "ei_saapuvia": "No arriving trains.",
        "ladataan": "Loading station data...",
        "peruttu": "Cancelled ❌",
        "reittihaku_otsikko": "🗺️ Route Search: **{lahto}** ➔ **{paikka}** ({pvm})",
        "reitti_poikkeus_varoitus": "⚠️ **Attention!** Exceptions or track works have been reported for your selected route or stations:",
        "reitti_ok": "✅ No known exceptions or track works on this route.",
        "rataetaisyys": "📏 **Route distance estimate:** ~{km} km (As the crow flies {linnu} km)",
        "saa_maaranpaassa": "🌤️ **Weather at destination ({asema}):** {lampo}°C",
        "valitse_junavuoro": "Select your desired train below:",
        "haetaan_junia": "Fetching train schedules...",
        "ei_junia_pvm": "No train schedules found for the selected date.",
        "reitin_junat_kartalla": "🗺️ Trains on the route map",
        "aikataulussa": "On time ✅",
        "historia_info": "📊 Past days average delay +{min} min",
        "historia_ei_tietoa": "📊 No historical data available",
        "matka_kesto": "⏱️ Travel time: ~{kesto} min | Avg speed estimate: ~{keskinopeus} km/h",
        "osta_liput": "🛒 Buy tickets from VR",
        "seuraa_live": "📡 Live tracking / info ({nro})",
    },
}

# --- SIVUN PERUSASETUKSET & KIELI ---
st.set_page_config(
    page_title="Raidetutka",
    page_icon="🚆",
    layout="wide",
)

st.sidebar.markdown("### 🌐 Language / Kieli")
valittu_kieli = st.sidebar.selectbox("Valitse kieli / Select language", ["Suomi", "English"])
t = TEKSTIT[valittu_kieli]

# --- EVÄSTEEN HYVÄKSYNTÄ (SESSION STATE) ---
if "evasteet_hyvaksytty" not in st.session_state:
    st.session_state.evasteet_hyvaksytty = False

if not st.session_state.evasteet_hyvaksytty:
    st.info(f"🍪 {t['evaste_banneri']}")
    if st.button(t["evaste_hyvaksy"], use_container_width=True):
        st.session_state.evasteet_hyvaksytty = True
        st.rerun()

# --- MODERNI SCANDINAVIAN UI -TYYLITTELY (GRAFIIKAT & KORTIT) ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f4f6f8;
        color: #1e293b;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .wagon-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 14px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease;
    }
    .wagon-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .train-box {
        background: #ffffff;
        border-left: 5px solid #0ea5e9;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    h1, h2, h3 {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    .stButton button, .stLinkButton a {
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- SESSIOMUUTTUJIEN ALUSTUS ---
if "suosikit" not in st.session_state:
    st.session_state.suosikit = [("Helsinki (HKI)", "Joensuu (JNS)")]

if "seuratut_junat" not in st.session_state:
    st.session_state.seuratut_junat = ["23"]

if "valittu_live_juna" not in st.session_state:
    st.session_state.valittu_live_juna = None

if "piilotetut_kartat" not in st.session_state:
    st.session_state.piilotetut_kartat = set()

if "haku_tehty" not in st.session_state:
    st.session_state.haku_tehty = False


@st.cache_data
def hae_asemat():
    url = "https://rata.digitraffic.fi/api/v1/metadata/stations"
    try:
        vastaus = requests.get(url, timeout=5)
        if vastaus.status_code == 200:
            asemat = vastaus.json()
            matkustajasektori = [a for a in asemat if a.get("passengerTraffic") == True]
            asema_lista = {}
            for a in matkustajasektori:
                nimi = f"{a['stationName']} ({a['stationShortCode']})"
                asema_lista[nimi] = {
                    "koodi": a["stationShortCode"],
                    "lat": a.get("latitude"),
                    "lon": a.get("longitude"),
                }
            return asema_lista
    except Exception:
        pass
    return {
        "Helsinki (HKI)": {"koodi": "HKI", "lat": 60.1719, "lon": 24.9414},
        "Joensuu (JNS)": {"koodi": "JNS", "lat": 62.5998, "lon": 29.7634},
        "Tampere (TPE)": {"koodi": "TPE", "lat": 61.5033, "lon": 23.7733},
    }


@st.cache_data(ttl=300)
def hae_rautatie_hairiot():
    url = "https://rata.digitraffic.fi/api/v1/messages"
    try:
        vastaus = requests.get(url, timeout=5)
        if vastaus.status_code == 200:
            return vastaus.json()
    except Exception:
        pass
    return []


@st.cache_data(ttl=300)
def hae_ratatyot_ja_nopeusrajoitukset():
    url = "https://rata.digitraffic.fi/api/v1/messages?messageType=WORKS"
    try:
        vastaus = requests.get(url, timeout=3)
        if vastaus.status_code == 200:
            return vastaus.json()
    except Exception:
        pass
    return []


@st.cache_data(ttl=60)
def hae_aseman_junat(asema_koodi):
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{asema_koodi}"
    try:
        vastaus = requests.get(url, timeout=5)
        if vastaus.status_code == 200:
            return vastaus.json()
    except Exception:
        pass
    return []


@st.cache_data(ttl=300)
def hae_vaunukoostumus(juna_numero, pvm):
    url = f"https://rata.digitraffic.fi/api/v1/compositions/{pvm}/{juna_numero}"
    try:
        vastaus = requests.get(url, timeout=3)
        if vastaus.status_code == 200:
            return vastaus.json()
    except Exception:
        pass
    return None


@st.cache_data(ttl=15)
def hae_junan_sijainti(juna_numero):
    url = f"https://rata.digitraffic.fi/api/v1/train-locations/latest/{juna_numero}"
    try:
        vastaus = requests.get(url, timeout=2)
        if vastaus.status_code == 200:
            data = vastaus.json()
            if data and isinstance(data, list) and len(data) > 0:
                sijainti_info = data[0]
                koordinaatit = sijainti_info.get("location", {}).get("coordinates", [])
                if len(koordinaatit) == 2:
                    lon, lat = koordinaatit
                    nopeus = sijainti_info.get("speed", 0)
                    return {"lat": lat, "lon": lon, "nopeus": nopeus}
    except Exception:
        pass
    return None


@st.cache_data(ttl=30)
def hae_junan_perustiedot(juna_numero):
    tanaan_pvm = date.today().strftime("%Y-%m-%d")
    url = f"https://rata.digitraffic.fi/api/v1/trains/{tanaan_pvm}/{juna_numero}"
    try:
        vastaus = requests.get(url, timeout=3)
        if vastaus.status_code == 200:
            data = vastaus.json()
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict):
                return data
    except Exception:
        pass
    return None


@st.cache_data(ttl=3600)
def hae_junan_historiatilastot(juna_numero):
    keski_myohassa = 0
    otanta = 0
    for i in range(1, 4):
        mennyt_pvm = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        url = f"https://rata.digitraffic.fi/api/v1/trains/{mennyt_pvm}/{juna_numero}"
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    t = data[0]
                    for rivi in reversed(t.get("timeTableRows", [])):
                        if rivi.get("differenceInMinutes") is not None:
                            keski_myohassa += rivi.get("differenceInMinutes")
                            otanta += 1
                            break
        except Exception:
            pass
    if otanta > 0:
        return round(keski_myohassa / otanta, 1)
    return None


def LaskeEtaisyysJaAika(lat1, lon1, lat2, lon2):
    R = 6371.0
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    a = sin(dLat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    linnun_matka = R * c
    rata_matka = linnun_matka * 1.25
    return round(rata_matka, 1)


asema_dict = hae_asemat()
asema_nimet = list(asema_dict.keys())

koodi_to_nimi = {}
for nimi, tiedot in asema_dict.items():
    koodi_to_nimi[tiedot["koodi"]] = nimi.split(" (")[0]

# --- SIVUPALKKI & ASETUKSET ---
st.sidebar.divider()
st.sidebar.markdown(f"### {t['sidebar_hallinta']}")
st.sidebar.divider()

live_paivitys_paalla = st.sidebar.checkbox(
    t["live_paivitys"], value=True
)
if live_paivitys_paalla:
    st_autorefresh(interval=15000, key="raidetutka_live_refresh")

st.sidebar.divider()

st.sidebar.markdown(f"### {t['hairiot_otsikko']}")
hairiot = hae_rautatie_hairiot()
if hairiot:
    for h in hairiot[:3]:
        otsikko = h.get("title", "Disruption")
        kuvaus = h.get("ingress", "")
        st.sidebar.warning(f"**{otsikko}**\n\n{kuvaus}")
else:
    st.sidebar.success(t["ei_hairioita"])

st.sidebar.divider()
st.sidebar.markdown(f"### {t['ratatyot_otsikko']}")
ratatyot = hae_ratatyot_ja_nopeusrajoitukset()
if ratatyot:
    for tyy in ratatyot[:2]:
        t_ots = tyy.get("title", "Track Work")
        t_ing = tyy.get("ingress", "Maintenance work on tracks.")
        st.sidebar.info(f"🛠️ **{t_ots}**\n\n{t_ing}")
else:
    st.sidebar.caption(t["ei_ratatoita"])

st.sidebar.divider()
st.sidebar.header(t["reitti_seuranta"])

st.sidebar.markdown(f"### {t['seuratut_junat']}")
seurattava_input = st.sidebar.text_input(
    t["seuratut_junat"], placeholder=t["lisaa_juna_placeholder"], label_visibility="collapsed"
)
col_lisaa, col_poista = st.sidebar.columns(2)
with col_lisaa:
    if st.button(t["lisaa_juna_btn"], use_container_width=True):
        if seurattava_input and seurattava_input not in st.session_state.seuratut_junat:
            st.session_state.seuratut_junat.append(seurattava_input)
            st.success(t["juna_lisatty"].format(nro=seurattava_input))
with col_poista:
    if st.button(t["tyhjenna_btn"], use_container_width=True):
        st.session_state.seuratut_junat = []
        st.session_state.valittu_live_juna = None
        st.rerun()

for j_nro in st.session_state.seuratut_junat:
    juna_info = hae_junan_perustiedot(j_nro)
    sijainti = hae_junan_sijainti(j_nro)

    t_tyyppi = "Train" if valittu_kieli == "English" else "Juna"
    lahto_asema = "Departure" if valittu_kieli == "English" else "Lähtö"
    paate_asema = "Destination" if valittu_kieli == "English" else "Määränpää"
    myohassa_min = 0

    if juna_info:
        t_tyyppi = juna_info.get("trainType", t_tyyppi)
        taulukko = juna_info.get("timeTableRows", [])
        if taulukko:
            lahto_koodi = taulukko[0].get("stationShortCode")
            paate_koodi = taulukko[-1].get("stationShortCode")
            lahto_asema = koodi_to_nimi.get(lahto_koodi, lahto_koodi)
            paate_asema = koodi_to_nimi.get(paate_koodi, paate_koodi)

            for rivi in reversed(taulukko):
                if rivi.get("differenceInMinutes") is not None:
                    myohassa_min = rivi.get("differenceInMinutes")
                    break

    st.sidebar.markdown(
        f"**🚆 {t_tyyppi} {j_nro}**\n📍 *{lahto_asema} ➔ {paate_asema}*"
    )

    if sijainti:
        kmh = round(sijainti["nopeus"] * 3.6)
        st.sidebar.markdown(f"🟢 Speed: **{kmh} km/h**" if valittu_kieli == "English" else f"🟢 Nopeus: **{kmh} km/h**")
    else:
        st.sidebar.markdown(t["ei_live_paikannusta"])

    if myohassa_min > 0:
        st.sidebar.error(t["myohassa_txt"].format(min=myohassa_min))
    else:
        st.sidebar.success(t["ajallaan_txt"])

    if st.sidebar.button(
        t["avaa_seuranta"].format(nro=j_nro),
        key=f"live_btn_{j_nro}",
        use_container_width=True,
    ):
        st.session_state.valittu_live_juna = j_nro
        st.rerun()

    st.sidebar.divider()

if st.session_state.suosikit:
    st.sidebar.markdown(f"### {t['suosikkireitit']}")
    for idx, (s_lahto, s_paikka) in enumerate(st.session_state.suosikit):
        if st.sidebar.button(
            f"{s_lahto} ➔ {s_paikka}",
            key=f"suosikki_{idx}",
            use_container_width=True,
        ):
            st.session_state.valittu_lahto = s_lahto
            st.session_state.valittu_paikka = s_paikka

oletus_lahto_idx = (
    asema_nimet.index(st.session_state.get("valittu_lahto", "Helsinki (HKI)"))
    if st.session_state.get("valittu_lahto", "Helsinki (HKI)") in asema_nimet
    else 0
)
oletus_paikka_idx = (
    asema_nimet.index(st.session_state.get("valittu_paikka", "Joensuu (JNS)"))
    if st.session_state.get("valittu_paikka", "Joensuu (JNS)") in asema_nimet
    else 1
)

valittu_lahto_nimi = st.sidebar.selectbox(
    t["lahtoasema"], asema_nimet, index=oletus_lahto_idx
)
valittu_paikka_nimi = st.sidebar.selectbox(
    t["maaranpaa"], asema_nimet, index=oletus_paikka_idx
)

if st.sidebar.button(
    t["tallenna_suosikki"], use_container_width=True
):
    uusi_suosikki = (valittu_lahto_nimi, valittu_paikka_nimi)
    if uusi_suosikki not in st.session_state.suosikit:
        st.session_state.suosikit.append(uusi_suosikki)
        st.sidebar.success(t["reitti_tallennettu"])

valittu_pvm = st.sidebar.date_input(t["matkustuspäivä"], value=date.today())

lahto = asema_dict[valittu_lahto_nimi]["koodi"]
paikka = asema_dict[valittu_paikka_nimi]["koodi"]

hakunappi = st.sidebar.button(
    t["hae_reitti"], type="primary", use_container_width=True
)

if hakunappi:
    st.session_state.haku_tehty = True
    st.session_state.valittu_live_juna = None

# --- PALAUTELOMAKE SIVUPALKISSA ---
st.sidebar.divider()
st.sidebar.markdown(f"### {t['palaute_otsikko']}")

with st.sidebar.form("palaute_lomake"):
    kayttajan_nimi = st.text_input(t["palaute_nimi"])
    palaute_tyyppi = st.selectbox(
        t["palaute_aihe"],
        t["palaute_vaihtoehdot"],
    )
    palaute_teksti = st.text_area(
        "Feedback",
        placeholder=t["palaute_placeholder"],
        label_visibility="collapsed",
    )

    laheta_palaute = st.form_submit_button(
        t["laheta_palaute"], use_container_width=True
    )

    if laheta_palaute:
        if palaute_teksti.strip():
            aikaleima = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rivi = [
                aikaleima,
                kayttajan_nimi if kayttajan_nimi else "Anonymous",
                palaute_tyyppi,
                palaute_teksti,
            ]
            palaute_tiedosto = os.path.join("/tmp", "palautteet.csv")
            try:
                file_exists = os.path.exists(palaute_tiedosto)
                with open(
                    palaute_tiedosto, mode="a", encoding="utf-8", newline=""
                ) as f:
                    kirjoittaja = csv.writer(f)
                    if not file_exists:
                        kirjoittaja.writerow(["Timestamp", "Name", "Type", "Feedback"])
                    kirjoittaja.writerow(rivi)
                st.success(t["palaute_kiitos"])
            except Exception as e:
                st.error(t["palaute_virhe"].format(e=e))
        else:
            st.warning(t["palaute_tyhja"])

# --- TIETOSUOJASELOSTE EXPANDER SIVUPALKISSA ---
st.sidebar.divider()
with st.sidebar.expander(t["tietosuoja_otsikko"]):
    st.markdown(t["tietosuoja_teksti"])

st.sidebar.divider()
st.sidebar.caption(t["footer"])

# --- PÄÄSIVU ---
st.title(t["pääotsikko"])
st.markdown(t["pääalaotsikko"])
st.divider()

suomi_aika = ZoneInfo("Europe/Helsinki")

valittu_nro = st.session_state.valittu_live_juna

if valittu_nro:
    st.markdown(f"### 📡 Train **{valittu_nro}** Tracking & Composition" if valittu_kieli == "English" else f"### 📡 Junan **{valittu_nro}** Seuranta & Koostumus")

    if st.button(t["palaa_reittihakuun"], use_container_width=True):
        st.session_state.valittu_live_juna = None
        st.rerun()

    juna_info = hae_junan_perustiedot(valittu_nro)
    if juna_info:
        t_tyyppi = juna_info.get("trainType", "Train")
        timeTable = juna_info.get("timeTableRows", [])

        lahto_koodi = timeTable[0].get("stationShortCode") if timeTable else ""
        paate_koodi = timeTable[-1].get("stationShortCode") if timeTable else ""
        l_nimi = koodi_to_nimi.get(lahto_koodi, lahto_koodi)
        p_nimi = koodi_to_nimi.get(paate_koodi, paate_koodi)

        st.info(f"Route: **{l_nimi} ➔ {p_nimi}** ({t_tyyppi})" if valittu_kieli == "English" else f"Reitti: **{l_nimi} ➔ {p_nimi}** ({t_tyyppi})")

        # --- VAUNUKOOSTUMUS JA PALVELUT ---
        tanaan_str = date.today().strftime("%Y-%m-%d")
        koostumus_data = hae_vaunukoostumus(valittu_nro, tanaan_str)
        if koostumus_data and "journeySections" in koostumus_data:
            st.markdown(f"#### {t['vaunut_otsikko']}")
            for section in koostumus_data.get("journeySections", []):
                vaunut = section.get("wagons", [])
                if vaunut:
                    try:
                        vaunut = sorted(vaunut, key=lambda x: int(x.get("salesNumber", 99)))
                    except Exception:
                        pass

                    st.markdown("---")
                    cols = st.columns(min(len(vaunut), 2))
                    for idx, v in enumerate(vaunut):
                        col_idx = idx % len(cols)
                        with cols[col_idx]:
                            v_tyyppi = v.get("wagonType", "Wagon")
                            v_nro = v.get("salesNumber")

                            ikoni = "🚃"
                            if v_nro:
                                kuvaus = f"Wagon {v_nro}" if valittu_kieli == "English" else f"Vaunu {v_nro}"
                            else:
                                kuvaus = "Wagon" if valittu_kieli == "English" else "Vaunu"

                            if v_tyyppi == "Ed":
                                kuvaus = f"Wagon {v_nro} (2nd class)" if (valittu_kieli == "English" and v_nro) else ("2nd class wagon" if valittu_kieli == "English" else f"Vaunu {v_nro} (2. luokka)" if v_nro else "2. luokan vaunu")
                            elif v_tyyppi == "Edfs":
                                ikoni = "🧸"
                                kuvaus = f"Wagon {v_nro} (Family area)" if (valittu_kieli == "English" and v_nro) else ("Family area" if valittu_kieli == "English" else f"Vaunu {v_nro} (Perheosasto)" if v_nro else "Perheosasto")
                            elif v_tyyppi == "Edo":
                                ikoni = "☕"
                                kuvaus = f"Wagon {v_nro} (Bistro)" if v_nro else "Bistro"
                            elif v_tyyppi in ["ERd", "Rx"]:
                                ikoni = "🍽️"
                                kuvaus = f"Wagon {v_nro} (Restaurant)" if (valittu_kieli == "English" and v_nro) else ("Restaurant car" if valittu_kieli == "English" else f"Vaunu {v_nro} (Ravintola)" if v_nro else "Ravintolavaunu")
                            elif v_tyyppi == "Eds":
                                ikoni = "🛋️"
                                kuvaus = f"Wagon {v_nro} (InterCity)" if v_nro else "InterCity"
                            elif v_tyyppi in ["CEd", "C"]:
                                ikoni = "🛏️"
                                kuvaus = f"Wagon {v_nro} (Sleeping)" if (valittu_kieli == "English" and v_nro) else ("Sleeping car" if valittu_kieli == "English" else f"Vaunu {v_nro} (Makuu)" if v_nro else "Makuuvaunu")
                            else:
                                kuvaus = f"Wagon {v_nro} ({v_tyyppi})" if v_nro else f"Vaunu ({v_tyyppi})"

                            tiedot = []
                            if v_tyyppi not in ["ERd", "Rx", "Edo"]:
                                if v.get("luggage", False):
                                    tiedot.append("🚲 Bike" if valittu_kieli == "English" else "🚲 Pyörä")
                                if v.get("petsAllowed", False):
                                    tiedot.append("🐾 Pets" if valittu_kieli == "English" else "🐾 Lemmikki")
                                if v.get("accessibility", False):
                                    tiedot.append("♿ Accessible" if valittu_kieli == "English" else "♿ Esteetön")
                            else:
                                tiedot.append("🍽️ Restaurant" if valittu_kieli == "English" else "🍽️ Ravintola")

                            palvelut_html = (
                                "<br>".join(tiedot)
                                if tiedot
                                else ('<span style="color: #94a3b8;">Standard wagon</span>' if valittu_kieli == "English" else '<span style="color: #94a3b8;">Perusvaunu</span>')
                            )

                            st.markdown(
                                f"""
                                        <div class="wagon-card">
                                            <div style="font-weight: 700; font-size: 1rem; margin-bottom: 4px; color: #0f172a;">{ikoni} {kuvaus}</div>
                                            <div style="font-size: 0.85rem; color: #475569; line-height: 1.4;">{palvelut_html}</div>
                                        </div>
                                        """,
                                unsafe_allow_html=True,
                            )
                    st.markdown("---")
                else:
                    st.info(t["ei_vaunutietoja"])
        else:
            st.caption(t["ei_vaunutietoja_info"])

        sijainti_data = hae_junan_sijainti(valittu_nro)
        if sijainti_data:
            j_lat = sijainti_data["lat"]
            j_lon = sijainti_data["lon"]
            j_nopeus = sijainti_data["nopeus"]
            kmh_nopeus = round(j_nopeus * 3.6)

            st.success(t["gps_aktiivinen"].format(nopeus=kmh_nopeus))

            kartta_ava = f"live_{valittu_nro}"
            if kartta_ava not in st.session_state.piilotetut_kartat:
                if st.button(t["sulje_kartta"], key=f"sulje_{kartta_ava}", use_container_width=True):
                    st.session_state.piilotetut_kartat.add(kartta_ava)
                    st.rerun()
                df_kartta = pd.DataFrame({"lat": [j_lat], "lon": [j_lon]})
                st.map(df_kartta, zoom=7, use_container_width=True)
            else:
                if st.button(t["nayta_kartta"], key=f"nayta_{kartta_ava}", use_container_width=True):
                    st.session_state.piilotetut_kartat.remove(kartta_ava)
                    st.rerun()
        else:
            st.warning(t["gps_ei_aktiivinen"])

        st.markdown(f"#### {t['ajoaikataulu']}")
        aikataulu_rivit = []
        for rivi in timeTable:
            s_koodi = rivi.get("stationShortCode")
            if s_koodi not in koodi_to_nimi:
                continue
            r_tyyppi = rivi.get("type")
            if valittu_kieli == "English":
                r_tyyppi_kieli = (
                    "Departure"
                    if r_tyyppi == "DEPARTURE"
                    else ("Arrival" if r_tyyppi == "ARRIVAL" else r_tyyppi)
                )
            else:
                r_tyyppi_kieli = (
                    "Lähtö"
                    if r_tyyppi == "DEPARTURE"
                    else ("Saapuminen" if r_tyyppi == "ARRIVAL" else r_tyyppi)
                )
            a_aika = rivi.get("scheduledTime")
            ero = rivi.get("differenceInMinutes", 0)
            track = rivi.get("commercialTrack")
            raide = str(track) if track is not None else "-"

            if a_aika:
                try:
                    dt_aika = datetime.fromisoformat(
                        a_aika.replace("Z", "+00:00")
                    ).astimezone(suomi_aika)
                    aikataulu_rivit.append({
                        t["asema"]: koodi_to_nimi.get(s_koodi, s_koodi),
                        t["tapahtuma"]: r_tyyppi_kieli,
                        t["aika"]: dt_aika.strftime("%H:%M"),
                        t["raide"]: raide,
                        t["myoh_min"]: ero,
                    })
                except Exception:
                    pass

        if aikataulu_rivit:
            st.dataframe(pd.DataFrame(aikataulu_rivit), use_container_width=True, hide_index=True)
    else:
        st.error(t["juna_ei_loydy"].format(nro=valittu_nro))

    st.divider()

# --- VIRALLINEN LAITURINÄYTTÖ ---
st.markdown(f"### {t['laiturinaytto_otsikko'].format(asema=valittu_lahto_nimi.split(' ')[0])}")
st.caption(t["laiturinaytto_sub"])

laituri_tab1, laituri_tab2 = st.tabs([t["tab_lahtevat"], t["tab_saapuvat"]])
aseman_junat_data = hae_aseman_junat(lahto)

with laituri_tab1:
    if aseman_junat_data:
        l_lahto_rivit = []
        naytetyt_laituri_lahto = set()
        for aj in aseman_junat_data:
            t_num = aj.get("trainNumber")
            if t_num in naytetyt_laituri_lahto:
                continue
            naytetyt_laituri_lahto.add(t_num)

            t_tyyppi = aj.get("trainType")
            cancelled = aj.get("cancelled", False)
            timetable = aj.get("timeTableRows", [])

            for r in timetable:
                if r.get("stationShortCode") == lahto and r.get("type") == "DEPARTURE":
                    sch = r.get("scheduledTime")
                    diff = r.get("differenceInMinutes", 0)
                    track = r.get("commercialTrack")
                    track_str = str(track) if track is not None else "-"
                    if sch:
                        try:
                            dt = datetime.fromisoformat(sch.replace("Z", "+00:00")).astimezone(
                                suomi_aika
                            )
                            paateasema_koodi = (
                                timetable[-1].get("stationShortCode") if timetable else ""
                            )
                            paateasema_nimi = koodi_to_nimi.get(
                                paateasema_koodi, paateasema_koodi
                            )

                            tila_str = (
                                t["peruttu"]
                                if cancelled
                                else (f"+{diff} min" if diff > 0 else ("On time 🟢" if valittu_kieli == "English" else "Ajallaan 🟢"))
                            )

                            l_lahto_rivit.append({
                                ("Time" if valittu_kieli == "English" else "Aika"): dt.strftime("%H:%M"),
                                ("Train" if valittu_kieli == "English" else "Juna"): f"{t_tyyppi} {t_num}",
                                ("Destination" if valittu_kieli == "English" else "Määränpää"): paateasema_nimi,
                                ("Track" if valittu_kieli == "English" else "Raide"): track_str,
                                ("Status" if valittu_kieli == "English" else "Tila"): tila_str,
                                "sort_aika": dt,
                            })
                        except Exception:
                            pass
        if l_lahto_rivit:
            l_lahto_rivit = sorted(l_lahto_rivit, key=lambda x: x["sort_aika"])
            df_lahto = pd.DataFrame(l_lahto_rivit).drop(columns=["sort_aika"])
            st.dataframe(df_lahto, use_container_width=True, hide_index=True)
        else:
            st.info(t["ei_lahtevia"])
    else:
        st.info(t["ladataan"])

with laituri_tab2:
    if aseman_junat_data:
        l_saapuu_rivit = []
        naytetyt_laituri_saapuu = set()
        for aj in aseman_junat_data:
            t_num = aj.get("trainNumber")
            if t_num in naytetyt_laituri_saapuu:
                continue
            naytetyt_laituri_saapuu.add(t_num)

            t_tyyppi = aj.get("trainType")
            cancelled = aj.get("cancelled", False)
            timetable = aj.get("timeTableRows", [])

            for r in timetable:
                if r.get("stationShortCode") == lahto and r.get("type") == "ARRIVAL":
                    sch = r.get("scheduledTime")
                    diff = r.get("differenceInMinutes", 0)
                    track = r.get("commercialTrack")
                    track_str = str(track) if track is not None else "-"
                    if sch:
                        try:
                            dt = datetime.fromisoformat(sch.replace("Z", "+00:00")).astimezone(
                                suomi_aika
                            )
                            lahtoasema_koodi = (
                                timetable[0].get("stationShortCode") if timetable else ""
                            )
                            lahtoasema_nimi = koodi_to_nimi.get(
                                lahtoasema_koodi, lahtoasema_koodi
                            )

                            tila_str = (
                                t["peruttu"]
                                if cancelled
                                else (f"+{diff} min" if diff > 0 else ("On time 🟢" if valittu_kieli == "English" else "Ajallaan 🟢"))
                            )

                            l_saapuu_rivit.append({
                                ("Time" if valittu_kieli == "English" else "Aika"): dt.strftime("%H:%M"),
                                ("Train" if valittu_kieli == "English" else "Juna"): f"{t_tyyppi} {t_num}",
                                ("Origin" if valittu_kieli == "English" else "Lähtöpaikka"): lahtoasema_nimi,
                                ("Track" if valittu_kieli == "English" else "Raide"): track_str,
                                ("Status" if valittu_kieli == "English" else "Tila"): tila_str,
                                "sort_aika": dt,
                            })
                        except Exception:
                            pass
        if l_saapuu_rivit:
            l_saapuu_rivit = sorted(l_saapuu_rivit, key=lambda x: x["sort_aika"])
            df_saapuu = pd.DataFrame(l_saapuu_rivit).drop(columns=["sort_aika"])
            st.dataframe(df_saapuu, use_container_width=True, hide_index=True)
        else:
            st.info(t["ei_saapuvia"])
    else:
        st.info(t["ladataan"])

st.divider()

if st.session_state.haku_tehty:
    st.markdown(t["reittihaku_otsikko"].format(
        lahto=valittu_lahto_nimi, paikka=valittu_paikka_nimi, pvm=valittu_pvm.strftime('%d.%m.%Y')
    ))

    kaikki_hairiot = hae_rautatie_hairiot() + hae_ratatyot_ja_nopeusrajoitukset()
    reitti_hairiot = []
    lahto_lyhenne = valittu_lahto_nimi.split("(")[-1].strip(")")
    paikka_lyhenne = valittu_paikka_nimi.split("(")[-1].strip(")")

    for h in kaikki_hairiot:
        h_teksti = (
            h.get("title", "") + " " + h.get("ingress", "") + " " + h.get("body", "")
        ).upper()
        if (
            lahto_lyhenne in h_teksti
            or paikka_lyhenne in h_teksti
            or valittu_lahto_nimi.split(" ")[0].upper() in h_teksti
            or valittu_paikka_nimi.split(" ")[0].upper() in h_teksti
        ):
            reitti_hairiot.append(h)

    if reitti_hairiot:
        st.error(t["reitti_poikkeus_varoitus"])
        for rh in reitti_hairiot[:2]:
            st.warning(f"**{rh.get('title', 'Disruption')}**: {rh.get('ingress', '')}")
    else:
        st.success(t["reitti_ok"])

    l_lat = asema_dict[valittu_lahto_nimi].get("lat")
    l_lon = asema_dict[valittu_lahto_nimi].get("lon")
    p_lat = asema_dict[valittu_paikka_nimi].get("lat")
    p_lon = asema_dict[valittu_paikka_nimi].get("lon")

    if l_lat and l_lon and p_lat and p_lon:
        etaisyys_km = LaskeEtaisyysJaAika(l_lat, l_lon, p_lat, p_lon)
        st.info(t["rataetaisyys"].format(km=etaisyys_km, linnu=round(etaisyys_km / 1.25, 1)))

    if p_lat and p_lon:
        try:
            sää_url = f"https://api.open-meteo.com/v1/forecast?latitude={p_lat}&longitude={p_lon}&current=temperature_2m,weather_code"
            s_vast = requests.get(sää_url, timeout=3).json()
            lampo = s_vast["current"]["temperature_2m"]
            st.success(t["saa_maaranpaassa"].format(asema=valittu_paikka_nimi.split(' ')[0], lampo=lampo))
        except Exception:
            pass

    st.markdown(t["valitse_junavuoro"])

    pvm_str = valittu_pvm.strftime("%Y-%m-%d")
    url = f"https://rata.digitraffic.fi/api/v1/trains/{pvm_str}"

    with st.spinner(t["haetaan_junia"]):
        try:
            vastaus = requests.get(url, timeout=10)
            junat = vastaus.json() if vastaus.status_code == 200 else []
        except Exception:
            junat = []

    if not isinstance(junat, list) or not junat:
        st.warning(t["ei_junia_pvm"])
    else:
        aktiiviset_junat = []
        naytetyt_reitti_junat = set()
        kartta_koordinaatit = []

        for juna in junat:
            j_num = juna.get("trainNumber")
            if j_num in naytetyt_reitti_junat:
                continue

            timeTable = juna.get("timeTableRows", [])
            asemat_koodit = [r.get("stationShortCode") for r in timeTable]

            if lahto in asemat_koodit and paikka in asemat_koodit:
                lahto_idx = asemat_koodit.index(lahto)
                paikka_idx = asemat_koodit.index(paikka)
                if lahto_idx > paikka_idx:
                    continue
            else:
                continue

            naytetyt_reitti_junat.add(j_num)
            t_tyyppi = juna.get("trainType", "Train")
            peruttu = juna.get("cancelled", False)

            lahto_aika_str = ""
            perille_aika_str = ""
            myohassa = 0
            lahto_dt = None
            perille_dt = None

            for rivi in timeTable:
                if rivi.get("stationShortCode") == lahto and rivi.get("type") == "DEPARTURE":
                    sch = rivi.get("scheduledTime")
                    diff = rivi.get("differenceInMinutes", 0)
                    if diff:
                        myohassa = diff
                    if sch:
                        try:
                            lahto_dt = datetime.fromisoformat(
                                sch.replace("Z", "+00:00")
                            ).astimezone(suomi_aika)
                            lahto_aika_str = lahto_dt.strftime("%H:%M")
                        except Exception:
                            pass
                if rivi.get("stationShortCode") == paikka and rivi.get("type") == "ARRIVAL":
                    sch = rivi.get("scheduledTime")
                    if sch:
                        try:
                            perille_dt = datetime.fromisoformat(
                                sch.replace("Z", "+00:00")
                            ).astimezone(suomi_aika)
                            perille_aika_str = perille_dt.strftime("%H:%M")
                        except Exception:
                            pass

            keskinopeus_arvio = 0
            kesto_min = 0
            if lahto_dt and perille_dt:
                kesto_min = int((perille_dt - lahto_dt).total_seconds() / 60)
                if kesto_min > 0 and 'etaisyys_km' in locals():
                    keskinopeus_arvio = round(etaisyys_km / (kesto_min / 60))

            historia_myohassa = hae_junan_historiatilastot(j_num)

            live_sijainti = hae_junan_sijainti(j_num)
            if live_sijainti:
                kartta_koordinaatit.append({
                    "lat": live_sijainti["lat"],
                    "lon": live_sijainti["lon"],
                    "juna": f"{t_tyyppi} {j_num}",
                })

            aktiiviset_junat.append({
                "numero": j_num,
                "tyyppi": t_tyyppi,
                "lahto": lahto_aika_str,
                "perille": perille_aika_str,
                "kesto": kesto_min,
                "keskinopeus": keskinopeus_arvio,
                "historia": historia_myohassa,
                "myohassa": myohassa,
                "peruttu": peruttu,
            })

        if kartta_koordinaatit:
            st.markdown(f"#### {t['reitin_junat_kartalla']}")
            df_reitti_kartta = pd.DataFrame(kartta_koordinaatit)
            st.map(df_reitti_kartta, zoom=6, use_container_width=True)

        if aktiiviset_junat:
            for j in aktiiviset_junat:
                if valittu_kieli == "English":
                    tila_teksti = (
                        "Cancelled ❌"
                        if j["peruttu"]
                        else (
                            f"Delayed +{j['myohassa']} min ⚠️"
                            if j["myohassa"] > 0
                            else "On time ✅"
                        )
                    )
                    historia_teksti = (
                        f"📊 Past days average delay +{j['historia']} min"
                        if j["historia"] is not None
                        else "📊 No historical data available"
                    )
                    matka_info = (
                        f"⏱️ Travel time: ~{j['kesto']} min | Avg speed estimate: ~{j['keskinopeus']} km/h"
                        if j["kesto"] > 0
                        else ""
                    )
                    lahto_perille_txt = f"Departure: {j['lahto']} ➔ Arrival: {j['perille']}"
                else:
                    tila_teksti = (
                        "Peruttu ❌"
                        if j["peruttu"]
                        else (
                            f"Myöhässä +{j['myohassa']} min ⚠️"
                            if j["myohassa"] > 0
                            else "Aikataulussa ✅"
                        )
                    )
                    historia_teksti = (
                        f"📊 Viime päivinä keskimäärin +{j['historia']} min myöhässä"
                        if j["historia"] is not None
                        else "📊 Historiatietoa ei saatavilla"
                    )
                    matka_info = (
                        f"⏱️ Matka-aika: ~{j['kesto']} min | Keskinopeusarvio: ~{j['keskinopeus']} km/h"
                        if j["kesto"] > 0
                        else ""
                    )
                    lahto_perille_txt = f"Lähtö: {j['lahto']} ➔ Perille: {j['perille']}"

                st.markdown(
                    f"""
                    <div class="train-box">
                        <div style="font-size: 1.1rem; font-weight: 700; margin-bottom: 6px;">🚆 {j['tyyppi']} {j['numero']}</div>
                        <div style="font-size: 0.95rem; color: #334155; margin-bottom: 4px;">{lahto_perille_txt}</div>
                        <div style="font-size: 0.85rem; color: #64748b; margin-bottom: 4px;">{matka_info}</div>
                        <div style="font-size: 0.9rem; font-weight: 600; margin-bottom: 4px;">Status: {tila_teksti}</div>
                        <div style="font-size: 0.8rem; color: #64748b; font-style: italic;">{historia_teksti}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                col_nappi1, col_nappi2 = st.columns(2)
                with col_nappi1:
                    vr_haku_url = f"https://www.vr.fi/matkailu?from={valittu_lahto_nimi.split(' ')[0]}&to={valittu_paikka_nimi.split(' ')[0]}&date={valittu_pvm.strftime('%Y-%m-%d')}"
                    st.link_button(
                        t["osta_liput"],
                        vr_haku_url,
                        use_container_width=True,
                    )
                with col_nappi2:
                    if st.button(
                        t["seuraa_live"].format(nro=j['numero']),
                        key=f"reitti_live_{j['numero']}",
                        use_container_width=True,
                    ):
                        st.session_state.valittu_live_juna = str(j["numero"])
                        st.rerun()

                st.divider()
