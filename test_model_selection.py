from app.services.llm_client import create_llm_client, get_model


def main():
    client = create_llm_client()
    model = get_model("fast")

    print("Testing MindMate Fast Model...")
    print("Model:", model)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are MindMate, a helpful personal AI assistant. "
                    "Give clear and concise answers."
                ),
            },
            {
                "role": "user",
                "content": "Give me three simple steps to achieve a study goal.",
            },
        ],
        max_tokens=150,
    )

    print("\n--- MindMate Response ---")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()