import streamlit as st

from config import get_google_api_key
from research_agents.professor_agent import process_professor_query
from research_agents.student_agent import process_student_query
from tools.load_data import ensure_chroma_loaded

ROUTE_LABELS = {
    "faculty_rag": "Faculty matching",
    "project": "Project suggestions",
    "collaboration": "Collaboration",
    "web_search": "Web search",
}

STUDENT_EXAMPLES = [
    "machine learning for healthcare",
    "project ideas in computer vision",
    "collaboration for renewable energy research",
    "latest trends in blockchain",
]

PROFESSOR_EXAMPLES = [
    "What are current trends in quantum computing?",
    "Recent advances in large language models",
    "Future research directions in biomedical engineering",
]

st.set_page_config(
    page_title="Research Matching Chatbot",
    page_icon="🎓",
    layout="wide",
)


def init_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "mode" not in st.session_state:
        st.session_state.mode = None


def reset_to_menu():
    st.session_state.mode = None
    st.session_state.messages = []


def format_faculty_matches(matches, top_n: int = 5) -> str:
    lines = ["### Related Faculty\n"]
    for faculty in matches[:top_n]:
        mobile = faculty.get("mobile_number")
        mobile_line = f"- Mobile: {mobile}  \n" if mobile and mobile != "N/A" else ""
        pubs = faculty.get("publications", "").strip()
        pubs_line = f"- Publications: {pubs}  \n" if pubs and pubs != "N/A" else "- Publications: None listed  \n"
        lines.append(
            f"**{faculty['name']}** — {faculty['score']}% match  \n"
            f"- Department: {faculty['department']}  \n"
            f"{mobile_line}"
            f"- Research areas: {faculty['research_areas']}  \n"
            f"{pubs_line}"
        )
    return "\n".join(lines)


def handle_student_query(query: str) -> str:
    result = process_student_query(query)
    route = result["route"]
    parts = [f"*Route: {ROUTE_LABELS.get(route, route)}*\n"]

    if route in ("faculty_rag", "project"):
        matches = result["matches"]
        if not matches:
            return (
                "No matching faculty found. "
                "Run `py tools/load_data.py` to load faculty profiles."
            )

        parts.append(format_faculty_matches(matches))

        if route == "project" and result["project_suggestions"]:
            parts.append("### Suggested Projects\n")
            parts.append(result["project_suggestions"])

        return "\n".join(parts)

    if route == "collaboration":
        parts.append("### Suggested Collaboration\n")

    parts.append(result["response"])
    return "\n".join(parts)


def handle_professor_query(query: str) -> str:
    return process_professor_query(query)


def render_role_selection():
    st.title("Research Matching Chatbot")
    st.caption("Choose how you want to use the assistant.")

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.subheader("Student")
        st.markdown(
            "Find faculty by research interest, get project ideas, "
            "discover collaborations, and search latest trends."
        )
        if st.button("Enter as Student", type="primary", use_container_width=True):
            st.session_state.mode = "Student"
            st.session_state.messages = []
            st.rerun()

    with col2:
        st.subheader("Professor")
        st.markdown(
            "Ask research questions and get insights on current trends, "
            "recent advancements, and future directions in your field."
        )
        if st.button("Enter as Professor", type="primary", use_container_width=True):
            st.session_state.mode = "Professor"
            st.session_state.messages = []
            st.rerun()


def render_sidebar():
    mode = st.session_state.mode

    with st.sidebar:
        st.header("Menu")
        st.info(f"**Current role:** {mode}")

        if st.button("Switch role", use_container_width=True):
            reset_to_menu()
            st.rerun()

        st.divider()

        if mode == "Student":
            st.markdown("**What you can do**")
            st.markdown(
                "- Find matching faculty by topic\n"
                "- Add *project* for project ideas\n"
                "- Add *collaboration* for faculty pairs\n"
                "- Add *latest* or *trend* for web search"
            )
        else:
            st.markdown("**Professor operations**")
            st.markdown(
                "- Ask about **current research trends**\n"
                "- Ask about **recent advancements**\n"
                "- Ask about **future research directions**"
            )

        if st.button("🔄 Reload / Sync Data", use_container_width=True):
            with st.spinner("Updating faculty database..."):
                ensure_chroma_loaded(force=True)
            st.success("Faculty data reloaded!")
            st.rerun()

        if st.button("Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def render_example_buttons(examples, label):
    st.markdown(f"**{label}**")
    cols = st.columns(len(examples))
    for col, example in zip(cols, examples):
        with col:
            if st.button(example, key=f"example_{example}", use_container_width=True):
                return example
    return None


def render_chat():
    mode = st.session_state.mode

    st.title(f"{mode} Mode")
    if mode == "Student":
        st.caption("Enter a research topic to find matching faculty and related help.")
    else:
        st.caption(
            "Ask research questions — the assistant covers trends, "
            "advancements, and future directions."
        )

    render_sidebar()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    examples = STUDENT_EXAMPLES if mode == "Student" else PROFESSOR_EXAMPLES
    example_label = "Try an example" if not st.session_state.messages else "Quick prompts"
    example_query = render_example_buttons(examples, example_label)

    placeholder = (
        "Research topic, e.g. machine learning for healthcare"
        if mode == "Student"
        else "Professor question, e.g. recent advances in quantum computing"
    )

    prompt = example_query or st.chat_input(placeholder)

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if mode == "Student":
                    response = handle_student_query(prompt)
                else:
                    response = handle_professor_query(prompt)

            st.markdown(response)
            st.session_state.messages.append(
                {"role": "assistant", "content": response}
            )


def main():
    init_session_state()

    if not get_google_api_key():
        st.error(
            "Missing API key. Add `GOOGLE_API_KEY` or `GEMINI_API_KEY` "
            "to your `.env` file or Streamlit secrets."
        )
        st.stop()

    ensure_chroma_loaded()

    if st.session_state.mode is None:
        render_role_selection()
    else:
        render_chat()


if __name__ == "__main__":
    main()

