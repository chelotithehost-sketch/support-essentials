import streamlit as st
import requests
import json
from datetime import datetime
import socket
import ssl
import whois
from whois import exceptions
import re
import random
import time
from PIL import Image
import io
import base64

# [Keep all your existing imports and configuration code here]
# [Keep GEMINI_API_KEY, GEMINI_MODELS, HOSTAFRICA_KB, etc.]

# --- ADD THIS NEW SECTION FOR CONVERSATIONAL AI ---

def initialize_chat_session():
    """Initialize chat session with context about the ticket"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'chat_context' not in st.session_state:
        st.session_state.chat_context = None

def chat_with_ai(user_message, ticket_context=None, image_data=None):
    """Have a conversation with AI about the ticket"""
    
    # Build context-aware prompt
    if ticket_context and not st.session_state.chat_context:
        # First message - set context
        system_prompt = f"""You are a HostAfrica technical support expert helping an agent analyze this ticket:

TICKET DETAILS:
{ticket_context}

The support agent will now ask you questions about this ticket. Provide helpful, technical answers based on HostAfrica's services (cPanel/DirectAdmin hosting, domains, email, SSL, VPS).

HostAfrica Nameservers:
- cPanel: ns1-4.host-ww.net
- DirectAdmin: dan1-2.host-ww.net"""
        
        st.session_state.chat_context = ticket_context
        full_prompt = f"{system_prompt}\n\nAgent Question: {user_message}"
    else:
        # Continue conversation
        full_prompt = user_message
    
    # Add chat history for context
    if len(st.session_state.chat_history) > 0:
        history_text = "\n".join([
            f"{'Agent' if msg['role'] == 'user' else 'AI'}: {msg['content']}" 
            for msg in st.session_state.chat_history[-4:]  # Last 4 messages
        ])
        full_prompt = f"Previous conversation:\n{history_text}\n\nAgent: {user_message}"
    
    # Try models in rotation
    for model_name in GEMINI_MODELS:
        try:
            import google.generativeai as genai
            model = genai.GenerativeModel(model_name)
            
            response = model.generate_content(full_prompt)
            return response.text, model_name
            
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                continue
            else:
                continue
    
    return "I'm currently unavailable. Please try again in a moment.", None

# --- MODIFY YOUR SIDEBAR TO ADD CHAT FEATURE ---

st.sidebar.title("🎫 Ticket Analyzer")

# Create tabs for different features
analysis_tab, chat_tab = st.sidebar.tabs(["📋 Analysis", "💬 AI Chat"])

with analysis_tab:
    st.markdown("""
    **Paste ticket for analysis**
    - Issue identification
    - Suggested checks
    - Recommended response
    - KB articles
    """)
    
    ticket_thread = st.text_area(
        "Ticket conversation:",
        height=150,
        placeholder="Paste ticket thread here...",
        key="ticket_input"
    )
    
    uploaded_image = st.file_uploader(
        "📎 Upload Screenshot (optional)",
        type=['png', 'jpg', 'jpeg', 'gif'],
        help="Upload error screenshots or interface issues",
        key="ticket_image"
    )
    
    if uploaded_image:
        st.image(uploaded_image, caption="Uploaded Screenshot", use_container_width=True)
        st.caption("✅ Screenshot will be analyzed")
    
    if st.button("🔍 Analyze Ticket", key="analyze_btn", use_container_width=True):
        if ticket_thread:
            with st.spinner("Analyzing..."):
                image_base64 = None
                if uploaded_image and GEMINI_API_KEY:
                    image_base64 = image_to_base64(uploaded_image)
                
                analysis = analyze_ticket_with_ai(ticket_thread, image_base64)
                
                if analysis:
                    st.success("✅ Analysis Complete")
                    st.markdown("**Issue Type:**")
                    st.info(analysis.get('issue_type', 'General'))
                    
                    if analysis.get('screenshot_analysis'):
                        st.markdown("**📷 Screenshot Analysis:**")
                        st.info(analysis['screenshot_analysis'])
                    
                    kb = analysis.get('kb_articles', [])
                    if kb:
                        st.markdown("**📚 KB Articles:**")
                        for a in kb:
                            st.markdown(f"- [{a['title']}]({a['url']})")
                    
                    st.markdown("**Checks:**")
                    for c in analysis.get('checks', []):
                        st.markdown(f"- {c}")
                    
                    st.markdown("**Actions:**")
                    for a in analysis.get('actions', []):
                        st.markdown(f"- {a}")
                    
                    with st.expander("📝 Response Template"):
                        resp = analysis.get('response_template', '')
                        st.text_area("Copy:", value=resp, height=300, key="resp")
                    
                    # Store ticket for chat context
                    st.session_state.ticket_for_chat = ticket_thread
        else:
            st.warning("Paste ticket first")

with chat_tab:
    st.markdown("""
    **💬 Ask AI about the ticket**
    
    Have a conversation with AI to:
    - Clarify technical details
    - Get additional suggestions
    - Explore troubleshooting steps
    - Discuss resolution strategies
    """)
    
    # Initialize chat
    initialize_chat_session()
    
    # Display chat history
    if len(st.session_state.chat_history) > 0:
        st.markdown("**Conversation:**")
        for msg in st.session_state.chat_history[-6:]:  # Show last 6 messages
            if msg['role'] == 'user':
                st.markdown(f"**🧑 You:** {msg['content']}")
            else:
                st.markdown(f"**🤖 AI:** {msg['content']}")
                if msg.get('model'):
                    st.caption(f"↳ via {msg['model']}")
        st.divider()
    
    # Chat input
    chat_question = st.text_input(
        "Ask about the ticket:",
        placeholder="e.g., What could cause this error?",
        key="chat_input"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("💬 Send", key="chat_send", use_container_width=True):
            if chat_question:
                # Check if we have ticket context
                ticket_context = st.session_state.get('ticket_for_chat', None)
                
                if not ticket_context:
                    st.warning("⚠️ Please analyze a ticket first in the Analysis tab")
                else:
                    with st.spinner("AI is thinking..."):
                        # Add user message
                        st.session_state.chat_history.append({
                            'role': 'user',
                            'content': chat_question
                        })
                        
                        # Get AI response
                        ai_response, model_used = chat_with_ai(
                            chat_question, 
                            ticket_context if len(st.session_state.chat_history) == 1 else None
                        )
                        
                        # Add AI response
                        st.session_state.chat_history.append({
                            'role': 'assistant',
                            'content': ai_response,
                            'model': model_used
                        })
                        
                        st.rerun()
    
    with col2:
        if st.button("🗑️ Clear", key="chat_clear", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.chat_context = None
            st.rerun()

st.sidebar.divider()

# [Keep rest of your existing sidebar code - Support Checklist, etc.]

# [Keep all your existing main app code below this]
