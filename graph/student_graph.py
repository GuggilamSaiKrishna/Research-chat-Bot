from typing import Literal, TypedDict

from google import genai
from langgraph.graph import END, START, StateGraph

from config import get_google_api_key
from tools.collaboration import collaboration_match
from tools.retriever import retrieve_faculty
from tools.tavily_search import web_search

client = genai.Client(api_key=get_google_api_key())


class StudentState(TypedDict):
    query: str
    route: str
    response: str
    matches: list
    context: str


def classify_query(state: StudentState) -> StudentState:
    query = state["query"].lower()

    if "collaboration" in query:
        route = "collaboration"
    elif "latest" in query or "trend" in query:
        route = "web_search"
    elif "project" in query:
        route = "project"
    else:
        route = "faculty_rag"

    return {"route": route}


def route_query(
    state: StudentState,
) -> Literal["collaboration", "web_search", "project", "faculty_rag"]:
    return state["route"]


def collaboration_node(state: StudentState) -> StudentState:
    return {"response": collaboration_match(state["query"])}


def web_search_node(state: StudentState) -> StudentState:
    search_result = web_search(state["query"])

    prompt = f"""
You are an official college research assistant for Vignan University.

Answer the user's question clearly and accurately based on the college website search results below.
Include relevant URLs/links from the results whenever applicable so users can visit the college website directly.

College Web Search Results:
{search_result}

Question:
{state["query"]}
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    return {"response": response.text}



def faculty_retrieve_node(state: StudentState) -> StudentState:
    matches = retrieve_faculty(state["query"])
    context = "\n\n".join(faculty["content"] for faculty in matches)

    return {
        "matches": matches,
        "context": context,
        "response": "",
    }


def build_student_graph():
    graph = StateGraph(StudentState)

    graph.add_node("classify", classify_query)
    graph.add_node("collaboration", collaboration_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("faculty_retrieve", faculty_retrieve_node)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges(
        "classify",
        route_query,
        {
            "collaboration": "collaboration",
            "web_search": "web_search",
            "project": "faculty_retrieve",
            "faculty_rag": "faculty_retrieve",
        },
    )
    graph.add_edge("collaboration", END)
    graph.add_edge("web_search", END)
    graph.add_edge("faculty_retrieve", END)

    return graph.compile()


student_graph = build_student_graph()
