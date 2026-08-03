import streamlit as st
import requests
from datetime import datetime, date
from zoneinfo import ZoneInfo
from openai import OpenAI

# Sivun perusasetukset
st.set_page_config(
    page_title="Raiderauha – Älykäs Junatutka & Rauhavahti", 
    page_icon="🚆", 
    layout="wide"
)

# Alustetaan muistit sessionstateen
if "rauharaportit" not in st.session_state:
    st.session_state.rauharaportit = {}

if "suosikit" not in st.session_state:
    st.session_state.suosikit = [("Helsinki (HKI)", "Joensuu (JNS)")]

# Alustetaan OpenAI turvallisesti Streamlitin secrets-asetuksesta
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    ai_kaytossa = True
except:
    ai_kaytossa = False

# Haetaan asemat Digitrafficin rajapinnasta
@st.cache_data
def hae_asemat():
    url = "https://rata.digitraffic.fi/api/v1/metadata/stations"
    try:
        vastaus = requests.get(url)
        if vastaus.status_code == 200:
            asemat = vastaus.json()
            matkustajasektori = [a for a in asemat if a.get('passengerTraffic') == True]
            asema_lista = {}
            for a in matkustajasektori:
                nimi = f"{a['stationName']} ({a['stationShortCode']})"
                asema_lista[nimi] = {
                    "koodi": a['stationShortCode'],
                    "lat": a.get('latitude'),
                    "lon": a.get('longitude')
                }
            return asema_lista
    except:
        pass
    return {
        "Helsinki (HKI)": {"koodi": "HKI", "lat": 60.1719, "lon": 24.9414}, 
        "Joensuu (JNS)": {"koodi": "JNS", "lat": 62.5998, "lon": 29.7634},
        "Tampere (TPE)": {"koodi": "TPE", "lat": 61.5033, "lon": 23.7733}
    }

asema_dict = hae_asemat()
asema_nimet = list(asema_dict.keys())

# --- SIVUPALKKI & ASETUKSET ---
st.sidebar.header("🎛️ Matkan tiedot & Asetukset")

# Pikavalinnat / Suosikit
if st.session_state.suosikit:
    st.sidebar.markdown("### ⭐ Suosikkireitit")
    for idx, (s_lahto, s_paikka) in enumerate(st.session_state.suosikit):
        if st.sidebar.button(f"{s_lahto} ➔ {s_paikka}", key=f"suosikki_{idx}"):
            st.session_state.valittu_lahto = s_lahto
            st.session_state.valittu_paikka = s_paikka

# Valinnat
oletus_lahto_idx = asema_nimet.index(st.session_state.get("valittu_lahto", "Helsinki (HKI)")) if st.session_state.get("valittu_lahto", "Helsinki (HKI)") in asema_nimet else 0
oletus_paikka_idx = asema_nimet.index(st.session_state.get("valittu_paikka", "Joensuu (JNS)")) if st.session_state.get("valittu_paikka", "Joensuu (JNS)") in asema_nimet else 1

valittu_lahto_nimi = st.sidebar.selectbox("Lähtöasema", asema_nimet, index=oletus_lahto_idx)
valittu_paikka_nimi = st.sidebar.selectbox("Määränpää", asema_nimet, index=oletus_paikka_idx)

# Tallenna suosikkeihin -painike
if st.sidebar.button("❤️ Tallenna suosikkireitiksi"):
    uusi_suosikki = (valittu_lahto_nimi, valittu_paikka_nimi)
    if uusi_suosikki not in st.session_state.suosikit:
        st.session_state.suosikit.append(uusi_suosikki)
        st.sidebar.success("Reitti tallennettu suosikkeihin!")

valittu_pvm = st.sidebar.date_input("Matkustuspäivä", value=date.today())

lahto = asema_dict[valittu_lahto_nimi]["koodi"]
paikka = asema_dict[valittu_paikka_nimi]["koodi"]

hakunappi = st.sidebar.button("🔍 Etsi junat ja Rauhavahti", type="primary")

st.title("🚆 Raiderauha")
st.markdown("##### *Reaaliaikainen junatutka, tekoälyn rauha-alueet, sää ja matkustajien live-raportit*")
st.divider()

if hakunappi:
    
    st.markdown(f"### 🗺️ Reitti: **{valittu_lahto_nimi}** ➔ **{valittu_paikka_nimi}** ({valittu_pvm.strftime('%d.%m.%Y')})")
    
    # HAE SÄÄÄNNÖT MÄÄRÄNPÄÄHÄN
    p_lat = asema_dict[valittu_paikka_nimi].get("lat")
    p_lon = asema_dict[valittu_paikka_nimi].get("lon")
    if p_lat and p_lon:
        try:
            sää_url = f"https://api.open-meteo.com/v1/forecast?latitude={p_lat}&longitude={p_lon}&current=temperature_2m,weather_code"
            s_vast = requests.get(sää_url).json()
            lampo = s_vast['current']['temperature_2m']
            st.success(f"🌤️ **Sää määränpäässä ({valittu_paikka_nimi.split(' ')[0]}):** {lampo}°C")
        except:
            pass

    st.info("📡 Haetaan aikatauluja ja Digitrafficin tietoja...")
    st.divider()
    
    url = f"https://rata.digitraffic.fi/api/v1/live-trains/station/{lahto}/{paikka}?departure_date={valittu_pvm.strftime('%Y-%m-%d')}"
    
    with st.spinner("Etsitään sopivia junavuoroja..."):
        vastaus = requests.get(url)
    
    if vastaus.status_code == 200:
        junat = vastaus.json()
        
        if not isinstance(junat, list) or not junat:
            st.warning("⚠️ Valitsemallesi päivälle ja välille ei löytynyt suoria junavuoroja.")
        else:
            aktiiviset_junat = []
            suomi_aika = ZoneInfo("Europe/Helsinki")
            nyt = datetime.now(suomi_aika)
            
            for juna in junat:
                if not isinstance(juna, dict) or juna.get('cancelled', False):
                    continue
                
                train_num = juna.get('trainNumber')
                train_type = juna.get('trainType')
                timeTable = juna.get('timeTableRows', [])
                
                lahto_aika_str = ""
                saapumis_aika_str = ""
                lahto_dt = None
                saapumis_dt = None
                
                for rivi in timeTable:
                    if rivi.get('stationShortCode') == lahto and rivi.get('type') == 'DEPARTURE':
                        aika_str = rivi.get('scheduledTime')
                        if aika_str:
                            dt_obj = datetime.fromisoformat(aika_str.replace('Z', '+00:00')).astimezone(suomi_aika)
                            lahto_aika_str = dt_obj.strftime('%H:%M')
                            lahto_dt = dt_obj
                    if rivi.get('stationShortCode') == paikka and rivi.get('type') == 'ARRIVAL':
                        aika_str = rivi.get('scheduledTime')
                        if aika_str:
                            dt_obj = datetime.fromisoformat(aika_str.replace('Z', '+00:00')).astimezone(suomi_aika)
                            saapumis_aika_str = dt_obj.strftime('%H:%M')
                            saapumis_dt = dt_obj
                
                if lahto_dt and saapumis_dt:
                    is_today = (valittu_pvm == date.today())
                    
                    if not is_today or (lahto_dt >= nyt or (lahto_dt <= nyt <= saapumis_dt)):
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
                            "tila": tila
                        })
            
            if not aktiiviset_junat:
                st.warning("⚠️ Valitsemallesi päivälle ei löytynyt enää aktiivisia/tulevia vuoroja tällä välillä.")
            else:
                st.success(f"Löytyi {len(aktiiviset_junat)} junavuoroa!")
                
                for juna in aktiiviset_junat:
                    t_num = juna["numero"]
                    t_tyyppi = juna["tyyppi"]
                    status_teksti = juna["tila"]
                    
                    with st.expander(f"🚆 {t_tyyppi} {t_num} | Lähtö klo {juna['lahto']} ➔ Perillä klo {juna['saapuminen']} ({status_teksti})"):
                        
                        st.markdown("#### 📍 Junan aikataulu ja myöhästymiset")
                        
                        timeTable = juna["aikataulu"]
                        asemat_map = {}
                        
                        naytetaan = False
                        for rivi in timeTable:
                            s_koodi = rivi.get('stationShortCode')
                            if s_koodi == lahto and rivi.get('type') == 'DEPARTURE':
                                naytetaan = True
                            
                            if naytetaan and s_koodi:
                                a_aika = rivi.get('scheduledTime')
                                myohassa = rivi.get('differenceInMinutes', 0)
                                onko_mennyt = rivi.get('actualTime') is not None
                                
                                if a_aika:
                                    dt_obj = datetime.fromisoformat(a_aika.replace('Z', '+00:00')).astimezone(suomi_aika)
                                    klo = dt_obj.strftime('%H:%M')
                                    if s_koodi not in asemat_map:
                                        asemat_map[s_koodi] = {
                                            "asema": s_koodi,
                                            "aika": klo,
                                            "myohassa": myohassa,
                                            "aktiivinen": onko_mennyt
                                        }
                                    else:
                                        if onko_mennyt:
                                            asemat_map[s_koodi]["aktiivinen"] = True
                            
                            if s_koodi == paikka and rivi.get('type') == 'ARRIVAL':
                                break
                        
                        asemat_matkalla = list(asemat_map.values())
                        
                        if asemat_matkalla:
                            cols = st.columns(min(len(asemat_matkalla), 6))
                            for idx, asema_info in enumerate(asemat_matkalla[:6]):
                                with cols[idx]:
                                    tila_emoji = "✅" if asema_info["aktiivinen"] else "⏳"
                                    myoha_str = f" (+{asema_info['myohassa']} min)" if asema_info['myohassa'] > 0 else ""
                                    st.metric(
                                        label=f"{tila_emoji} {asema_info['asema']}",
                                        value=asema_info["aika"],
                                        delta=myoha_str if myoha_str else None
                                    )
                        
                        # --- JATKOYHTEYKSIEN TARKISTUS ---
                        viimeinen_asema = asemat_matkalla[-1] if asemat_matkalla else None
                        if viimeinen_asema and viimeinen_asema["myohassa"] > 0:
                            st.warning(f"⚠️ **Vaihdot vaarassa:** Juna on tällä hetkellä noin {viimeinen_asema['myohassa']} minuuttia myöhässä perille saapuessa. Tarkista jatkoyhteydet!")
                        else:
                            st.success("✅ **Vaihtoyhteydet:** Juna näyttäisi olevan aikataulussaan, vaihto jatkokulkuun sujuu hyvin.")

                        st.divider()
                        
                        # --- TEKOÄLYN RAUHAVAHTI ---
                        if ai_kaytossa:
                            with st.spinner("🤖 Tekoälyn Rauhavahti analysoi junaa..."):
                                try:
                                    prompt = f"Olet VR:n matkaoppaan assistentti (Rauhavahti). Anna lyhyt ja oivaltava rauhoittava arvio ja vaunusuositus junalle {t_tyyppi} {t_num} reitillä {valittu_lahto_nimi} - {valittu_paikka_nimi}."
                                    completion = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], max_tokens=150)
                                    st.info(f"🤖 **Tekoälyn Rauhavahti-analyysi:**\n\n{completion.choices[0].message.content}")
                                except:
                                    pass
                        
                        # --- JOUKOISTETUT MATKUSTAJIEN RAUHARAPORTIT ---
                        st.markdown("#### 🗣️ Matkustajien live-rauharaportit")
                        
                        uusi_raportti = st.text_input(f"Ilmoita tunnelma tai vaunutieto tälle junalle ({t_num}):", key=f"inp_{t_num}", placeholder="Esim. Vaunu 3 on superhiljainen, vaunu 5 täynnä porukkaa")
                        if st.button("Lähetä raportti", key=f"btn_{t_num}"):
                            if uusi_raportti:
                                if t_num not in st.session_state.rauharaportit:
                                    st.session_state.rauharaportit[t_num] = []
                                st.session_state.rauharaportit[t_num].append(uusi_raportti)
                                st.success("Kiitos! Raporttisi lisättiin muiden nähtäväksi.")
                        
                        if t_num in st.session_state.rauharaportit and st.session_state.rauharaportit[t_num]:
                            for r in st.session_state.rauharaportit[t_num]:
                                st.write(f"💬 *\"{r}\"*")
                        else:
                            st.caption("Ei vielä matkustajien raportteja tälle junalle. Ole ensimmäinen!")
                        
                        st.divider()
                        
                        # --- VAUNUKARTTA ---
                        st.markdown("#### 🗺️ Vaunukartta ja sisäiset rauha-alueet")
                        
                        vaunut = []
                        komp_url = f"https://rata.digitraffic.fi/api/v1/compositions/{t_num}"
                        try:
                            komp_vastaus = requests.get(komp_url)
                            if komp_vastaus.status_code == 200:
                                komp_data = komp_vastaus.json()
                                sections = komp_data.get('journeySections', [])
                                if sections:
                                    vaunut = sections[0].get('wagons', [])
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
                                    {"wagonType": "InterCity", "salesNumber": "7"}
                                ]
                            else:
                                vaunut = [
                                    {"wagonType": "Ravintola", "salesNumber": "1"},
                                    {"wagonType": "Vaunu", "salesNumber": "2"},
                                    {"wagonType": "Vaunu", "salesNumber": "3"}
                                ]
                        
                        v_cols = st.columns(len(vaunut) if len(vaunut) <= 8 else 8)
                        for idx, v in enumerate(vaunut[:8]):
                            v_nimi = v.get('wagonType', 'Vaunu')
                            v_nro = v.get('salesNumber', str(idx+1))
                            with v_cols[idx]:
                                st.metric(label=f"Vaunu {v_nro}", value=v_nimi)
                        
                        # Vaunun sisäinen rauha-aluekartta
                        st.markdown("---")
                        st.markdown("#### 💺 Vaunun sisäinen rauha-kartta")
                        
                        v_col1, v_col2, v_col3, v_col4, v_col5 = st.columns(5)
                        with v_col1:
                            st.error("🔴 **Vessa / Ovi**\n\n*Vilkas*")
                        with v_col2:
                            st.warning("🟠 **Päätypaikat**\n\n*Melko vilkas*")
                        with v_col3:
                            st.success("🟢 **Keskiosa**\n\n*Erittäin rauhallinen*\n⭐ **Paras**")
                        with v_col4:
                            st.warning("🟠 **Päätypaikat**\n\n*Melko vilkas*")
                        with v_col5:
                            st.error("🔴 **Vessa / Ovi**\n\n*Vilkas*")

    else:
        st.error("Virhe haettaessa junatietoja.")
else:
    st.info("👈 Valitse asemat ja matkustuspäivä sivupalkista, ja klikkaa **Etsi junat ja Rauhavahti**.")
