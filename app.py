from datetime import date, datetime, timedelta
from math import atan2, cos, radians, sin, sqrt
from zoneinfo import ZoneInfo
import csv
import os
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# Sivun perusasetukset ja SEO-otsikko
st.set_page_config(
    page_title=(
        "Raidetutka – Reaaliaikainen Junatutka, Aikataulut & Rataliikennehäiriöt"
    ),
    page_icon="🚆",
    layout="wide",
)

# --- SKANDINAAVINEN & MOBIILIOPTIMOITU UI-TYYLITTELY ---
st.markdown(
    """
    <style>
    /* Raikas vaalea päätausta */
    .stApp {
        background-color: #f8f9fa;
        color: #212529;
    }
    
    /* Tyylitellyt kortit (Modern Cards) */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e9ecef;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
        margin-bottom: 12px;
    }
    
    /* Vaunukortti mobiiliystävällisenä */
    .wagon-card {
        background-color: #ffffff;
        border: 1px solid #dee2e6;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    }
    
    /* Otsikoiden tyylit responsiivisiksi */
    h1 {
        font-size: 1.8rem !important;
        color: #1a1a1a !important;
    }
    h2 {
        font-size: 1.4rem !important;
        color: #1a1a1a !important;
    }
    h3 {
        font-size: 1.15rem !important;
        color: #1a1a1a !important;
    }
    
    /* Sivupalkin selkeytys */
    [data-testid="stSidebar"] {
        background-color: #f1f3f5;
        border-right: 1px solid #e9ecef;
    }
    
    /* Mobiililaitteiden painikkeiden korjaus */
    .stButton button, .stLinkButton a {
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
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
    <meta name="description" content="Raidetutka on ammattimainen junatutka VR:n reaaliaikaisilla aikatauluilla, rataliikennehäiriöillä ja live-sijainneilla." />
    <meta name="keywords" content="junatutka, junan myöhästyminen, VR aikataulut, rataliikennehäiriöt, live junatutka" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
"""
components.html(ga_script, height=0, width=0)

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


@st.cache_data(ttl=300)
def hae_aseman_tiedotteet(asema_koodi):
    url = "https://rata.digitraffic.fi/api/v1/messages"
    try:
        vastaus = requests.get(url, timeout=5)
        if vastaus.status_code == 200:
            return vastaus.json()[:5]
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


@st.cache_data(ttl=600)
def hae_radan_saatiedot():
    url = "https://tie.digitraffic.fi/api/v1/data/weather-data"
    try:
        vastaus = requests.get(url, timeout=3)
        if vastaus.status_code == 200:
            return vastaus.json().get("weatherStations", [])[:5]
    except Exception:
        pass
    return []


@st.cache_data(ttl=300)
def hae_vaunukoostumus(juna_numero, pvm):
    url = f"https://rata.digitraffic.fi/api/v1/compositions/{pvm}/{juna_numero}"
    try:
        vastaus = requests.get(url, timeout=3)
        if vastaus.status_code == 200:
            data = vastaus.json()
            return data
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
st.sidebar.markdown("### 🚆 Raidetutka Hallinta")
st.sidebar.divider()

live_paivitys_paalla = st.sidebar.checkbox(
    "🔄 Automaattinen live-päivitys (15s)", value=True
)
if live_paivitys_paalla:
    st_autorefresh(interval=15000, key="raidetutka_live_refresh")

st.sidebar.divider()

st.sidebar.markdown("### 🚨 Rataliikennehäiriöt")
hairiot = hae_rautatie_hairiot()
if hairiot:
    for h in hairiot[:3]:
        otsikko = h.get("title", "Häiriö")
        kuvaus = h.get("ingress", "")
        st.sidebar.warning(f"**{otsikko}**\n\n{kuvaus}")
else:
    st.sidebar.success("Ei tiedossa olevia rataliikennehäiriöitä.")

st.sidebar.divider()
st.sidebar.markdown("### 🚧 Ratatyöt & Nopeusrajoitukset")
ratatyot = hae_ratatyot_ja_nopeusrajoitukset()
if ratatyot:
    for tyy in ratatyot[:2]:
        t_ots = tyy.get("title", "Ratatyö")
        t_ing = tyy.get("ingress", "Radalla tehdään kunnossapitotöitä.")
        st.sidebar.info(f"🛠️ **{t_ots}**\n\n{t_ing}")
else:
    st.sidebar.caption("Ei aktiivisia ratatöitä tai hidastuksia.")

st.sidebar.divider()
st.sidebar.header("🎛️ Reitti & Seuranta")

st.sidebar.markdown("### ⭐ Seuratut junat")
seurattava_input = st.sidebar.text_input(
    "Lisää junanumero seurantaan", placeholder="Esim. 67"
)
col_lisaa, col_poista = st.sidebar.columns(2)
with col_lisaa:
    if st.button("Lisää juna", use_container_width=True):
        if seurattava_input and seurattava_input not in st.session_state.seuratut_junat:
            st.session_state.seuratut_junat.append(seurattava_input)
            st.success(f"Juna {seurattava_input} lisätty.")
with col_poista:
    if st.button("Tyhjennä", use_container_width=True):
        st.session_state.seuratut_junat = []
        st.session_state.valittu_live_juna = None
        st.rerun()

for j_nro in st.session_state.seuratut_junat:
    juna_info = hae_junan_perustiedot(j_nro)
    sijainti = hae_junan_sijainti(j_nro)

    t_tyyppi = "Juna"
    lahto_asema = "Lähtö"
    paate_asema = "Määränpää"
    myohassa_min = 0

    if juna_info:
        t_tyyppi = juna_info.get("trainType", "Juna")
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
        st.sidebar.markdown(f"🟢 Nopeus: **{kmh} km/h**")
    else:
        st.sidebar.markdown("⏳ Ei live-paikannusta")

    if myohassa_min > 0:
        st.sidebar.error(f"⚠️ Myöhässä: +{myohassa_min} min")
    else:
        st.sidebar.success("✅ Ajallaan")

    if st.sidebar.button(
        f"📡 Avaa seuranta ({j_nro})",
        key=f"live_btn_{j_nro}",
        use_container_width=True,
    ):
        st.session_state.valittu_live_juna = j_nro
        st.rerun()

    st.sidebar.divider()

if st.session_state.suosikit:
    st.sidebar.markdown("### ⭐ Suosikkireitit")
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
    "Lähtöasema", asema_nimet, index=oletus_lahto_idx
)
valittu_paikka_nimi = st.sidebar.selectbox(
    "Määränpää", asema_nimet, index=oletus_paikka_idx
)

if st.sidebar.button(
    "❤️ Tallenna suosikkireitiksi", use_container_width=True
):
    uusi_suosikki = (valittu_lahto_nimi, valittu_paikka_nimi)
    if uusi_suosikki not in st.session_state.suosikit:
        st.session_state.suosikit.append(uusi_suosikki)
        st.sidebar.success("Reitti tallennettu suosikkeihin.")

valittu_pvm = st.sidebar.date_input("Matkustuspäivä", value=date.today())

lahto = asema_dict[valittu_lahto_nimi]["koodi"]
paikka = asema_dict[valittu_paikka_nimi]["koodi"]

hakunappi = st.sidebar.button(
    "🔍 Hae reitti", type="primary", use_container_width=True
)

if hakunappi:
    st.session_state.haku_tehty = True
    st.session_state.valittu_live_juna = None

# --- PALAUTELOMAKE SIVUPALKISSA ---
st.sidebar.divider()
st.sidebar.markdown("### 💬 Palaute & Kehitysehdotukset")

with st.sidebar.form("palaute_lomake"):
    kayttajan_nimi = st.text_input("Nimi (valinnainen)")
    palaute_tyyppi = st.selectbox(
        "Aihealue",
        [
            "Kehitysehdotus",
            "Virheilmoitus / Bugi",
            "Yleinen palaute",
        ],
    )
    palaute_teksti = st.text_area(
        "Palaute",
        placeholder="Kirjoita palautteesi tähän...",
    )

    laheta_palaute = st.form_submit_button(
        "Lähetä palaute", use_container_width=True
    )

    if laheta_palaute:
        if palaute_teksti.strip():
            aikaleima = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            rivi = [
                aikaleima,
                kayttajan_nimi if kayttajan_nimi else "Anonyymi",
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
                        kirjoittaja.writerow(["Aikaleima", "Nimi", "Tyyppi", "Palaute"])
                    kirjoittaja.writerow(rivi)
                st.success("Kiitos palautestasi.")
            except Exception as e:
                st.error(f"Tallennusvirhe: {e}")
        else:
            st.warning("Kirjoita palauteteksti ennen lähettämistä.")

st.sidebar.divider()
st.sidebar.caption(
    "Tiedot: [Fintraffic / Digitraffic (CC 4.0 BY)](https://www.digitraffic.fi) &"
    " Open-Meteo."
)

# --- PÄÄSIVU ---
st.title("🚆 Raidetutka")
st.markdown(
    "##### *Reaaliaikainen junatutka, aikataulut ja vaunukoostumukset*"
)
st.divider()

suomi_aika = ZoneInfo("Europe/Helsinki")

# Pakotetaan sivu heti ylös, jos live-juna on valittuna
if st.session_state.valittu_live_juna:
    components.html(
        """
        <script>
            function scrollToTop() {
                const body = window.parent.document.querySelector('section.main');
                if (body) {
                    body.scrollTo({top: 0, behavior: 'instant'});
                }
                window.parent.scrollTo({top: 0, behavior: 'instant'});
            }
            scrollToTop();
            setTimeout(scrollToTop, 50);
        </script>
        """,
        height=0,
    )

    valittu_nro = st.session_state.valittu_live_juna
    st.markdown(f"### 📡 Junan **{valittu_nro}** Seuranta & Koostumus")

    if st.button("⬅️ Palaa reittihakuun", use_container_width=True):
        st.session_state.valittu_live_juna = None
        st.rerun()

    juna_info = hae_junan_perustiedot(valittu_nro)
    if juna_info:
        t_tyyppi = juna_info.get("trainType", "Juna")
        timeTable = juna_info.get("timeTableRows", [])

        lahto_koodi = timeTable[0].get("stationShortCode") if timeTable else ""
        paate_koodi = timeTable[-1].get("stationShortCode") if timeTable else ""
        l_nimi = koodi_to_nimi.get(lahto_koodi, lahto_koodi)
        p_nimi = koodi_to_nimi.get(paate_koodi, paate_koodi)

        st.info(f"Reitti: **{l_nimi} ➔ {p_nimi}** ({t_tyyppi})")

        # --- VAUNUKOOSTUMUS JA PALVELUT ---
        tanaan_str = date.today().strftime("%Y-%m-%d")
        koostumus_data = hae_vaunukoostumus(valittu_nro, tanaan_str)
        if koostumus_data and "journeySections" in koostumus_data:
            st.markdown("#### 🚃 Vaunukoostumus & Palvelut")
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
                            v_tyyppi = v.get("wagonType", "Vaunu")
                            v_nro = v.get("salesNumber", "-")

                            ikoni = "🚃"
                            kuvaus = f"Vaunu {v_nro}"

                            if v_tyyppi == "Ed":
                                kuvaus = f"Vaunu {v_nro} (2. luokka)"
                            elif v_tyyppi == "Edfs":
                                ikoni = "🧸"
                                kuvaus = f"Vaunu {v_nro} (Perheosasto)"
                            elif v_tyyppi == "Edo":
                                ikoni = "☕"
                                kuvaus = f"Vaunu {v_nro} (Bistro)"
                            elif v_tyyppi == "ERd" or v_tyyppi == "Rx":
                                ikoni = "🍽️"
                                kuvaus = f"Vaunu {v_nro} (Ravintola)"
                            elif v_tyyppi == "Eds":
                                ikoni = "🛋️"
                                kuvaus = f"Vaunu {v_nro} (InterCity)"
                            elif v_tyyppi == "CEd" or v_tyyppi == "C":
                                ikoni = "🛏️"
                                kuvaus = f"Vaunu {v_nro} (Makuu)"
                            else:
                                kuvaus = f"Vaunu {v_nro} ({v_tyyppi})"

                            tiedot = []
                            if v_tyyppi not in ["ERd", "Rx", "Edo"]:
                                if v.get("luggage", False):
                                    tiedot.append("🚲 Pyörä")
                                if v.get("petsAllowed", False):
                                    tiedot.append("🐾 Lemmikki")
                                if v.get("accessibility", False):
                                    tiedot.append("♿ Esteetön")
                            else:
                                tiedot.append("🍽️ Ravintola")

                            palvelut_html = (
                                "<br>".join(tiedot)
                                if tiedot
                                else '<span style="color: #adb5bd;">Perusvaunu</span>'
                            )

                            st.markdown(
                                f"""
                                        <div class="wagon-card">
                                            <div style="font-weight: bold; font-size: 0.95rem; margin-bottom: 3px;">{ikoni} {kuvaus}</div>
                                            <div style="font-size: 0.8rem; color: #495057;">{palvelut_html}</div>
                                        </div>
                                        """,
                                unsafe_allow_html=True,
                            )
                    st.markdown("---")
                else:
                    st.info("Ei tarkempia vaunutietoja saatavilla.")
        else:
            st.caption("ℹ️ Vaunukoostumustietoja ei ole saatavilla tälle junalle.")

        sijainti_data = hae_junan_sijainti(valittu_nro)
        if sijainti_data:
            j_lat = sijainti_data["lat"]
            j_lon = sijainti_data["lon"]
            j_nopeus = sijainti_data["nopeus"]
            kmh_nopeus = round(j_nopeus * 3.6)

            st.success(f"📍 **Sijainti:** Nopeus **{kmh_nopeus} km/h**.")

            kartta_ava = f"live_{valittu_nro}"
            if kartta_ava not in st.session_state.piilotetut_kartat:
                if st.button("Sulje kartta", key=f"sulje_{kartta_ava}", use_container_width=True):
                    st.session_state.piilotetut_kartat.add(kartta_ava)
                    st.rerun()
                df_kartta = pd.DataFrame({"lat": [j_lat], "lon": [j_lon]})
                st.map(df_kartta, zoom=7, use_container_width=True)
            else:
                if st.button("🗺️ Näytä kartta", key=f"nayta_{kartta_ava}", use_container_width=True):
                    st.session_state.piilotetut_kartat.remove(kartta_ava)
                    st.rerun()
        else:
            st.warning("ℹ️ GPS-paikannus ei ole aktiivinen.")

        st.markdown("#### 📍 Ajoaikataulu")
        aikataulu_rivit = []
        for rivi in timeTable:
            s_koodi = rivi.get("stationShortCode")
            if s_koodi not in koodi_to_nimi:
                continue
            r_tyyppi = rivi.get("type")
            r_tyyppi_suomeksi = (
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
                        "Asema": koodi_to_nimi.get(s_koodi, s_koodi),
                        "Tapahtuma": r_tyyppi_suomeksi,
                        "Aika": dt_aika.strftime("%H:%M"),
                        "Raide": raide,
                        "Myöh (min)": ero,
                    })
                except Exception:
                    pass

        if aikataulu_rivit:
            st.dataframe(pd.DataFrame(aikataulu_rivit), use_container_width=True, hide_index=True)
    else:
        st.error(f"Junan {valittu_nro} tietoja ei löytynyt.")

    st.divider()

# --- VIRALLINEN LAITURINÄYTTÖ ---
st.markdown(f"### 📺 Laiturinäyttö – {valittu_lahto_nimi.split(' ')[0]}")
st.caption("Aseman reaaliaikainen aikataulunäyttö.")

laituri_tab1, laituri_tab2 = st.tabs(["🚂 Lähtevät", "📥 Saapuvat"])
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

                            l_lahto_rivit.append({
                                "Aika": dt.strftime("%H:%M"),
                                "Juna": f"{t_tyyppi} {t_num}",
                                "Määränpää": paateasema_nimi,
                                "Raide": track_str,
                                "Tila": (
                                    "Peruttu ❌"
                                    if cancelled
                                    else (f"+{diff} min" if diff > 0 else "Ajallaan 🟢")
                                ),
                                "sort_aika": dt,
                            })
                        except Exception:
                            pass
        if l_lahto_rivit:
            l_lahto_rivit = sorted(l_lahto_rivit, key=lambda x: x["sort_aika"])
            df_lahto = pd.DataFrame(l_lahto_rivit).drop(columns=["sort_aika"])
            st.dataframe(df_lahto, use_container_width=True, hide_index=True)
        else:
            st.info("Ei lähteviä junia.")
    else:
        st.info("Ladataan asematietoja...")

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

                            l_saapuu_rivit.append({
                                "Aika": dt.strftime("%H:%M"),
                                "Juna": f"{t_tyyppi} {t_num}",
                                "Lähtöpaikka": lahtoasema_nimi,
                                "Raide": track_str,
                                "Tila": (
                                    "Peruttu ❌"
                                    if cancelled
                                    else (f"+{diff} min" if diff > 0 else "Ajallaan 🟢")
                                ),
                                "sort_aika": dt,
                            })
                        except Exception:
                            pass
        if l_saapuu_rivit:
            l_saapuu_rivit = sorted(l_saapuu_rivit, key=lambda x: x["sort_aika"])
            df_saapuu = pd.DataFrame(l_saapuu_rivit).drop(columns=["sort_aika"])
            st.dataframe(df_saapuu, use_container_width=True, hide_index=True)
        else:
            st.info("Ei saapuvia junia.")
    else:
        st.info("Ladataan asematietoja...")

st.divider()

if st.session_state.haku_tehty:
    st.markdown(
        f"### 🗺️ Reittihaku: **{valittu_lahto_nimi}** ➔"
        f" **{valittu_paikka_nimi}** ({valittu_pvm.strftime('%d.%m.%Y')})"
    )

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
        st.error(
            "⚠️ **Huomio!** Valitsemallesi reitille tai sen asemille on kirjattu"
            " poikkeuksia tai ratatöitä:"
        )
        for rh in reitti_hairiot[:2]:
            st.warning(f"**{rh.get('title', 'Häiriö')}**: {rh.get('ingress', '')}")
    else:
        st.success(
            "✅ Ei tiedossa olevia poikkeuksia tai ratatöitä tällä reitillä."
        )

    l_lat = asema_dict[valittu_lahto_nimi].get("lat")
    l_lon = asema_dict[valittu_lahto_nimi].get("lon")
    p_lat = asema_dict[valittu_paikka_nimi].get("lat")
    p_lon = asema_dict[valittu_paikka_nimi].get("lon")

    if l_lat and l_lon and p_lat and p_lon:
        etaisyys_km = LaskeEtaisyysJaAika(l_lat, l_lon, p_lat, p_lon)
        st.info(
            f"📏 **Rataetäisyys-arvio:** ~{etaisyys_km} km (Linnuntie"
            f" {round(etaisyys_km / 1.25, 1)} km)"
        )

    if p_lat and p_lon:
        try:
            sää_url = f"https://api.open-meteo.com/v1/forecast?latitude={p_lat}&longitude={p_lon}&current=temperature_2m,weather_code"
            s_vast = requests.get(sää_url, timeout=3).json()
            lampo = s_vast["current"]["temperature_2m"]
            st.success(
                f"🌤️ **Sää määränpäässä ({valittu_paikka_nimi.split(' ')[0]}):**"
                f" {lampo}°C"
            )
        except Exception:
            pass

    st.markdown("Valitse alta haluamasi junavuoro:")

    pvm_str = valittu_pvm.strftime("%Y-%m-%d")
    url = f"https://rata.digitraffic.fi/api/v1/trains/{pvm_str}"

    with st.spinner("Haetaan junavuoroja..."):
        try:
            vastaus = requests.get(url, timeout=10)
            junat = vastaus.json() if vastaus.status_code == 200 else []
        except Exception:
            junat = []

    if not isinstance(junat, list) or not junat:
        st.warning("Valitsemallesi päivälle ei löytynyt junavuoroja rajapinnasta.")
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
            t_tyyppi = juna.get("trainType", "Juna")
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
            st.markdown("#### 🗺️ Reitin junat kartalla")
            df_reitti_kartta = pd.DataFrame(kartta_koordinaatit)
            st.map(df_reitti_kartta, zoom=6, use_container_width=True)

        if aktiiviset_junat:
            for j in aktiiviset_junat:
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
                    f"⏱️ Matka-aika: ~{j['kesto']} min | Keskinopeusarvio:"
                    f" ~{j['keskinopeus']} km/h"
                    if j["kesto"] > 0
                    else ""
                )

                st.markdown(
                    f"🚆 **{j['tyyppi']} {j['numero']}**\n\nLähtö: {j['lahto']} ➔"
                    f" Perille: {j['perille']}\n{matka_info}\nTila: {tila_teksti}\n*{historia_teksti}*"
                )
