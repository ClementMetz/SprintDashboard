
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from auxiliary import athle_regressor,standardize_event,clean_up_perf
import hashlib


def requestffa(driver,athletename,firstname,gender,by_licence_nb=False,licence_nb=0,clubname=''):
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
                #id
                primary_key = hashlib.sha256()
                primary_key.update(t[i].encode())
                primary_key.update(str(licence_nb).encode())
                l = t[i].split('|||')
                if len(l)<=3: #clubline found
                    continue
                #day, month and date
                date = l[1].split('/')
                d = date[0]
                m = date[1]
                day = int(d)
                month = int(m)
                if len(m)==1:
                    m = '0'+m
                if len(d)==1:
                    d = '0'+d
                date = str(y)+"-"+m+"-"+d
                #event
                event = l[3]
                event,hidden_event = standardize_event(event,gender)
                #perf
                perf = l[6]
                perf = clean_up_perf(perf,event)
                if perf == 'o':
                    continue
                unit_perf = perf.replace("'",".").replace("m",".")
                perf_chunks = unit_perf.split(".")
                while len(perf_chunks)!=4:
                    perf_chunks = [0]+perf_chunks
                if len(perf_chunks[3])==1:
                    perf_chunks[3] = perf_chunks[3]+'0' #11"7 -> 11"70
                try: #check for failed clean-up, if failed skip the entry
                    for j in range(4):
                        perf_chunks[j] = int(perf_chunks[j])
                except:
                    continue

                h,mins,s,hund = tuple(perf_chunks)
                unit_perf = h*3600+mins*60+s+hund/100

                #wind
                if len(l)==13:
                    try:
                        wind = float(l[7].replace(' ','').replace('(',')').split(')')[1])
                    except:
                        wind = None
                else:
                    wind = None
                
                #points
                try: #compute points
                    points = regressor.reg(hidden_event,perf)
                except: #event unknown by regressor, try scraping points
                    if len(l)==12: #no wind
                        points = l[7]
                    elif len(l)==13: #wind
                        points = l[8]
                    else: #unknown points and event
                        continue
                
                if type(points)!=int: #weird output for unknown event
                    continue

                entry = [primary_key.hexdigest(),licence_nb,by_licence_nb,event] + perf_chunks + [unit_perf,points,y,month,day,date,wind]
                
                entries.append(entry)

        except:
            pass

        data+=entries
        driver.back()

    print(str(len(data))+' entries found.')
    return(data)