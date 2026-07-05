from agent_server.app.retriever import scan_sources


def main() -> None:
    result = scan_sources()
    print("category | extension | characters | path")
    print("-" * 72)
    for item in result.items:
        print(f"{item.category} | {item.extension} | {item.characters} | {item.path}")
    print(f"excluded_files={result.excluded_files}")


if __name__ == "__main__":
    main()
