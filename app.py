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
                                
                                # Tarkistetaan suoraan Digitrafficin datasta, onko juna oikeasti käynyt tällä asemalla
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
                            for asema_info in asemat_matkalla:
                                tila_emoji = "✅" if asema_info["aktiivinen"] else "⏳"
                                myoha_str = f" (+{asema_info['myohassa']} min myöhässä)" if asema_info['myohassa'] > 0 else ""
                                st.write(f"{tila_emoji} **{asema_info['asema']}** – klo {asema_info['aika']}{myoha_str}")
