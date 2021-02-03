#!/usr/bin/env python
# coding: utf-8

# In[2]:


from multiprocessing import Process, Pool
import multiprocessing
import os, time
import mysql.connector as mariadb
from mysql.connector import Error
import requests
import json
import time,datetime,random


def put_queue(q, user_id):
    connection = mariadb.connect(host='192.168.1.10', user='admin', port='3307', password='pw', database='line_notify')
    if connection.is_connected():
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT item_id FROM sub_list")
        sub_item = cursor.fetchall()
        for i in sub_item:
            q.put(i[0])
    return q

def itemid_find_user_id(item_id):
    try:
        connection = mariadb.connect(host='192.168.1.10', user='admin', port='3307', password='pw', database='line_notify')
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT acc_token FROM sub_list WHERE item_id = '%s'"%(item_id))
            acc_token = cursor.fetchall()
            token = [a_list[0] for a_list in acc_token]
            idd,price,qty,salestatus,url,dtime = get_sum(item_id, token)
            save_time = int(datetime.datetime.now().strftime("%H"))
            if idd:
                if save_time == 0 or save_time == 12:
                    cursor.execute("INSERT INTO item_detail (id, price, qty, salestatus, url, dtime) VALUES ('%s','%d','%d','%d','%s','%s')"%(idd,price,qty,salestatus,url,dtime))
                    connection.commit()
            return token
    except Error as e:
        print("資料庫連接失敗：", e)
    except BaseException as e:
        print(e)
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            
#抓取商品資訊
def get_sum(item_id, token):
    time.sleep(random.randint(0,5))
    p_url = "https://ecapi.pchome.com.tw/ecshop/prodapi/v2/prod/button&id="+item_id+"&fields=Seq,Id,Price,Qty,ButtonType,SaleStatus"
    r =requests.get(p_url)
    try:
        if r.status_code == 200:
            code = json.loads(r.text)
            code = code[0]
            idd = code['Id']
            qty = code['Qty']
            price = code['Price']['P']
            salestatus = code['SaleStatus']
            url = 'https://24h.pchome.com.tw/prod/'+idd
            dtime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if salestatus != 0:
                for send_token in token:
                    connection = mariadb.connect(host='192.168.1.10', user='admin', port='3307', password='pw', database='line_notify')
                    if connection.is_connected():
                        cursor = connection.cursor()
                        cursor.execute("SELECT w_price FROM sub_list WHERE acc_token = '%s' AND item_id = '%s'"%(send_token, item_id))
                        w_price = cursor.fetchone()
                        w_price = w_price[0]
                        print(price,w_price)
                        if w_price == None:
                            sent_notify(idd,price,qty,salestatus,url,send_token)
                        elif price <= w_price:
                            sent_notify(idd,price,qty,salestatus,url,send_token)
                print (item_id,'傳送成功')
            else:
                print (item_id,'商品不足')
            return idd,price,qty,salestatus,url,dtime
        else:
            print (item_id,'requests 錯誤')
    except BaseException as e:
        print(item_id,'商品錯誤')
        print(e)
    
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
    print(r.status_code)
    
if __name__ == "__main__":
    manager = multiprocessing.Manager()
    queue = manager.Queue()
    p = Pool()
    put_queue(queue,user_id)
    while not queue.empty():
        item_id = queue.get()
        p.map_async(itemid_find_user_id,(item_id,))
    p.close()
    p.join()

