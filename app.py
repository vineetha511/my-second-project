
import streamlit as st
import sqlite3
import pandas as pd
import hashlib
import time
import requests
import io
import PyPDF2
from datetime import datetime

# -----------------------------------------------------------------------------
# CONFIGURATION & THEME
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="ResearchHub AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark + Purple Theme
st.markdown("""
<style>
    /* Global Reset & Dark Theme */
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #12141c;
        border-right: 1px solid #2b2d3e;
    }
    
    [data-testid="stSidebar"] .stRadio > div {
        flex-direction: column;
        gap: 0.5rem;
    }

    [data-testid="stSidebar"] .stRadio label {
        background-color: transparent;
        color: #b0b3c5;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        transition: all 0.2s ease;
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        border: 1px solid transparent;
        cursor: pointer;
    }

    [data-testid="stSidebar"] .stRadio label:hover {
        background-color: #1e2029;
        color: #ffffff;
    }

    /* Active Sidebar Item */
    [data-testid="stSidebar"] .stRadio div[aria-checked="true"] > label {
        background-color: #6c5ce7 !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(108, 92, 231, 0.3);
        border: none;
    }

    /* Headers */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700 !important;
    }
    h1 { font-size: 2.2rem !important; margin-bottom: 1.5rem !important; }
    h2 { font-size: 1.8rem !important; margin-bottom: 1rem !important; }
    h3 { font-size: 1.4rem !important; margin-bottom: 0.8rem !important; }

    /* Cards */
    .card {
        background-color: #1a1c24;
        border: 1px solid #2d2f36;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        border-color: #6c5ce7;
    }

    .stat-card {
        background: linear-gradient(135deg, #1a1c24 0%, #242630 100%);
        border-left: 4px solid #6c5ce7;
    }

    /* Buttons */
    .stButton button {
        background-color: #6c5ce7;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        transition: all 0.2s ease;
        box-shadow: 0 4px 6px rgba(108, 92, 231, 0.2);
    }
    
    .stButton button:hover {
        background-color: #5b4cc4;
        box-shadow: 0 6px 12px rgba(108, 92, 231, 0.4);
        transform: translateY(-1px);
    }

    /* Inputs */
    .stTextInput input, .stSelectbox div, .stTextArea textarea {
        background-color: #1a1c24 !important;
        color: #ffffff !important;
        border: 1px solid #363945 !important;
        border-radius: 8px;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #6c5ce7 !important;
        box-shadow: 0 0 0 1px #6c5ce7 !important;
    }

    /* Dividers */
    hr {
        border-color: #2d2f36;
    }

    /* Tables/Dataframes */
    [data-testid="stDataFrame"] {
        border: 1px solid #2d2f36;
        border-radius: 8px;
        overflow: hidden;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #1a1c24 !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0e1117; 
    }
    ::-webkit-scrollbar-thumb {
        background: #363945; 
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #4b4f5d; 
    }
    
    /* Document List Item */
    .doc-item {
        padding: 10px;
        border-radius: 6px;
        cursor: pointer;
        margin-bottom: 5px;
        color: #b0b3c5;
        transition: background 0.2s;
    }
    .doc-item:hover {
        background-color: #2d2f36;
        color: white;
    }
    .doc-item.active {
        background-color: #2d2f36;
        color: #6c5ce7;
        border-left: 3px solid #6c5ce7;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# DATABASE MANAGEMENT
# -----------------------------------------------------------------------------

DB_FILE = 'researchhub.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS workspaces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS papers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER,
        title TEXT NOT NULL,
        authors TEXT,
        abstract TEXT,
        content TEXT,
        source TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS chats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workspace_id INTEGER,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workspace_id) REFERENCES workspaces (id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title TEXT NOT NULL,
        content TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    conn.commit()
    conn.close()

init_db()

# -----------------------------------------------------------------------------
# AUTHENTICATION & DATA LAYERS
# -----------------------------------------------------------------------------

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

def get_workspaces(user_id):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM workspaces WHERE user_id = ?", conn, params=(user_id,))
    conn.close()
    return df

def create_workspace(user_id, name, description):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO workspaces (user_id, name, description) VALUES (?, ?, ?)", (user_id, name, description))
    conn.commit()
    conn.close()

def add_paper(workspace_id, title, authors, abstract, content, source):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO papers (workspace_id, title, authors, abstract, content, source) VALUES (?, ?, ?, ?, ?, ?)", (workspace_id, title, authors, abstract, content, source))
    conn.commit()
    conn.close()

def get_papers(workspace_id):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM papers WHERE workspace_id = ?", conn, params=(workspace_id,))
    conn.close()
    return df

def save_chat(workspace_id, role, content):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO chats (workspace_id, role, content) VALUES (?, ?, ?)", (workspace_id, role, content))
    conn.commit()
    conn.close()

def get_chat_history(workspace_id):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT role, content FROM chats WHERE workspace_id = ? ORDER BY id ASC", conn, params=(workspace_id,))
    conn.close()
    return df.to_dict('records')

def get_docs(user_id):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM docs WHERE user_id = ?", conn, params=(user_id,))
    conn.close()
    return df

def save_doc(user_id, doc_id, title, content):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if doc_id:
        c.execute("UPDATE docs SET title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?", (title, content, doc_id, user_id))
    else:
        c.execute("INSERT INTO docs (user_id, title, content) VALUES (?, ?, ?)", (user_id, title, content))
    conn.commit()
    conn.close()

# -----------------------------------------------------------------------------
# AI ENGINE
# -----------------------------------------------------------------------------

def get_groq_response(messages, api_key, model="llama-3.3-70b-versatile"):
    try:
        from groq import Groq
        
        client = Groq(api_key=api_key)

        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.7
        )

        return chat_completion.choices[0].message.content

    except Exception as e:
        return f"Groq API Error: {str(e)}"


def mock_llm_response(prompt, context=""):
    time.sleep(1)
    if "summarize" in prompt.lower():
        return f"**Summary**\n\nThe selected papers provide a comprehensive view on the topic. Key findings include improved model efficiency and robust evaluation metrics.\n(Mock AI Response)"
    elif "extract" in prompt.lower():
        return "**Key Insights**\n- Insight 1: Scalability is crucial.\n- Insight 2: Data quality variants affect performance.\n(Mock AI Response)"
    else:
        return f"This is a mock response to '{prompt}'. Connect an API key for real inference."

def generate_ai_response(prompt, context_papers, api_key=None):
    context_text = ""
    for paper in context_papers:
        context_text += f"Title: {paper['title']}\nAbstract: {paper['abstract']}\nContent: {paper['content'][:800]}\n\n"
    
    system_prompt = f"You are a helpful Research Assistant.\nCONTEXT:\n{context_text}"
    
    if api_key and api_key.strip() != "":
        messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}]
        return get_groq_response(messages, api_key)
    else:
        return mock_llm_response(prompt, context_text)

# -----------------------------------------------------------------------------
# SEARCH ENGINE
# -----------------------------------------------------------------------------

def search_arxiv(query, max_results=5):
    base_url = "http://export.arxiv.org/api/query?"
    search_query = f"search_query=all:{query}&start=0&max_results={max_results}"
    try:
        response = requests.get(base_url + search_query)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        papers = []
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
            summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
            authors = [a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]
            link = entry.find('atom:id', ns).text
            papers.append({'title': title, 'abstract': summary, 'authors': ", ".join(authors), 'source': link, 'content': summary})
        return papers
    except:
        return []

# -----------------------------------------------------------------------------
# UI COMPONENTS
# -----------------------------------------------------------------------------

def sidebar_nav():
    with st.sidebar:
        st.markdown("""
        <div style="padding: 1rem 0; text-align: center; margin-bottom: 1rem;">
            <h2 style="margin:0; background: linear-gradient(45deg, #a29bfe, #6c5ce7); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">ResearchHub</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if 'user_id' in st.session_state:
            # Styled Navigation
            nav_options = {
                "Home": "🏠",
                "Dashboard": "📊",
                "Search Papers": "🔍",
                "Workspaces": "📁",
                "AI Tools": "🧠",
                "Upload PDF": "📤",
                "Doc Space": "📝",
                "AI Chatbot": "💬"
            }
            
            selected = st.radio(
                "Navigate",
                options=list(nav_options.keys()),
                format_func=lambda x: f"{nav_options[x]}  {x}",
                label_visibility="collapsed"
            )
            
            st.markdown("---")
            if st.button("Logout", use_container_width=True):
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()
                
            with st.expander("⚙️ Settings"):
                if 'groq_key' not in st.session_state:
                    st.session_state['groq_key'] = ""

                st.session_state['groq_key'] = st.text_input(
                  "Groq API Key",
    value=st.session_state['groq_key'],
    type="password"
)

            
            return selected
        else:
            return "Login"

# -----------------------------------------------------------------------------
# PAGES
# -----------------------------------------------------------------------------

def page_login():
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div class="card" style="text-align: center;">
            <h1>ResearchHub AI</h1>
            <p style="color: #b0b3c5;">Your automated research assistant.</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form("login"):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In", use_container_width=True):
                    uid = authenticate_user(u, p)
                    if uid:
                        st.session_state['user_id'] = uid
                        st.session_state['username'] = u
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
        
        with tab2:
            with st.form("register"):
                nu = st.text_input("New Username")
                np = st.text_input("New Password", type="password")
                if st.form_submit_button("Create Account", use_container_width=True):
                    if register_user(nu, np):
                        st.success("Account created! Please login.")
                    else:
                        st.error("Username taken")

def page_home():
    st.markdown("""
    <div style="text-align: center; padding: 4rem 2rem;">
        <h1 style="font-size: 3.5rem; background: linear-gradient(135deg, #fff 0%, #a29bfe 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Accelerate Your Research
        </h1>
        <p style="font-size: 1.25rem; color: #b0b3c5; max-width: 600px; margin: 0 auto 3rem auto;">
            ResearchHub AI connects you with millions of papers, provides instant AI summaries, and helps you draft insights effortlessly.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    features = [
        ("🔍 Discover", "Search arXiv instantly and build your library."),
        ("🧠 Analyze", "Use AI to summarize and extract key insights."),
        ("📝 Create", "Draft literature reviews and notes in one place.")
    ]
    
    for col, (title, desc) in zip([col1, col2, col3], features):
        with col:
            st.markdown(f"""
            <div class="card" style="height: 200px;">
                <h3>{title}</h3>
                <p style="color: #b0b3c5;">{desc}</p>
            </div>
            """, unsafe_allow_html=True)

def page_dashboard():
    st.title("Dashboard")
    uid = st.session_state['user_id']
    workspaces = get_workspaces(uid)
    
    # Stats
    col1, col2, col3 = st.columns(3)
    
    total_papers = 0
    if not workspaces.empty:
        for wid in workspaces['id']:
            total_papers += len(get_papers(wid))
            
    stats = [
        ("Total Workspaces", len(workspaces), "📂"),
        ("Papers Imported", total_papers, "📄"),
        ("Active Session", "Online", "🟢")
    ]
    
    for col, (label, val, icon) in zip([col1, col2, col3], stats):
        with col:
            st.markdown(f"""
            <div class="card stat-card">
                <div style="font-size: 2rem;">{icon}</div>
                <div style="margin-top: 10px; font-size: 2.5rem; font-weight: 700;">{val}</div>
                <div style="color: #b0b3c5;">{label}</div>
            </div>
            """, unsafe_allow_html=True)
            
    # Workspaces Grid
    st.markdown("### Your Workspaces")
    
    # Create New Button
    if st.button("➕ Create New Workspace"):
        with st.form("quick_create"):
            name = st.text_input("Name")
            desc = st.text_area("Description")
            if st.form_submit_button("Create"):
                create_workspace(uid, name, desc)
                st.rerun()

    if not workspaces.empty:
        cols = st.columns(3)
        for i, (idx, row) in enumerate(workspaces.iterrows()):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="card">
                    <h4>{row['name']}</h4>
                    <p style="font-size: 0.9rem; color: #b0b3c5;">{row['description']}</p>
                    <p style="font-size: 0.8rem; color: #6c5ce7;">{row['created_at'][:10]}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Open {row['name']}", key=f"open_{row['id']}", use_container_width=True):
                    st.session_state['current_workspace_id'] = row['id']
                    st.session_state['current_workspace_name'] = row['name']
                    st.success(f"Active: {row['name']}")

def page_search():
    st.title("Search Papers")
    
    if 'current_workspace_id' not in st.session_state:
        st.warning("⚠️ Please select a workspace from Dashboard or Workspaces tab first.")
        return
        
    c1, c2 = st.columns([4,1])
    with c1:
        query = st.text_input("Keywords", placeholder="e.g. Generative Adversarial Networks", label_visibility="collapsed")
    with c2:
        search_btn = st.button("Search arXiv", use_container_width=True)
        
    if search_btn and query:
        with st.spinner("Searching..."):
            st.session_state['search_results'] = search_arxiv(query)
            
    if 'search_results' in st.session_state:
        st.markdown(f"Found {len(st.session_state['search_results'])} results")
        for i, p in enumerate(st.session_state['search_results']):
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <div style="display:flex; justify-content:space-between;">
                        <h4 style="color:#a29bfe;">{p['title']}</h4>
                    </div>
                    <p style="color: #ffffff; font-style:italic; font-size: 0.9rem;">{p['authors']}</p>
                    <p style="color: #b0b3c5; font-size: 0.95rem;">{p['abstract'][:250]}...</p>
                    <a href="{p['source']}" style="color: #6c5ce7; text-decoration: none; font-size: 0.9rem;" target="_blank">View Source</a>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"📥 Import to {st.session_state['current_workspace_name']}", key=f"add_{i}"):
                    add_paper(st.session_state['current_workspace_id'], p['title'], p['authors'], p['abstract'], p['content'], p['source'])
                    st.success("Imported!")

def page_ai_tools():
    st.title("AI Tools")
    
    if 'current_workspace_id' not in st.session_state:
        st.warning("⚠️ Select a workspace first.")
        return

    papers = get_papers(st.session_state['current_workspace_id'])
    if papers.empty:
        st.info("No papers in this workspace.")
        return

    # Selection
    st.markdown("### 1. Select Papers")
    selected_titles = st.multiselect("Choose papers for analysis", papers['title'].tolist())
    
    st.markdown("### 2. Choose Action")
    col1, col2, col3 = st.columns(3)
    
    action = None
    
    with col1:
        st.markdown('<div class="card" style="text-align: center;"><h4>📑</h4></div>', unsafe_allow_html=True)
        if st.button("Generate Summaries", use_container_width=True):
            action = "Summarize"
            
    with col2:
        st.markdown('<div class="card" style="text-align: center;"><h4>💡</h4></div>', unsafe_allow_html=True)
        if st.button("Extract Key Insights", use_container_width=True):
            action = "Extract Key Insights"
            
    with col3:
        st.markdown('<div class="card" style="text-align: center;"><h4>📖</h4></div>', unsafe_allow_html=True)
        if st.button("Literature Review", use_container_width=True):
            action = "Generate Literature Review"
            
    if action:
        if not selected_titles:
            st.warning("⚠️ Please select at least one paper to analyze.")
        else:
            st.markdown("---")
            st.markdown(f"### Results: {action}")
            with st.spinner("Processing..."):
                subset = papers[papers['title'].isin(selected_titles)].to_dict('records')
                prompt = f"Perform task: {action} on these papers."
                res = generate_ai_response(prompt, subset, st.session_state.get('groq_key'))
                
                st.markdown(f'''
                <div class="card">
                    {res}
                </div>
                ''', unsafe_allow_html=True)

def page_upload():
    st.title("Upload PDF")
    
    if 'current_workspace_id' not in st.session_state:
        st.warning("⚠️ Select a workspace first.")
        return

    st.markdown("""
    <div class="card" style="text-align: center; border-style: dashed; padding: 3rem;">
        <h3>📤 Drag and Drop PDF here</h3>
        <p style="color: #b0b3c5;">Limit 200MB per file.</p>
    </div>
    """, unsafe_allow_html=True)
    
    f = st.file_uploader("", type="pdf", label_visibility="collapsed")
    
    if f:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Save to Workspace", use_container_width=True):
                try:
                    reader = PyPDF2.PdfReader(f)
                    text = "".join([p.extract_text() for p in reader.pages])
                    add_paper(st.session_state['current_workspace_id'], f.name, "Uploaded", text[:500], text, "Local")
                    st.success("Saved!")
                except Exception as e:
                    st.error(f"Error: {e}")
        with col2:
             if st.button("Generate Summary", use_container_width=True):
                 st.info("Using AI to summarize uploaded doc...")

def page_doc_space():
    st.title("Doc Space")
    uid = st.session_state['user_id']
    docs = get_docs(uid)
    
    c1, c2 = st.columns([1, 3])
    
    with c1:
        st.markdown("### My Docs")
        if st.button("➕ New Doc", use_container_width=True):
            st.session_state['active_doc'] = {'id': None, 'title': 'Untitled', 'content': ''}
            st.rerun()
            
        for i, row in docs.iterrows():
            if st.button(f"📄 {row['title']}", key=f"doc_list_{row['id']}", use_container_width=True):
                st.session_state['active_doc'] = row.to_dict()
                st.rerun()
                
    with c2:
        if 'active_doc' in st.session_state:
            d = st.session_state['active_doc']
            new_title = st.text_input("Document Title", value=d['title'])
            new_content = st.text_area("Content", value=d['content'], height=600)
            
            if st.button("Save Changes"):
                save_doc(uid, d['id'], new_title, new_content)
                st.success("Saved")
                # Refresh state
                st.session_state['active_doc']['id'] = d['id'] # Needs reload logic for real ID fetch if new
                st.session_state['active_doc']['title'] = new_title
                st.session_state['active_doc']['content'] = new_content
        else:
            st.info("Select or create a document to start writing.")

def page_workspaces_list():
    st.title("Workspaces")
    # Using Dashboard grid logic here ideally, or list view
    page_dashboard() # Reuse dashboard logic for list view simplicity as they overlap

def page_chatbot():
    st.title("AI Chatbot")
    if 'current_workspace_id' not in st.session_state:
        st.warning("Select workspace.")
        return
        
    ws_id = st.session_state['current_workspace_id']
    st.caption(f"Context: {st.session_state['current_workspace_name']}")
    
    msgs = get_chat_history(ws_id)
    for m in msgs:
        with st.chat_message(m['role']):
            st.write(m['content'])
            
    if p := st.chat_input():
        save_chat(ws_id, "user", p)
        with st.chat_message("user"):
            st.write(p)
            
        with st.chat_message("assistant"):
            papers = get_papers(ws_id).to_dict('records')
            response = generate_ai_response(p, papers, st.session_state.get('groq_key'))
            st.write(response)
            save_chat(ws_id, "assistant", response)

# -----------------------------------------------------------------------------
# MAIN APP
# -----------------------------------------------------------------------------

def main():
    if 'user_id' not in st.session_state:
        page_login()
    else:
        choice = sidebar_nav()
        
        if choice == "Home": page_home()
        elif choice == "Dashboard": page_dashboard()
        elif choice == "Search Papers": page_search()
        elif choice == "Workspaces": page_workspaces_list()
        elif choice == "AI Tools": page_ai_tools()
        elif choice == "Upload PDF": page_upload()
        elif choice == "Doc Space": page_doc_space()
        elif choice == "AI Chatbot": page_chatbot()
        else: page_dashboard()

if __name__ == "__main__":
    main()
