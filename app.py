# Importing required packages
import streamlit as st
from streamlit_chat import message
import openai

st.set_page_config(page_title="Kristian's Chat with PDFs")
st.title("KCP")
st.sidebar.markdown("Developed by Kristian Jackson](https://twitter.com/RealKrisJackson)", unsafe_allow_html=True)
st.sidebar.markdown("Current Version: 1.0.1")
st.sidebar.markdown("Not optimised")
st.sidebar.markdown("May run out of OpenAI credits")

model = "gpt-4"

def get_initial_message():
    messages=[
            {"role": "system", "content": """
            You are Lana, a helpful US Congressional Legislative Analyst.
            This title reflects the individual's expertise in analyzing and understanding legislation, as well as their ability to provide insights and recommendations based on their knowledge of the legislative process. Other potential job titles for similar roles could include "Legislative Affairs Specialist," "Policy Analyst," or "Government Relations Specialist."
            You use specific information, backed by sources in your answers, focusing on accuracy and also insight gained from years of experience reading and synthesizing legislative information.
            Your language should be for a CPA to understand.
            If you do not know the answer to a question, do not make information up - instead, ask a follow-up question in order to gain more context.
            Use a mix of technical and colloquial US english language to create an accessible and engaging tone.
            Provide your answers using professional language that an executive would appreciate.
            """},
            {"role": "user", "content": "I want to learn about the legislation contained in the PDF that I uploaded"},
            {"role": "assistant", "content": "Fine and good day. Here is a summary of the document that was uploaded:"}
        ]
    return messages

def get_chatgpt_response(messages, model=model):
    print("model: ", model)
    response = openai.ChatCompletion.create(
    model=model,
    messages=messages
    )
    return response['choices'][0]['message']['content']

def update_chat(messages, role, content):
    messages.append({"role": role, "content": content})
    return messages

if 'generated' not in st.session_state:
    st.session_state['generated'] = []
    
if 'past' not in st.session_state:
    st.session_state['past'] = []

# Add a file uploader widget and restrict the file type to PDF
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

# Check if a file has been uploaded
if uploaded_file is not None:
    # Perform any actions you want with the uploaded file here
    # For example, you can read the content of the file
    file_content = uploaded_file.read()

query = st.text_input("Question: ", "What is the summary of the PDF I just uploaded?", key="input")

if 'messages' not in st.session_state:
    st.session_state['messages'] = get_initial_message()

if query:
    with st.spinner("generating..."):
        messages = st.session_state['messages']
        messages = update_chat(messages, "user", query)
        response = get_chatgpt_response(messages, model)
        messages = update_chat(messages, "assistant", response)
        st.session_state.past.append(query)
        st.session_state.generated.append(response)

if st.session_state['generated']:

    for i in range(len(st.session_state['generated'])-1, -1, -1):
        message(st.session_state["generated"][i], key=str(i))
        message(st.session_state['past'][i], is_user=True, key=str(i) + '_user')