from app.schemas.profile import UserProfile


def main():
    profile = UserProfile(
        education="Second-year engineering student",
        goals=["Learn AI development"],
        skills=["Basic Python"],
        interests=["Artificial Intelligence"],
        daily_available_minutes=60,
        learning_preferences=["Step-by-step explanations"],
    )

    print("MindMate Profile Schema Test")
    print("----------------------------")
    print(profile.model_dump_json(indent=2))


if __name__ == "__main__":
    main()