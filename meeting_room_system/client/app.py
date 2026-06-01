"""Client entry point."""

from .pages import MeetingRoomApp


def main():
    app = MeetingRoomApp()
    app.mainloop()


if __name__ == "__main__":
    main()

