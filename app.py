if st.session_state.haku_tehty:
    st.markdown(
        f"### 🗺️ Reittihaku: **{valittu_lahto_nimi}** ➔ **{valittu_paikka_nimi}** ({valittu_pvm.strftime('%d.%m.%Y')})"
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
            st.success(f"🌤️ **Sää määränpäässä ({valittu_paikka_nimi.split(' ')[0]}):** {lampo}°C")
        except Exception:
            pass

    if l_lat and l_lon and p_lat and p_lon:
        R = 6371
        dLat = radians(p_lat - l_lat)
        dLon = radians(p_lon - l_lon)
        a = sin(dLat / 2) ** 2 + cos(radians(l_lat)) * cos(radians(p_lat)) * sin(dLon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        etaisyys_km = R * c
        todellinen_arvio_km = etaisyys_km * 1.2
        auton_paastot_kg = (todellinen_arvio_km * 120) / 1000
        saastetty_co2 = auton_paastot_kg

        st.info(
            f"🌱 **Ympäristövaikutus:** Junamatkustaminen tällä noin **{todellinen_arvio_km:.0f} km** matkalla säästää arviolta **{saastetty_co2:.1f} kg CO₂** -päästöjä maantiekuljetukseen verrattuna."
        )

    st.markdown("Valitse alta haluamasi junavuoro nähdäksesi tarkat tiedot ja reaaliaikaisen sijainnin:")

    pvm_str = valittu_pvm.strftime("%Y-%m-%d")
    # Haetaan kyseisen päivän kaikki junat virallisesta reittirajapinnasta
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

        for juna in junat:
            j_num = juna.get("trainNumber")
            if j_num in naytetyt_reitti_junat:
                continue
            
            timeTable = juna.get("timeTableRows", [])
            asemat_koodit = [r.get("stationShortCode") for r in timeTable]
            
            # Tarkistetaan, että sekä lähtö että määränpää ovat junan reitillä ja oikeassa järjestyksessä
            if lahto in asemat_koodit and paikka in asemat_koodit:
                lahto_idx = asemat_koodit.index(lahto)
                paikka_idx = asemat_koodit.index(paikka)
                if lahto_idx > paikka_idx:
                    continue  # Väärä suunta
            else:
                continue

            naytetyt_reitti_junat.add(j_num)
            t_tyyppi = juna.get("trainType", "Juna")
            peruttu = juna.get("cancelled", False)

            lahto_aika_str = ""
            perille_aika_str = ""
            myohassa = 0

            for rivi in timeTable:
                if rivi.get("stationShortCode") == lahto and rivi.get("type") == "DEPARTURE":
                    sch = rivi.get("scheduledTime")
                    diff = rivi.get("differenceInMinutes", 0)
                    if diff:
                        myohassa = diff
                    if sch:
                        try:
                            dt = datetime.fromisoformat(sch.replace("Z", "+00:00")).astimezone(suomi_aika)
                            lahto_aika_str = dt.strftime("%H:%M")
                        except Exception:
                            pass
                if rivi.get("stationShortCode") == paikka and rivi.get("type") == "ARRIVAL":
                    sch = rivi.get("scheduledTime")
                    if sch:
                        try:
                            dt = datetime.fromisoformat(sch.replace("Z", "+00:00")).astimezone(suomi_aika)
                            perille_aika_str = dt.strftime("%H:%M")
                        except Exception:
                            pass

            aktiiviset_junat.append({
                "numero": j_num,
                "tyyppi": t_tyyppi,
                "lahto": lahto_aika_str,
                "perille": perille_aika_str,
                "myohassa": myohassa,
                "peruttu": peruttu
            })

        if aktiiviset_junat:
            st.markdown("#### Löytyneet junavuorot:")
            for j in aktiiviset_junat:
                tila_teksti = "Peruttu ❌" if j["peruttu"] else (f"Myöhässä +{j['myohassa']} min ⚠️" if j['myohassa'] > 0 else "Ajallaan 🟢")
                
                col_j1, col_j2, col_j3 = st.columns([3, 3, 2])
                with col_j1:
                    st.markdown(f"**🚆 {j['tyyppi']} {j['numero']}**")
                    st.caption(f"Lähtö: {j['lahto']} ➔ Perillä: {j['perille']}")
                with col_j2:
                    st.markdown(f"Tila: **{tila_teksti}**")
                with col_j3:
                    if st.button("Valitse & Seuraa", key=f"valitse_juna_{j['numero']}"):
                        st.session_state.valittu_live_juna = str(j['numero'])
                        st.rerun()
                st.divider()
        else:
            st.warning("Ei suoria junavuoroja tälle välille valittuna päivänä.")
