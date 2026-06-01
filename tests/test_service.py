import tempfile
import unittest

from meeting_room_system.server.repository import MeetingRepository
from meeting_room_system.server.service import MeetingService


class MeetingServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repository = MeetingRepository(f"{self.tmp.name}/test.db")
        self.service = MeetingService(self.repository)

    def tearDown(self):
        self.repository.close()
        self.tmp.cleanup()

    def book(self, **overrides):
        data = {
            "organizerName": "张三",
            "roomName": "1层10人1",
            "topic": "项目讨论",
            "startTime": "2099-06-02 10:00",
            "endTime": "2099-06-02 11:00",
            "attendeeCount": 6,
        }
        data.update(overrides)
        return self.service.book_meeting(data)

    def test_book_success(self):
        response = self.book()
        self.assertTrue(response["success"])
        self.assertEqual(response["data"]["meetingId"], 1)

    def test_room_not_found(self):
        response = self.book(roomName="不存在的会议室")
        self.assertFalse(response["success"])
        self.assertEqual(response["code"], "ROOM_NOT_FOUND")

    def test_capacity_exceeded(self):
        response = self.book(roomName="1层5人1", attendeeCount=6)
        self.assertFalse(response["success"])
        self.assertEqual(response["code"], "CAPACITY_EXCEEDED")

    def test_time_format_error(self):
        response = self.book(startTime="2099/06/02 10:00")
        self.assertFalse(response["success"])
        self.assertEqual(response["code"], "VALIDATION_ERROR")

    def test_start_after_end(self):
        response = self.book(startTime="2099-06-02 12:00", endTime="2099-06-02 11:00")
        self.assertFalse(response["success"])
        self.assertEqual(response["code"], "VALIDATION_ERROR")

    def test_past_time_rejected(self):
        response = self.book(startTime="2000-01-01 10:00", endTime="2000-01-01 11:00")
        self.assertFalse(response["success"])
        self.assertEqual(response["code"], "VALIDATION_ERROR")

    def test_same_room_conflict(self):
        self.assertTrue(self.book()["success"])
        response = self.book(startTime="2099-06-02 10:30", endTime="2099-06-02 11:30")
        self.assertFalse(response["success"])
        self.assertEqual(response["code"], "TIME_CONFLICT")

    def test_different_room_same_time_allowed(self):
        self.assertTrue(self.book()["success"])
        response = self.book(roomName="1层10人2")
        self.assertTrue(response["success"])

    def test_adjacent_time_allowed(self):
        self.assertTrue(self.book()["success"])
        response = self.book(startTime="2099-06-02 11:00", endTime="2099-06-02 12:00")
        self.assertTrue(response["success"])

    def test_cancel_success(self):
        meeting_id = self.book()["data"]["meetingId"]
        response = self.service.cancel_meeting(
            {"meetingId": meeting_id, "requesterName": "张三", "isAdmin": False}
        )
        self.assertTrue(response["success"])
        missing = self.service.query_by_id({"meetingId": meeting_id})
        self.assertFalse(missing["success"])

    def test_cancel_forbidden_for_other_user(self):
        meeting_id = self.book()["data"]["meetingId"]
        response = self.service.cancel_meeting(
            {"meetingId": meeting_id, "requesterName": "李四", "isAdmin": False}
        )
        self.assertFalse(response["success"])
        self.assertEqual(response["code"], "FORBIDDEN")

    def test_admin_can_cancel_any_meeting(self):
        meeting_id = self.book()["data"]["meetingId"]
        response = self.service.cancel_meeting(
            {"meetingId": meeting_id, "requesterName": "Admin", "isAdmin": True}
        )
        self.assertTrue(response["success"])

    def test_query_missing_id(self):
        response = self.service.query_by_id({"meetingId": 999})
        self.assertFalse(response["success"])
        self.assertEqual(response["code"], "NOT_FOUND")

    def test_query_available_rooms(self):
        self.assertTrue(self.book(roomName="1层10人1")["success"])
        response = self.service.query_available_rooms(
            {
                "startTime": "2099-06-02 10:30",
                "endTime": "2099-06-02 10:45",
                "attendeeCount": 6,
            }
        )
        self.assertTrue(response["success"])
        room_names = {room["roomName"] for room in response["data"]["rooms"]}
        self.assertNotIn("1层10人1", room_names)
        self.assertIn("1层10人2", room_names)
        self.assertNotIn("1层5人1", room_names)

    def test_list_all_meetings(self):
        self.assertTrue(self.book()["success"])
        response = self.service.list_all_meetings()
        self.assertTrue(response["success"])
        self.assertEqual(len(response["data"]["meetings"]), 1)


if __name__ == "__main__":
    unittest.main()

