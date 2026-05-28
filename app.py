import streamlit as st
import time
import os
import random
from dotenv import load_dotenv

# Import utilities
from utils.storage import DEFAULT_STATE
from utils.save_manager import ForgeSaveManager
from utils.pdf_export import ForgePDFExporter
from utils.groq_client import GroqClient
from utils.agents import (
    CEOAgent, CTOAgent, PMAgent, DevAgent, MarketerAgent,
    orchestrate_sprint_meeting
)
from utils.simulation import StartupSimulation

# Page configuration
st.set_page_config(
    page_title="StartupForge-AI | Agent Accelerator",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Fidelity CSS styling injection
st.markdown("""
<style>
    /* Global Background and Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #08090f !important;
        color: #e2e8f0 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Header styling */
    [data-testid="stHeader"] {
        background-color: rgba(8, 9, 15, 0.8) !important;
        backdrop-filter: blur(12px);
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0d0f1a !important;
        border-right: 1px solid #1f243d;
    }
    
    /* Premium Glowing Cards */
    .glow-card {
        background: linear-gradient(135deg, #111322 0%, #15182e 100%);
        border: 1px solid #1f243d;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: all 0.3s ease;
    }
    .glow-card:hover {
        border-color: #8a2be2;
        box-shadow: 0 8px 32px 0 rgba(138, 43, 226, 0.15);
        transform: translateY(-2px);
    }
    
    /* Metrics grid */
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-top: 4px;
    }
    .cyan-text { color: #00f2fe; text-shadow: 0 0 10px rgba(0, 242, 254, 0.3); }
    .purple-text { color: #8a2be2; text-shadow: 0 0 10px rgba(138, 43, 226, 0.3); }
    .green-text { color: #00e676; text-shadow: 0 0 10px rgba(0, 230, 118, 0.3); }
    .amber-text { color: #ffb000; text-shadow: 0 0 10px rgba(255, 176, 0, 0.3); }
    .coral-text { color: #ff1744; text-shadow: 0 0 10px rgba(255, 23, 68, 0.3); }
    
    /* Agent Profile Cards */
    .agent-card {
        background: #0f111f;
        border: 1px solid #1c203b;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .agent-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
    }
    .agent-ceo::before { background: linear-gradient(90deg, #ffb000, #ff5f00); }
    .agent-cto::before { background: linear-gradient(90deg, #00f2fe, #4facfe); }
    .agent-pm::before { background: linear-gradient(90deg, #9b51e0, #8a2be2); }
    .agent-dev::before { background: linear-gradient(90deg, #00e676, #00b0ff); }
    .agent-marketer::before { background: linear-gradient(90deg, #ff1744, #ff9100); }
    
    .agent-role {
        font-size: 0.75rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #718096;
        margin-bottom: 4px;
    }
    .agent-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #fff;
    }
    
    /* Monospace Terminal Code */
    .terminal-box {
        background-color: #05060b !important;
        border: 1px solid #141729 !important;
        border-radius: 12px;
        padding: 18px;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem;
        color: #00e676;
        box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
        height: 380px;
        overflow-y: auto;
    }
    .terminal-line {
        margin-bottom: 12px;
        line-height: 1.5;
    }
    .terminal-timestamp { color: #5f7a9e; }
    .terminal-sender { font-weight: 700; color: #ffb000; }
    .terminal-msg { color: #e2e8f0; }

    /* Custom Dialog elements */
    .speech-bubble {
        background: #13162b;
        border-left: 4px solid #8a2be2;
        padding: 12px 16px;
        margin: 12px 0;
        border-radius: 0 12px 12px 0;
    }
    
    /* Inputs overrides */
    div[data-baseweb="input"] {
        background-color: #111322 !important;
        border: 1px solid #1f243d !important;
        border-radius: 8px !important;
        color: white !important;
    }
    button[kind="primary"] {
        background: linear-gradient(90deg, #8a2be2 0%, #00f2fe 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        box-shadow: 0 4px 15px rgba(138, 43, 226, 0.4) !important;
    }
    button[kind="secondary"] {
        background-color: #111322 !important;
        border: 1px solid #1f243d !important;
        color: white !important;
        border-radius: 8px !important;
    }
    
    /* Remove Streamlit default anchor links */
    .css-15z55uz, .css-zn24rx, .st-emotion-cache-15z55uz {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# Instantiate Forge Save Manager
save_manager = ForgeSaveManager()

# Initialize Session State
if "state" not in st.session_state:
    st.session_state.state = save_manager.load_state("current_game.json", DEFAULT_STATE)
    st.session_state.groq_client = GroqClient()
    st.session_state.active_meeting = None
    st.session_state.active_meeting_mode = None
    st.session_state.active_meeting_topic = None
    
    # Load persistent chat history from JSON
    st.session_state.chat_history = save_manager.load_chat_history()

state = st.session_state.state
groq_client = st.session_state.groq_client

# Instantiating Agent Class Instances from local state variables
agents = {
    "CEO": CEOAgent("Sarah (CEO)", state["agents"]["CEO"]),
    "CTO": CTOAgent("Dave (CTO)", state["agents"]["CTO"]),
    "PM": PMAgent("Alex (PM)", state["agents"]["PM"]),
    "Developer": DevAgent("Jack (Dev)", state["agents"]["Developer"]),
    "Marketer": MarketerAgent("Tori (Marketer)", state["agents"]["Marketer"])
}

# --- SIDEBAR PANELS ---
with st.sidebar:
    st.image("https://img.icons8.com/nolan/96/artificial-intelligence.png", width=70)
    st.markdown("<h2 style='margin-top:0;'>StartupForge-AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#718096; font-size:0.9rem;'>Virtual Agent Incubator Engine</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    # 1. Groq API Status Indicator
    if groq_client.is_connected:
        st.write("Connected:", groq_client.is_connected)
        st.success("🟢 Groq API Connected")
    else:
        st.warning("🟡 Groq Offline Mode (Simulation Fallback active)")
        st.markdown(
            "<span style='font-size:0.8rem; color:#a0aec0;'>"
            "Add a valid GROQ_API_KEY in your .env file to enable live LPU generation."
            "</span>", 
            unsafe_allow_html=True
        )
        
    st.markdown("---")
    
    # 2. Idea Input / Startup Pitch
    st.subheader("💡 Pitch New Idea")
    new_name = st.text_input("Startup Name", value=state["startup_name"])
    new_idea = st.text_area("Product & Feature Idea", value=state["startup_idea"], height=100)
    
    if st.button("Apply Pitch", type="secondary"):
        state["startup_name"] = new_name
        state["startup_idea"] = new_idea
        state["logs"].append({
            "sender": "System",
            "message": f"Startup concept rebranded to '{new_name}'. Objective: {new_idea}",
            "timestamp": f"Day {state['day']}"
        })
        save_manager.save_state(state)
        st.toast("Startup concept updated!", icon="💡")
        st.rerun()
        
    st.markdown("---")
    
    # 3. Game State Persistence Controls
    st.subheader("💾 Checkpoint Saves")
    save_name = st.text_input("Save Slot", value="current_game")
    
    col_save, col_load = st.columns(2)
    with col_save:
        if st.button("Save State", use_container_width=True):
            # Update agents sub-dicts before serialization
            for role, agent_obj in agents.items():
                state["agents"][role] = agent_obj.to_dict()
            save_manager.save_state(state, save_name)
            st.toast("Checkpoint saved successfully!", icon="💾")
    with col_load:
        if st.button("Load State", use_container_width=True):
            st.session_state.state = save_manager.load_state(save_name, DEFAULT_STATE)
            st.toast("Checkpoint loaded successfully!", icon="📂")
            st.rerun()
 
    if st.button("Reset Entire Run", type="secondary", use_container_width=True):
        st.session_state.state = DEFAULT_STATE.copy()
        save_manager.save_state(DEFAULT_STATE)
        save_manager.clear_chat_history()
        st.session_state.chat_history = []
        st.session_state.active_meeting = None
        st.toast("Workspace reset to Day 1", icon="🔄")
        st.rerun()

# --- TOP ROW HEADER GRID ---
col_title, col_day_btn = st.columns([4, 1])
with col_title:
    st.markdown(f"<h1 style='margin-bottom: 0;'>🚀 {state['startup_name']} Forge Hub</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #718096;'>Core Concept: <i>\"{state['startup_idea']}\"</i></p>", unsafe_allow_html=True)

with col_day_btn:
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    if st.button("➡️ Ticks Simulation (Next Day)", type="primary", use_container_width=True):
        # Sync current agent state numbers
        for role, agent_obj in agents.items():
            state["agents"][role] = agent_obj.to_dict()
            
        # Tick the business loop
        updated_state, event_banner = StartupSimulation.tick_day(state)
        st.session_state.state = updated_state
        
        # Save change
        save_manager.save_state(updated_state)
        
        if event_banner:
            st.balloons() if "SUCCESS" in event_banner else st.toast("New incident triggered!", icon="⚠️")
        st.rerun()

# --- HIGH-FIDELITY TABS NAVIGATION ---
tab_ops, tab_reports, tab_brain = st.tabs([
    "📊 Simulation & Operations",
    "📁 Saved Reports Vault",
    "🧠 Brain & Memory Vault"
])

# =========================================================================
# TAB 1: SIMULATION & OPERATIONS
# =========================================================================
with tab_ops:
    # 1. CORE BUSINESS METRICS ROW (glowing cards)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class='glow-card'>
            <div style='color:#718096; font-size:0.8rem; font-weight:800; text-transform:uppercase;'>Days Operational</div>
            <div class='metric-value amber-text'>{state['day']}</div>
            <div style='font-size:0.75rem; color:#718096; margin-top:4px;'>Stage: {state['stage']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='glow-card'>
            <div style='color:#718096; font-size:0.8rem; font-weight:800; text-transform:uppercase;'>Operational Capital</div>
            <div class='metric-value green-text'>${state['budget']:,.2f}</div>
            <div style='font-size:0.75rem; color:#718096; margin-top:4px;'>Burn: ${StartupSimulation.calculate_burn_rate(state):,.1f}/day</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='glow-card'>
            <div style='color:#718096; font-size:0.8rem; font-weight:800; text-transform:uppercase;'>Active User Base</div>
            <div class='metric-value cyan-text'>{state['users']:,}</div>
            <div style='font-size:0.75rem; color:#718096; margin-top:4px;'>Monthly MRR: ${state['mrr']:,.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='glow-card'>
            <div style='color:#718096; font-size:0.8rem; font-weight:800; text-transform:uppercase;'>Product Valuation</div>
            <div class='metric-value purple-text'>${state['valuation']:,.2f}</div>
            <div style='font-size:0.75rem; color:#718096; margin-top:4px;'>VC Multiplier: 5x MRR</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class='glow-card'>
            <div style='color:#718096; font-size:0.8rem; font-weight:800; text-transform:uppercase;'>Code Health Index</div>
            <div class='metric-value {'coral-text' if state['code_quality'] < 60 else 'cyan-text'}'>{state['code_quality']}%</div>
            <div style='font-size:0.75rem; color:#718096; margin-top:4px;'>Tech Debt: {state['tech_debt']} points</div>
        </div>
        """, unsafe_allow_html=True)
    
    # 2. ACTIVE AGENT COLLABORATORS GRID
    st.markdown("<h3 style='margin-top: 10px;'>👾 Active AI Agent Co-founders</h3>", unsafe_allow_html=True)
    col_ceo, col_cto, col_pm, col_dev, col_mkt = st.columns(5)
    
    agent_columns = [
        (col_ceo, agents["CEO"], "agent-ceo"),
        (col_cto, agents["CTO"], "agent-cto"),
        (col_pm, agents["PM"], "agent-pm"),
        (col_dev, agents["Developer"], "agent-dev"),
        (col_mkt, agents["Marketer"], "agent-marketer")
    ]
    
    for col, agt, css_class in agent_columns:
        with col:
            # Determine health color
            energy_color = "#00e676" if agt.energy > 60 else ("#ffb000" if agt.energy > 30 else "#ff1744")
            st.markdown(f"""
            <div class='agent-card {css_class}'>
                <div class='agent-role'>{agt.role}</div>
                <div class='agent-name'>{agt.name}</div>
                <div style='font-size:0.8rem; color:#718096; margin:8px 0;'>Level: {agt.level} | Focus: {agt.focus}</div>
                <div style='text-align: left; font-size: 0.75rem; color:#a0aec0; margin-bottom: 2px;'>Energy: {agt.energy}%</div>
                <div style='background-color:#141729; border-radius:4px; height:8px; width:100%; position:relative; overflow:hidden;'>
                    <div style='background-color:{energy_color}; width:{agt.energy}%; height:100%; border-radius:4px;'></div>
                </div>
                <div style='font-size:0.75rem; color:#cbd5e0; font-style:italic; margin-top:10px;'>Mood: "{agt.mood}"</div>
            </div>
            """, unsafe_allow_html=True)
            
    # 3. INTERACTIVE FORGE SPRINT CONVERSATION
    st.markdown("<h3 style='margin-top:20px;'>💬 Forge Sprint Meeting Room</h3>", unsafe_allow_html=True)
    
    col_mode, col_topic = st.columns([1, 2])
    with col_mode:
        agent_mode = st.selectbox(
            "Choose Mode",
            [
                "Simulation",
                "Branding Agent",
                "Idea Generator",
                "Market Research",
                "Business Plan",
                "Roadmap"
            ]
        )
    with col_topic:
        sprint_input = st.text_input(
            "Sprint Discussion Topic / Concept Pitch",
            placeholder="Enter startup topic or idea"
        )
        
    if st.button("Run Agent", type="primary", use_container_width=True):
        if not sprint_input:
            st.error("Please enter a topic")
        else:
            with st.spinner("Processing..."):
                # Save topic/mode in state for active display and saving
                st.session_state.active_meeting_topic = sprint_input
                st.session_state.active_meeting_mode = agent_mode
                
                # Fetch live memory to inject into LPU/Simulator context
                loaded_memories = save_manager.load_memories()
                memories_text_list = [m["text"] for m in loaded_memories]

                if agent_mode == "Branding Agent":
                    sys_prompt = "You are a startup branding expert."
                    if memories_text_list:
                        sys_prompt += "\n\nShared Company Memory (Past Decisions):\n" + "\n".join(f"- {m}" for m in memories_text_list)
                        
                    st.session_state.active_meeting = [{
                        "sender": "Branding Agent",
                        "role": "Branding",
                        "message": groq_client.query(
                            sys_prompt,
                            f"Generate startup name, slogan, colors and branding ideas for: {sprint_input}"
                        )
                    }]
                    
                elif agent_mode == "Idea Generator":
                    sys_prompt = "You are a startup idea generation expert."
                    if memories_text_list:
                        sys_prompt += "\n\nShared Company Memory (Past Decisions):\n" + "\n".join(f"- {m}" for m in memories_text_list)
                        
                    st.session_state.active_meeting = [{
                        "sender": "Idea Agent",
                        "role": "Ideas",
                        "message": groq_client.query(
                            sys_prompt,
                            f"Generate 5 startup ideas for: {sprint_input}\n\nProvide Name, Problem Solved, Audience, Key Features, Revenue Model, Difficulty."
                        )
                    }]
                    
                elif agent_mode == "Market Research":
                    sys_prompt = "You are a market research expert."
                    if memories_text_list:
                        sys_prompt += "\n\nShared Company Memory (Past Decisions):\n" + "\n".join(f"- {m}" for m in memories_text_list)
                        
                    st.session_state.active_meeting = [{
                        "sender": "Research Agent",
                        "role": "Research",
                        "message": groq_client.query(
                            sys_prompt,
                            f"Analyze startup opportunity for: {sprint_input}\n\nProvide Market Demand, Audience, Competitors, SWOT, SWOT Analysis, Growth Potential."
                        )
                    }]
                    
                elif agent_mode == "Business Plan":
                    sys_prompt = "You are a startup business strategist."
                    if memories_text_list:
                        sys_prompt += "\n\nShared Company Memory (Past Decisions):\n" + "\n".join(f"- {m}" for m in memories_text_list)
                        
                    st.session_state.active_meeting = [{
                        "sender": "Business Agent",
                        "role": "Business",
                        "message": groq_client.query(
                            sys_prompt,
                            f"Create complete startup business strategy for: {sprint_input}\n\nProvide Business Model, Revenue streams, pricing, cost, risks, scale plan."
                        )
                    }]
                    
                elif agent_mode == "Roadmap":
                    sys_prompt = "You are a startup roadmap planner."
                    if memories_text_list:
                        sys_prompt += "\n\nShared Company Memory (Past Decisions):\n" + "\n".join(f"- {m}" for m in memories_text_list)
                        
                    st.session_state.active_meeting = [{
                        "sender": "Roadmap Agent",
                        "role": "Roadmap",
                        "message": groq_client.query(
                            sys_prompt,
                            f"Create a complete startup roadmap for: {sprint_input}\n\nInclude MVP Features, Tech Stack, Development Phases, Launch Timeline, Scaling Strategy."
                        )
                    }]
                    
                else:
                    # Simulation Mode: Orchestrated board meeting!
                    conversation_msgs = orchestrate_sprint_meeting(
                        groq_client,
                        agents,
                        sprint_input,
                        memories_text_list
                    )
                    st.session_state.active_meeting = conversation_msgs
                    
                # -------------------------------------------------------------
                # Persistent Chat History Memory: Add entry & save
                # -------------------------------------------------------------
                save_manager.add_chat_entry(
                    topic=st.session_state.active_meeting_topic,
                    mode=st.session_state.active_meeting_mode,
                    day=state["day"],
                    messages=st.session_state.active_meeting
                )
                # Sync session state variable
                st.session_state.chat_history = save_manager.load_chat_history()

            st.rerun()

    # --- Render active output panel ---
    if st.session_state.active_meeting:
        st.markdown("<div style='background-color:#111322; border:1px solid #1f243d; border-radius:12px; padding:20px; margin-bottom:20px;'>", unsafe_allow_html=True)
        st.markdown(f"<h4>Agent Output Panel: <i>\"{st.session_state.active_meeting_topic}\"</i> ({st.session_state.active_meeting_mode})</h4>", unsafe_allow_html=True)
        
        # Display the discussion dialogue
        for speaker in st.session_state.active_meeting:
            role_label = f"<span style='color:#a0aec0; font-size:0.8rem; font-weight:800;'>[{speaker['role']}]</span>"
            st.markdown(f"""
            <div class='speech-bubble'>
                <strong>{speaker['sender']}</strong> {role_label}<br/>
                <span style='color:#cbd5e0;'>{speaker['message']}</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        # --- ACTION BUTTONS (Save Report & PDF Exporter) ---
        col_btn_save, col_btn_pdf, col_btn_md, col_btn_close = st.columns([1, 1.2, 1, 0.8])
        
        report_title = f"{st.session_state.active_meeting_mode}: {st.session_state.active_meeting_topic}"
        report_data = {
            "title": report_title,
            "type": st.session_state.active_meeting_mode,
            "day": state["day"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": st.session_state.active_meeting
        }

        with col_btn_save:
            if st.button("💾 Save Report to Vault", use_container_width=True):
                save_manager.save_report(
                    title=report_title,
                    report_type=st.session_state.active_meeting_mode,
                    day=state["day"],
                    content=st.session_state.active_meeting
                )
                st.toast("Saved successfully in 'saved_reports'!", icon="💾")
                
        with col_btn_pdf:
            # 1. Compile PDF to the /exports folder
            pdf_filename = f"report_{int(time.time())}.pdf"
            pdf_path = os.path.join(save_manager.exports_dir, pdf_filename)
            
            if ForgePDFExporter.is_available():
                success = ForgePDFExporter.generate_report_pdf(report_data, pdf_path)
                if success:
                    # Provide direct download in Streamlit
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label="📥 Export Report (PDF)",
                        data=pdf_bytes,
                        file_name=pdf_filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.error("PDF generation failed")
            else:
                st.warning("PDF Exporter Offline (ReportLab missing)")
                
        with col_btn_md:
            # Provide direct download in Markdown
            md_filename = f"report_{int(time.time())}.md"
            md_content = save_manager.convert_report_to_markdown(report_data)
            st.download_button(
                label="📥 Export (Markdown)",
                data=md_content.encode("utf-8"),
                file_name=md_filename,
                mime="text/markdown",
                use_container_width=True
            )

        with col_btn_close:
            if st.button("❌ Close Panel", use_container_width=True):
                st.session_state.active_meeting = None
                st.session_state.active_meeting_mode = None
                st.session_state.active_meeting_topic = None
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
        
    # 4. SYSTEM LOGGER TERMINAL WINDOW
    st.markdown("<h3>🖥️ System Logs & Forge Terminal</h3>", unsafe_allow_html=True)
    
    terminal_html = "<div class='terminal-box'>"
    for log in reversed(state["logs"]):
        timestamp_tag = f"<span class='terminal-timestamp'>[{log['timestamp']}]</span>"
        sender_tag = f"<span class='terminal-sender'>{log['sender']}:</span>"
        msg_tag = f"<span class='terminal-msg'>{log['message']}</span>"
        terminal_html += f"<div class='terminal-line'>{timestamp_tag} {sender_tag} {msg_tag}</div>"
    terminal_html += "</div>"
    
    st.markdown(terminal_html, unsafe_allow_html=True)

# =========================================================================
# TAB 2: SAVED REPORTS VAULT
# =========================================================================
with tab_reports:
    st.markdown("<h3>📁 Saved Executive Reports</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#718096;'>Access saved startup board room meeting summaries, roadmaps, and business strategies below.</p>", unsafe_allow_html=True)
    st.markdown("---")

    saved_reports = save_manager.list_reports()

    if not saved_reports:
        st.info("No saved reports yet. Run sprints or generate plans on the main board and click '💾 Save Report to Vault' to persist documents.")
    else:
        # Layout reports in columns of 2
        cols = st.columns(2)
        for idx, r in enumerate(saved_reports):
            col_target = cols[idx % 2]
            with col_target:
                st.markdown(f"""
                <div class='glow-card' style='margin-bottom: 20px; border-left: 4px solid #8a2be2;'>
                    <span style='background-color:#1c203b; color:#8a2be2; font-size:0.75rem; padding:4px 8px; border-radius:4px; font-weight:800;'>{r['type'].upper()}</span>
                    <h4 style='margin: 8px 0 4px 0; color:#fff;'>{r['title']}</h4>
                    <p style='color:#718096; font-size:0.8rem; margin-bottom:12px;'>Day {r.get('day', 1)} | Generated: {r['timestamp']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Expandable inline reading panel
                with st.expander("📖 View Report Details"):
                    st.markdown(save_manager.convert_report_to_markdown(r))
                
                # PDF Exporter & Downloader
                col_pdf_dl, col_md_dl, col_del = st.columns([1.5, 1.5, 1])
                
                with col_pdf_dl:
                    r_filename = f"{r['_filename_base']}.pdf"
                    r_path = os.path.join(save_manager.exports_dir, r_filename)
                    
                    if ForgePDFExporter.is_available():
                        if ForgePDFExporter.generate_report_pdf(r, r_path):
                            with open(r_path, "rb") as f:
                                r_pdf_bytes = f.read()
                            st.download_button(
                                label="📥 Export PDF",
                                data=r_pdf_bytes,
                                file_name=r_filename,
                                mime="application/pdf",
                                key=f"pdf_dl_{r['id']}",
                                use_container_width=True
                            )
                        else:
                            st.error("PDF generation failed")
                    else:
                        st.warning("PDF Offline")
                        
                with col_md_dl:
                    r_md_filename = f"{r['_filename_base']}.md"
                    r_md_content = save_manager.convert_report_to_markdown(r)
                    st.download_button(
                        label="📥 Export Markdown",
                        data=r_md_content.encode("utf-8"),
                        file_name=r_md_filename,
                        mime="text/markdown",
                        key=f"md_dl_{r['id']}",
                        use_container_width=True
                    )

                with col_del:
                    if st.button("🗑️ Delete", key=f"del_{r['id']}", use_container_width=True):
                        save_manager.delete_report(r['_filename_base'])
                        st.toast("Report deleted", icon="🗑️")
                        st.rerun()
                st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)

# =========================================================================
# TAB 3: BRAIN & COMPANY MEMORY VAULT
# =========================================================================
with tab_brain:
    st.markdown("<h3>🧠 Brain & Cognitive Memory Vault</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#718096;'>Inject memories directly into your AI co-founders' cognitive models to keep them aligned with core directives.</p>", unsafe_allow_html=True)
    st.markdown("---")

    col_brain_left, col_brain_right = st.columns([1, 1.2])

    with col_brain_left:
        st.subheader("💡 Core Directives & Memories")
        
        # Load active memories
        memories = save_manager.load_memories()

        # Add new memory form
        with st.form("new_memory_form", clear_on_submit=True):
            st.markdown("<span style='font-size:0.9rem; font-weight:800; color:#a0aec0;'>Add Strategic Decision / Guideline</span>", unsafe_allow_html=True)
            mem_text = st.text_area("Memory Content", placeholder="e.g. Pivot startup focus to developers. Tech stack must be lightweight python APIs.", height=80)
            mem_cat = st.selectbox("Category", ["Strategy", "Tech Stack", "Marketing", "Product", "Team"])
            
            submitted = st.form_submit_button("🧠 Inject Memory into AI Co-founders", use_container_width=True)
            if submitted:
                if mem_text:
                    save_manager.add_memory_item(mem_text, mem_cat)
                    st.toast("Strategic Memory injected successfully!", icon="🧠")
                    st.rerun()
                else:
                    st.error("Please fill in the memory content")

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        st.subheader("📋 Active Cognitive Memories")
        
        if not memories:
            st.info("No guidelines are currently active. Add some directives to align your startup agents.")
        else:
            for m in memories:
                # Color code category tags
                cat_colors = {
                    "Strategy": "#ffb000",
                    "Tech Stack": "#00f2fe",
                    "Marketing": "#ff1744",
                    "Product": "#9b51e0",
                    "Team": "#00e676"
                }
                tag_col = cat_colors.get(m.get("category", "Strategy"), "#718096")
                
                st.markdown(f"""
                <div style='background-color:#111322; border: 1px solid #1f243d; border-radius:10px; padding:15px; margin-bottom:12px; position:relative;'>
                    <span style='color:{tag_col}; font-weight:800; font-size:0.75rem; text-transform:uppercase;'>[{m['category']}]</span><br/>
                    <span style='color:#cbd5e0; font-size:0.9rem;'>"{m['text']}"</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Delete memory button
                if st.button("🗑️ Remove memory Guideline", key=f"del_mem_{m['id']}", use_container_width=True):
                    save_manager.delete_memory_item(m['id'])
                    st.toast("Memory guideline removed", icon="🗑️")
                    st.rerun()

    with col_brain_right:
        st.subheader("📚 Persistent Co-founder Meeting Archives")
        st.markdown("<p style='color:#718096;'>Timeline of all previous startup meetings, roadmaps, and sprint discussions saved in <code>chat_memory.json</code>.</p>", unsafe_allow_html=True)

        chat_history = st.session_state.chat_history

        if not chat_history:
            st.info("No discussions recorded in persistent chat memory yet.")
        else:
            col_clear_chat, _ = st.columns([1, 1.5])
            with col_clear_chat:
                if st.button("🧹 Clear Chat History", use_container_width=True):
                    save_manager.clear_chat_history()
                    st.session_state.chat_history = []
                    st.toast("Chat history memory cleared!", icon="🧹")
                    st.rerun()
            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

            # Display chats reversed (newest first)
            for idx, entry in enumerate(reversed(chat_history)):
                badge_type = entry.get("mode", "Sprint")
                st.markdown(f"""
                <div style='background-color:#0b0d17; border: 1px solid #1c203b; border-radius:8px; padding:12px 16px; margin-bottom:12px;'>
                    <span style='color:#5f7a9e; font-size:0.75rem; font-weight:600;'>{entry['timestamp']} (Day {entry.get('day', 1)})</span> | 
                    <span style='color:#8a2be2; font-size:0.75rem; font-weight:800;'>{badge_type.upper()}</span>
                    <h5 style='margin: 4px 0 8px 0; color:#fff;'>Topic: "{entry['topic']}"</h5>
                </div>
                """, unsafe_allow_html=True)

                with st.expander("📖 Expand Discussion Transcript"):
                    for msg in entry["messages"]:
                        role_tag = f"<span style='color:#a0aec0; font-size:0.75rem; font-weight:700;'>[{msg.get('role', 'Agent')}]</span>"
                        st.markdown(f"""
                        <div style='background-color:#13162b; border-left: 2px solid #8a2be2; padding:8px 12px; margin-bottom:8px; border-radius:0 8px 8px 0;'>
                            <strong>{msg.get('sender', 'Agent')}</strong> {role_tag}<br/>
                            <span style='color:#cbd5e0; font-size:0.9rem;'>{msg.get('message', '')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
