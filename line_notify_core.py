#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import requests
import json
import re
from flask import Flask, request, abort

import mysql.connector as mariadb
from mysql.connector import Error

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FollowEvent,
)

app = Flask(__name__)

line_bot_api = LineBotApi('')
handler = WebhookHandler('')

@app.route("/", methods=['GET'])
def index():
    return 'OK!'

#line 官方帳號 /callback測試Event
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

#line官方帳號收到訊息時的Event
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    get_message = event.message.text
    print(get_message)
    user_id = event.source.user_id
    register_url = 'https://notify-bot.line.me/oauth/authorize?response_type=code&scope=notify&response_mode=form_post&client_id="id"&redirect_uri=https://line.husan.cc/register&state=' + user_id
    mage = re.split(r'[\s]\s*',get_message)
    try:
        if mage[0] == "註冊":
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=register_url))
        elif 'add' == mage[0]:
            try:
                notice = add_item(mage[1],user_id,mage[2])
            except:
                notice = add_item(mage[1],user_id,None)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=notice))
        elif 'del' == mage[0]:
            notice = del_item(mage[1],user_id)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=notice))
        elif 'list' == mage[0]:
            item_list ,price_list= search_sub(user_id)
            notice = '您訂閱的項目有:'
            for i in range(len(item_list)):
                notice+='\n'
                notice=notice + item_list[i] +'\t' +str(price_list[i])
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=notice))
        elif 'send' == mage[0]:
            acc_token = get_notify_id(user_id)
            status = sent_message(mage[1],acc_token)
            if status == 200:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text='send OK!'))
        else:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='請輸入指令:\nlist \n└查詢通知項目。\nadd 商品ID 價格 \n└新增商品通知，低於設定價格時通知。\nEX:add DYAJID-A900AVJ4G 500\ndel 商品ID \n└刪除商品通知。\nEX:del DYAJID-A900AVJ4G'))
    except BaseException as e:
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text='指令錯誤，請重新確認!'))
        print(e)
    # get user id when reply
    user_id = event.source.user_id
    print("user_id =", user_id)
    
    profile = line_bot_api.get_profile(user_id)

#notify註冊時會post至/register
@app.route("/register",methods=['POST']) #註冊事件
def register():
    if request.method == 'POST':
        code = request.form.get('code') #拿code去要access_token
        print("code = ", code)
        state = request.form.get('state') #state = user_id 使用者id
        print("user_id = ",state)
        profile = line_bot_api.get_profile(state)
        user_name = profile.display_name
        print("username = ",user_name) #帳號名稱
        
        access_token = get_token(code) #取得access_token 發訊息給使用者的token
        print("access_token = ",access_token)
        r_code = send_test_message(access_token)#發測試通知
    if r_code == 200:
        save_profile(user_name, code, state, access_token)#存入資料庫
        return '發送成功'    
    else:
        return '發送失敗'
    
#加好友時發送通知
@handler.add(FollowEvent)
def handle_follow(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="感謝訂閱!請輸入\"註冊\"啟動服務。"))

#拿使用者code向notify-bot post取得access_token
def get_token(code):
    headers = {
        "Content-Type":"application/x-www-form-urlencoded"
    }
    params = {
        "grant_type":"authorization_code",
        "code": code,
        "redirect_uri":"https://line.husan.cc/register", # host_ip
        "client_id":"client_id", #notify client_id
        "client_secret":"client_secret" #notify client_secret
    }
    r = requests.post('https://notify-bot.line.me/oauth/token',headers=headers,params=params)
    source = json.loads(r.text)
    access_token = source['access_token']
    return access_token

#發送測試訊息至使用者notify
def send_test_message(access_token):
    headers = {
        "Authorization":"Bearer " + str(access_token),
        "Content-Type":"application/x-www-form-urlencoded",
        "notificationDisabled":"True"
    }
    params = {
        "message":"\n帳號連結成功"
    }
    r = requests.post("https://notify-api.line.me/api/notify",headers=headers,params=params)
    return r.status_code

#使用者資料存入資料庫
def save_profile(username, code, user_id, access_token): 
    try:
        connection = mariadb.connect(host='192.168.1.10', user='admin', port='3307', password='pw', database='line_notify')
        if connection.is_connected():
            db_Info = connection.get_server_info()
            print("資料庫版本：", db_Info)
            cursor = connection.cursor()
            cursor.execute("INSERT INTO user_info (id, username, code, user_id, access_token) VALUES (null,'%s','%s','%s','%s')"%(username, code, user_id, access_token))
            connection.commit() #存檔
            cursor.execute("SELECT * FROM user_info")
            # 列出查詢的資料
            for i in cursor:
                print(i)

    except Error as e:
        print("資料庫連接失敗0：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            #print("資料庫連線已關閉")
#新增訂閱項目
def add_item(item_id, user_id,w_price):
    try:
        connection = mariadb.connect(host='192.168.1.10', user='admin', port='3307', password='pw', database='line_notify')
        if connection.is_connected():
            cursor = connection.cursor()
            acc_token = get_notify_id(user_id)
            try:
                cursor.execute("INSERT INTO sub_list (item_id, w_price ,user_id, acc_token) VALUES ('%s','%d','%s','%s')"%(item_id, int(w_price) ,user_id, acc_token))
            except:
                cursor.execute("INSERT INTO sub_list (item_id,user_id, acc_token) VALUES ('%s','%s','%s')"%(item_id ,user_id, acc_token))
            connection.commit() #存檔          
        return 'Add Done!'
    
    except Error as e:
        print("資料庫連接失敗2：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
#刪除訂閱項目
def del_item(item_id, user_id):
    try:
        connection = mariadb.connect(host='192.168.1.10', user='admin', port='3307', password='pw', database='line_notify')
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("DELETE FROM sub_list WHERE item_id = '%s' AND user_id = '%s'"%(item_id,user_id))
            connection.commit() #存檔 
            return 'Delete Done!'
    except Error as e:
        print("資料庫連接失敗3：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
#查詢訂閱項目            
def search_sub(user_id):
    try:
        connection = mariadb.connect(host='192.168.1.10', user='admin', port='3307', password='pw', database='line_notify')
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT item_id , w_price FROM sub_list WHERE user_id LIKE '%s'"%(user_id))
            sub_item = cursor.fetchall()
            price_list = [item[1] for item in sub_item]
            item_list = [item[0] for item in sub_item]
            return item_list,price_list
    except Error as e:
        print("資料庫連接失敗1：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
#取得notify_access_token
def get_notify_id(user_id):
    try:
        connection = mariadb.connect(host='192.168.1.10', user='admin', port='3307', password='pw', database='line_notify')
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            cursor.execute("SELECT access_token FROM user_info WHERE user_id LIKE '%s'"%(user_id))
            acc_token = cursor.fetchall() 
            return acc_token[0][0]
    except Error as e:
        print("資料庫連接失敗4：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
#發送訊息
def sent_message(message,access_token):
    headers = {
        "Authorization":"Bearer " + access_token,
        "Content-Type":"application/x-www-form-urlencoded"
    }
    params = {
        "message":message
    }
    r = requests.post("https://notify-api.line.me/api/notify",headers=headers,params=params)
    print(r.status_code)
    return r.status_code
    
        
if __name__ == "__main__":
    app.run('0.0.0.0',port=3000)

