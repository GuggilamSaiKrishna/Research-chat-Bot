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
            self.drawString(54, 750, "Vignan Research Matching System — Technical Architecture & Workflow Manual")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)
            
        # Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, "VIGNAN UNIVERSITY — RESEARCH MATCHING CHATBOT DOCUMENTATION")
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

    PRIMARY = colors.HexColor("#1E3A8A")     # Navy Blue
    SECONDARY = colors.HexColor("#0D9488")   # Teal
    DARK_TEXT = colors.HexColor("#0F172A")   # Slate 900
    BORDER_COLOR = colors.HexColor("#E2E8F0")
    BG_LIGHT = colors.HexColor("#F8FAFC")

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=PRIMARY,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=PRIMARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=DARK_TEXT,
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=12,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F1F5F9"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.5,
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
    story.append(Paragraph("Vignan Research Matching Chatbot", title_style))
    story.append(Paragraph("Complete Technical Architecture, Methods, Technologies & Operational Manual", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=12))

    # Executive Summary Box
    summary_text = (
        "<b>Executive Summary:</b> The Vignan Research Matching Chatbot is an intelligent academic platform "
        "powered by <b>LangGraph</b> stateful orchestration, <b>Google Gemini 2.5 Flash LLM</b>, <b>Chroma Vector DB</b>, "
        "<b>BeautifulSoup4 Multithreaded Web Scraper</b>, and <b>Tavily Site-Specific Web Search</b>. "
        "It connects directly to the official Vignan University faculty portal (<code>vignan.ac.in/newvignan/people.php</code>) "
        "to extract, sanitize, vector-index, and retrieve research expertise across <b>717 faculty members</b>."
    )
    story.append(Paragraph(summary_text, callout_style))
    story.append(Spacer(1, 8))

    # Section 1: Technologies & Frameworks Stack
    story.append(Paragraph("1. Technologies & Frameworks Stack", h1_style))
    story.append(Paragraph("The platform is engineered using modern, production-grade AI & web technologies:", body_style))

    tech_table_data = [
        [Paragraph("<b>Layer / Domain</b>", body_style), Paragraph("<b>Technologies Used</b>", body_style), Paragraph("<b>Purpose & Functionality</b>", body_style)],
        [
            Paragraph("<b>Agent Orchestration</b>", body_style),
            Paragraph("LangGraph 0.2+, LangChain Core", body_style),
            Paragraph("Stateful multi-route agent state graph (<code>StateGraph</code>, <code>TypedDict</code>) for intent classification and decision routing.", body_style)
        ],
        [
            Paragraph("<b>Large Language Model</b>", body_style),
            Paragraph("Google Gemini 2.5 Flash<br/>(<code>gemini-2.5-flash</code>)", body_style),
            Paragraph("Advanced reasoning for project ideation, interdisciplinary synthesis, and web research summarization.", body_style)
        ],
        [
            Paragraph("<b>Vector Store & RAG</b>", body_style),
            Paragraph("Chroma DB, Google Embeddings<br/>(<code>gemini-embedding-001</code>)", body_style),
            Paragraph("High-dimensional similarity indexing and hybrid tokenized fallback retrieval engine.", body_style)
        ],
        [
            Paragraph("<b>Live Web Scraper</b>", body_style),
            Paragraph("BeautifulSoup4, Requests,<br/>ThreadPoolExecutor", body_style),
            Paragraph("Concurrent scraping of 717 faculty cards & profile details from <code>vignan.ac.in/newvignan/people.php</code>.", body_style)
        ],
        [
            Paragraph("<b>Web Search Engine</b>", body_style),
            Paragraph("Tavily Search API<br/>(<code>tavily-python</code>)", body_style),
            Paragraph("Domain-restricted live web search (<code>site:vignan.ac.in</code>) for news, events, and department updates.", body_style)
        ],
        [
            Paragraph("<b>Backend Web Server</b>", body_style),
            Paragraph("FastAPI, Uvicorn, Pydantic,<br/>Python-Dotenv", body_style),
            Paragraph("Asynchronous REST API endpoints (<code>/api/student</code>, <code>/api/professor</code>, <code>/api/reload</code>).", body_style)
        ],
        [
            Paragraph("<b>Frontend Web UI</b>", body_style),
            Paragraph("HTML5, CSS3, JavaScript<br/>(Fetch API, DOM manipulation)", body_style),
            Paragraph("Responsive dual-mode Web UI with client-side tag guards, toast alerts, and instant card rendering.", body_style)
        ],
        [
            Paragraph("<b>Cloud Deployment</b>", body_style),
            Paragraph("GitHub, Render Cloud Web Service<br/>(<code>render.yaml</code>, <code>Procfile</code>)", body_style),
            Paragraph("Automated CI/CD deployment pipeline triggering on push to <code>origin/main</code>.", body_style)
        ]
    ]

    t_tech = Table(tech_table_data, colWidths=[110, 150, 244])
    t_tech.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_tech)
    story.append(Spacer(1, 10))

    # Section 2: Detailed End-to-End System Working & Methods
    story.append(Paragraph("2. Detailed System Working & Core Methods", h1_style))
    
    story.append(Paragraph("<b>Method 1: Live Faculty Web Scraping & Data Sanitization Pipeline</b>", h2_style))
    story.append(Paragraph(
        "Faculty profiles are fetched dynamically from the official portal via <code>tools/scrape_vignan_people.py</code>. "
        "The script extracts card IDs from <code>people.php</code> and executes multithreaded POST calls to <code>getfaculty.php</code>. "
        "A rigorous multi-stage cleaning pipeline processes raw text:",
        body_style
    ))
    story.append(Paragraph("• <b>File Path & PDF Removal:</b> Excludes local links (e.g. <code>file:///C:/Users/Admin/Downloads/...</code>) and document extensions.", bullet_style))
    story.append(Paragraph("• <b>Administrative Metrics Filtering:</b> Regex filters strip out noisy tags such as <code>h-index</code>, <code>i-10 index</code>, <code>citations</code>, <code>Ph.D awarded</code>, <code>A.P. Sanctioned</code>, <code>890 Rs.</code>, and publication count numbers.", bullet_style))
    story.append(Paragraph("• <b>Patent & Publication Reclassification:</b> Long titles or strings starting with <i>Patent:</i> are automatically reclassified under <code>publications</code>, keeping <code>research_areas</code> clean and focused.", bullet_style))

    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Method 2: LangGraph Stateful Decision Router</b>", h2_style))
    story.append(Paragraph(
        "Student queries are handled by a stateful graph router in <code>graph/student_graph.py</code> using a <code>StudentState</code> dict. "
        "The graph evaluates query intent dynamically and routes execution into one of 4 distinct nodes:",
        body_style
    ))

    routes_data = [
        [Paragraph("<b>Graph Node</b>", body_style), Paragraph("<b>Condition / Trigger Keyword</b>", body_style), Paragraph("<b>Operational Method</b>", body_style)],
        [
            Paragraph("<code>faculty_rag</code>", body_style),
            Paragraph("Default student query", body_style),
            Paragraph("Queries Chroma vector DB & fallback retriever to return matching faculty cards with percentage scores.", body_style)
        ],
        [
            Paragraph("<code>project</code>", body_style),
            Paragraph("Contains <code>'project'</code>", body_style),
            Paragraph("Retrieves faculty context and invokes Gemini 2.5 Flash to propose 3 tailored research project proposals.", body_style)
        ],
        [
            Paragraph("<code>collaboration</code>", body_style),
            Paragraph("Contains <code>'collaboration'</code>", body_style),
            Paragraph("Analyzes research intersections between top matching professors to craft interdisciplinary proposals.", body_style)
        ],
        [
            Paragraph("<code>web_search</code>", body_style),
            Paragraph("Contains <code>'latest'</code> or <code>'trend'</code>", body_style),
            Paragraph("Queries Tavily Search restricted to <code>site:vignan.ac.in</code> and synthesizes answer with live web links.", body_style)
        ]
    ]

    t_routes = Table(routes_data, colWidths=[100, 150, 254])
    t_routes.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_routes)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Method 3: Hybrid Retrieval & Scoring Formula</b>", h2_style))
    story.append(Paragraph(
        "Faculty matching combines high-dimensional vector search with a token-weighted fallback engine in <code>tools/retriever.py</code>. "
        "Similarity distance scores from Chroma DB are converted to human-readable percentages via:",
        body_style
    ))
    story.append(Paragraph("<code>Cosine Similarity % = max(0.0, 1.0 - (Distance_Score / 2.0)) * 100</code>", code_style))

    story.append(Spacer(1, 8))

    # Section 3: Project Directory Structure
    story.append(Paragraph("3. Complete Project Structure", h1_style))
    dir_str = """sai2/
├── app.py                         # CLI launcher (Student/Professor selection)
├── server.py                      # FastAPI web server (port 8050)
├── config.py                      # Environment loader & domain settings
├── Procfile & render.yaml         # Cloud deployment specifications
├── requirements.txt               # Dependencies list (fastapi, langgraph, bs4, etc.)
├── generate_pdf.py                # PDF documentation builder
├── data/
│   └── faculty_profiles/
│       └── faculty.json           # Sanitized dataset of 717 faculty members
├── graph/
│   └── student_graph.py           # LangGraph state machine & decision router
├── research_agents/
│   ├── student_agent.py           # Student graph runner
│   └── professor_agent.py         # Strategic research analysis agent
├── static/
│   ├── index.html                 # Responsive Web UI landing page
│   ├── app.js                     # Frontend API client & tag filters
│   └── style.css                  # UI styling & animations
└── tools/
    ├── scrape_vignan_people.py    # Multithreaded live website scraper
    ├── load_data.py               # Vector DB preprocessor & indexer
    ├── retriever.py               # Hybrid vector & fallback retriever
    ├── collaboration.py           # Interdisciplinary match tool
    ├── project_suggester.py       # Gemini project ideation engine
    └── tavily_search.py           # College-domain restricted Tavily web search"""
    story.append(Paragraph(dir_str.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    story.append(Spacer(1, 10))

    # Section 4: Execution & Setup Instructions
    story.append(Paragraph("4. Execution & Setup Instructions", h1_style))
    story.append(Paragraph("<b>1. Start Web Server:</b> <code>py server.py</code> $\\rightarrow$ Open <code>http://localhost:8050</code>", bullet_style))
    story.append(Paragraph("<b>2. Run Live Scraper:</b> <code>py tools/scrape_vignan_people.py</code>", bullet_style))
    story.append(Paragraph("<b>3. Run Command-Line Interface:</b> <code>py app.py</code>", bullet_style))
    story.append(Paragraph("<b>4. Render Cloud Deployment:</b> Automated on <code>git push origin main</code> to <code>GuggilamSaiKrishna/Research-chat-Bot</code>.", bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated at: {pdf_path}")

if __name__ == "__main__":
    create_pdf()
