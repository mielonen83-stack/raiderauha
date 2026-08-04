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
st.sidebar.markdown("### 🌐 Language / Kieli")
valittu_kieli = st.sidebar.selectbox("Valitse kieli / Select language", ["Suomi", "English"])
t = TEKSTIT[valittu_kieli]

st.set_page_config(
    page_title=t["page_title"],
    page_icon="🚆",
    layout="wide",
)

# --- RAIDETUTKA DESIGN SYSTEM: "LAITURINÄYTTÖ" (SPLIT-FLAP) -TEEMA ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

    :root {
        --rt-bg: #F1F3F1;
        --rt-surface: #FFFFFF;
        --rt-surface-alt: #E8EDEA;
        --rt-ink: #101A18;
        --rt-ink-muted: #57655F;
        --rt-rail-deep: #0D2E2A;
        --rt-rail-deep-2: #123B34;
        --rt-amber: #E8A33D;
        --rt-signal: #1F7A5C;
        --rt-alert: #C1443C;
        --rt-border: #DDE3DF;
        --rt-radius: 10px;
        --rt-font-display: 'Big Shoulders Display', sans-serif;
        --rt-font-body: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        --rt-font-mono: 'IBM Plex Mono', 'SFMono-Regular', monospace;
    }

    html, body, .stApp {
        background-color: var(--rt-bg) !important;
        color: var(--rt-ink) !important;
        font-family: var(--rt-font-body) !important;
    }

    .stApp * {
        font-family: var(--rt-font-body);
    }

    h1, h2, h3, h4 {
        font-family: var(--rt-font-display) !important;
        color: var(--rt-rail-deep) !important;
        letter-spacing: 0.01em;
        font-weight: 700 !important;
    }
    h1 {
        font-size: clamp(1.65rem, 5vw, 2.4rem) !important;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    h2 { font-size: clamp(1.25rem, 3.6vw, 1.55rem) !important; }
    h3, h4 { font-size: clamp(1.05rem, 3vw, 1.2rem) !important; }

    h1::after {
        content: "";
        display: block;
        width: 64px;
        height: 3px;
        background: var(--rt-amber);
        margin-top: 6px;
        border-radius: 2px;
    }

    .metric-card {
        background-color: var(--rt-surface);
        border: 1px solid var(--rt-border);
        border-left: 3px solid var(--rt-rail-deep);
        padding: 16px 18px;
        border-radius: var(--rt-radius);
        box-shadow: 0 1px 2px rgba(13, 46, 42, 0.05);
        margin-bottom: 12px;
    }
    .wagon-card {
        background-color: var(--rt-surface);
        border: 1px solid var(--rt-border);
        padding: 14px 10px;
        border-radius: var(--rt-radius);
        text-align: center;
        margin-bottom: 8px;
        box-shadow: 0 1px 2px rgba(13, 46, 42, 0.04);
        transition: box-shadow 0.15s ease, border-color 0.15s ease;
    }
    .wagon-card:hover {
        border-color: var(--rt-rail-deep);
        box-shadow: 0 3px 10px rgba(13, 46, 42, 0.08);
    }

    [data-testid="stSidebar"] {
        background-color: var(--rt-rail-deep) !important;
        border-right: none;
    }
    [data-testid="stSidebar"] * {
        color: #EAF2EF !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(234, 242, 239, 0.15) !important;
        margin: 0.8rem 0 !important;
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea,
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: var(--rt-rail-deep-2) !important;
        border: 1px solid rgba(234, 242, 239, 0.25) !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] [data-testid="stCheckbox"] label {
        color: #EAF2EF !important;
    }

    .stButton button, .stLinkButton a, .stFormSubmitButton button {
        width: 100% !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        letter-spacing: 0.01em;
        border: 1px solid var(--rt-border) !important;
        transition: transform 0.08s ease, box-shadow 0.15s ease;
        min-height: 44px;
    }
    .stButton button:active, .stLinkButton a:active {
        transform: scale(0.98);
    }
    [data-testid="stSidebar"] .stButton button,
    [data-testid="stSidebar"] .stLinkButton a {
        background-color: var(--rt-rail-deep-2) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(234, 242, 239, 0.25) !important;
    }
    [data-testid="stSidebar"] .stButton button:hover {
        border-color: var(--rt-amber) !important;
        color: var(--rt-amber) !important;
    }
    button[kind="primary"], .stButton button[kind="primary"] {
        background-color: var(--rt-amber) !important;
        color: var(--rt-rail-deep) !important;
        border: 1px solid var(--rt-amber) !important;
        font-weight: 700 !important;
    }
    button[kind="primary"]:hover {
        filter: brightness(1.06);
    }

    [data-testid="stTabs"] button[data-baseweb="tab"] {
        font-family: var(--rt-font-display);
        font-weight: 700;
        font-size: 1rem;
        color: var(--rt-ink-muted);
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--rt-rail-deep) !important;
    }
    [data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        background-color: var(--rt-amber) !important;
        height: 3px !important;
    }
    [data-baseweb="tab-border"] { background-color: var(--rt-border) !important; }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--rt-border);
        border-radius: var(--rt-radius);
        overflow: hidden;
    }
    [data-testid="stDataFrame"] * {
        font-family: var(--rt-font-mono) !important;
        font-size: 0.86rem !important;
    }
    [data-testid="stDataFrameResizable"] div[role="columnheader"] {
        background-color: var(--rt-surface-alt) !important;
        font-family: var(--rt-font-body) !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        font-size: 0.72rem !important;
        letter-spacing: 0.04em;
        color: var(--rt-ink-muted) !important;
    }

    [data-testid="stAlert"] {
        border-radius: var(--rt-radius) !important;
        border: 1px solid transparent;
        font-size: 0.92rem;
    }
    [data-testid="stAlertContentSuccess"] { color: var(--rt-signal) !important; }
    [data-testid="stAlertContentError"] { color: var(--rt-alert) !important; }

    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div,
    .stDateInput input {
        border-radius: 8px !important;
        border: 1px solid var(--rt-border) !important;
    }

    .stApp p, .stApp li, .stApp span, .stApp label {
        color: var(--rt-ink);
    }

    .rt-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-family: var(--rt-font-mono);
        font-weight: 600;
        font-size: 0.82rem;
        padding: 3px 10px;
        border-radius: 999px;
        border: 1px solid var(--rt-border);
        background: var(--rt-surface-alt);
    }
    .rt-chip.ok { color: var(--rt-signal); border-color: rgba(31,122,92,0.35); }
    .rt-chip.warn { color: var(--rt-amber); border-color: rgba(232,163,61,0.4); }
    .rt-chip.alert { color: var(--rt-alert); border-color: rgba(193,68,60,0.35); }

    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-thumb { background: var(--rt-rail-deep-2); border-radius: 8px; }

    @media (max-width: 640px) {
        .block-container {
            padding-left: 0.9rem !important;
            padding-right: 0.9rem !important;
            padding-top: 1.2rem !important;
        }
        h1::after { width: 44px; }
        .metric-card, .wagon-card {
            padding: 12px !important;
        }
        [data-testid="stDataFrame"] * {
            font-size: 0.78rem !important;
        }
        .stButton button, .stLinkButton a, .stFormSubmitButton button {
            font-size: 0.92rem !important;
            padding: 0.6rem 0.8rem !important;
        }
        [data-testid="stTabs"] button[data-baseweb="tab"] {
            font-size: 0.88rem;
            padding: 8px 10px;
        }
        [data-testid="column"] {
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }
    }

    @media (prefers-reduced-motion: reduce) {
        * { transition: none !important; animation: none !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- GOOGLE ANALYTICS & EVÄSTEBANNERI (COOKIE CONSENT) ---
GA_MEASUREMENT_ID = "G-ET3PWNZCXH"

cookie_banner_script = f"""
    <script>
      // Tarkistetaan onko evästeet jo hyväksytty
      function checkCookieConsent() {{
          return localStorage.getItem("raidetutka_cookie_consent");
      }}

      // Ladataan Google Analytics vain jos hyväksytty
      function loadGoogleAnalytics() {{
          if (window.gaLoaded) return;
          window.gaLoaded = true;
          
          var script = document.createElement('script');
          script.async = true;
          script.src = 'https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}';
          document.head.appendChild(script);

          window.dataLayer = window.dataLayer || [];
          function gtag(){{dataLayer.push(arguments);}}
          gtag('js', new Date());
          gtag('config', '{GA_MEASUREMENT_ID}');
      }}

      // Luodaan evästebanneri HTML, jos ei vielä vastattu
      function createCookieBanner() {{
          if (checkCookieConsent()) {{
              if (checkCookieConsent() === "accepted") {{
                  loadGoogleAnalytics();
              }}
              return;
          }}

          if (document.getElementById('cookie-banner')) return;

          var banner = document.createElement('div');
          banner.id = 'cookie-banner';
          banner.style.cssText = 'position: fixed; bottom: 0; left: 0; width: 100%; background-color: #0D2E2A; color: #FFFFFF; padding: 16px 20px; box-shadow: 0 -4px 15px rgba(0,0,0,0.2); z-index: 999999; display: flex; flex-direction: column; gap: 10px; font-family: "IBM Plex Sans", sans-serif; box-sizing: border-box;';
          
          var textContainer = document.div;
          banner.innerHTML = `
              <div style="max-width: 1200px; margin: 0 auto; width: 100%; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 15px;">
                  <div style="font-size: 0.9rem; line-height: 1.4; flex: 1; min-width: 280px;">
                      🍪 Käytämme evästeitä parantaaksemme käyttökokemusta ja analysoidaksemme sivuston liikennettä (Google Analytics). Hyväksymällä evästeet autat meitä kehittämään Raidetutkaa.
                  </div>
                  <div style="display: flex; gap: 10px; flex-shrink: 0;">
                      <button id="cookie-reject" style="background-color: transparent; border: 1px solid rgba(234,242,239,0.4); color: #FFFFFF; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem;">Vain pakolliset</button>
                      <button id="cookie-accept" style="background-color: #E8A33D; border: none; color: #0D2E2A; padding: 8px 18px; border-radius: 6px; cursor: pointer; font-weight: 700; font-size: 0.85rem;">Hyväksy kaikki</button>
                  </div>
              </div>
          `;

          document.body.appendChild(banner);

          document.getElementById('cookie-accept').onclick = function() {{
              localStorage.setItem("raidetutka_cookie_consent", "accepted");
              loadGoogleAnalytics();
              banner.remove();
          }};

          document.getElementById('cookie-reject').onclick = function() {{
              localStorage.setItem("raidetutka_cookie_consent", "rejected");
              banner.remove();
          }};
      }}

      if (document.readyState === 'complete') {{
          createCookieBanner();
      }} else {{
          window.addEventListener('load', createCookieBanner);
      }}
    </script>
    <meta name="description" content="Raidetutka is a professional train tracker with real-time VR schedules, traffic disruptions and live locations." />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
"""
components.html(cookie_banner_script, height=0, width=0)

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

st.sidebar.divider()
st.sidebar.caption(t["footer"])

# --- PÄÄSIVU ---
st.title(t["pääotsikko"])
st.markdown(t["pääalaotsikko"])
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
                                else ('<span style="color: #adb5bd;">Standard wagon</span>' if valittu_kieli == "English" else '<span style="color: #adb5bd;">Perusvaunu</span>')
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
                    f"🚆 **{j['tyyppi']} {j['numero']}**\n\n{lahto_perille_txt}\n{matka_info}\nStatus: {tila_tekstri if 'tila_tekstri' in locals() else tila_teksti}\n*{historia_teksti}*"
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
