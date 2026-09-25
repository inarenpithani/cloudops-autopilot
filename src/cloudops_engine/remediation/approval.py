def request_approval(recommendation: str) -> bool:
    print(f"Recommended action: {recommendation}")

    response = input("Approve this action? (yes/no): ").strip().lower()

    return response == "yes"