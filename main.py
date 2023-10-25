import gspread
import os
from flask import Flask
from flask import request
from selenium import webdriver
from Request import requestffa


app = Flask(__name__)


def build_sheet_output(data,alias):
    output=[]
    for x in data:
        sample = [alias,x[1][0],x[2].replace("'",".").replace("m",".").replace("0",'x')+'x',x[3],x[5],x[6]]
        count = sample[2].count('.')
        while count<3:
            sample[2] = '0.'+sample[2]
            count+=1
        output.append(sample)
    return(str(output).replace("'","").replace('"',""))

@app.route("/", methods=["GET","POST"])
def main():
    
    sheet_id = request.args.get('sheet_id')
    line_nb = request.args.get('line_nb')
    athletename = request.args.get('name')
    firstname = request.args.get('firstname')
    gender = request.args.get('gender')
    licence_nb = request.args.get('licence_nb')
    by_licence_nb = licence_nb!=''
    alias = request.args.get('alias')


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
    output = build_sheet_output(data,alias)

    gc = gspread.service_account(filename='sprint-383421-757a3d429705.json')
    sheet = gc.open_by_key(sheet_id)
    dashboard = sheet.worksheet("Dashboard")

    dashboard.batch_clear(["K{}".format(line_nb)])
    dashboard.update('K{}'.format(line_nb),output[1:-1])
    if output!="": #found existing athlete
        dashboard.update('F{}'.format(line_nb),False)

    return "Done!"

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))