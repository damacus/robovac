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
import math
import struct
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
    # Dock position in 1/10 map pixel (header bytes 12-15). Pose frames are
    # offsets from it, so the route can be drawn without waiting for a media
    # header frame.
    dock: tuple[int, int] | None = None

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
    dock = (int.from_bytes(raw[12:14], "big"), int.from_bytes(raw[14:16], "big"))
    return RoboVacMapLayout(width=width, height=height, pixels=data, dock=dock)


def fetch_and_decode(session: TuyaAPISession, dev_id: str) -> RoboVacMapLayout:
    """Fetch and decode a device's current map layout in one call."""
    return decode_layout(fetch_layout_bytes(session, dev_id))


# Live robot pose, reverse engineered 2026-10-31. ``tuya.m.device.media.latest``
# v3.0 returns only the newest frame of the current clean record
# (``subRecordId``), so a route has to be built by polling and accumulating
# points. Two frame kinds alternate:
#   header, 24 bytes: little-endian int32 x6 = map width, map height,
#       dock x, dock y, robot x, robot y (position unit: 1/10 map pixel)
#   pose, 10 bytes: length prefix 0x09 + protobuf {1: x, 2: y, 3: z}. x and y
#       are zigzag-encoded offsets from the dock, in the same unit. z is not
#       decoded.
POSE_UNITS_PER_PIXEL = 10
_HEADER_FRAME_LEN = 24
_MAX_JUMP_PIXELS = 60
_OFF_MAP_MARGIN = 3


@dataclass(frozen=True)
class RoboVacPose:
    """A robot position in map pixels, tagged with its clean record id."""

    record_id: int
    x: float
    y: float


def _read_varint(data: bytes, pos: int) -> tuple[int, int]:
    """Read one protobuf varint, returning (value, next position)."""
    value = shift = 0
    while True:
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, pos
        shift += 7


def _unzigzag(value: int) -> int:
    return (value >> 1) ^ -(value & 1)


def pose_offset(frame_hex: str) -> tuple[int, int] | None:
    """Decode a pose frame to its raw (x, y) offset from the dock.

    The offset is in 1/10 map pixel. Header frames and malformed frames give
    ``None``. The dock is not needed, so offsets can be kept until a header
    frame reveals it.
    """
    try:
        raw = bytes.fromhex(frame_hex)
        if len(raw) == _HEADER_FRAME_LEN or raw[0] != len(raw) - 1:
            return None
        fields: dict[int, int] = {}
        pos = 1
        while pos < len(raw):
            tag, pos = _read_varint(raw, pos)
            fields[tag >> 3], pos = _read_varint(raw, pos)
        if 1 not in fields or 2 not in fields:
            return None
        return _unzigzag(fields[1]), _unzigzag(fields[2])
    except (ValueError, IndexError):
        return None


def decode_pose_frame(
    frame_hex: str, dock: tuple[int, int] | None
) -> tuple[tuple[int, int] | None, tuple[float, float] | None]:
    """Decode one media frame into (dock, robot position in map pixels).

    A header frame yields the dock and the robot position it carries. A pose
    frame yields only a position and needs ``dock`` from an earlier header.
    Unknown or malformed frames yield ``(dock, None)``.
    """
    try:
        raw = bytes.fromhex(frame_hex)
        if len(raw) == _HEADER_FRAME_LEN:
            _, _, dock_x, dock_y, robot_x, robot_y = struct.unpack("<6i", raw)
            return (dock_x, dock_y), (
                robot_x / POSE_UNITS_PER_PIXEL, robot_y / POSE_UNITS_PER_PIXEL,
            )
    except (ValueError, struct.error):
        return dock, None
    offset = pose_offset(frame_hex)
    if dock is None or offset is None:
        return dock, None
    return dock, (
        (dock[0] + offset[0]) / POSE_UNITS_PER_PIXEL,
        (dock[1] + offset[1]) / POSE_UNITS_PER_PIXEL,
    )


def fetch_frames(session: TuyaAPISession, dev_id: str) -> tuple[int, list[str]]:
    """Fetch the newest media frame(s) as (clean record id, hex frames)."""
    resp: dict[str, Any] = session._request(  # noqa: SLF001 - same private API the integration already calls for dp.get
        action="tuya.m.device.media.latest",
        version="3.0",
        data={"devId": dev_id, "start": 0, "size": 20},
    )
    return int(resp.get("subRecordId") or 0), list(resp.get("dataList") or [])


class RouteTracker:
    """Accumulates the route of the current clean from polled media frames.

    Pose frames are offsets from the dock, so offsets are kept raw and turned
    into map pixels once the dock is known. A new clean record id starts a new
    route. An empty poll answer has no record id and is not a new clean, so it
    must never reset the route.
    """

    def __init__(self, max_points: int = 20000) -> None:
        self.dock: tuple[int, int] | None = None
        self.record_id = 0
        self._offsets: list[tuple[int, int]] = []
        self._max_points = max_points
        self._dock_fixed = False

    def set_layout_dock(self, dock: tuple[int, int]) -> None:
        """Use the dock from the current map layout; media headers no longer change it.

        A new map can move the dock, so the layout is refreshed during a clean
        and this keeps the route and the drawn map in the same frame.
        """
        self.dock = dock
        self._dock_fixed = True

    def update(self, record_id: int, frames: list[str]) -> bool:
        """Add polled frames; return True when the drawable route changed."""
        if not record_id or not frames:
            return False
        if record_id != self.record_id:
            self.record_id = record_id
            self._offsets = []
        changed = False
        for frame_hex in frames:
            if not self._dock_fixed:
                self.dock, _ = decode_pose_frame(frame_hex, self.dock)
            offset = pose_offset(frame_hex)
            if offset is not None and (
                not self._offsets or self._offsets[-1] != offset
            ):
                self._offsets.append(offset)
                del self._offsets[:-self._max_points]
                changed = True
        return changed and self.dock is not None

    @property
    def point_count(self) -> int:
        """Return how many route points are held, with or without a dock."""
        return len(self._offsets)

    def segments(self, width: int, height: int) -> list[list[tuple[float, float]]]:
        """Return the route as drawable pieces that stay on a width x height map.

        A point outside the map, or a jump of more than ``_MAX_JUMP_PIXELS``
        from the previous point, starts a new piece. The robot cannot move that
        far between two polls, so such points are glitches or a changed map and
        must not be joined by a straight line.
        """
        pieces: list[list[tuple[float, float]]] = []
        current: list[tuple[float, float]] = []
        for x, y in self.path():
            on_map = (
                -_OFF_MAP_MARGIN <= x < width + _OFF_MAP_MARGIN
                and -_OFF_MAP_MARGIN <= y < height + _OFF_MAP_MARGIN
            )
            if not on_map:
                if current:
                    pieces.append(current)
                    current = []
                continue
            if current and math.hypot(x - current[-1][0], y - current[-1][1]) > _MAX_JUMP_PIXELS:
                pieces.append(current)
                current = []
            current.append((x, y))
        if current:
            pieces.append(current)
        return pieces

    def path(self) -> list[tuple[float, float]]:
        """Return the route in map pixels, or an empty list without a dock."""
        if self.dock is None:
            return []
        dock_x, dock_y = self.dock
        return [
            ((dock_x + dx) / POSE_UNITS_PER_PIXEL, (dock_y + dy) / POSE_UNITS_PER_PIXEL)
            for dx, dy in self._offsets
        ]


def fetch_pose(
    session: TuyaAPISession, dev_id: str, dock: tuple[int, int] | None
) -> tuple[tuple[int, int] | None, RoboVacPose | None]:
    """Fetch the newest media frame and decode it to (dock, pose)."""
    record_id, frames = fetch_frames(session, dev_id)
    pose: RoboVacPose | None = None
    for frame_hex in frames:
        dock, xy = decode_pose_frame(frame_hex, dock)
        if xy is not None:
            pose = RoboVacPose(record_id=record_id, x=xy[0], y=xy[1])
    return dock, pose
