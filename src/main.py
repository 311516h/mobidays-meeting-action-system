from src.storage import init_db


def main() -> None:
    init_db()
    print("database initialized")


if __name__ == "__main__":
    main()

