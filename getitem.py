#!/usr/bin/env python
# coding: utf-8

from multiprocessing import Process, Pool
import multiprocessing
import os, time
import mysql.connector as mariadb
#import mariadb
from mysql.connector import Error
import requests
import json
import time,datetime,random
from requests.adapters import HTTPAdapter
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, _base

host='192.168.10.1'
user=''
port=''
password=''
database=''

def get_proxy_ip():
    r = None
    while not r:
        try:
            r = requests.get('http://proxy.husan.cc')
        except:
            time.sleep(1)
    
    return r.text
    
requests.adapters.DEFAULT_RETRIES = 2 # 增加重连次数
s = requests.session()
s.keep_alive = False # 关闭多余连接
s.mount('https://', HTTPAdapter(max_retries=3))

def put_queue(q):
    all_item = []
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database, charset="utf8mb4")
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT DISTINCT item_id FROM sub_list")# WHERE user_id LIKE '%s'"%(user_id)
            sub_item = cursor.fetchall()
            #print(sub_item)
            for i in sub_item:
                all_item.append(i[0])
            
                q.put(i[0])
            #item_list = [item[0] for item in sub_item]
                print('put: ',i[0])
        return all_item        
    except Error as e:
        print("資料庫連接失敗：", e)
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()


def itemid_find_user_id(item_id):
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT acc_token FROM sub_list WHERE item_id = '%s'"%(item_id))
            acc_token = cursor.fetchall()
            token = [a_list[0] for a_list in acc_token]
            #print('all_token' ,token)
            #idd,price,qty,salestatus,url,dtime = get_sum(item_id, token)
            return token
    except Error as e:
        print("資料庫連接失敗：", e)
    except BaseException as e:
        print(e)
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            #print("資料庫連線已關閉")
            
def save_item_detail(idd,price,qty,salestatus,url,dtime):
    save_time_H = int(datetime.datetime.now().strftime("%H"))
    save_time_M = int(datetime.datetime.now().strftime("%M"))
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT `id`, `price`, `qty`, `salestatus`, `dtime` FROM `item_detail` WHERE `id` = '%s' ORDER BY `dtime` desc limit 1"%(idd))
            detail = cursor.fetchone()
            print('old:',detail)
            print('new:',idd,price,qty,salestatus)
            if detail != None:
                o_price = detail[1]
                o_qty = detail[2]
                o_salestatus = detail[3]
            else:
                o_price = -1
                o_qty = -1
                o_salestatus = -1
            if price != o_price or qty != o_qty or salestatus != o_salestatus:
                print('不一樣')
                cursor.execute("INSERT INTO item_detail (id, price, qty, salestatus, url, dtime) VALUES ('%s','%d','%d','%d','%s','%s')"%(idd,price,qty,salestatus,url,dtime))
                connection.commit()
            elif save_time_H == 0 or save_time_H == 12 :#or save_time_H == 6 or save_time_H == 18
                if save_time_M == 0:
                    cursor.execute("INSERT INTO item_detail (id, price, qty, salestatus, url, dtime) VALUES ('%s','%d','%d','%d','%s','%s')"%(idd,price,qty,salestatus,url,dtime))
                    connection.commit()
    except BaseException as e:
        print(idd,e)
        print(detail)
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
                
            

            
#抓取商品資訊
def get_sum(item_id):
    re_status = False
    re_time = 0
    while not re_status:
        try:
            p_url = "https://ecapi.pchome.com.tw/ecshop/prodapi/v2/prod/button&id="+item_id+"&fields=Seq,Id,Price,Qty,ButtonType,SaleStatus"
            proxies ={
                "http": get_proxy_ip(),
                "https": get_proxy_ip()
            }
            '''
            if re_time > 8:
                proxies ={
                "http": 'kidhu.com:3128',
                "https": 'kidhu.com:3128'
                }
            else:
                proxies ={
                    "http": get_proxy_ip(),
                    "https": get_proxy_ip()
                }
            '''
            print(datetime.datetime.now().strftime("%H:%M:%S"),item_id,proxies['https'])
            r = s.get (p_url,proxies =proxies, timeout=3, stream=True)
            print(datetime.datetime.now().strftime("%H:%M:%S"),item_id,r.status_code)
            if r.status_code == 200:
                re_status = True #跳出迴圈
            elif r.status_code == 403:
                print(datetime.datetime.now().strftime("%H:%M:%S"),item_id,'request 403',re_time)
                re_time += 1
                re_status = False #繼續
        except:
            re_status = False #繼續
            print(item_id,'查詢商品資訊失敗次數:',re_time)
            re_time += 1
    
    code = json.loads(r.text)
    code = code[0]
    idd = code['Id']
    qty = code['Qty']
    price = code['Price']['P']
    salestatus = code['SaleStatus']
    url = 'https://24h.pchome.com.tw/prod/'+idd
    dtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if idd:
        save_item_detail(idd,price,qty,salestatus,url,dtime)
    token = itemid_find_user_id(item_id)
    if salestatus != 0:
        try:
            connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
            for send_token in token:#批次查詢每個人訂閱價格＆通知
                if connection.is_connected():
                    cursor = connection.cursor()
                    cursor.execute("SELECT w_price FROM sub_list WHERE acc_token = '%s' AND item_id = '%s'"%(send_token, item_id))
                    w_price = cursor.fetchone()
                    #print(w_price,type(w_price))
                    if w_price[0] != None:
                        w_price = w_price[0]
                        print(price,w_price,send_token)
                    else:
                        w_price = w_price[0]
                        print("無設定價格",send_token)
                        print(price,"None")
                    if w_price == None:#無寫商品價格時通知
                        notify_status = sent_notify(idd,price,qty,salestatus,url,send_token)
                        if notify_status == 200:
                            print (item_id,'傳送成功',send_token)
                        else:
                            print (item_id,'傳送失敗',send_token)
                    elif price <= w_price or w_price == 0: #商品低於訂閱價格& 訂閱價格=0時通知
                        notify_status = sent_notify(idd,price,qty,salestatus,url,send_token)
                        if notify_status == 200:
                            print (item_id,'傳送成功',send_token)
                        else:
                            print (item_id,'傳送失敗',send_token)
                    else:
                        print(item_id,'未達訂閱價格',send_token)
        except Error as e:
            print("資料庫連接失敗3：", e)
        finally:
            if (connection.is_connected()):
                cursor.close()
                connection.close()
    else:
        print (item_id,'未開放購買')        
    
    
#傳送訊息
def sent_notify(idd,price,qty,salestatus,url, token):
    headers = {
        "Authorization":"Bearer " + token,
        "Content-Type":"application/x-www-form-urlencoded"
    }
    params = {
        "message":"\n物品id:"+idd+"\n價格:"+str(price)+"\n剩餘數量:"+str(qty)+"\n物品狀態:"+str(salestatus)+"\n網址"+url
    }
    r = requests.post("https://notify-api.line.me/api/notify",headers=headers,params=params)
    print("傳送狀態:",r.status_code)
    return(r.status_code)
    
if __name__ == "__main__":
    print("---------------------"+str(datetime.datetime.now())+"------------------------------")
    manager = multiprocessing.Manager()
    global queue 
    queue = manager.Queue()
    p = Pool()
    print('--------------')
    all_item = put_queue(queue)
    print('--------------')
    print(queue.qsize())
    start_time = datetime.datetime.now()
    with ThreadPoolExecutor(max_workers=300) as executor:
        results = executor.map(get_sum, all_item, timeout=1)
    end_time = datetime.datetime.now()
    print(end_time-start_time)
    
    print("---------------------"+str(datetime.datetime.now())+"  done------------------------------")
