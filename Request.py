
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import sys
sys.path.append('..')
from auxiliary import athle_regressor,standardize_event,clean_up_perf


def request(driver,athletename,firstname,gender,by_licence_nb=False,licence_nb=0,clubname=''):
    regressor = athle_regressor()
    now = datetime.now().year
    element = driver.find_element(By.XPATH,'/html/body/div/div[2]/table/tbody/tr/td[4]')
    element.click()
    
    data = []

    for y in range(now-10,now+1):
        entries = []
        year = str(y)
        
        select = Select(driver.find_element(By.XPATH,'/html/body/div/div[2]/div[5]/div/form/table/tbody/tr/td/table/tbody/tr[1]/td[2]/select'))
        select.select_by_visible_text(year)
        
        if by_licence_nb: #to avoid namesakes
            element = driver.find_element(By.XPATH,'/html/body/div/div[2]/div[5]/div/form/table/tbody/tr/td/table/tbody/tr[6]/td[2]/input')
            element.send_keys(licence_nb)

        element = driver.find_element(By.XPATH,'/html/body/div/div[2]/div[5]/div/form/table/tbody/tr/td/table/tbody/tr[3]/td[2]/input')
        element.send_keys(athletename)

        element = driver.find_element(By.XPATH,'/html/body/div/div[2]/div[5]/div/form/table/tbody/tr/td/table/tbody/tr[4]/td[2]/input')
        element.send_keys(firstname)

        element = driver.find_element(By.XPATH,'/html/body/div/div[2]/div[5]/div/form/div[1]/input')
        element.click()

        tablexpath = '/html/body/div/div[2]/table[2]/tbody'

        try:
            table = driver.find_element(By.XPATH,tablexpath)
            soup = BeautifulSoup(table.get_attribute('innerHTML'), 'html.parser')
            t = soup.get_text(separator='|||').split('\n')
            for i in range (2,len(t)):
                l = t[i].split('|||')
                if len(l)<=3: #clubline found
                    continue
                date = l[1]
                event = l[3]
                event,hidden_event = standardize_event(event,gender)
                perf = l[6]
                perf = clean_up_perf(perf,event)
                if len(l)==12: #no wind
                    points = l[7]
                    category = l[8]
                elif len(l)==13: #wind
                    points = l[8]
                    category = l[9]
                else:
                    points = 0
                    category = "unknown"

                entry = [firstname+'_'+athletename,[event,hidden_event],perf,points,category,year,date]
                
                try: #compute points
                    entry[3] = regressor.reg(hidden_event,perf)
                    entries.append(entry)
                except: #event unknown by regressor
                    pass

        except:
            pass

        data+=entries
        driver.back()

    print(str(len(data))+' entries found.')
    return(data)