from config import get_genai_client


def process_professor_query(query: str) -> str:
    prompt = f"""
You are an AI research assistant for university professors.

Professor Question:
{query}

Answer with:
1. Current research trends
2. Recent advancements
3. Future research directions

Keep the answer concise.
"""

    client = get_genai_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return response.text


def professor_chat():
    print("\nProfessor Mode")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Professor: ")

        if query.lower() == "exit":
            break

        print("\nAssistant:\n")
        print(process_professor_query(query))
