from config import get_genai_client

def suggest_project(context, interest):

    prompt = f"""
You are an AI Research Guide.

Faculty Research:
{context}

Student Interest:
{interest}

Suggest:
1. Three project ideas
2. Difficulty (Easy/Medium/Hard)
3. Required Skills
4. Expected Outcome.

Keep the answer short and clear.
"""

    client = get_genai_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    return response.text