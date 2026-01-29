from __future__ import annotations

# Shared UA/IP heuristics used by SQL filters and in-memory checks.

BROWSER_UA_INCLUDES = (
    "chrome/",
    "firefox/",
    "safari/",
    "edg/",
    "edge/",
    "opera/",
    "opr/",
    "msie ",
    "trident/",
)

BOT_UA_MARKERS = (
    "bot",
    "crawler",
    "spider",
    "curl",
    "python",
    "axios",
    "node-fetch",
    "go-http-client",
    "java/",
    "apache-httpclient",
    "libwww-perl",
    "wget",
    "headlesschrome",
)

DATACENTER_IP_PREFIXES = (
    "3.",
    "13.",
    "18.",
    "20.",
    "23.",
    "34.",
    "35.",
    "40.",
    "45.",
    "51.",
    "52.",
    "54.",
    "64.",
    "66.",
    "74.125.",
    "104.",
    "108.",
    "142.250.",
    "142.251.",
    "157.",
    "168.63.",
    "172.253.",
    "173.194.",
    "209.85.",
    "216.58.",
    "216.239.",
)
