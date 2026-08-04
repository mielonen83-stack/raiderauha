# --- GOOGLE ANALYTICS & EVÄSTEBANNERI (PÄÄSIVUN TASOLLA) ---
GA_MEASUREMENT_ID = "G-ET3PWNZCXH"

cookie_banner_script = f"""
    <script>
      // Suoritetaan pääsivun (parent) DOM:ssa, jotta Analytics näkee oikean osoitteen ja tapahtumat
      const doc = window.parent.document;

      function checkCookieConsent() {{
          return doc.defaultView.localStorage.getItem("raidetutka_cookie_consent");
      }}

      function loadGoogleAnalytics() {{
          if (doc.defaultView.gaLoaded) return;
          doc.defaultView.gaLoaded = true;
          
          var script = doc.createElement('script');
          script.async = true;
          script.src = 'https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}';
          doc.head.appendChild(script);

          doc.defaultView.dataLayer = doc.defaultView.dataLayer || [];
          function gtag(){{doc.defaultView.dataLayer.push(arguments);}}
          doc.defaultView.gtag = gtag;
          gtag('js', new Date());
          gtag('config', '{GA_MEASUREMENT_ID}');
      }}

      function createCookieBanner() {{
          if (checkCookieConsent()) {{
              if (checkCookieConsent() === "accepted") {{
                  loadGoogleAnalytics();
              }}
              return;
          }}

          if (doc.getElementById('cookie-banner')) return;

          var banner = doc.createElement('div');
          banner.id = 'cookie-banner';
          banner.style.cssText = 'position: fixed; bottom: 0; left: 0; width: 100%; background-color: #0D2E2A; color: #FFFFFF; padding: 16px 20px; box-shadow: 0 -4px 15px rgba(0,0,0,0.2); z-index: 999999; display: flex; flex-direction: column; gap: 10px; font-family: "IBM Plex Sans", sans-serif; box-sizing: border-box;';
          
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

          doc.body.appendChild(banner);

          doc.getElementById('cookie-accept').onclick = function() {{
              doc.defaultView.localStorage.setItem("raidetutka_cookie_consent", "accepted");
              loadGoogleAnalytics();
              banner.remove();
          }};

          doc.getElementById('cookie-reject').onclick = function() {{
              doc.defaultView.localStorage.setItem("raidetutka_cookie_consent", "rejected");
              banner.remove();
          }};
      }}

      if (doc.readyState === 'complete') {{
          createCookieBanner();
      }} else {{
          doc.defaultView.addEventListener('load', createCookieBanner);
      }}
    </script>
"""
components.html(cookie_banner_script, height=0, width=0)
