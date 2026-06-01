"""Server entry point."""

from meeting_room_system.config import server_settings
from .repository import MeetingRepository
from .rpc_server import RpcServer
from .service import MeetingService


def main():
    host, port, db_path = server_settings()
    repository = MeetingRepository(db_path)
    service = MeetingService(repository)
    RpcServer(service, host=host, port=port).serve_forever()


if __name__ == "__main__":
    main()
