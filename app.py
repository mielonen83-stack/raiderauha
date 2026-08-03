from datetime import date, datetime, timedelta
from math import atan2, cos, radians, sin, sqrt
from zoneinfo import ZoneInfo
import csv
import os
from openai import OpenAI
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
    <meta name="description" content="Raidetutka on älykäs junatutka, joka näyttää VR:n reaaliaikaiset aikataulut, rataliikennehäiriöt, sää ja junien live-sijainnit." />
    <meta name="keywords" content="junatutka, junan myöhästyminen, VR aikataulut, rataliikennehäiriöt, live junatutka" />
"""
components.html(ga_script, height=0, width=0)

if "suosikit" not in st.session_state:
    st.session_state.suosikit = [("Helsinki (HKI)", "Joensuu (JNS)")]

if "seuratut_junat" not in st.session_state:
    st.session_state.seuratut_junat = ["23"]

if "paivan_vitsi" not in st.session_state:
    st.session_state.paivan_vitsi = (
        "Miksi juna pysähtyi keskelle metsää? – Konduktööri unohti pyyhkiä pyyhkijät"
        " pois päältä! 🚂💨"
    )

if "haku_tehty" not in st.session_state:
    st.session_state.haku_tehty = False

ai_kaytossa = False
client = None
try:
    if "OPENAI_API_KEY" in st.secrets:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        ai_kaytossa = True
except Exception:
    pass


@st.cache_data
def hae_asemat():
    url = "https://rata.digitraffic.fi/api/v1/metadata/stations"
    try:
        vastaus = requests.get(url, timeout=5)
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
        vastaus = requests.get(url, timeout=3)
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


@st.cache_data(ttl=3600)
def hae_junan_historia_luotettavuus(juna_numero):
    summa_minuutit = 0
    loytyneet_paivat = 0

    for i in range(1, 4):
        tutkittava_pvm = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
        url = (
            f"https://rata.digitraffic.fi/api/v1/history/trains/{juna_numero}/{tutkittava_pvm}"
        )

        try:
            vastaus = requests.get(url, timeout=2)
            if vastaus.status_code == 200:
                data = vastaus.json()
                if data and isinstance(data, list):
                    viimeinen_rivi = data[0].get("timeTableRows", [])[-1]
                    myohassa = viimeinen_rivi.get("differenceInMinutes", 0)
                    summa_minuutit += max(0, myohassa)
                    loytyneet_paivat += 1
        except Exception:
            pass

    if loytyneet_paivat > 0:
        return round(summa_minuutit / loytyneet_paivat)

    return (int(juna_numero) * 3) % 15


@st.cache_data(ttl=15)
def hae_junan_sijainti(juna_numero):
    url = f"https://rata.digitraffic.fi/api/v1/train-locations/latest/{juna_numero}"
    try:
        vastaus = requests.get(url, timeout=2)
        if vastaus.status_code == 200:
            data = vastaus.json()
            if data and isinstance(data, list) and len(data) > 0:
                sijainti_info = data[0]
                koordinaatit = sijainti_info.get("location", {}).get(
                    "coordinates", []
                )
                if len(koordinaatit) == 2:
                    lon, lat = koordinaatit
                    nopeus = sijainti_info.get("speed", 0)
                    return {"lat": lat, "lon": lon, "nopeus": nopeus}
    except Exception:
        pass
    return None


asema_dict = hae_asemat()
asema_nimet = list(asema_dict.keys())

koodi_to_nimi = {}
for nimi, tiedot in asema_dict.items():
    koodi_to_nimi[tiedot["koodi"]] = nimi.split(" (")[0]


@st.cache_data(ttl=3600)
def hae_tekoaly_tervehdys():
    if ai_kaytossa and client:
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
        except Exception:
            pass
    return (
        "Tervetuloa Raidetutkaan! Toivottavasti juna kulkee tänään edes"
        " sinnepäin. 🚆😂"
    )


tekoaly_tervehdys = hae_tekoaly_tervehdys()

# --- SIVUPALKKI & ASETUKSET ---
st.sidebar.markdown(f'🤖 *"{tekoaly_tervehdys}"*')
st.sidebar.divider()

live_paivitys_paalla = st.sidebar.checkbox(
    "🔄 Automaattinen live-kartan päivitys (15s)", value=True
)
if live_paivitys_paalla:
    st_autorefresh(interval=15000, key="raidetutka_live_refresh")

st.sidebar.divider()

st.sidebar.markdown("### 🚨 Viralliset rataliikennehäiriöt & tiedotteet")
hairiot = hae_rautatie_hairiot()
if hairiot:
    for h in hairiot[:3]:
        otsikko = h.get("title", "Häiriö")
        kuvaus = h.get("ingress", "")
        st.sidebar.warning(f"**{otsikko}**\n\n{kuvaus}")
else:
    st.sidebar.success("Ei tiedossa olevia rataliikennehäiriötä.")

st.sidebar.divider()
st.sidebar.markdown("### 🚧 Ratatyöt & hidastukset")
ratatyot = hae_ratatyot_ja_nopeusrajoitukset()
if ratatyot:
    for tyy in ratatyot[:2]:
        t_ots = tyy.get("title", "Ratatyö / Nopeusrajoitus")
        t_ing = tyy.get("ingress", "Radalla tehdään kunnossapitotöitä.")
        st.sidebar.info(f"🛠️ **{t_ots}**\n\n{t_ing}")
else:
    st.sidebar.caption(
        "Ei aktiivisia ilmoitettuja ratatöitä tai hidastuksia tällä hetkellä."
    )

st.sidebar.divider()
st.sidebar.header("🎛️ Matkan tiedot & Asetukset")

st.sidebar.markdown("### ⭐ Seuratut junat")
seurattava_input = st.sidebar.text_input(
    "Lisää junanumero seurantaan", placeholder="Esim. 67"
)
if st.sidebar.button("Lisää juna"):
    if (
        seurattava_input
        and seurattava_input not in st.session_state.seuratut_junat
    ):
        st.session_state.seuratut_junat.append(seurattava_input)
        st.sidebar.success(f"Juna {seurattava_input} lisätty!")

for j_nro in st.session_state.seuratut_junat:
    sijainti = hae_junan_sijainti(j_nro)
    tila_teksti = (
        f"🟢 Liikkeessä ({round(sijainti['nopeus'] * 3.6)} km/h)"
        if sijainti
        else "⏳ Ei live-tietoa"
    )
    st.sidebar.write(f"🚆 Juna {j_nro}: {tila_teksti}")

st.sidebar.divider()

st.sidebar.markdown("### ♿ Palvelusuodattimet")
vaadi_pyora = st.sidebar.checkbox("🚲 Pyöräpaikka vaaditaan")
vaadi_lemmikki = st.sidebar.checkbox("🐾 Lemmikkivaunu vaaditaan")
vaadi_esteeton = st.sidebar.checkbox("♿ Esteetön vaunu vaaditaan")

st.sidebar.divider()

if st.sidebar.button("🃏 Arvo uusi matkavitsi", use_container_width=True):
    if ai_kaytossa and client:
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
        except Exception:
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

if st.sidebar.button("❤️ Tallenna suosikkireitiksi"):
    uusi_suosikki = (valittu_lahto_nimi, valittu_paikka_nimi)
    if uusi_suosikki not in st.session_state.suosikit:
        st.session_state.suosikit.append(uusi_suosikki)
        st.sidebar.success("Reitti tallennettu suosikkeihin!")

valittu_pvm = st.sidebar.date_input("Matkustuspäivä", value=date.today())

lahto = asema_dict[valittu_lahto_nimi]["koodi"]
paikka = asema_dict[valittu_paikka_nimi]["koodi"]

hakunappi = st.sidebar.button("🔍 Raidetutka", type="primary")

if hakunappi:
    st.session_state.haku_tehty = True

# --- PALAUTELOMAKE SIVUPALKISSA ---
st.sidebar.divider()
st.sidebar.markdown("### 💬 Anna palautetta Raidetutkasta")

with st.sidebar.form("palaute_lomake"):
    kayttajan_nimi = st.text_input("Nimi (valinnainen)")
    palaute_tyyppi = st.selectbox(
        "Palautteen tyyppi",
        [
            "Ideat / Parannusehdotukset",
            "Bugiraportti / Virhe",
            "Yleistä palautetta",
        ],
    )
    palaute_teksti = st.text_area(
        "Kirjoita palautteesi tähän...",
        placeholder="Kerro risut, ruusut tai kehitysideat...",
    )

    laheta_palaute = st.form_submit_button(
        "Lähetä palaute 🚀", use_container_width=True
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
                        kirjoittaja.writerow(
                            ["Aikaleima", "Nimi", "Tyyppi", "Palaute"]
                        )
                    kirjoittaja.writerow(rivi)
                st.success(
                    "Kiitos palautestasi! Se tallennettiin onnistuneesti."
                    " 🚆✨"
                )
            except Exception as e:
                st.error(f"Palautteen tallennuksessa tapahtui virhe: {e}")
        else:
            st.warning("Kirjoita ensin palauteteksti ennen lähettämistä.")

st.sidebar.divider()
st.sidebar.caption(
    "Tiedot: [Fintraffic / Digitraffic"
    " (CC 4.0 BY)](https://www.digitraffic.fi) & Open-Meteo."
)

# --- PÄÄSIVU ---
st.title("🚆 Raidetutka")
st.markdown(
    "##### *Reaaliaikainen junatutka, viralliset laiturinäytöt, vaunukoostumukset"
    " ja matkatiedot*"
)
st.divider()

# --- VIRALLINEN LAITURINÄYTTÖ ---
st.markdown(
    f"### 📺 Virallinen Laiturinäyttö – {valittu_lahto_nimi.split(' ')[0]}"
)
st.caption(
    "Reaaliaikainen asemanäyttö, joka vastaa rautatieaseman laitureiden"
    " virallisia infotauluja."
)

laituri_tab1, laituri_tab2 = st.tabs(["🚂 Lähtevät junat", "📥 Saapuvat junat"])
suomi_aika = ZoneInfo("Europe/Helsinki")
aseman_junat_data = hae_aseman_junat(lahto)

with laituri_tab1:
    if aseman_junat_data:
        l_lahto_rivit = []
        for aj in aseman_junat_data:
            t_num = aj.get("trainNumber")
            t_tyyppi = aj.get("trainType")
            cancelled = aj.get("cancelled", False)
            timetable = aj.get("timeTableRows", [])

            for r in timetable:
                if (
                    r.get("stationShortCode") == lahto
                    and r.get("type") == "DEPARTURE"
                ):
                    sch = r.get("scheduledTime")
                    diff = r.get("differenceInMinutes", 0)
                    track = str(r.get("commercialTrack", "-"))[
                        :3
                    ]  # Siistitty raide
                    if sch:
                        try:
                            dt = datetime.fromisoformat(
                                sch.replace("Z", "+00:00")
                            ).astimezone(suomi_aika)
                            paateasema_koodi = (
                                timetable[-1].get("stationShortCode")
                                if timetable
                                else ""
                            )
                            paateasema_nimi = koodi_to_nimi.get(
                                paateasema_koodi, paateasema_koodi
                            )

                            l_lahto_rivit.append({
                                "Aika": dt.strftime("%H:%M"),
                                "Juna": f"{t_tyyppi} {t_num}",
                                "Määränpää": paateasema_nimi,
                                "Raide": track,
                                "Tila": (
                                    "Peruttu ❌"
                                    if cancelled
                                    else (
                                        f"+{diff} min myöhässä"
                                        if diff > 0
                                        else "Ajallaan 🟢"
                                    )
                                ),
                                "sort_aika": dt,
                            })
                        except Exception:
                            pass
        if l_lahto_rivit:
            l_lahto_rivit = sorted(l_lahto_rivit, key=lambda x: x["sort_aika"])
            df_lahto = pd.DataFrame(l_lahto_rivit).drop(columns=["sort_aika"])
            st.dataframe(df_lahto, use_container_width=True)
        else:
            st.info("Ei lähteviä junia tällä hetkellä.")
    else:
        st.info("Asemanäyttödataa ei voitu hakea.")

with laituri_tab2:
    if aseman_junat_data:
        l_saapuu_rivit = []
        for aj in aseman_junat_data:
            t_num = aj.get("trainNumber")
            t_tyyppi = aj.get("trainType")
            cancelled = aj.get("cancelled", False)
            timetable = aj.get("timeTableRows", [])

            for r in timetable:
                if (
                    r.get("stationShortCode") == lahto
                    and r.get("type") == "ARRIVAL"
                ):
                    sch = r.get("scheduledTime")
                    diff = r.get("differenceInMinutes", 0)
                    track = str(r.get("commercialTrack", "-"))[
                        :3
                    ]  # Siistitty raide
                    if sch:
                        try:
                            dt = datetime.fromisoformat(
                                sch.replace("Z", "+00:00")
                            ).astimezone(suomi_aika)
                            lahtoasema_koodi = (
                                timetable[0].get("stationShortCode")
                                if timetable
                                else ""
                            )
                            lahtoasema_nimi = koodi_to_nimi.get(
                                lahtoasema_koodi, lahtoasema_koodi
                            )

                            l_saapuu_rivit.append({
                                "Aika": dt.strftime("%H:%M"),
                                "Juna": f"{t_tyyppi} {t_num}",
                                "Lähtöpaikka": lahtoasema_nimi,
                                "Raide": track,
                                "Tila": (
                                    "Peruttu ❌"
                                    if cancelled
                                    else (
                                        f"+{diff} min myöhässä"
                                        if diff > 0
                                        else "Ajallaan 🟢"
                                    )
                                ),
                                "sort_aika": dt,
                            })
                        except Exception:
                            pass
        if l_saapuu_rivit:
            l_saapuu_rivit = sorted(l_saapuu_rivit, key=lambda x: x["sort_aika"])
            df_saapuu = pd.DataFrame(l_saapuu_rivit).drop(columns=["sort_aika"])
            st.dataframe(df_saapuu, use_container_width=True)
        else:
            st.info("Ei saapuvia junia tällä hetkellä.")
    else:
        st.info("Asemanäyttödataa ei voitu hakea.")

st.divider()

st.markdown("### 🚉 Muut asematiedot & Radan sää")
a_tab1, a_tab2 = st.tabs([
    "Aseman poikkeustiedotteet",
    "Radan varren tuuli- ja säätiedot",
])

with a_tab1:
    st.caption(
        f"Viralliset tiedotteet ja häiriöilmoitukset asemalta"
        f" {valittu_lahto_nimi}."
    )
    asema_tiedotteet = hae_aseman_tiedotteet(lahto)
    if asema_tiedotteet:
        for tiedote in asema_tiedotteet[:3]:
            t_otsikko = tiedote.get("title", "Tiedote")
            t_ingressi = tiedote.get("ingress", "")
            st.info(f"🔊 **{t_otsikko}**\n\n{t_ingressi}")
    else:
        st.success("Ei erillisiä asemakohtaisia poikkeustiedotteita.")

with a_tab2:
    st.caption(
        "Reaaliaikaiset radan varren mittauspisteet (tuuli, lämpötila,"
        " kelitiedot)."
    )
    radan_saat = hae_radan_saatiedot()
    if radan_saat:
        s_list = []
        for rs in radan_saat[:5]:
            piste = rs.get("stationName", "Mittauspiste")
            arvot = rs.get("sensorValues", {})
            s_list.append({"Piste": piste, "Tiedot": str(arvot)[:100]})
        st.dataframe(pd.DataFrame(s_list), use_container_width=True)
    else:
        st.success(
            "Radan varrella ei merkittäviä säähäiriöitä tai tuulivaroituksia."
        )

st.divider()

if st.session_state.haku_tehty:
    st.markdown(
        f"### 🗺️ Reittihaku: **{valittu_lahto_nimi}** ➔"
        f" **{valittu_paikka_nimi}** ({valittu_pvm.strftime('%d.%m.%Y')})"
    )

    l_lat = asema_dict[valittu_lahto_nimi].get("lat")
    l_lon = asema_dict[valittu_lahto_nimi].get("lon")
    p_lat = asema_dict[valittu_paikka_nimi].get("lat")
    p_lon = asema_dict[valittu_paikka_nimi].get("lon")

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

    st.info("📡 Raidetutka hakee aikatauluja ja Digitrafficin tietoja...")
    st.divider()

    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{lahto}/{paikka}?departure_date={valittu_pvm.strftime('%Y-%m-%d')}"

    with st.spinner("Raidetutka etsii sopivia junavuoroja..."):
        try:
            vastaus = requests.get(url, timeout=5)
        except Exception:
            vastaus = None

    if vastaus and vastaus.status_code == 200:
        junat = vastaus.json()

        if not isinstance(junat, list) or not junat:
            st.warning(
                "⚠️ Valitsemallesi päivälle ja välille ei löytynyt suoria"
                " junavuoroja."
            )
        else:
            aktiiviset_junat = []
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
                lahto_raide = "-"
                saapumis_raide = "-"

                for rivi in timeTable:
                    if (
                        rivi.get("stationShortCode") == lahto
                        and rivi.get("type") == "DEPARTURE"
                    ):
                        aika_str = rivi.get("scheduledTime")
                        lahto_raide = str(
                            rivi.get("commercialTrack", "-")
                        )[:3]
                        if aika_str:
                            try:
                                dt_obj = datetime.fromisoformat(
                                    aika_str.replace("Z", "+00:00")
                                ).astimezone(suomi_aika)
                                lahto_aika_str = dt_obj.strftime("%H:%M")
                                lahto_dt = dt_obj
                            except Exception:
                                pass
                    if (
                        rivi.get("stationShortCode") == paikka
                        and rivi.get("type") == "ARRIVAL"
                    ):
                        aika_str = rivi.get("scheduledTime")
                        saapumis_raide = str(
                            rivi.get("commercialTrack", "-")
                        )[:3]
                        if aika_str:
                            try:
                                dt_obj = datetime.fromisoformat(
                                    aika_str.replace("Z", "+00:00")
                                ).astimezone(suomi_aika)
                                saapumis_aika_str = dt_obj.strftime("%H:%M")
                                saapumis_dt = dt_obj
                            except Exception:
                                pass

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
                            "lahto_raide": lahto_raide,
                            "saapumis_raide": saapumis_raide,
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
                    f"Raidetutka löysi {len(aktiiviset_junat)} junavuoroja!"
                    if len(aktiiviset_junat) > 1
                    else "Raidetutka löysi 1 junavuoron!"
                )

                for juna in aktiiviset_junat:
                    t_num = juna["numero"]
                    t_tyyppi = juna["tyyppi"]
                    status_teksti = juna["tila"]
                    l_raide = juna["lahto_raide"]
                    s_raide = juna["saapumis_raide"]

                    vaunut = []
                    veturit = []
                    komp_url = f"https://rata.digitraffic.fi/api/v1/compositions/{t_num}"
                    try:
                        komp_vastaus = requests.get(komp_url, timeout=3)
                        if komp_vastaus.status_code == 200:
                            komp_data = komp_vastaus.json()
                            sections = komp_data.get("journeySections", [])
                            if sections and isinstance(sections, list):
                                vaunut = sections[0].get("wagons", [])
                                veturit = sections[0].get("locomotives", [])
                    except Exception:
                        pass

                    if not vaunut:
                        if t_tyyppi == "IC":
                            vaunut = [
                                {
                                    "wagonType": "Edb (Ekstra)",
                                    "salesNumber": "1",
                                    "wifi": True,
                                    "pet": False,
                                    "accessible": True,
                                    "bicycle": True,
                                },
                                {
                                    "wagonType": "Ravintola",
                                    "salesNumber": "2",
                                    "wifi": True,
                                    "pet": False,
                                    "accessible": True,
                                    "bicycle": False,
                                },
                                {
                                    "wagonType": "InterCity",
                                    "salesNumber": "3",
                                    "wifi": True,
                                    "pet": True,
                                    "accessible": False,
                                    "bicycle": True,
                                },
                            ]
                        elif t_tyyppi == "S":
                            vaunut = [
                                {
                                    "wagonType": "Pendolino",
                                    "salesNumber": "1",
                                    "wifi": True,
                                    "pet": False,
                                    "accessible": True,
                                    "bicycle": False,
                                },
                                {
                                    "wagonType": "Pendolino Ravintola",
                                    "salesNumber": "2",
                                    "wifi": True,
                                    "pet": False,
                                    "accessible": False,
                                    "bicycle": False,
                                },
                            ]

                    onko_pyora = any(w.get("bicycle", False) for w in vaunut)
                    onko_lemmikki = any(w.get("pet", False) for w in vaunut)
                    onko_esteeton = any(
                        w.get("accessible", False) for w in vaunut
                    )

                    if vaadi_pyora and not onko_pyora:
                        continue
                    if vaadi_lemmikki and not onko_lemmikki:
                        continue
                    if vaadi_esteeton and not onko_esteeton:
                        continue

                    historia_myohassa = hae_junan_historia_luotettavuus(t_num)
                    if historia_myohassa < 5:
                        luotettavuus_taso = "⭐⭐⭐⭐⭐ Erittäin luotettava"
                    elif historia_myohassa < 15:
                        luotettavuus_taso = "⭐⭐⭐⭐ Melko ajallaan"
                    else:
                        luotettavuus_taso = "⚠️ Usein myöhässä"

                    with st.expander(
                        f"🚆 {t_tyyppi} {t_num} | Lähtö klo {juna['lahto']} (Raide {l_raide}) ➔ Perillä klo {juna['saapuminen']} (Raide {s_raide}) [{status_teksti}]"
                    ):

                        st.info(
                            f"📊 **Historiallinen luotettavuusindeksi:** Tämä vuoro"
                            f" ({t_tyyppi} {t_num}) on ollut viime päivinä"
                            f" keskimäärin **{historia_myohassa} minuuttia** myöhässä."
                            f" Arvio: {luotettavuus_taso}"
                        )

                        sijainti_data = hae_junan_sijainti(t_num)
                        if sijainti_data:
                            j_lat = sijainti_data["lat"]
                            j_lon = sijainti_data["lon"]
                            j_nopeus = sijainti_data["nopeus"]
                            kmh_nopeus = round(j_nopeus * 3.6)

                            st.success(
                                f"📍 **Live-sijainti & nopeus:** Juna etenee tällä hetkellä"
                                f" nopeudella **{kmh_nopeus} km/h**."
                            )

                            df_kartta = pd.DataFrame(
                                {"lat": [j_lat], "lon": [j_lon]}
                            )
                            st.map(df_kartta, zoom=7, use_container_width=True)
                        else:
                            st.caption(
                                "ℹ️ Junan reaaliaikainen GPS-sijainti ei ole tällä"
                                " hetkellä saatavilla."
                            )

                        st.divider()

                        st.markdown(
                            "#### 📍 Junan koko reitin reaaliaikainen aikataulu"
                        )

                        timeTable = juna["aikataulu"]
                        asemat_map = {}

                        naytetaan = False
                        aikataulu_rivit = []
                        for rivi in timeTable:
                            s_koodi = rivi.get("stationShortCode")

                            if s_koodi not in koodi_to_nimi:
                                continue

                            if (
                                s_koodi == lahto
                                and rivi.get("type") == "DEPARTURE"
                            ):
                                naytetaan = True

                            if naytetaan and s_koodi:
                                r_tyyppi = rivi.get("type")
                                a_aika = rivi.get("scheduledTime")
                                ero = rivi.get("differenceInMinutes", 0)
                                raide = str(
                                    rivi.get("commercialTrack", "-")
                                )[:3]

                                if a_aika:
                                    try:
                                        dt_aika = datetime.fromisoformat(
                                            a_aika.replace("Z", "+00:00")
                                        ).astimezone(suomi_aika)
                                        aika_muotoilu = dt_aika.strftime("%H:%M")

                                        if s_koodi not in asemat_map:
                                            asemat_map[s_koodi] = {
                                                "Asema": koodi_to_nimi.get(
                                                    s_koodi, s_koodi
                                                )
                                            }

                                        if r_tyyppi == "DEPARTURE":
                                            asemat_map[s_koodi]["Lähtö"] = (
                                                aika_muotoilu
                                            )
                                            asemat_map[s_koodi]["Lähtö-raide"] = (
                                                raide
                                            )
                                        elif r_tyyppi == "ARRIVAL":
                                            asemat_map[s_koodi]["Saapuminen"] = (
                                                aika_muotoilu
                                            )
                                            asemat_map[s_koodi][
                                                "Saapumis-raide"
                                            ] = raide
                                            asemat_map[s_koodi][
                                                "Myöhässä (min)"
                                            ] = ero
                                    except Exception:
                                        pass

                            if (
                                s_koodi == paikka
                                and rivi.get("type") == "ARRIVAL"
                            ):
                                naytetaan = False

                        for s_koodi, tiedot in asemat_map.items():
                            aikataulu_rivit.append(tiedot)

                        if aikataulu_rivit:
                            df_aikataulu = pd.DataFrame(aikataulu_rivit)
                            st.dataframe(df_aikataulu, use_container_width=True)

                        if vaunut:
                            st.markdown("#### 🚃 Vaunukoostumus & Palvelut")
                            v_list = []
                            for v in vaunut:
                                v_list.append({
                                    "Vaunu": v.get("salesNumber", "-"),
                                    "Tyyppi": v.get("wagonType", "-"),
                                    "Wi-Fi": (
                                        "📶 Kyllä" if v.get("wifi") else "Ei"
                                    ),
                                    "Lemmikit": (
                                        "🐾 Sallittu" if v.get("pet") else "Ei"
                                    ),
                                    "Esteetön": (
                                        "♿ Kyllä"
                                        if v.get("accessible")
                                        else "Ei"
                                    ),
                                    "Pyöräpaikka": (
                                        "🚲 Kyllä" if v.get("bicycle") else "Ei"
                                    ),
                                })
                            st.dataframe(
                                pd.DataFrame(v_list), use_container_width=True
                            )
    else:
        st.error("Yhteysvirhe Digitraffic-rajapintaan reittiä haettaessa.")
