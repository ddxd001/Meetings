"""Server entry point."""

import os

from .repository import MeetingRepository
from .rpc_server import RpcServer
from .service import MeetingService


def default_db_path():
    package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(package_dir, "data", "meetings.db")


def main():
    db_path = os.environ.get("MEETING_DB", default_db_path())
    repository = MeetingRepository(db_path)
    service = MeetingService(repository)
    RpcServer(service).serve_forever()


if __name__ == "__main__":
    main()

