"""Fetch and decode a RoboVac's cloud floor-plan map (X8-Pro-class devices).

Reverse engineered 2026-10-25 against a Eufy T2276 (X8 Pro SES). The map
flows over plain HTTPS to a Tuya/AWS S3-compatible object store, not over
local DPS, not over MQTT:

    1. ``thing.m.dev.storage.config.get`` (v1.0, plain JSON postData, same
       transport as every other TuyaAPISession call) returns short-lived
       AWS STS credentials (access key, secret key, session token), a
       bucket name, and a per-device path prefix.
    2. The current room layout always lives at
       ``<bucket>.<endpoint>/<path prefix>/common/layout/lay.bin``.
    3. That URL needs an AWS SigV4 *query* signature. Tuya's "region" is a
       literal domain string (e.g. ``tuyaeu.com``), not a real AWS region,
       so a full boto3 S3 client refuses to use it; this module signs the
       request by hand with only ``hashlib``/``hmac`` (stdlib).
    4. The file itself is a small custom wrapper: a 24-byte header (magic
       ``b"0pam"``, width, height, compressed/uncompressed lengths) around
       a raw LZ4 block (not an LZ4 frame). Decompressed, it is exactly
       width*height bytes, one byte per pixel: the high 6 bits are the
       room id (0-31 real, 60=no data, 61=room gap, 62=obstacle,
       63=unknown/outside), the low 2 bits are a pixel type. This matches
       the room-outline raster documented in martijnpoppen/eufy-clean's
       ``proto/cloud/p2pdata.proto`` (``MapPixels``) -- Eufy's cloud copy
       is a thin wrapper around the same Tuya pixel encoding used
       elsewhere.
"""
from __future__ import annotations

import datetime
import hashlib
import hmac
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests

from .tuyawebapi import TuyaAPISession

MAP_MAGIC = b"0pam"
MAP_HEADER_LEN = 24

# Pixel byte (data[i]) -> (room_id, pixel_type). room_id = byte >> 2.
ROOM_ID_NO_DATA = 60
ROOM_ID_GAP = 61
ROOM_ID_OBSTACLE = 62
ROOM_ID_UNKNOWN = 63


class MapFetchError(Exception):
    """Raised when the cloud map can't be fetched or doesn't parse."""


def _lz4_block_decompress(data: bytes, uncompressed_size: int) -> bytes:
    """Decompress a raw LZ4 block (no frame header), pure Python.

    HA's custom-component requirements install into the core container,
    which has no C compiler and (for a new-enough Python) no prebuilt
    wheel for the ``lz4`` PyPI package -- that combination makes it fail
    to install there. The map file is small (a few KB), so a plain-Python
    decoder is fast enough and avoids the dependency entirely.
    """
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        token = data[i]
        i += 1
        lit_len = token >> 4
        if lit_len == 15:
            while True:
                b = data[i]
                i += 1
                lit_len += b
                if b != 255:
                    break
        out += data[i:i + lit_len]
        i += lit_len
        if len(out) >= uncompressed_size:
            break
        offset = data[i] | (data[i + 1] << 8)
        i += 2
        match_len = (token & 0x0F) + 4
        if (token & 0x0F) == 15:
            while True:
                b = data[i]
                i += 1
                match_len += b
                if b != 255:
                    break
        start = len(out) - offset
        for j in range(match_len):
            out.append(out[start + j])
    if len(out) != uncompressed_size:
        raise MapFetchError(
            f"LZ4 decompress produced {len(out)} bytes, expected {uncompressed_size}"
        )
    return bytes(out)


@dataclass(frozen=True)
class RoboVacMapLayout:
    """A decoded floor-plan layout: one room id per pixel."""

    width: int
    height: int
    pixels: bytes  # len == width * height, each byte's top 6 bits = room id

    def room_ids(self) -> set[int]:
        """Return the set of real room ids (0-31) present in this map."""
        return {b >> 2 for b in self.pixels if (b >> 2) < ROOM_ID_NO_DATA}


def _presign_s3_get(
    *, access_key: str, secret_key: str, session_token: str,
    region: str, host: str, path: str, expires: int = 300,
) -> str:
    """Build an AWS SigV4 presigned GET URL by hand (no boto3 dependency).

    `region` is Tuya's literal config value (e.g. "tuyaeu.com"), which
    botocore's own client/session rejects as an invalid AWS region name --
    hence the manual implementation instead of boto3.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    datestamp = now.strftime("%Y%m%d")
    credential_scope = f"{datestamp}/{region}/s3/aws4_request"

    canonical_uri = quote(path, safe="/")
    query_params = {
        "X-Amz-Algorithm": "AWS4-HMAC-SHA256",
        "X-Amz-Credential": f"{access_key}/{credential_scope}",
        "X-Amz-Date": amz_date,
        "X-Amz-Expires": str(expires),
        "X-Amz-SignedHeaders": "host",
        "X-Amz-Security-Token": session_token,
    }
    canonical_querystring = "&".join(
        f"{quote(k, safe='')}={quote(v, safe='')}"
        for k, v in sorted(query_params.items())
    )
    canonical_headers = f"host:{host}\n"
    signed_headers = "host"
    payload_hash = "UNSIGNED-PAYLOAD"
    canonical_request = "\n".join(
        ["GET", canonical_uri, canonical_querystring, canonical_headers,
         signed_headers, payload_hash]
    )
    string_to_sign = "\n".join(
        ["AWS4-HMAC-SHA256", amz_date, credential_scope,
         hashlib.sha256(canonical_request.encode()).hexdigest()]
    )

    def _sign(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode(), hashlib.sha256).digest()

    k_date = _sign(("AWS4" + secret_key).encode(), datestamp)
    k_region = _sign(k_date, region)
    k_service = _sign(k_region, "s3")
    k_signing = _sign(k_service, "aws4_request")
    signature = hmac.new(k_signing, string_to_sign.encode(), hashlib.sha256).hexdigest()

    return (
        f"https://{host}{canonical_uri}?{canonical_querystring}"
        f"&X-Amz-Signature={signature}"
    )


def fetch_layout_bytes(session: TuyaAPISession, dev_id: str) -> bytes:
    """Fetch the raw lay.bin bytes for a device's current map."""
    cfg: dict[str, Any] = session._request(  # noqa: SLF001 - same private API the integration already calls for dp.get
        action="thing.m.dev.storage.config.get",
        version="1.0",
        data={"type": "Common", "devId": dev_id},
    )
    for key in ("ak", "sk", "token", "bucket", "endpoint", "region", "pathConfig"):
        if key not in cfg:
            raise MapFetchError(f"storage config missing {key!r}: {cfg}")

    host = f"{cfg['bucket']}.{cfg['endpoint']}"
    path = cfg["pathConfig"]["common"].rstrip("/") + "/layout/lay.bin"
    url = _presign_s3_get(
        access_key=cfg["ak"], secret_key=cfg["sk"], session_token=cfg["token"],
        region=cfg["region"], host=host, path=path,
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    return resp.content


def decode_layout(raw: bytes) -> RoboVacMapLayout:
    """Parse a lay.bin payload into a RoboVacMapLayout."""
    if len(raw) < MAP_HEADER_LEN or raw[:4] != MAP_MAGIC:
        raise MapFetchError(f"bad map magic: {raw[:4]!r}")

    width = int.from_bytes(raw[8:10], "big")
    height = int.from_bytes(raw[10:12], "big")
    uncompressed_len = int.from_bytes(raw[22:24], "big")
    payload = raw[MAP_HEADER_LEN:]

    try:
        data = _lz4_block_decompress(payload, uncompressed_len)
    except MapFetchError:
        raise
    except Exception as err:  # noqa: BLE001 - surface as our own error type
        raise MapFetchError(f"LZ4 decompress failed: {err}") from err

    if len(data) != width * height:
        raise MapFetchError(
            f"decompressed size {len(data)} != width*height {width}*{height}"
        )
    return RoboVacMapLayout(width=width, height=height, pixels=data)


def fetch_and_decode(session: TuyaAPISession, dev_id: str) -> RoboVacMapLayout:
    """Fetch and decode a device's current map layout in one call."""
    return decode_layout(fetch_layout_bytes(session, dev_id))
