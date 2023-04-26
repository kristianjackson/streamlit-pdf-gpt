# Importing required packages
import streamlit as st
from streamlit_chat import message
import openai
import os 
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from langchain.document_loaders import TextLoader
from langchain.document_loaders import PyPDFLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
import tempfile
import textwrap

st.set_page_config(page_title="KCP")
st.title("Kristian's Chat with PDFs")
st.sidebar.markdown("Developed by Kristian Jackson<br>(https://twitter.com/RealKrisJackson)", unsafe_allow_html=True)
st.sidebar.markdown("Current Version: 1.0.1")
st.sidebar.markdown("Not optimised")
st.sidebar.markdown("May run out of OpenAI credits")

model = "gpt-4"

def qa(db, query, chain_type, k):
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": k})
    qa = RetrievalQA.from_chain_type(
        llm=OpenAI(), chain_type=chain_type, retriever=retriever, return_source_documents=True)
    result = qa({"query": query})
    return result

def get_initial_message():
    messages=[
            {"role": "system", "content": """
            You are Lana, a helpful US Congressional Legislative Analyst.
            This title reflects the individual's expertise in analyzing and understanding legislation, as well as their ability to provide insights and recommendations based on their knowledge of the legislative process. Other potential job titles for similar roles could include "Legislative Affairs Specialist," "Policy Analyst," or "Government Relations Specialist."
            You use specific information, backed by sources in your answers, focusing on accuracy and also insight gained from years of experience reading and synthesizing legislative information.
            Your language should be for a CPA to understand.
            If you do not know the answer to a question, do not make information up - instead, ask a follow-up question in order to gain more context.
            Use a mix of technical and colloquial US english language to create an accessible and engaging tone.
            Provide your answers using professional language that an executive would understand.
            """}
        ]
    return messages

def get_chatgpt_response(messages, model, db, query, num_sources):
    response = qa(db=db, query=query, chain_type="map_reduce", k=num_sources)
    formatted_response = response["result"].replace("\n", " ").strip()
    # Extract and format sources
    sources = response.get("sources", [])
    sources_text = "\n".join([f"Source {i+1}: {src}" for i, src in enumerate(sources)])
    # Append sources to the response
    formatted_response += f"\n\nSources:\n{sources_text}"
    return formatted_response

def update_chat(messages, role, content):
    messages.append({"role": role, "content": content})
    return messages

if 'processing_status' not in st.session_state:
    st.session_state['processing_status'] = False

if 'file_uploaded' not in st.session_state:
    st.session_state['file_uploaded'] = False

if 'generated' not in st.session_state:
    st.session_state['generated'] = []
    
if 'past' not in st.session_state:
    st.session_state['past'] = []

# Add a file uploader widget and restrict the file type to PDF
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

query = st.text_input("Question: ", "", key="input")

num_sources = st.slider('Sources', 2, 10, 5)  # min: 0h, max: 23h, default: 17h

if 'messages' not in st.session_state:
    st.session_state['messages'] = get_initial_message()


processing_info = st.empty()
processing_success = st.empty()
generating_spinner = None

if uploaded_file:
    st.session_state.file_uploaded = True
    if 'db' not in st.session_state or st.session_state.uploaded_file != uploaded_file:
        st.session_state.uploaded_file = uploaded_file
        st.session_state.processing_status = True  # Set processing_status to True
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(uploaded_file.read())
            tmp.flush()
            loader = PyPDFLoader(tmp.name)
            documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        embeddings = OpenAIEmbeddings()
        st.session_state.db = Chroma.from_documents(texts, embeddings)
        st.session_state.processing_status = False  # Set processing_status to False after processing is done

if query:
    if 'db' not in st.session_state:
        st.error("Please upload a PDF file before submitting a query.")
    else:
        with st.spinner("Generating..."):
            messages = st.session_state['messages']
            messages = update_chat(messages, "user", query)
            response = get_chatgpt_response(messages, model, st.session_state.db, query, num_sources)
            messages = update_chat(messages, "assistant", response)
            st.session_state.past.append(query)
            st.session_state.generated.append(response)

def display_message(content, is_user=False):
    css = """
    <style>
        .msg-container {
            display: flex;
            justify-content: flex-start;  # Change to flex-start
            margin-bottom: 8px;
        }
        .msg {
            display: inline-block;
            padding: 8px 12px;
            margin: 4px;
            border-radius: 12px;
            font-size: 16px;
            max-width: 80%;
            word-wrap: break-word;
            line-height: 1.4;
            font-family: Arial, sans-serif;
            white-space: pre-wrap;
        }
        .assistant {
            background-color: #efefef;
            color: #333;
            border: 1px solid #e0e0e0;
            order: 1;
        }
        .user {
            background-color: #4a77f9;
            color: #fff;
            order: 2;
            align-self: flex-end;  # Add this line
        }
    </style>
    """
    message_type = "user" if is_user else "assistant"
    html = f'<div class="msg {message_type}">{content}</div>'
    container = f'<div class="msg-container">{html}</div>'
    return st.markdown(css + container, unsafe_allow_html=True)

if st.session_state.processing_status:
    processing_info.info("Processing the uploaded PDF file...")
else:
    processing_info.empty()

if not st.session_state.processing_status and st.session_state.file_uploaded:
    processing_success.success("Finished processing the uploaded PDF file.")
else:
    processing_success.empty()

if st.session_state['generated']:
    for i in range(len(st.session_state['generated'])-1, -1, -1):
        display_message(st.session_state["generated"][i])
        display_message(st.session_state['past'][i], is_user=True)
