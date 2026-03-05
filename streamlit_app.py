import streamlit as st
from chatbot import MFFAQChatbot
import time

# Page Configuration
st.set_page_config(page_title="SBI Mutual Fund FAQ Assistant", page_icon="📈")

st.title("📈 SBI Mutual Fund FAQ Assistant")
st.markdown("""
This chatbot provides factual information about **SBI Large Cap**, **SBI Flexicap**, and **SBI ELSS Tax Saver** funds.
*All information is sourced from official public records on INDmoney.*
""")

# Sidebar for Configuration
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("OpenAI API Key (optional)", type="password")
    st.info("If no API key is provided, the bot will run in 'Mock Mode' to demonstrate logic.")
    
    if st.button("Clear History"):
        st.session_state.messages = []

# Initialize Chatbot and Session State
bot = MFFAQChatbot()

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about expense ratio, exit load, lock-in, etc."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        context, sources = bot.get_context(prompt)
        
        if not api_key:
            # Mock Mode Logic
            st.warning("Running in Mock Mode (No API Key)")
            time.sleep(1)
            if sources:
                response = f"Simulated Response: Based on the facts, the information you requested about '{prompt}' can be found in the context provided. For example, {context.splitlines()[0]}. \n\nSource: {sources[0]}"
            else:
                response = "I am sorry, but I do NOT have that information in my records."
        else:
            # Actual LLM Call (Requires OpenAI package)
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                full_prompt = bot.create_prompt(prompt, context)
                
                response_obj = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": bot.system_prompt},
                        {"role": "user", "content": full_prompt}
                    ]
                )
                response = response_obj.choices[0].message.content
            except Exception as e:
                response = f"Error calling LLM: {str(e)}"

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# Bottom warning
st.caption("Disclaimer: This bot provides facts only. No financial advice provided.")
