"""Tests for decoding the live robot pose frames of the cloud map."""

from typing import Any

import pytest

from custom_components.robovac.map_fetch import (
    RoboVacMapLayout,
    RoboVacPose,
    RouteTracker,
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


def _layout(rows: list[list[int]], dock: tuple[int, int] | None) -> RoboVacMapLayout:
    """Build a layout from rows of room ids (63 = outside)."""
    return RoboVacMapLayout(
        width=len(rows[0]),
        height=len(rows),
        pixels=bytes((room << 2) | (3 if room == 63 else 0) for row in rows for room in row),
        dock=dock,
    )


def test_room_summary_gives_id_size_and_centre_from_the_dock() -> None:
    """Centres are relative to the dock; outside pixels are ignored."""
    layout = _layout([[0, 0, 2, 2], [0, 0, 2, 63]], dock=(20, 10))  # dock at (2.0, 1.0)

    assert layout.room_summary() == [
        {"id": 0, "pixels": 4, "x": -1.5, "y": -0.5},
        {"id": 2, "pixels": 3, "x": 0.3, "y": -0.7},
    ]


def test_room_summary_is_unchanged_when_the_whole_map_shifts_with_the_dock() -> None:
    """A new map origin moves the dock too, so dock-relative centres stay equal."""
    first = _layout([[0, 0, 2, 2], [0, 0, 2, 2]], dock=(10, 10))
    shifted = _layout(
        [[63, 63, 63, 63], [63, 0, 0, 2], [63, 0, 0, 2]],  # same rooms, one px right and down
        dock=(20, 20),
    )
    shifted_rooms = _layout([[63, 0, 0, 2, 2], [63, 0, 0, 2, 2]], dock=(20, 10))

    assert first.room_summary() == shifted_rooms.room_summary()
    assert [room["id"] for room in shifted.room_summary()] == [0, 2]


def test_room_summary_without_dock_uses_the_map_corner() -> None:
    """Without a dock the centre is measured from pixel (0, 0)."""
    layout = _layout([[5, 5]], dock=None)

    assert layout.room_summary() == [{"id": 5, "pixels": 2, "x": 0.5, "y": 0.0}]


def test_room_summary_of_a_map_without_rooms_is_empty() -> None:
    """A map of only outside pixels has no rooms."""
    assert _layout([[63, 63]], dock=(0, 0)).room_summary() == []


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


def test_tracker_collects_points_once_dock_is_known() -> None:
    """Points are returned in map pixels when the dock comes from the layout."""
    tracker = RouteTracker()
    tracker.dock = DOCK

    assert tracker.update(7, [POSE_FRAME_1]) is True
    assert tracker.update(7, [POSE_FRAME_2]) is True

    first, second = tracker.path()
    assert first == pytest.approx((158.4, 16.1))
    assert second == pytest.approx((142.9, 16.3))


def test_tracker_buffers_offsets_until_a_header_gives_the_dock() -> None:
    """Without a dock nothing is drawable; a header resolves the buffered points."""
    tracker = RouteTracker()

    assert tracker.update(7, [POSE_FRAME_1]) is False
    assert tracker.path() == []
    assert tracker.point_count == 1

    assert tracker.update(7, [HEADER_FRAME, POSE_FRAME_2]) is True
    assert tracker.dock == DOCK
    assert len(tracker.path()) == 2


@pytest.mark.parametrize(
    ("record_id", "frames"), [(0, []), (0, [POSE_FRAME_1]), (7, []), (0, [HEADER_FRAME])]
)
def test_tracker_ignores_empty_poll_answers(record_id: int, frames: list[str]) -> None:
    """An answer without a record id or frames is not a new clean and keeps the route."""
    tracker = RouteTracker()
    tracker.dock = DOCK
    tracker.update(7, [POSE_FRAME_1, POSE_FRAME_2])

    assert tracker.update(record_id, frames) is False

    assert tracker.record_id == 7
    assert len(tracker.path()) == 2


def test_tracker_starts_a_new_route_for_a_new_record() -> None:
    """A new clean record id drops the previous route."""
    tracker = RouteTracker()
    tracker.dock = DOCK
    tracker.update(7, [POSE_FRAME_1, POSE_FRAME_2])

    assert tracker.update(8, [POSE_FRAME_2]) is True

    assert tracker.record_id == 8
    assert len(tracker.path()) == 1


def test_tracker_skips_repeated_frames_and_caps_length() -> None:
    """The same newest frame polled twice adds one point; old points age out."""
    tracker = RouteTracker(max_points=2)
    tracker.dock = DOCK

    assert tracker.update(7, [POSE_FRAME_1]) is True
    assert tracker.update(7, [POSE_FRAME_1]) is False
    tracker.update(7, [POSE_FRAME_2])
    tracker.update(7, ["0908870710990418aa18"])

    assert tracker.point_count == 2


def _frame(dx: int, dy: int) -> str:
    """Build a pose frame hex string for a raw offset (zigzag-encodes dx, dy)."""

    def varint(value: int) -> bytes:
        out = bytearray()
        while True:
            byte = value & 0x7F
            value >>= 7
            out.append(byte | (0x80 if value else 0))
            if not value:
                return bytes(out)

    def zigzag(value: int) -> int:
        return (value << 1) ^ (value >> 31)

    body = b"\x08" + varint(zigzag(dx)) + b"\x10" + varint(zigzag(dy)) + b"\x18\x00"
    return (bytes([len(body)]) + body).hex()


def test_segments_split_at_off_map_points_and_jumps() -> None:
    """A point off the map or a huge jump must not be joined to its neighbours."""
    tracker = RouteTracker()
    tracker.set_layout_dock((500, 500))  # dock at pixel (50, 50)
    frames = [
        _frame(0, 0),        # (50, 50) on the map
        _frame(100, 0),      # (60, 50) normal step
        _frame(9000, 0),     # (950, 50) far off a 100 px wide map
        _frame(-100, 100),   # (40, 60) back on the map
        _frame(-100, -900),  # (40, -30) off the map
        _frame(0, 0),        # (50, 50) back on the map
        _frame(700, 0),      # (120, 50) on a 200 px map but a 70 px jump
    ]
    for index, frame in enumerate(frames):
        tracker.update(7, [frame])
        assert tracker.point_count == index + 1

    assert tracker.segments(200, 100) == [
        [(50.0, 50.0), (60.0, 50.0)],
        [(40.0, 60.0)],
        [(50.0, 50.0)],
        [(120.0, 50.0)],
    ]


def test_segments_of_a_smooth_route_stay_in_one_piece() -> None:
    """Normal robot steps give a single connected piece."""
    tracker = RouteTracker()
    tracker.set_layout_dock((500, 500))
    for step in range(5):
        tracker.update(7, [_frame(step * 50, step * 20)])

    pieces = tracker.segments(200, 100)

    assert len(pieces) == 1
    assert len(pieces[0]) == 5


def test_layout_dock_wins_over_media_header() -> None:
    """After the layout sets the dock, a header frame must not move it."""
    tracker = RouteTracker()
    tracker.set_layout_dock((1780, 490))

    tracker.update(7, [HEADER_FRAME, POSE_FRAME_1])  # header says dock (1720, 430)

    assert tracker.dock == (1780, 490)
    assert tracker.path()[0] == pytest.approx((164.4, 22.1))


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
