from graph.student_graph import student_graph
from tools.project_suggester import suggest_project


def display_faculty_matches(matches, top_n: int = 5):
    print("\nRelated Faculty (sorted by match)\n")

    for i, faculty in enumerate(matches[:top_n], start=1):
        print(f"{i}. {faculty['name']} — {faculty['score']}% Match")
        print(f"   Department: {faculty['department']}")
        if faculty.get("mobile_number") and faculty["mobile_number"] != "N/A":
            print(f"   Mobile: {faculty['mobile_number']}")
        print(f"   Research Areas: {faculty['research_areas']}")
        pubs = faculty.get("publications", "").strip()
        print(f"   Publications: {pubs if pubs and pubs != 'N/A' else 'None listed'}")
        print()


def process_student_query(query: str) -> dict:
    result = student_graph.invoke(
        {
            "query": query,
            "route": "",
            "response": "",
            "matches": [],
            "context": "",
        }
    )

    route = result["route"]
    output = {
        "route": route,
        "response": result.get("response", ""),
        "matches": result.get("matches", []),
        "project_suggestions": None,
    }

    if route == "project" and output["matches"]:
        output["project_suggestions"] = suggest_project(result["context"], query)

    return output


def student_chat():
    print("\n========== Student Mode ==========")
    print("Enter a research topic to find matching faculty.")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Research topic: ").strip()

        if not query:
            continue

        if query.lower() == "exit":
            print("Goodbye!")
            break

        output = process_student_query(query)
        route = output["route"]

        if route in ("faculty_rag", "project"):
            matches = output["matches"]

            if not matches:
                print("\nNo faculty found. Run: py tools/load_data.py\n")
                continue

            display_faculty_matches(matches)

            if route == "project" and output["project_suggestions"]:
                print("Suggested Projects\n")
                print(output["project_suggestions"])
                print()

            continue

        if route == "collaboration":
            print("\nSuggested Collaboration\n")

        print(output["response"])
        print()
