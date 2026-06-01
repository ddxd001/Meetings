"""Business rules for meeting room booking."""

import threading
from datetime import datetime

from .models import TIME_FORMAT


def ok(msg="OK", data=None):
    return {"success": True, "code": "OK", "msg": msg, "data": data or {}}


def fail(code, msg, data=None):
    return {"success": False, "code": code, "msg": msg, "data": data or {}}


class MeetingService:
    def __init__(self, repository):
        self.repository = repository
        self._lock = threading.RLock()

    def dispatch(self, action, data):
        handlers = {
            "login": self.login,
            "listRooms": self.list_rooms,
            "listAllMeetings": self.list_all_meetings,
            "bookMeeting": self.book_meeting,
            "book": self.book_meeting,
            "queryByID": self.query_by_id,
            "queryById": self.query_by_id,
            "queryByOrganizer": self.query_by_organizer,
            "queryByRoom": self.query_by_room,
            "queryAvailableRooms": self.query_available_rooms,
            "cancelMeeting": self.cancel_meeting,
            "cancel": self.cancel_meeting,
        }
        handler = handlers.get(action)
        if handler is None:
            return fail("UNKNOWN_ACTION", "未知操作")
        return handler(data or {})

    def login(self, data):
        username = str(data.get("username", "")).strip()
        if not username:
            return fail("VALIDATION_ERROR", "用户名不能为空")
        self.repository.save_user(username)
        return ok("登录成功", {"username": username})

    def list_rooms(self, data=None):
        rooms = [room.to_dict() for room in self.repository.list_rooms()]
        return ok("查询成功", {"rooms": rooms})

    def list_all_meetings(self, data=None):
        meetings = [meeting.to_dict() for meeting in self.repository.list_all_meetings()]
        return ok("查询成功", {"meetings": meetings})

    def book_meeting(self, data):
        with self._lock:
            valid, payload = self._validate_meeting_payload(data)
            if not valid:
                return payload

            room = payload["room"]
            conflicts = self.repository.find_conflicts(
                room.room_id,
                payload["start_time_text"],
                payload["end_time_text"],
            )
            if conflicts:
                return fail("TIME_CONFLICT", "该会议室在所选时间段已被预约")

            meeting_id = self.repository.add_meeting(
                payload["organizer_name"],
                room.room_id,
                payload["topic"],
                payload["start_time_text"],
                payload["end_time_text"],
                payload["attendee_count"],
            )
            return ok("预约成功", {"meetingId": meeting_id})

    def query_by_id(self, data):
        meeting_id = self._read_int(data.get("meetingId"))
        if meeting_id is None:
            return fail("VALIDATION_ERROR", "预约ID必须为整数")

        meeting = self.repository.find_meeting_by_id(meeting_id)
        if meeting is None:
            return fail("NOT_FOUND", "无此预约ID")
        return ok("查询成功", {"meeting": meeting.to_dict()})

    def query_by_organizer(self, data):
        organizer_name = str(data.get("organizerName", "")).strip()
        if not organizer_name:
            return fail("VALIDATION_ERROR", "组织者姓名不能为空")

        meetings = [
            meeting.to_dict()
            for meeting in self.repository.find_meetings_by_organizer(organizer_name)
        ]
        return ok("查询成功", {"meetings": meetings})

    def query_by_room(self, data):
        room_result = self._resolve_room(data)
        if room_result["error"]:
            return room_result["error"]

        meetings = [
            meeting.to_dict()
            for meeting in self.repository.find_meetings_by_room(room_result["room"].room_id)
        ]
        return ok("查询成功", {"meetings": meetings})

    def query_available_rooms(self, data):
        start_time, end_time, error = self._read_time_range(data)
        if error:
            return error

        attendee_count = data.get("attendeeCount")
        if attendee_count in (None, ""):
            attendee_count = 1
        else:
            attendee_count = self._read_int(attendee_count)
            if attendee_count is None or attendee_count <= 0:
                return fail("VALIDATION_ERROR", "参与人数必须为大于0的整数")

        rooms = []
        for room in self.repository.list_rooms():
            if room.capacity < attendee_count:
                continue
            conflicts = self.repository.find_conflicts(
                room.room_id,
                start_time.strftime(TIME_FORMAT),
                end_time.strftime(TIME_FORMAT),
            )
            if not conflicts:
                rooms.append(room.to_dict())
        return ok("查询成功", {"rooms": rooms})

    def cancel_meeting(self, data):
        meeting_id = self._read_int(data.get("meetingId"))
        if meeting_id is None:
            return fail("VALIDATION_ERROR", "预约ID必须为整数")

        requester_name = str(data.get("requesterName", "")).strip()
        is_admin = bool(data.get("isAdmin", False))

        meeting = self.repository.find_meeting_by_id(meeting_id)
        if meeting is None:
            return fail("NOT_FOUND", "无此预约ID，取消失败")

        if not is_admin and requester_name != meeting.organizer_name:
            return fail("FORBIDDEN", "只能取消自己预约的会议室")

        deleted = self.repository.delete_meeting(meeting_id)
        if not deleted:
            return fail("NOT_FOUND", "无此预约ID，取消失败")
        return ok("取消成功")

    def _validate_meeting_payload(self, data):
        organizer_name = str(data.get("organizerName", "")).strip()
        topic = str(data.get("topic", "")).strip()
        attendee_count = self._read_int(data.get("attendeeCount"))

        if not organizer_name or not topic:
            return False, fail("VALIDATION_ERROR", "组织者和会议主题不能为空")
        if attendee_count is None or attendee_count <= 0:
            return False, fail("VALIDATION_ERROR", "参与人数必须为大于0的整数")

        room_result = self._resolve_room(data)
        if room_result["error"]:
            return False, room_result["error"]
        room = room_result["room"]
        if attendee_count > room.capacity:
            return False, fail("CAPACITY_EXCEEDED", "参与人数不能超过会议室容量")

        start_time, end_time, error = self._read_time_range(data)
        if error:
            return False, error
        if start_time < datetime.now():
            return False, fail("VALIDATION_ERROR", "开始时间不能早于当前时间")

        return True, {
            "organizer_name": organizer_name,
            "room": room,
            "topic": topic,
            "start_time_text": start_time.strftime(TIME_FORMAT),
            "end_time_text": end_time.strftime(TIME_FORMAT),
            "attendee_count": attendee_count,
        }

    def _resolve_room(self, data):
        room_id = data.get("roomId")
        room_name = str(data.get("roomName", "")).strip()

        room = None
        if room_id not in (None, ""):
            parsed_id = self._read_int(room_id)
            if parsed_id is None:
                return {"room": None, "error": fail("VALIDATION_ERROR", "会议室ID必须为整数")}
            room = self.repository.get_room_by_id(parsed_id)
        elif room_name:
            room = self.repository.get_room_by_name(room_name)
        else:
            return {"room": None, "error": fail("VALIDATION_ERROR", "会议室不能为空")}

        if room is None:
            return {"room": None, "error": fail("ROOM_NOT_FOUND", "会议室不存在")}
        return {"room": room, "error": None}

    def _read_time_range(self, data):
        start_text = str(data.get("startTime", "")).strip()
        end_text = str(data.get("endTime", "")).strip()
        if not start_text or not end_text:
            return None, None, fail("VALIDATION_ERROR", "开始时间和结束时间不能为空")
        try:
            start_time = datetime.strptime(start_text, TIME_FORMAT)
            end_time = datetime.strptime(end_text, TIME_FORMAT)
        except ValueError:
            return None, None, fail("VALIDATION_ERROR", "时间格式应为 yyyy-MM-dd HH:mm")
        if start_time >= end_time:
            return None, None, fail("VALIDATION_ERROR", "开始时间必须早于结束时间")
        return start_time, end_time, None

    def _read_int(self, value):
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.strip():
            try:
                return int(value.strip())
            except ValueError:
                return None
        return None

