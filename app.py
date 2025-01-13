import streamlit as st
import fin_bot



if 'messages' not in st.session_state:
    st.session_state.messages = []


def reset_conversation():
    st.session_state.messages = []

#Set app title
st.set_page_config(page_title="Financial Bot")

#Set page title
st.title("Financial QnA BOT")

col1, col2 = st.columns([3, 1])
with col2:
    st.button("Reset Chat", on_click=reset_conversation)


# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


if prompt := st.chat_input("Please ask your question:"):
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    response  = fin_bot.get_response(prompt)
    
    print(response)
    with st.chat_message("assistant"):
        st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    
    