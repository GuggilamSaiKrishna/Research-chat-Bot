import sys
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "Research Matching Chatbot System Architecture & Technical Manual")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, "CONFIDENTIAL & PROPRIETARY — HACKATHON DOCUMENTATION")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        
        self.restoreState()


def create_pdf(filename="Research_Matching_Chatbot_Explanation.pdf"):
    pdf_path = os.path.join(os.getcwd(), filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#1E1B4B")      # Deep Indigo / Navy
    SECONDARY = colors.HexColor("#0284C7")    # Bright Ocean Blue
    ACCENT = colors.HexColor("#0D9488")       # Teal Accent
    DARK_TEXT = colors.HexColor("#1E293B")    # Slate 800
    MUTED_TEXT = colors.HexColor("#475569")   # Slate 600
    BG_LIGHT = colors.HexColor("#F8FAFC")     # Light background
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=SECONDARY,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=DARK_TEXT,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=body_style,
        fontName='Courier',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#0F172A"),
        backColor=BG_LIGHT,
        borderColor=BORDER_COLOR,
        borderWidth=1,
        borderPadding=6,
        spaceBefore=4,
        spaceAfter=6
    )

    callout_style = ParagraphStyle(
        'Callout_Custom',
        parent=body_style,
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#0369A1"),
        backColor=colors.HexColor("#F0F9FF"),
        borderColor=colors.HexColor("#BAE6FD"),
        borderWidth=1,
        borderPadding=8,
        spaceBefore=6,
        spaceAfter=8
    )

    story = []

    # Title Banner
    story.append(Paragraph("Research Matching Chatbot System", title_style))
    story.append(Paragraph("Comprehensive Technical Architecture, Workflow & System Explanation Document", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=15))

    # Executive Summary Box
    summary_text = (
        "<b>Executive Summary:</b> The Research Matching Chatbot is an AI-driven, multi-agent academic platform "
        "built using <b>LangGraph</b>, <b>Google Gemini 2.5 Flash LLM</b>, and <b>Chroma Vector DB</b>. "
        "It acts as a dynamic bridge between students and academic faculty members, providing tailored faculty recommendations "
        "via Retrieval-Augmented Generation (RAG), automated research project ideation, interdisciplinary faculty collaboration "
        "analysis, live web research trend lookup, and professor-oriented strategic research synthesis."
    )
    story.append(Paragraph(summary_text, callout_style))
    story.append(Spacer(1, 10))

    # Section 1: System Overview & Dual-Role Paradigm
    story.append(Paragraph("1. System Overview & Operational Roles", h1_style))
    story.append(Paragraph(
        "The platform operates under two primary user modes tailored for academic ecosystems:",
        body_style
    ))

    roles_data = [
        [
            Paragraph("<b>User Role</b>", body_style),
            Paragraph("<b>Core Capabilities</b>", body_style),
            Paragraph("<b>Underlying Mechanism</b>", body_style)
        ],
        [
            Paragraph("<b>Student Mode</b>", body_style),
            Paragraph("• Faculty RAG Matching<br/>• Project Ideation<br/>• Collaboration Discovery<br/>• Latest Research Web Search", body_style),
            Paragraph("LangGraph State Router (4 routes: <code>faculty_rag</code>, <code>project</code>, <code>collaboration</code>, <code>web_search</code>) connected to Chroma DB and Tavily Search.", body_style)
        ],
        [
            Paragraph("<b>Professor Mode</b>", body_style),
            Paragraph("• Current Research Trends<br/>• Recent Advancements<br/>• Future Research Directions", body_style),
            Paragraph("Direct structured prompt synthesis via Gemini 2.5 Flash delivering structured, high-level research analysis.", body_style)
        ]
    ]

    t_roles = Table(roles_data, colWidths=[110, 200, 194])
    t_roles.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_roles)
    story.append(Spacer(1, 12))

    # Section 2: LangGraph Orchestration Engine
    story.append(Paragraph("2. LangGraph Stateful Workflow Engine", h1_style))
    story.append(Paragraph(
        "At the core of the Student Mode execution is a <b>LangGraph StateGraph</b> router (defined in <code>graph/student_graph.py</code>). "
        "Unlike basic chain-based LLM calls, LangGraph maintains a state dictionary (<code>StudentState</code>) and evaluates intent dynamically.",
        body_style
    ))

    story.append(Paragraph("<b>State Schema Definition (<code>StudentState</code>):</b>", h2_style))
    code_state = """class StudentState(TypedDict):
    query: str       # Original prompt entered by the student
    route: str       # Target route determined by classifier
    response: str    # Generated final text response or synthesis
    matches: list    # List of retrieved matching faculty dictionaries
    context: str     # Formatted text context of top faculty profiles"""
    story.append(Paragraph(code_state.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    story.append(Paragraph("<b>Graph Nodes & Routing Logic:</b>", h2_style))
    story.append(Paragraph("• <b>START → Classify Node:</b> Analyzes incoming query string keywords to set <code>route</code> flag.", bullet_style))
    story.append(Paragraph("• <b>Conditional Edge (<code>route_query</code>):</b> Directs state execution based on route classification:", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;1. <code>collaboration</code> → Executes <code>collaboration_node</code> (Finds top 2 faculty pairs).", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;2. <code>web_search</code> → Executes <code>web_search_node</code> (Invokes Tavily API + Gemini synthesis).", bullet_style))
    story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;3. <code>project</code> or <code>faculty_rag</code> → Executes <code>faculty_retrieve_node</code> (Chroma DB similarity search).", bullet_style))

    graph_flow_data = [
        [Paragraph("<b>Intent Classifier Keyword Rule</b>", body_style), Paragraph("<b>Target Route</b>", body_style), Paragraph("<b>Execution Flow & Output</b>", body_style)],
        [Paragraph("Contains <code>'collaboration'</code>", body_style), Paragraph("<code>collaboration</code>", body_style), Paragraph("Retrieves top 2 faculty profiles and crafts interdisciplinary synergy reasoning.", body_style)],
        [Paragraph("Contains <code>'latest'</code> or <code>'trend'</code>", body_style), Paragraph("<code>web_search</code>", body_style), Paragraph("Queries Tavily search API for real-time web results and synthesizes summary.", body_style)],
        [Paragraph("Contains <code>'project'</code>", body_style), Paragraph("<code>project</code>", body_style), Paragraph("Retrieves faculty matches and generates 3 detailed project ideas with difficulty ratings.", body_style)],
        [Paragraph("Default query", body_style), Paragraph("<code>faculty_rag</code>", body_style), Paragraph("Performs Chroma DB RAG search and outputs matched faculty with similarity score.", body_style)],
    ]
    t_graph = Table(graph_flow_data, colWidths=[140, 100, 264])
    t_graph.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_graph)
    story.append(Spacer(1, 14))

    # Section 3: Data Vectorization & Hybrid RAG Infrastructure
    story.append(Paragraph("3. Vector Database & RAG Infrastructure", h1_style))
    story.append(Paragraph(
        "Faculty profiles stored in <code>data/faculty_profiles/faculty.json</code> are converted into vector embeddings "
        "using Google's <b>gemini-embedding-001</b> model and persisted locally in <b>Chroma DB</b>.",
        body_style
    ))

    story.append(Paragraph("<b>Key Engineering Architectural Highlights:</b>", h2_style))
    story.append(Paragraph("• <b>SHA-256 Cache Syncing:</b> A <code>.data_hash</code> file stores the SHA-256 hash of <code>faculty.json</code>. Database re-indexing is triggered automatically only when data modification is detected.", bullet_style))
    story.append(Paragraph("• <b>Strict Publication Filtering Rule:</b> Only faculty members with listed publications are indexed into the vector store, ensuring high accuracy academic retrieval.", bullet_style))
    story.append(Paragraph("• <b>Similarity Score Normalization:</b> Distance scores returned by Chroma vector similarity searches are converted into percentage match metrics using the formula:<br/>"
                           "&nbsp;&nbsp;&nbsp;&nbsp;<code>Cosine Similarity % = max(0.0, 1.0 - (Score / 2.0)) * 100</code>", bullet_style))
    story.append(Paragraph("• <b>Robust Hybrid Fallback Engine:</b> If vector DB loading or embedding API is unavailable, <code>retriever.py</code> gracefully falls back to an in-memory tokenized keyword matching engine across faculty profiles and publications.", bullet_style))

    story.append(Spacer(1, 10))

    # Section 4: Deep Dive into Tool Modules
    story.append(Paragraph("4. Tool Modules & Agent Extensions", h1_style))

    tools_info = [
        ("tools/load_data.py", "Handles Chroma DB initialization, SHA-256 hash tracking, JSON document transformation, and embedding indexing with gemini-embedding-001."),
        ("tools/retriever.py", "Performs vector similarity search against Chroma DB with exact publication keyword boost and fallback tokenized matching."),
        ("tools/project_suggester.py", "Uses Gemini 2.5 Flash to generate 3 customized project ideas, difficulty levels, required skills, and expected outcomes based on matched faculty context."),
        ("tools/collaboration.py", "Analyzes research intersections between top matching professors to propose collaborative interdisciplinary research initiatives."),
        ("tools/tavily_search.py", "Integrates Tavily Web Search API to fetch live external web context for queries regarding breaking research news and latest industry trends."),
        ("research_agents/professor_agent.py", "Dedicated agent module for professors that synthesizes current trends, recent advances, and future research directions.")
    ]

    for tool_name, tool_desc in tools_info:
        story.append(Paragraph(f"• <b><code>{tool_name}</code></b>: {tool_desc}", bullet_style))

    story.append(Spacer(1, 12))

    # Section 5: Streamlit Web UI Architecture
    story.append(Paragraph("5. User Interface & Streamlit Web Layer", h1_style))
    story.append(Paragraph(
        "The application features a modern Streamlit user interface (<code>streamlit_app.py</code>) designed for usability:",
        body_style
    ))
    story.append(Paragraph("• <b>Dual-Role Landing Screen:</b> Interactive selection between <i>Student Mode</i> and <i>Professor Mode</i>.", bullet_style))
    story.append(Paragraph("• <b>Dynamic Sidebar Controls:</b> Provides role indicator, role switcher, chat clearing, quick examples, and a manual <i>🔄 Reload / Sync Data</i> button to force vector index rebuilds.", bullet_style))
    story.append(Paragraph("• <b>Formatted Match Output:</b> Displays faculty cards with percentage match indicators, department, mobile contact info, research topics, and publications.", bullet_style))
    story.append(Paragraph("• <b>Quick Prompt Chips:</b> Enables single-click prompt insertion for standard student and professor queries.", bullet_style))

    story.append(Spacer(1, 12))

    # Section 6: File & Directory Directory Structure
    story.append(Paragraph("6. Project Directory Map", h1_style))
    dir_structure = """sai2/
├── app.py                    # Command-line interface (CLI) launcher
├── streamlit_app.py          # Web GUI application (Streamlit)
├── config.py                 # Environment & API Key loader (.env)
├── requirements.txt          # Dependencies list
├── data/
│   └── faculty_profiles/
│       └── faculty.json      # Structured JSON database of faculty members
├── graph/
│   └── student_graph.py      # LangGraph state graph definition & router
├── research_agents/
│   ├── student_agent.py      # Student query handler & graph runner
│   └── professor_agent.py    # Professor research query processor
├── tools/
│   ├── load_data.py          # Data preprocessor & Chroma DB loader
│   ├── retriever.py          # Hybrid RAG retriever engine
│   ├── collaboration.py      # Faculty collaboration match tool
│   ├── project_suggester.py  # Gemini project ideation engine
│   ├── rag.py                # Standalone RAG CLI demo script
│   └── tavily_search.py      # Tavily live web search API client
└── chroma_db/                # Local persistent Chroma vector store"""
    story.append(Paragraph(dir_structure.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    story.append(Spacer(1, 14))

    # Section 7: Verification & Quickstart
    story.append(Paragraph("7. Setup, Environment & Execution Guide", h1_style))
    story.append(Paragraph("<b>1. Environment Configuration (<code>.env</code>):</b>", h2_style))
    env_code = """GOOGLE_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here"""
    story.append(Paragraph(env_code.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    story.append(Paragraph("<b>2. Run Streamlit Application:</b>", h2_style))
    story.append(Paragraph("<code>streamlit run streamlit_app.py</code>", code_style))

    story.append(Paragraph("<b>3. Run Command-Line Chatbot Interface:</b>", h2_style))
    story.append(Paragraph("<code>py app.py</code>", code_style))

    story.append(Paragraph("<b>4. Rebuild Vector Index manually:</b>", h2_style))
    story.append(Paragraph("<code>py tools/load_data.py</code>", code_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {pdf_path}")

if __name__ == "__main__":
    create_pdf()
