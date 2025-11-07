import streamlit as st
from pathlib import Path
from langchain.agents import create_agent
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq
from langchain.messages import AIMessage, ToolMessage
from groq import APIError
from urllib.parse import quote_plus

st.set_page_config(page_title="LangChain: Chat with SQL DB", page_icon="🦜")
st.title("🦜 LangChain: Chat with SQL DB")

LOCALDB="USE_LOCALDB"
MYSQL="USE_MYSQL"

radio_opt=["Use SQLLite 3 Database- Student.db","Connect to you MySQL Database"]
selected_opt=st.sidebar.radio(label="Choose the DB which you want to chat",options=radio_opt)

if radio_opt.index(selected_opt)==1:
    db_uri=MYSQL
    mysql_host=st.sidebar.text_input("Provide MySQL Host")
    mysql_user=st.sidebar.text_input("MYSQL User")
    mysql_password=st.sidebar.text_input("MYSQL password",type="password")
    mysql_db=st.sidebar.text_input("MySQL database")
else:
    db_uri=LOCALDB

api_key=st.sidebar.text_input(label="GRoq API Key",type="password")

if not db_uri:
    st.info("Please enter the database information and uri")
    st.stop()

if not api_key:
    st.info("Please add the groq api key")
    st.stop()

## LLM model
llm = ChatGroq(groq_api_key=api_key, model_name="llama-3.1-8b-instant", streaming=True)

@st.cache_resource(ttl="2h")
def configure_db(db_uri,mysql_host=None,mysql_user=None,mysql_password=None,mysql_db=None):
    if db_uri==LOCALDB:
        dbfilepath=(Path(__file__).parent/"student.db").absolute()
        print(dbfilepath)
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    elif db_uri==MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details.")
            st.stop()
        mysql_password_encoded = quote_plus(mysql_password)
        return SQLDatabase(create_engine(f"mysql+mysqlconnector://{mysql_user}:{mysql_password_encoded}@{mysql_host}/{mysql_db}")) 

if db_uri==MYSQL:
    db=configure_db(db_uri,mysql_host,mysql_user,mysql_password,mysql_db)
else:
    db=configure_db(db_uri)

## toolkit
toolkit = SQLDatabaseToolkit(db=db, llm=llm, include_tables="all")

tools = toolkit.get_tools()

# system_prompt = """
# You are an agent designed to interact with a SQL database.
# Given an input question, create a syntactically correct query to run,
# then look at the results of the query and return the answer.
# """

system_prompt = """
You are an intelligent agent designed to interact with a SQL database.
The database has the following tables and columns:

Table STUDENT:
- STUDENT_ID (int, primary key)
- NAME (varchar)
- CLASS (varchar)
- SECTION (varchar)
- MARKS (int)

Table STUDENT_INFO:
- INFO_ID (int, primary key)
- STUDENT_ID (int, foreign key to STUDENT)
- DOB (date)
- ADDRESS (varchar)
- PHONE (varchar)

Given an input question, create a syntactically correct query to run,
then look at the results of the query and return the answer.
"""

## create agent
query_agent = create_agent(
    llm,
    tools,
    system_prompt=system_prompt,
)

if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# -----------------------------
# User input
# -----------------------------
prompt = st.chat_input()

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.chat_message("assistant"):
        # Containers for reasoning and final output
        reasoning_box = st.container()
        final_box = st.empty()
        final_response = ""

        try:
            # Manual event streaming (we print everything ourselves)
            for i,event in enumerate(query_agent.stream(
                {"messages": [{"role": "user", "content": prompt}]},
                stream_mode="values",
                config={"recursion_limit": 50}
            )):
                messages = event.get("messages", [])
                if not messages:
                    continue

                last_msg = messages[-1]

                # Show intermediate reasoning or tool use
                if isinstance(last_msg, ToolMessage):
                    with st.expander(f"🧰 Tool Used: {last_msg.name}", expanded=False):
                         st.markdown(last_msg.content)
                elif isinstance(last_msg, AIMessage):
                      final_box.markdown(f"💬 **Assistant:**")
                      content = last_msg.content.strip()
                      if content:
                          with st.expander(f"🧠 AI Reasoning Step {i+1}", expanded=False):
                              st.markdown(content)
                          # Update possible final answer progressively
                          final_response = content

            # After streaming completes, show only the final result cleanly
            if final_response:
                st.session_state.messages.append({"role": "assistant", "content": final_response})
                final_box.markdown(f"✅ **Final Answer:** {final_response}")
            else:
                st.warning("⚠️ No final response generated.")

        except APIError as e:
            error_msg = f"⚠️ Groq API Error: {str(e)}"
            st.session_state.messages.append({'role': 'assistant', "content": error_msg})
            st.error(error_msg)

        except Exception as e:
            error_msg = f"⚠️ Unexpected error: {str(e)}"
            st.session_state.messages.append({'role': 'assistant', "content": error_msg})
            st.error(error_msg)