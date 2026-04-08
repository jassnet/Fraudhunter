from __future__ import annotations

from ipaddress import ip_address, ip_network

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

DATACENTER_IP_CIDRS = (
    "3.5.140.0/22",
    "13.124.0.0/14",
    "18.176.0.0/15",
    "20.33.0.0/16",
    "34.84.0.0/15",
    "34.96.0.0/20",
    "35.72.0.0/13",
    "40.74.0.0/15",
    "52.192.0.0/11",
    "54.64.0.0/10",
    "104.154.0.0/15",
    "104.196.0.0/14",
    "142.250.0.0/15",
    "142.251.0.0/16",
    "168.63.129.16/32",
    "172.253.0.0/16",
    "173.194.0.0/16",
    "209.85.128.0/17",
    "216.58.192.0/19",
    "216.239.32.0/19",
)

DATACENTER_IP_NETWORKS = tuple(ip_network(value) for value in DATACENTER_IP_CIDRS)
DATACENTER_IP_PREFIXES = tuple(sorted({cidr.split("/")[0].rsplit(".", 1)[0] + "." for cidr in DATACENTER_IP_CIDRS}))


def is_datacenter_ip(value: str) -> bool:
    if not value:
        return False
    try:
        candidate = ip_address(value)
    except ValueError:
        return False
    return any(candidate in network for network in DATACENTER_IP_NETWORKS)
