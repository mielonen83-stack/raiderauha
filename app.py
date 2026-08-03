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

              # Korvataan staattinen st.map interaktiivisella Folium-kartalla, joka päivittyy oikein
              try:
                import folium
                from streamlit_folium import st_folium

                m = folium.Map(
                    location=[j_lat, j_lon], zoom_start=8, control_scale=True
                )
                folium.CircleMarker(
                    location=[j_lat, j_lon],
                    radius=8,
                    color="red",
                    fill=True,
                    fill_color="red",
                    fill_opacity=0.8,
                    popup=f"Juna {t_tyyppi} {t_num} ({kmh_nopeus} km/h)",
                ).add_to(m)

                st_folium(m, height=300, use_container_width=True, key=f"map_{t_num}")
              except ImportError:
                # Varakoodi, jos kirjastoa ei ole asennettu
                df_kartta = pd.DataFrame({"lat": [j_lat], "lon": [j_lon]})
                st.map(df_kartta, zoom=7, use_container_width=True)
            else:
              st.caption(
                  "ℹ️ Junan reaaliaikainen GPS-sijainti ei ole tällä hetkellä"
                  " saatavilla."
              )
