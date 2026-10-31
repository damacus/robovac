"""Tests for decoding the live robot pose frames of the cloud map."""

from typing import Any

import pytest

from custom_components.robovac.map_fetch import (
    RoboVacPose,
    decode_pose_frame,
    fetch_pose,
)

# Frames captured from a real T2276 clean on 2026-10-31.
HEADER_FRAME = "fe0000006e000000b8060000ae010000b0060000d2010000"
POSE_FRAME_1 = "09088f0210990418a419"
POSE_FRAME_2 = "0908c50410950418c018"
DOCK = (1720, 430)


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
