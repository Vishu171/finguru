
import snowflake.connector
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
import prompts
from tabulate import tabulate


st.set_page_config(layout="wide")





# Variables
sf_db = st.secrets["sf_database"]
sf_schema = st.secrets["sf_schema"]
username=st.secrets["streamlit_username"]
password=st.secrets["streamlit_password"]
tick_list = {'BRK.A': "Bershire Hathaway(BRK.A)",
             'AAPL': "Apple(AAPL)",
             'PG' : "Proctor and Gamble(PG)",
             'JNJ' : "Johnson and Johnson(JNJ)",
             'MA' : "Mastercard(MA)",
             'MCO' : "Moodys Corp(MCO)",
             'VZ' : "Verizon(VZ)",
             'KO' : "Kotak(KO)",
             'AXP' : "American Express(AXP)",
             'BAC' : "Bank of America(BAC)"}
#tick_list = ['BRK.A','AAPL','PG','JNJ','MA','MCO','VZ','KO','AXP', 'BAC']
fin_statement_list = ['income_statement','balance_sheet','cash_flow_statement']
year_cutoff = 20 # year cutoff for financial statement plotting






# establish snowpark connection
conn = st.experimental_connection("snowpark")

# Reset the connection before using it if it isn't healthy
try:
    query_test = conn.query('select 1')
except:
    conn.reset()

@st.cache_data
def pull_financials(database, schema, statement, ticker):
    """
    query to pull financial data from snowflake based on database, schema, statement and ticker
    """
    df = conn.query(f"select * from {database}.{schema}.{statement} where ticker = '{ticker}' order by year desc")
    df.columns = [col.lower() for col in df.columns]
    return df

# metrics for kpi cards
@st.cache_data
def kpi_recent(df, metric, periods=2, unit=1000000000):
    """
    filters a financial statement dataframe down to the most recent periods
    df is the financial statement. Metric is the column to be used.
    """
    return df.sort_values('year',ascending=False).head(periods)[metric]/unit

def plot_financials(df, x, y, x_cutoff, title):
    """"
    helper to plot the altair financial charts
    """
    return st.altair_chart(alt.Chart(df.head(x_cutoff)).mark_bar().encode(
        x=x,
        y=y
        ).properties(title=title)
    ) 

# adding this to test out caching
st.cache_data(ttl=86400)
def fs_chain(str_input):
    """
    performs qa capability for a question using sql vector db store
    the prompts.fs_chain is used but with caching
    """
    output = prompts.fs_chain(str_input)
    type(output)
    return output

    

# adding this to test out caching
st.cache_data(ttl=86400)
def sf_query(str_input):
    """
    performs snowflake query with caching
    """
    data = conn.query(str_input)
    
    return data



def format_func(option):
    return tick_list[option]






def creds_entered():
    if len(st.session_state["user1"])>0 and len(st.session_state["passwd"])>0:
          if  st.session_state["user1"].strip() != username or st.session_state["passwd"].strip() != password: 
              st.session_state["authenticated"] = False
              st.error("Invalid Username/Password ")

          elif st.session_state["user1"].strip() == username and st.session_state["passwd"].strip() == password:
              st.session_state["authenticated"] = True


def authenticate_user():
      if "authenticated" not in st.session_state:
        buff, col, buff2 = st.columns([1,1,1])

        #col.text_input('smaller text window:')
        
        col.text_input(label="Username:", value="", key="user1", on_change=creds_entered) 
        col.text_input(label="Password", value="", key="passwd", type="password", on_change=creds_entered)
        return False
      else:
           if st.session_state["authenticated"]: 
                return True
           else:  
                  buff, col, buff2 = st.columns([1,1,1])
                  col.text_input(label="Username:", value="", key="user1", on_change=creds_entered) 
                  col.text_input(label="Password:", value="", key="passwd", type="password", on_change=creds_entered)
                  return False

if authenticate_user():
    # create tabs
    tab1,  tab3 = st.tabs([
        "Explore Company Statements ", 
        
        "Explore Annual Reports "
        ]
              
        )
    css = '''
      <style>
          .stTabs [data-baseweb="tab-highlight"] {
              background-color:#00008B;
          }
      </style>
      '''


    st.markdown(css, unsafe_allow_html=True)

    st.markdown("""
      <style>

        .stTabs [data-baseweb="tab-list"] {
          gap: 5px;
          }

        .stTabs [data-baseweb="tab"] {
          height: 15px;
              white-space: pre-wrap;
          width: 200px ;
          background-color: none;
          color: #00008B;
          border-radius: 4px 4px 0px 0px;
          gap: 1px;
          padding-top: 20px;
          padding-bottom: 20px;
          }

        .stTabs [aria-selected="true"] {
            background-color: none;
            color: #00008B;
        }

      </style>""", unsafe_allow_html=True)
    with st.sidebar:
      

        from PIL import Image
        image = Image.open('./assets/F-GeniusJade.png')
        st.image(image, caption='')
        #st.write("Explore Company Statements")
        #str_input = st.text_input(label=' Enter the question:')
        #st.write("Explore Annual Reports")
        #query = st.text_input(label='Enter the question: ')


      
    #str_input = st.text_input(label=' Enter the question:') 
    with tab1:
        st.markdown("""
        I am  Finance Assistant of your company. I possess the ability to extract information from your company's financial statements like balance sheet, income statements, etc spanning across 2003 to 2022. Please ask me questions and I will try my level best to provide accurate responses.
          
      
          **Some Sample Questions:**
      
          - What is the net income of JGSDL in 2022?
          - Compare this year revenue of JGSDL with last year?
        
        
        """)

      
        
        str_input = st.text_input(label=' Enter the question:') 
        if "messages" not in st.session_state:
              st.session_state.messages = []

        for message in st.session_state.messages:
              with st.chat_message(message["role"]):
                   
                  st.markdown(message["content"], unsafe_allow_html = True)
        
        if prompt := str_input:
             st.chat_message("user").markdown(prompt, unsafe_allow_html = True)
              # Add user message to chat history
             st.session_state.messages.append({"role": "user", "content": prompt})

        if len(str_input) > 1:
            #with st.spinner('Looking up your question i'):
                try:
                    output = fs_chain(str_input)
                    #st.write(output)
                    try:
                    # if the output doesn't work we will try one additional attempt to fix it
                        query_result = sf_query(output['result'])
                   
                        if len(query_result) >= 1:
                          #st.write(query_result)
                          with st.chat_message("assistant"):
                            st.markdown(tabulate(query_result, tablefmt="html"), unsafe_allow_html = True) 
                        #st.write(output)
                          st.session_state.messages.append({"role": "assistant", "content": tabulate(query_result, tablefmt="html")})
                    except:
                        
                        st.session_state.messages.append({"role": "assistant", "content": "The first attempt didn't pull what you were needing. Trying again..."})
                        output = fs_chain(f'You need to fix the code but ONLY produce SQL code output. If the question is complex, consider using one or more CTE. Examine the DDL statements and answer this question: {output}')
                        st.write(sf_query(output['result']))
                        #st.write(output)

                    #result_2 = prompts.letter_chain(str_input)
                    #st.write('PineCone:', result_2['result'])  
                    #output = fs_chain(str_input)
                    #query_result = sf_query(output['result'])
                      #st.write(query_result)
                    #df_2 = pd.DataFrame(query_result)
                    #df_str_2 = df_2.to_string(index=True)
                    #str_input_2 = str_input + ' '+ df_str_2
                      #st.write(str_input_2)
                    #result_3 = prompts.letter_chain(str_input_2)
                    #st.write('Result after sending the question and data:', result_3['result'])
                    
                     

                  
                    #result_2 = prompts.letter_chain(df_str_2)
                    #st.write('Summary:', result_2['result'])  
                    #result_4 = prompts.letter_chain(str_input)
                    #st.write('Result after sending question:', result_4['result'])   
                except:
                    st.session_state.messages.append({"role": "assistant", "content": "Please try to improve your question. Note this tab is for financial statement questions. Use Tab 2 to ask from Annual Reports ."})
                    st.session_state.messages.append({"role": "assistant", "content": f"Final errored query used:"})
                    #sst.write(output)
        


   
    with tab3:
        st.markdown("""
      
        I am capable of reviewing the annual reports from 2018 to 2022. Please ask me questions and I will try my level best to provide accurate responses
               
         **Some Sample Questions:**
      
         - How many shareholders does JGSDL have?
         - What are the risks JGSDL is facing?
        
        
        """
        )
        
        # Create a text input to edit the selected question
        #query = st.text_input(label='Enter the question:')
        query = st.text_input(label='Enter the question: ')
        if "messagestab2" not in st.session_state:
              st.session_state.messagestab2 = []

        for message in st.session_state.messagestab2:
              with st.chat_message(message["role"]):
                   
                  st.markdown(message["content"], unsafe_allow_html = True)
        
        if prompt := query:
             st.chat_message("user").markdown(prompt, unsafe_allow_html = True)
              # Add user message to chat history
             st.session_state.messagestab2.append({"role": "user", "content": prompt})
        #query = st.text_input(label=f'✉️ Enter the question: ')
        # Display the selected question and the edited question
        
        #st.write('Enter the question:', query)
        #query = st.text_input("What would you like to ask Warren Buffett?")
        if len(query)>1:
            #with st.spinner('Looking through lots of Shareholder letters now...'):
                
                try:
                    #st.caption(":blue[FinGuru's response:]")
                    #st.write(prompts.letter_qa(query))
                     with st.chat_message("assistant"):
                    
                      result = prompts.letter_chain(query)
                      st.write(result['result'])
                    #st.caption(":blue[Source Documents Used] :📄:")
                    #st.write(result['source_documents'])
                except:
                    st.write("Please try to improve your question")


      


