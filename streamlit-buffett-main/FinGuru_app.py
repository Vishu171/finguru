import snowflake.connector
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
import prompts
from tabulate import tabulate
from PIL import Image
from streamlit_option_menu import option_menu

st.set_page_config(layout="wide")

username=st.secrets["streamlit_username"]
password=st.secrets["streamlit_password"]
column_list = ['CASH_AND_EQUIVALENTS','SHORT_TERM_INVESTMENTS','CASH_AND_SHORT_TERM_INVESTMENTS','NET_RECEIVABLES','INVENTORY','TOTAL_CURRENT_ASSETS','PROPERTY_PLANT_EQUIPMENTNET','GOODWILL','INTANGIBLE_ASSETS','GOOD_WILL_AND_INTANGIBLE_ASSETS','LONG_TERM_INVESTMENTS','TAX_ASSETS','OTHER_NON_CURRENT_ASSETS','TOTAL_NON_CURRENT_ASSETS','OTHER_ASSETS','TOTAL_ASSETS','ACCOUNTS_PAYABLES','SHORT_TERM_DEBT','TAX_PAYABLES','OTHER_CURRENT_LIABILITIES','TOTAL_CURRENT_LIABILITIES','LONG_TERM_DEBT','DEFERRED_REVENUE_NONCURRENT','DEFERRED_TAX_LIABILITIES_NONCURRENT','OTHER_NONCURRENT_LIABILITIES','TOTAL_LIABILITIES','RETAINED_EARNINGS','ACCUMULATED_OTHER_COMPREHENSIVE_INCOME','OTHER_TOTAL_STOCKHOLDERS_EQUIT','TOTAL_STOCKHOLDERS_EQUITY','TOTAL_EQUITY','TOTAL_LIABILITIES_AND_STOCKHOLDERS_EQUITY','MINORITY_INTEREST','TOTAL_LIABILITIES_AND_TOTAL_EQUITY','TOTAL_INVESTMENTS','TOTAL_DEBT','NET_DEBT','NET_INCOME','DEPRECIATION_AND_AMORTIZATION','DEFERRED_INCOME_TAX','STOCK_BASED_COMPENSATION','CHANGE_IN_WORKING_CAPITAL','ACCOUNTS_RECEIVABLES','INVENTORY','ACCOUNTS_PAYABLES','OTHER_WORKING_CAPITAL','OTHER_NON_CASH_ITEMS','NET_OPERATING_ACTIVITIES','INVESTMENTS_IN_PROPERTY_PLANT_AND_EQUIPMENT','ACQUISITIONS','PURCHASES_OF_INVESTMENTS','SALES_OF_INVESTMENTS','OTHER_INVESTING_ACTIVITES','NET_INVESTING_ACTIVITES','DEBT_PAYMENT','COMMON_STOCK_ISSUED','COMMON_STOCK_REPURCHASED','DIVIDENDS_PAID','OTHER_FINANCING_ACTIVITES','NET_FINANCING_ACTIVITIES','NET_CHANGE_IN_CASH','OPERATING_CASH_FLOW','CAPITAL_EXPENDITURE','FREE_CASH_FLOW','REVENUE','COST_OF_REVENUE','GROSS_PROFIT','GROSS_PROFIT_RATIO','RESEARCH_AND_DEVELOPMENT_EXPENSES','SELLING_GENERAL_AND_ADMINISTRATIVE_EXPENSES','OPERATING_EXPENSES','COST_AND_EXPENSES','INTEREST_INCOME','INTEREST_EXPENSE','DEPRECIATION_AND_AMORTIZATION','EBITDA_EARNINGS_BEFORE_INTEREST_TAX_DEPRECATION_AND_AMORITZATION','OPERATING_INCOME','OTHER_INCOME_EXPENSES','INCOME_BEFORE_TAX','INCOME_TAX_EXPENSE','NET_INCOME','EPS_EARNINGS_PER_SHARE','EPS_EARNINGS_PER_SHARE_DILUTED','WEIGHTED_AVERAGE_SHARES_OUTSTANDING','WEIGHTED_AVERAGE_SHARES_OUTSTANDING_DILUTED']

# establish snowpark connection
conn = st.experimental_connection("snowpark")

# Reset the connection before using it if it isn't healthy
try:
    query_test = conn.query('select 1')
except:
    conn.reset()

# adding this to test out caching
st.cache_data(ttl=86400)

def plot_financials(df_2, x, y, x_cutoff, title):
    """"
    helper to plot the altair financial charts
    
    return st.altair_chart(alt.Chart(df_2.head(x_cutoff)).mark_bar().encode(
        x=x,
        y=y
        ).properties(title=title)
    ) 
    """
    df_subset = df_2.head(x_cutoff)
    # Create a bar chart using st.bar_chart()
    return st.bar_chart(df_subset.set_index(x)[y])
    
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

def creds_entered():
    if len(st.session_state["streamlit_username"])>0 and len(st.session_state["streamlit_password"])>0:
          if  st.session_state["streamlit_username"].strip() != username or st.session_state["streamlit_password"].strip() != password: 
              st.session_state["authenticated"] = False
              st.error("Invalid Username/Password ")

          elif st.session_state["streamlit_username"].strip() == username and st.session_state["streamlit_password"].strip() == password:
              st.session_state["authenticated"] = True


def authenticate_user():
      if "authenticated" not in st.session_state:
        buff, col, buff2 = st.columns([1,1,1])
        col.text_input(label="Username:", value="", key="streamlit_username", on_change=creds_entered) 
        col.text_input(label="Password", value="", key="streamlit_password", type="password", on_change=creds_entered)
        return False
      else:
           if st.session_state["authenticated"]: 
                return True
           else:  
                  buff, col, buff2 = st.columns([1,1,1])
                  col.text_input(label="Username:", value="", key="streamlit_username", on_change=creds_entered) 
                  col.text_input(label="Password:", value="", key="streamlit_password", type="password", on_change=creds_entered)
                  return False

if authenticate_user():
    with st.sidebar:
      image = Image.open("streamlit-buffett-main/assets/FinGPT.png")
      image = st.image('streamlit-buffett-main/assets/FinGPT.png',width=280)
      selected = option_menu( menu_title="Explore",
      menu_icon = "search",
      options=["Company Statements", 'Annual Reports'], 
      icons=['database', 'filetype-pdf'],  
      default_index=0,
      styles={"container":{"font-family": "Garamond"},
        "nav-link": {"font-size": "20px", "text-align": "left", "margin":"0px", "--hover-color": "grey"}})
    if selected =='Company Statements':
        str_input = st.chat_input("Enter your question:")
        st.markdown("""
        I am  Finance Assistant of your company. I possess the ability to extract information from your company's financial statements like balance sheet, income statements, etc spanning across 2003 to 2022. Please ask me questions and I will try my level best to provide accurate responses.
          
      
          **Some Sample Questions:**
      
          - What is the net income of JGSDL in 2022?
          - What are the cash and short term investment of JGSDL  in last 4 years?
        
        
        """)
        
        if "messages" not in st.session_state.keys():
              st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"], unsafe_allow_html = True)
        
        if prompt := str_input:
            st.chat_message("user").markdown(prompt, unsafe_allow_html = True)
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})

            try:
                output = fs_chain(str_input)
                try:
                    # if the output doesn't work we will try one additional attempt to fix it
                    query_result = sf_query(output['result'])
                    if len(query_result) >= 1:
                      with st.chat_message("assistant"):
                        df_2 = pd.DataFrame(query_result)
                        for name in df_2.columns:
                            if name in column_list:
                                new_name = f"{name} ($ millions)"
                                df_2.rename(columns={name : new_name}, inplace=True)
                        
                            #st.bar_chart(df_2) 
                        col1, col2 = st.columns(2)
                        df_2.columns = df_2.columns.str.replace('_', ' ')
                        headers = df_2.columns
                        with col1:
                         st.markdown(tabulate(df_2, tablefmt="html",headers=headers,showindex=False), unsafe_allow_html = True) 
                        if len(df_2.index) >2 :
                            title_name = df_2.columns[0]+'-'+df_2.columns[1]
                            with col2:
                             plot_financials(df_2,df_2.columns[0],df_2.columns[1], cutoff,title_name)
                      st.session_state.messages.append({"role": "assistant", "content": tabulate(df_2, tablefmt="html",headers=headers,showindex=False)})
                except:
                    st.session_state.messages.append({"role": "assistant", "content": "The first attempt didn't pull what you were needing. Trying again..."})
                    output = fs_chain(f'You need to fix the code but ONLY produce SQL code output. If the question is complex, consider using one or more CTE. Examine the DDL statements and answer this question: {output}')
                    st.write(sf_query(output['result']))
            except:
                st.session_state.messages.append({"role": "assistant", "content": "Please try to improve your question. Note this tab is for financial statement questions. Use Tab 2 to ask from Annual Reports ."})
                #sst.write(output)
    else:
        query = st.chat_input("Enter your question:")
        st.markdown("""

        I am capable of reviewing the annual reports from 2018 to 2022. Please ask me questions and I will try my level best to provide accurate responses
              
        **Some Sample Questions:**
      
        - What are the operating expenses of the JGSDL for last 2 years?
        - What are the risks JGSDL is facing?
        
        """)
        
        # Create a text input to edit the selected question
        if "messages_1" not in st.session_state.keys():
              st.session_state.messages_1 = []

        for message in st.session_state.messages_1:
            with st.chat_message(message["role"]):
                st.markdown(message["content"], unsafe_allow_html = True)
        
        if prompt1 := query:
            st.chat_message("user").markdown(prompt1, unsafe_allow_html = True)
              # Add user message to chat history
            st.session_state.messages_1.append({"role": "user", "content": prompt1})
            try:
                with st.chat_message("assistant"):
                  result = prompts.letter_chain(query)
                  st.write(result['result'])
                  st.session_state.messages_1.append({"role": "assistant", "content":result['result'] } )

            except:
                st.write("Please try to improve your question")


