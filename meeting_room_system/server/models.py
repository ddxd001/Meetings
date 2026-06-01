"""Core data models."""

from dataclasses import dataclass


TIME_FORMAT = "%Y-%m-%d %H:%M"


@dataclass(frozen=True)
class Room:
    room_id: int
    name: str
    floor: int
    capacity: int

    def to_dict(self):
        return {
            "roomId": self.room_id,
            "roomName": self.name,
            "floor": self.floor,
            "capacity": self.capacity,
        }


@dataclass(frozen=True)
class Meeting:
    meeting_id: int
    organizer_name: str
    room_id: int
    room_name: str
    topic: str
    start_time: str
    end_time: str
    attendee_count: int

    def to_dict(self):
        return {
            "meetingId": self.meeting_id,
            "organizerName": self.organizer_name,
            "roomId": self.room_id,
            "roomName": self.room_name,
            "topic": self.topic,
            "startTime": self.start_time,
            "endTime": self.end_time,
            "attendeeCount": self.attendee_count,
        }


def default_rooms():
    rooms = []
    room_id = 1
    for floor in range(1, 7):
        for index in range(1, 4):
            rooms.append(Room(room_id, f"{floor}层10人{index}", floor, 10))
            room_id += 1
        for index in range(1, 3):
            rooms.append(Room(room_id, f"{floor}层5人{index}", floor, 5))
            room_id += 1
    return rooms

