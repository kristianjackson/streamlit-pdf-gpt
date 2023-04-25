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

def qa(file, query, chain_type, k):
    # load document
    loader = PyPDFLoader(file)
    documents = loader.load()
    # split the documents into chunks
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)
    # select which embeddings we want to use
    embeddings = OpenAIEmbeddings()
    # create the vectorestore to use as the index
    db = Chroma.from_documents(texts, embeddings)
    # expose this index in a retriever interface
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": k})
    # create a chain to answer questions 
    qa = RetrievalQA.from_chain_type(
        llm=OpenAI(), chain_type=chain_type, retriever=retriever, return_source_documents=True)
    result = qa({"query": query})
    print(result['result'])
    return result

convos = []  # store all panel objects in a list

def qa_result(_):
     
    # save pdf file to a temp file 
    if file_input.value is not None:
        file_input.save("/.cache/temp.pdf")
    
        prompt_text = prompt.value
        if prompt_text:
            result = qa(file="/.cache/temp.pdf", query=prompt_text, chain_type=select_chain_type.value, k=select_k.value)
            convos.extend([
                pn.Row(
                    pn.panel("\U0001F60A", width=10),
                    prompt_text,
                    width=600
                ),
                pn.Row(
                    pn.panel("\U0001F916", width=10),
                    pn.Column(
                        result["result"],
                        "Relevant source text:",
                        pn.pane.Markdown('\n--------------------------------------------------------------------\n'.join(doc.page_content for doc in result["source_documents"]))
                    )
                )
            ])
            #return convos
    return pn.Column(*convos, margin=15, width=575, min_height=400)

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
            {"role": "user", "content": "Please introduce yourself"}
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

num_sources = st.slider('Sources', 2, 10, 5)  # min: 0h, max: 23h, default: 17h

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