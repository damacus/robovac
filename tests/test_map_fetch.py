"""Tests for decoding the live robot pose frames of the cloud map."""

from typing import Any

import pytest

from custom_components.robovac.map_fetch import (
    RoboVacPose,
    decode_layout,
    decode_pose_frame,
    fetch_frames,
    fetch_pose,
    pose_offset,
)

# Frames captured from a real T2276 clean on 2026-10-31.
HEADER_FRAME = "fe0000006e000000b8060000ae010000b0060000d2010000"
POSE_FRAME_1 = "09088f0210990418a419"
POSE_FRAME_2 = "0908c50410950418c018"
DOCK = (1720, 430)


def _lay_bin(width: int, height: int, dock: tuple[int, int], pixels: bytes) -> bytes:
    """Build a minimal lay.bin: header plus an LZ4 block of literals only."""
    block = bytes([len(pixels) << 4]) + pixels  # token: literal length, no match
    header = (
        b"0pam"
        + (16).to_bytes(2, "big") + (256).to_bytes(2, "big")
        + width.to_bytes(2, "big") + height.to_bytes(2, "big")
        + dock[0].to_bytes(2, "big") + dock[1].to_bytes(2, "big")
        + (0).to_bytes(2, "big") + len(block).to_bytes(2, "big")
        + (0).to_bytes(2, "big") + len(pixels).to_bytes(2, "big")
    )
    return header + block


def test_decode_layout_reads_dock_from_header() -> None:
    """Header bytes 12-15 are the dock position, in 1/10 map pixel."""
    layout = decode_layout(_lay_bin(2, 2, DOCK, bytes([0, 4, 8, 12])))

    assert (layout.width, layout.height) == (2, 2)
    assert layout.dock == DOCK
    assert layout.pixels == bytes([0, 4, 8, 12])


def test_header_frame_dock_matches_layout_dock() -> None:
    """The media header frame and the layout header agree on the dock."""
    layout = decode_layout(_lay_bin(2, 2, DOCK, bytes([0, 4, 8, 12])))

    assert decode_pose_frame(HEADER_FRAME, None)[0] == layout.dock


def test_header_frame_yields_dock_and_robot_position() -> None:
    """A header frame carries the dock and the robot position in 1/10 pixel."""
    dock, xy = decode_pose_frame(HEADER_FRAME, None)

    assert dock == DOCK
    assert xy == (171.2, 46.6)


def test_pose_frame_is_zigzag_offset_from_dock() -> None:
    """x=271 and y=537 decode to offsets -136 and -269 from the dock."""
    dock, xy = decode_pose_frame(POSE_FRAME_1, DOCK)

    assert dock == DOCK
    assert xy == pytest.approx((158.4, 16.1))


def test_pose_frame_with_even_values_is_positive_offset() -> None:
    """Zigzag even values are positive: x=2 -> +1, y=4 -> +2."""
    # length 6, field 1 varint 2, field 2 varint 4, field 3 varint 0
    _, xy = decode_pose_frame("0608021004" + "1800", DOCK)

    assert xy == pytest.approx((172.1, 43.2))


def test_pose_frame_without_known_dock_is_ignored() -> None:
    """A pose frame is relative to the dock, so it needs an earlier header."""
    dock, xy = decode_pose_frame(POSE_FRAME_1, None)

    assert dock is None
    assert xy is None


@pytest.mark.parametrize(
    "frame",
    ["", "zz", "0908", "09", "ff" * 10, "0608" + "0000000000", "0508021004"],
)
def test_malformed_frame_is_ignored_and_keeps_dock(frame: str) -> None:
    """Bad data never raises and never drops the known dock."""
    dock, xy = decode_pose_frame(frame, DOCK)

    assert dock == DOCK
    assert xy is None


def test_pose_offset_needs_no_dock() -> None:
    """A pose frame decodes to its raw zigzag offset even before the dock is known."""
    assert pose_offset(POSE_FRAME_1) == (-136, -269)
    assert pose_offset(POSE_FRAME_2) == (-291, -267)


@pytest.mark.parametrize(
    "frame", [HEADER_FRAME, "", "zz", "09", "0908", "0608" + "0000000000"]
)
def test_pose_offset_ignores_header_and_malformed_frames(frame: str) -> None:
    """Only well-formed pose frames give an offset."""
    assert pose_offset(frame) is None


def test_offsets_buffered_before_header_resolve_to_same_positions() -> None:
    """Offsets kept before the dock is known give the same points as a known dock."""
    offsets = [pose_offset(f) for f in (POSE_FRAME_1, POSE_FRAME_2)]
    _, late = decode_pose_frame(HEADER_FRAME, None)
    assert late is not None  # header reveals the dock

    resolved = [
        ((DOCK[0] + dx) / 10, (DOCK[1] + dy) / 10)
        for dx, dy in offsets  # type: ignore[misc]
    ]

    assert resolved[0] == pytest.approx(decode_pose_frame(POSE_FRAME_1, DOCK)[1])
    assert resolved[1] == pytest.approx(decode_pose_frame(POSE_FRAME_2, DOCK)[1])


class _FakeSession:
    """Stands in for TuyaAPISession; records the request it receives."""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def _request(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return self.response


def test_fetch_pose_requests_media_latest_and_decodes() -> None:
    """The newest frame is fetched with the v3.0 action and tagged with its record."""
    session = _FakeSession({"subRecordId": 1566, "dataList": [HEADER_FRAME]})

    dock, pose = fetch_pose(session, "dev1", None)  # type: ignore[arg-type]

    assert session.calls == [
        {
            "action": "tuya.m.device.media.latest",
            "version": "3.0",
            "data": {"devId": "dev1", "start": 0, "size": 20},
        }
    ]
    assert dock == DOCK
    assert pose == RoboVacPose(record_id=1566, x=171.2, y=46.6)


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        ({"subRecordId": 5, "dataList": [POSE_FRAME_1]}, (5, [POSE_FRAME_1])),
        ({"subRecordId": 5, "dataList": None}, (5, [])),
        ({}, (0, [])),
    ],
)
def test_fetch_frames_returns_record_id_and_raw_frames(
    response: dict[str, Any], expected: tuple[int, list[str]]
) -> None:
    """Frames are returned undecoded, with the clean record id (0 when missing)."""
    session = _FakeSession(response)

    assert fetch_frames(session, "dev1") == expected  # type: ignore[arg-type]
    assert session.calls[0]["action"] == "tuya.m.device.media.latest"


def test_fetch_pose_reuses_dock_from_earlier_header() -> None:
    """Pose-only responses decode using the dock from a previous call."""
    session = _FakeSession({"subRecordId": 7, "dataList": [POSE_FRAME_2]})

    dock, pose = fetch_pose(session, "dev1", DOCK)  # type: ignore[arg-type]

    assert dock == DOCK
    assert pose is not None
    assert pose.record_id == 7
    assert (pose.x, pose.y) == pytest.approx((142.9, 16.3))


@pytest.mark.parametrize(
    "response",
    [{}, {"dataList": []}, {"subRecordId": 3, "dataList": None}, {"dataList": ["zz"]}],
)
def test_fetch_pose_without_usable_frame_returns_no_pose(
    response: dict[str, Any],
) -> None:
    """An empty or unreadable response yields no pose and keeps the dock."""
    session = _FakeSession(response)

    dock, pose = fetch_pose(session, "dev1", DOCK)  # type: ignore[arg-type]

    assert dock == DOCK
    assert pose is None
