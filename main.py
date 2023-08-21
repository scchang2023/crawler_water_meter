# 載入 selenium 相關模組
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
# delay
import time
# 存成 csv 檔
import csv
# 取得目前時間模組
import datetime
# 系統路徑
import os
import requests

PRICE_PCM = 17

def create_chrome_driver()->webdriver:
    options = Options()
    options.add_argument("--headless")
    
    # for windows
    current_cwd = os.path.abspath(os.getcwd())
    options.chrome_executable_path=f"{current_cwd}\chromedriver-win64\chromedriver.exe"

    # for linux
    # unzip chromedriver_linux64.zip
    # sudo mv chromedriver /usr/local/bin/ 安裝 chromedriver
    # chromedriver --version 查是否成功安裝 chromedriver
    # options.chrome_executable_path="/usr/local/bin/chromedriver"
    # print(options.chrome_executable_path)
    # 建立 driver 物件實體
    return webdriver.Chrome(options=options)

def close_chrome_driver(dr:webdriver)->None:
    dr.close()

def login_meters_page(dr:webdriver)->None:
    print("連線至水錶登入頁面")
    dr.get("http://www.cnyiot.com/MLogin.aspx")
    time.sleep(3)
    print("自動輸入帳密並登入")
    username_input = dr.find_element(By.ID, "username")
    password_input = dr.find_element(By.ID, "password")
    username_input.send_keys("00011049")
    password_input.send_keys("14725818")
    btn_singin = dr.find_element(By.ID, "subBt")
    btn_singin.send_keys(Keys.ENTER)
    time.sleep(3)

def get_meters_management(dr:webdriver)->list:
    print("連線至水錶管理頁面")
    dr.get("http://www.cnyiot.com/MMpublicw.aspx")
    time.sleep(3)
    print("取得水錶管理")
    meter_element = dr.find_element(By.ID, "table1")
    time.sleep(3)
    # print(meter_element.text)
    meter_element_list = meter_element.text.splitlines()
    meter_element_list = meter_element_list[9:]
    # print(meter_element_list)
    data = []
    for i in meter_element_list:
        meter_item={}
        i = i.replace("在线 （通水 )","在线(通水)")
        i = i.split(' ')
        meter_item['水錶名稱'] = i[0]
        meter_item['水錶號碼'] = i[1]
        meter_item['總水量'] = i[5]
        meter_item['狀態'] = i[6]
        meter_item['供電方式'] = i[7]
        data.append(meter_item)
    print(data)
    return data

def save_meters_management_csv(data:list)->None:
    print("儲存水錶管理頁面")
    # current_time = datetime.datetime.now()
    # print(current_time)
    current_date = datetime.date.today()
    # print(current_date)    
    filename = f"目前水錶管理-{current_date}.csv"    
    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = ['水錶名稱','水錶號碼', '總水量','狀態','供電方式']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def get_meter_history(dr:webdriver, meter:str)->(list, float):
    print(f"連線至水錶 {meter} 歷史記錄頁面")
    url = f"http://www.cnyiot.com/MMpublicHis.aspx?ID={meter}"
    dr.get(url)
    time.sleep(3)
    print(f"取得水錶 {meter} 歷史記錄")
    meter_element = dr.find_element(By.ID, "table1") 
    # print(meter_element.text)
    meter_element_list:list = meter_element.text.splitlines()
    meter_element_list = meter_element_list[7:]
    data = []
    usage = 0.0
    for i in meter_element_list:
        meter_item={}
        i = i.replace("查看详情","")
        i = i.split(' ')
        meter_item['開始時間'] = i[1]+ ' ' +i[2]
        meter_item['結束時間'] = i[3]+ ' ' +i[4]
        meter_item['開始總水量'] = i[5]
        meter_item['結束總水量'] = i[6]
        meter_item['使用水量'] = i[8]
        usage += float(i[8])
        data.append(meter_item)
    print(data)
    return data, usage

def save_meter_history_csv(meter:str, data:list, usage:float, price_pcm: int)->None:
    print(f"儲存水錶 {meter} 歷史記錄")
    current_date = datetime.date.today()
    filename = f"{meter}-{current_date}.csv"
    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = ['開始時間', '結束時間','開始總水量', '結束總水量', '使用水量']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    bill = round(price_pcm * usage)
    usage_str = "%.1f"%usage
    with open(filename, mode='a', encoding='utf-8', newline='') as file:
        file.writelines(f"""使用總水量(度),{usage_str}
每度水(元),{price_pcm}
金額(元),{bill}""")

def send_line_notify(msg:str)->requests.Response:
    url = 'https://notify-api.line.me/api/notify'
    # 個人測試
    token = 'pbgUOOVbAa9HgFWJRixB6zIdrOEvK7KQ2FWeoZGZTiJ'
    # 新富昌群組用
    # token = 'al3yDsfErCVsK5XQjahLKTGiG2dpyjbAg1F2CTuyKWQ'
    headers = {
        'Authorization': 'Bearer ' + token, # 設定權杖
        'Content-Type' : 'application/json'
    }
    params = {
        'message': msg # 設定要發送的訊息
    }
    return requests.post(url, headers=headers, params=params) # 使用 post 方法

def send_meters_management_line_notify(data:list)->requests.Response:
    msg:str="""
    [目前水錶管理]
    """
    for i in data:
        line:str = f"""
    [水錶名稱:{i['水錶名稱']}]
    [水錶號碼:{i['水錶號碼']}]
    [總水量:{i['總水量']}]
    [狀態:{i['狀態']}]
    [供電方式:{i['供電方式']}]
    """
        msg = msg + line
    print("傳送水錶管理頁面至 LINE Notify")
    return send_line_notify(msg)

def send_meter_history_line_notify(meter:str, data:list, usage:float, price_pcm:int)->requests.Response:
    usage = 0.0
    for i in data:
        usage += float(i['使用水量'])
    bill = round(price_pcm * usage)
    usage_str ="%.1f"%usage
    current_date = str(datetime.date.today())
    current_month = current_date[:7]
    if(meter =='1F前面水錶' or meter =='2F前面水錶'):
        tenant = "21世紀"
    else:
        tenant = "G12汽車"
    msg:str=f"""
    [{meter}-{tenant}]
    [用水月份:{current_month}]
    [開始時間:{data[-1]['開始時間']}]
    [結束時間:{data[0]['結束時間']}]
    [開始總水量(度):{data[-1]['開始總水量']}]
    [結束總水量(度):{data[0]['結束總水量']}]
    [總使用水量(度):{usage_str}]
    [每度水(元):{price_pcm}]
    [金額(元):{bill}]
    """
    print(f"傳送水錶 {meter} 歷史記錄至LINE")
    return send_line_notify(msg)

def send_bill_total_line_notify(name:str, bill:int)->requests.Response:
    current_date = str(datetime.date.today())
    current_month = current_date[:7]
    msg:str=f"""
    [{name}]
    [用水月份:{current_month}]
    [總金額(元):{bill}]
    """
    return send_line_notify(msg)

def main():
    driver = create_chrome_driver()
    login_meters_page(driver)
    meters_management = get_meters_management(driver)
    send_meters_management_line_notify(meters_management)
    save_meters_management_csv(meters_management)
    print("\n")
    bill_G12, bill_21Century = 0, 0
    for i in meters_management:
        meter_history, usage = get_meter_history(driver, i["水錶號碼"])
        send_meter_history_line_notify(i["水錶名稱"],meter_history, usage, PRICE_PCM)
        save_meter_history_csv(i["水錶名稱"], meter_history, usage, PRICE_PCM)
        print("\n")
        if(i["水錶名稱"]=='1F前面水錶' or i["水錶名稱"]=='2F前面水錶'):
            bill_21Century += round(usage*PRICE_PCM)
        else:
            bill_G12 += round(usage*PRICE_PCM)
    close_chrome_driver(driver)
    send_bill_total_line_notify("G12汽車", bill_G12)
    time.sleep(3)
    send_bill_total_line_notify("21世紀", bill_21Century)

if __name__ == "__main__":
    main()