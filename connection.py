# Useful libraries
import pandas as pd
import streamlit as st
from office365.sharepoint.files.file import File
from office365.sharepoint.client_context import ClientContext
from office365.runtime.auth.authentication_context import AuthenticationContext

# Page setup
st.set_page_config(layout = 'wide')

# SharePoint and Folder urls
sharepoint_url = "https://gemfor.sharepoint.com/sites/cloud-support/"
folder_in_sharepoint = "/17/Forms/AllItems.aspx?id=%2Fsites%2Fcloud-support%2F17%2F值班監控日誌%2F例行工作%20日%2F202410監控日誌%2FEXCEL&viewid=0713be7b-0a1f-4d24-8f8d-3a9c54d5da06"

# First section: e-mail and password as input
placeholder = st.empty()
with placeholder.container():
  col1, col2, col3 = st.columns(3)
  with col2:
    st.markdown("## **SharePoint connection with Streamlit**")
    st.markdown("--------------")
    email_user = st.text_input("Your e-mail")
    password_user = st.text_input("Your password", type="password")

    # Save the button status
    Button = st.button("Connect")
    if st.session_state.get('button') != True:
      st.session_state['button'] = Button

# Authentication and connection to SharePoint
def authentication(email_user, password_user, sharepoint_url) :
  auth = AuthenticationContext(sharepoint_url) 
  auth.acquire_token_for_user(email_user, password_user)
  ctx = ClientContext(sharepoint_url, auth)
  web = ctx.web
  ctx.load(web)
  ctx.execute_query()
  return ctx

# Second section: display results
# Check if the button "Connect" has been clicked
if st.session_state['button'] :  
  try :                            
    placeholder.empty()
    if "ctx" not in st.session_state :
        st.session_state["ctx"] = authentication(email_user, 
                                                 password_user,
                                                 sharepoint_url)
    
    st.write("Authentication: successfull!")
    st.write("Connected to SharePoint: **{}**".format( st.session_state["ctx"].web.properties['Title']))
  
    # Connection to the SharePoint folder
    target_folder = st.session_state["ctx"].web.get_folder_by_server_relative_url(folder_in_sharepoint)
    
    # Read and load items
    items = target_folder.files
    st.session_state["ctx"].load(items)
    st.session_state["ctx"].execute_query()
    
    # Save some information for each file using item.properties
    names, last_mod, relative_url = [], [], []
    for item in items:
        names.append( item.properties["Name"] )
        last_mod.append( item.properties["TimeLastModified"] )
        relative_url.append( item.properties["ServerRelativeUrl"] )
     
    # Create and display the final data frame
    Index = ["File name", "Last modified", "Relative url"]
    dataframe = pd.DataFrame([names, last_mod, relative_url], index = Index).T
    st.write("")
    st.write("")
    st.write("These are the files in the folder:")
    st.table(dataframe)
  
  # Handle the error in the authentication section
  except :
    col1, col2, col3 = st.columns(3)
    with col2:
      st.write("**Authentication error: reload the page**")