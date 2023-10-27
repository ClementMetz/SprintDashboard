
import os
from flask import Flask
from flask import request
from selenium import webdriver
#from Request import requestffa
from request2 import requestffa
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import bigquery
"""
#from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials





#SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
#credential_path = "sprint-383421-25956e952f47.json"
#os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credential_path, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return(creds)



def get_clients_with_credentials(): #Get API clients (local with account service credentials)
    creds = get_credentials()
    try:
        service = build('sheets', 'v4', credentials=creds)
        sheet_client = service.spreadsheets()
        bigquery_client = bigquery.Client()

    except HttpError as err:
        print(err)
    
    return(sheet_client,bigquery_client)
"""

app = Flask(__name__)

def get_clients(): #Get API clients
    try:
        service = build('sheets', 'v4')
        sheet_client = service.spreadsheets()
        bigquery_client = bigquery.Client()

    except HttpError as err:
        print(err)
    
    #except:
        #sheet_client,bigquery_client = get_clients_with_credentials()
    
    return(sheet_client,bigquery_client)

def build_sheet_output(data,alias):
    output = []
    for x in data:
        y = x[2:]
        y = [alias] + y
        output.append(y)
    return([[str(output)[2:-2].replace("'","")]])



@app.route("/", methods=["GET","POST"])
def main():
    
    sheet_id = request.args.get('sheet_id','')
    line_nb = request.args.get('line_nb','')
    athletename = request.args.get('name','')
    firstname = request.args.get('firstname','')
    gender = request.args.get('gender','')
    licence_nb = request.args.get('licence_nb','')
    by_licence_nb = licence_nb!=''
    alias = request.args.get('alias','')

    driver_options = webdriver.ChromeOptions()
    driver_options.add_argument("headless")
    driver_options.add_argument("disable-gpu")
    driver_options.add_argument("disable-extensions")
    driver_options.add_argument("no-sandbox")
    driver_options.add_argument("disable-dev-shm-usage")
    driver = webdriver.Chrome(options=driver_options) #service=ChromeDriverManager().install(), 

    url = "https://bases.athle.fr/asp.net/accueil.aspx?frmbase=resultats"
    driver.get(url)

    data = requestffa(driver,athletename,firstname,gender,by_licence_nb,licence_nb,'')
    sheet_client, bigquery_client = get_clients()
    
    if by_licence_nb:

        database_name = 'competition_data'
        table_name = 'athletes'
        # Référence à la table résultats
        table_ref_athletes = bigquery_client.dataset(database_name).table(table_name)
        table_athletes = bigquery_client.get_table(table_ref_athletes)

        athlete_data = [[int(licence_nb),athletename,firstname,gender]]
        query = f"SELECT COUNT(*) FROM `sprint-383421.{database_name}.{table_name}` WHERE licence_nb = {licence_nb}" #check if athlete already in table
        query_job = bigquery_client.query(query)
        result = query_job.result()
        for row in result:
            if row[0]==0:
                bigquery_client.insert_rows(table_athletes, athlete_data)


        # Reference to results table
        table_name = 'results_data'
        table_ref_results = bigquery_client.dataset(database_name).table(table_name)
        table_results = bigquery_client.get_table(table_ref_results)

        #Check for duplicates in table
        results_data = data
        test_tuple = tuple([str(x[0]) for x in results_data])
        query = f"SELECT DISTINCT id FROM `sprint-383421.{database_name}.{table_name}` WHERE id IN {test_tuple}"
        query_job = bigquery_client.query(query)
        result = query_job.result()
        #Remove duplicates in data
        duplicates = [x[0] for x in result]
        entry_nb=0
        l = len(results_data)
        while entry_nb < l:
            if results_data[entry_nb][0] in duplicates:
                del(results_data[entry_nb])
                l-=1
            else:
                y,m,d = str(results_data[entry_nb][8]),str(results_data[entry_nb][9]),str(results_data[entry_nb][10])
                if len(m)==1:
                    m = '0'+m
                if len(d)==1:
                    d = '0'+d
                date = y+"-"+m+"-"+d
                h,mins,s,hund = results_data[entry_nb][3],results_data[entry_nb][4],results_data[entry_nb][5],results_data[entry_nb][6]
                results_data[entry_nb].append(date)
                results_data[entry_nb].append(h*3600+mins*60+s+hund/100)
                entry_nb+=1
        
        if entry_nb>0:
            bigquery_client.insert_rows(table_results, results_data)


    else:
        output = build_sheet_output(data,alias)
        print(output)
        sheet_client.values().clear(spreadsheetId=sheet_id,
                    range="local_data!L{}".format(line_nb)).execute()    
        sheet_client.values().update(spreadsheetId=sheet_id,
                    range="local_data!L{}".format(line_nb),valueInputOption = "USER_ENTERED",body= {'values' : output}).execute() #output[1:-1]
        if output!="": #found existing athlete
            sheet_client.values().update(spreadsheetId=sheet_id,
                    range="Dashboard!F{}".format(line_nb),valueInputOption = "USER_ENTERED",body= {'values' : [[False]]}).execute() #Delete option Scrape

    return "Done!"

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))