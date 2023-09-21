import snowflake.connector
import numpy as np
import pandas as pd
import streamlit as st
import altair as alt
import prompts
#import tkinter as tk



st.set_page_config(layout="wide")

# Variables
sf_db = st.secrets["sf_database"]
sf_schema = st.secrets["sf_schema"]
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

chat_history = []




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




# create tabs
tab1, tab2, tab3 = st.tabs([
    "Explore Company Statements ", 
    "Explore Company Status ",
    "Explore Annual Reports "
    ]
          
    )

with st.sidebar:('''
#JADE
''')
  

    #from PIL import Image
    #image = Image.open('/content/drive/MyDrive/NewSnowflake/streamlit-buffett-main/assets/Jade.png')
    #st.image(image, caption='')

   

   

with tab1:
    st.markdown("""
    # Greetings from FinGuru !! 
    
    A warm welcome to all! I'm FinGuru, your Intelligent Finance Virtual Assistant. As an AI expert, I'm here to assist you with all your financial inquiries. I possess the ability to analyze financial statements from a variety of companies. Whether you have questions about budgeting, investing, or any other financial topic, I'm here to provide you with insightful answers and guidance. Feel free to ask me anything related to finance!
    
    **Here are some guidelines to ask questions to FinGuru**

    - Keep your query clear and straightforward manner.
    - Avoid overly complex or jargon-filled language.
    - Use a mix of open-ended questions (e.g., "How can I help you today?") and closed-ended questions (e.g., "Yes or no?") based on the situation.
    - Provide multiple-choice options when appropriate to make it easier for me to respond
    - Be polite and empathetic in your questions.
    - Use courteous language and expressions.
    """)

   
    
    str_input = st.text_input(label=' Enter the question: :question:')  

    if len(str_input) > 1:
        #with st.spinner('Looking up your question i'):
            try:
                output = fs_chain(str_input)
                #st.write(output)
                try:
                    # if the output doesn't work we will try one additional attempt to fix it
                    query_result = sf_query(output['result'])
                   
                    if len(query_result) > 1:
                        st.write(query_result)
                        #st.write(output)
                except:
                    st.write("The first attempt didn't pull what you were needing. Trying again...")
                    output = fs_chain(f'You need to fix the code but ONLY produce SQL code output. If the question is complex, consider using one or more CTE. Examine the DDL statements and answer this question: {output}')
                    st.write(sf_query(output['result']))
                    #st.write(output)
            except:
                st.write("Please try to improve your question. Note this tab is for financial statement questions. Use Tab 3 to ask from shareholder letters. Also, only a handful of companies are available, which you can see on the side bar.")
                st.write(f"Final errored query used:")
                #sst.write(output)
    


with tab2: 
    st.markdown("""
    
    Are you curious to know how other companies are faring? Interested in tracking their financial metrics like Net income, cash flow, profit margin, etc. Eager to read their income statement, balance sheet and profit and loss statements!!
    
    
    ### FinGuru is here you help you with the Exploration.Simply select the company from the drop down and get started !!
   
    
    """)
    #sel_tick = st.selectbox("Select a ticker to view", tick_list)
    option = st.selectbox("Select Company", options=list(tick_list.keys()), format_func=format_func)
    #st.write(f"You selected option {option} called {format_func(option)}")

    # pull the financial statements
    # This whole section could be more efficient...
    inc_st = pull_financials(sf_db, sf_schema, 'income_statement_annual', option)
    bal_st = pull_financials(sf_db, sf_schema, 'balance_sheet_annual', option)
    bal_st['debt_to_equity'] = bal_st['total_debt'].div(bal_st['total_equity'])
    cf_st =  pull_financials(sf_db, sf_schema, 'cash_flow_statement_annual', option) 
  
    col1, col2 = st.columns((1,1))
    with col1:
        # Net Income metric
        net_inc = kpi_recent(inc_st, 'net_income')
        st.metric('Net Income', 
                  f'${net_inc[0]}B', 
                  delta=round(net_inc[0]-net_inc[1],2),
                  delta_color="normal", 
                  help=None, 
                  label_visibility="visible")
        plot_financials(inc_st, 'year', 'net_income', year_cutoff, 'Net Income')
        
        # netincome ratio
        net_inc_ratio = kpi_recent(inc_st, 'net_income_ratio', periods=2, unit=1)
        st.metric('Net Profit Margin', 
                  f'{round(net_inc_ratio[0]*100,2)}%',
                  delta=round(net_inc_ratio[0]-net_inc_ratio[1],2), 
                  delta_color="normal", 
                  help=None, 
                  label_visibility="visible")
        plot_financials(inc_st, 'year', 'net_income_ratio', year_cutoff, 'Net Profit Margin')
    
    with col2:
        # free cashflow
        fcf = kpi_recent(cf_st, 'free_cash_flow' )
        st.metric('Free Cashflow', 
                  f'${fcf[0]}B', 
                  delta=round(fcf[0]-fcf[1],2), 
                  delta_color="normal", 
                  help=None, 
                  label_visibility="visible")
        plot_financials(cf_st, 'year', 'free_cash_flow', year_cutoff, 'Free Cash Flow')

        # debt to equity
        debt_ratio = kpi_recent(bal_st, 'debt_to_equity', periods=2, unit=1)
        st.metric('Debt to Equity', 
                  f'{round(debt_ratio[0],2)}', 
                  delta=round(debt_ratio[0]-debt_ratio[1],2), 
                  delta_color="normal", 
                  help=None, 
                  label_visibility="visible")
        plot_financials(bal_st, 'year', 'debt_to_equity', year_cutoff, 'Debt to Equity')

    # enable a financial statment to be selected and viewed
    sel_statement = st.selectbox("Select a statement to view", fin_statement_list)
    fin_statement_dict = {'income_statement': inc_st,
                          'balance_sheet': bal_st, 
                          'cash_flow_statement':cf_st}
    st.dataframe(fin_statement_dict[sel_statement])

with tab3:
    st.markdown("""
  
     Your CEO has released the annual letter to the shareholders. It is an important document with key information, performance upddates and company's strategy to shareholders
     
    It is the much awatied document but you are hesitant to read and understand the company's Performance, Strategic outlook, Operational highlights, Market and Industry Analysis and Financial information
    ### Call out to FinGuru !!!
    
    
    """
    )
    
    # Create a text input to edit the selected question
    #query = st.text_input(label='Enter the question:')
    query = st.text_input(label=':question: Enter the question: ') 
    #query = st.text_input(label=f'✉️ Enter the question: ')
    # Display the selected question and the edited question
    
    #st.write('Enter the question:', query)
    #query = st.text_input("What would you like to ask Warren Buffett?")
    if len(query)>1:
        #with st.spinner('Looking through lots of Shareholder letters now...'):
            
            try:
                #st.caption(":blue[FinGuru's response:]")
                #st.write(prompts.letter_qa(query))
                result = prompts.letter_chain(query)
                st.write(result['result'])
                #st.caption(":blue[Source Documents Used] :📄:")
                #st.write(result['source_documents'])
            except:
                st.write("Please try to improve your question")

   


