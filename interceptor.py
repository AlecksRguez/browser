"""
Interceptor de URLs para bloquear anuncios y rastreadores.
Opera bloqueando peticiones a dominios conocidos de publicidad
antes de que salgan del navegador.
"""
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor

# Dominios de publicidad y rastreo conocidos
# Solo se bloquean los dominios específicos de ads/tracking,
# NO los dominios principales de redes sociales o servicios.
BLOCKED_DOMAINS = {
    # --- Google Ads ---
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "googletagservices.com",
    "adservice.google.com",
    "pagead2.googlesyndication.com",
    "fundingchoicesmessages.google.com",
    "tpc.googlesyndication.com",
    # Google Analytics (rastreo)
    "google-analytics.com",
    "ssl.google-analytics.com",
    # Google Tag Manager (rastreo)
    "googletagmanager.com",

    # --- Facebook / Meta Ads ---
    "connect.facebook.net",      # Pixel de rastreo de Facebook
    "an.facebook.com",           # Audience Network (red de anuncios)
    "graph.facebook.com",        # API de tracking

    # --- Twitter / X Ads ---
    "ads.twitter.com",
    "analytics.twitter.com",
    "static.ads-twitter.com",

    # --- Redes publicitarias principales ---
    "adnxs.com",                 # AppNexus / Xandr
    "advertising.com",           # AOL Advertising
    "ads.yahoo.com",
    "pubmatic.com",
    "rubiconproject.com",
    "openx.net",
    "openx.com",
    "criteo.com",
    "criteo.net",
    "taboola.com",
    "outbrain.com",
    "revcontent.com",
    "sharethrough.com",
    "appnexus.com",
    "casalemedia.com",
    "indexww.com",
    "sovrn.com",
    "spotxchange.com",
    "sizmek.com",
    "smartadserver.com",
    "turn.com",
    "adroll.com",
    "amazon-adsystem.com",
    "media.net",
    "zemanta.com",
    "yieldmo.com",
    "adsrvr.org",                # The Trade Desk
    "thetradedesk.com",
    "districtm.ca",
    "contextweb.com",
    "rhythmone.com",
    "lijit.com",
    "pulsepoint.com",
    "undertone.com",
    "nativo.net",
    "tribalfusion.com",
    "zedo.com",
    "yieldmanager.com",
    "tradedoubler.com",
    "valueclick.com",
    "valueclick.net",
    "bidswitch.net",
    "teads.tv",
    "mgid.com",
    "dianomi.com",
    "spoutable.com",
    "realmedia.com",
    "bannerconnect.net",
    "adblade.com",
    "adcolony.com",
    "emxdgt.com",
    "flashtalking.com",
    "lijit.com",
    "optimatics.com",
    "yieldlab.net",
    "xaxis.com",
    "w55c.net",
    "weborama.fr",
    "smartclip.net",

    # --- Anuncios en videos ---
    "springserve.com",
    "vindico.com",
    "vidazoo.com",
    "jwpltx.com",
    "iponweb.net",

    # --- Anuncios móviles ---
    "admob.com",
    "inmobi.com",
    "mopub.com",
    "tapjoy.com",
    "applovin.com",
    "fyber.com",
    "loopme.me",
    "smaato.net",
    "vserv.mobi",

    # --- Analytics / Rastreo de comportamiento ---
    "scorecardresearch.com",
    "comscore.com",
    "quantserve.com",
    "statcounter.com",
    "chartbeat.com",
    "hotjar.com",
    "mixpanel.com",
    "segment.com",
    "segment.io",
    "kissmetrics.com",
    "optimizely.com",
    "mouseflow.com",
    "inspectlet.com",
    "clicktale.net",
    "crazyegg.com",
    "fullstory.com",
    "luckyorange.com",
    "logrocket.com",
    "heap.io",
    "amplitude.com",
    "keen.io",
    "woopra.com",
    "intercom-attachments-1.com",

    # --- Data brokers / Targeting ---
    "demdex.net",
    "krxd.net",
    "mathtag.com",
    "bluekai.com",
    "exelator.com",
    "rlcdn.com",
    "rfihub.com",
    "everesttech.net",
    "addthis.com",
    "sharethis.com",
    "agkn.com",
    "neustar.biz",
    "semasio.net",
    "cxense.com",
    "parrable.com",
    "permutive.com",
    "crowdscience.com",
    "peer39.net",
    "owneriq.net",
    "skimlinks.com",

    # --- Otros rastreadores ---
    "bounceexchange.com",
    "moat.com",
    "moatads.com",
    "doubleverify.com",
    "adsafeprotected.com",
    "confiant.com",
    "fraudlogix.com",
    "geoedge.com",
    "integral-marketing.com",
    "pagefair.com",
}


class AdBlockInterceptor(QWebEngineUrlRequestInterceptor):
    """
    Intercepta y bloquea peticiones a dominios de anuncios y rastreo.
    Usa coincidencia por subdominio para máxima cobertura.
    """

    def __init__(self):
        super().__init__()
        self.blocked_domains = set(BLOCKED_DOMAINS)
        self.blocked_count = 0
        self.enabled = True

    def _is_blocked(self, host: str) -> bool:
        """
        Devuelve True si el host o alguno de sus dominios padre
        está en la lista negra.
        """
        if not host:
            return False
        if host in self.blocked_domains:
            return True
        # Verificar dominios padre: sub.example.com -> example.com -> com
        parts = host.split(".")
        for i in range(1, len(parts) - 1):
            if ".".join(parts[i:]) in self.blocked_domains:
                return True
        return False

    def interceptRequest(self, info):
        if not self.enabled:
            return
        host = info.requestUrl().host().lower()
        if self._is_blocked(host):
            info.block(True)
            self.blocked_count += 1
