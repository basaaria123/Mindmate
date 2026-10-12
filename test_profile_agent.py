from app.agents.profile_agent import extract_user_profile


def main():
    user_message = (
        "I am a second-year engineering student. "
        "My goal is to learn AI development. "
        "I know basic Python and am interested in artificial intelligence. "
        "I can spend one hour every day learning. "
        "I prefer step-by-step explanations."
    )

    print("Testing MindMate Profile Extraction Agent...")
    print("\nUser message:")
    print(user_message)

    profile = extract_user_profile(user_message)

    print("\n--- Extracted Profile ---")
    print(profile.model_dump_json(indent=2))


if __name__ == "__main__":
    main()