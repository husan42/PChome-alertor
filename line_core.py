#!/usr/bin/env python
# coding: utf-8

import requests
import json
import re
from flask import Flask, request, abort,current_app
#import numpy as np
import matplotlib.pyplot as plt
import mysql.connector as mariadb
import matplotlib.dates as mdates
from matplotlib.ticker import MaxNLocator
from adjustText import adjust_text
from mysql.connector import Error
from PIL import Image
import sys

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, FollowEvent,ImageSendMessage,
)

import logging
from logging import FileHandler

app = Flask(__name__,static_url_path = "/plt" , static_folder = "./plt/") 

line_bot_api = LineBotApi('')
handler = WebhookHandler('')

host='192.168.10.1'
user=''
port=''
password=''
database='line_notify'

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
    #app.logger.info("Request body: " + body)

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
    user_id = event.source.user_id
    #print(user_id,get_message)
    current_app.logger.debug(user_id+' 輸入: '+get_message)
    register_url = 'https://notify-bot.line.me/oauth/authorize?response_type=code&scope=notify&response_mode=form_post&client_id=xxxx&redirect_uri=https://xxxx/register&state=' + user_id
    mage = re.split(r'[\s]\s*',get_message)
    try:
        if mage[0] == "註冊":
            '''
            line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=register_url))
            '''
            
            ifregister = check_account(user_id)
            
            if ifregister == None:
                #current_app.logger.debug(user_id+' 未曾註冊')
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=register_url))
            else:
                line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text='您已註冊，請輸入help查看指令教學。'))
            
            
        elif 'add' == mage[0] or 'Add' == mage[0]:
            item_id = re.findall(r'\w{6}-\w{9}',mage[1]) #確認商品ID格式
            if len(item_id) == 0:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text='商品ID錯誤，請確認。\n商品ID為:"前7碼"-"後9碼"的英文數字組合\n例:DYAJID-A900AVJ4G'))
            else:
                item_id = item_id[0]
                try:
                    try:
                        notice = add_item(item_id,user_id,mage[2],mage[3])#有價格跟備註
                    except:
                        notice = add_item(item_id,user_id,mage[2],None)#有價格或有備註
                except:
                    notice = add_item(item_id,user_id,None,None)#無價格、無備註
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text=notice))
        elif 'edit' == mage[0] or 'Edit' == mage[0]:
            try:
                try:
                    notice = edit_item(mage[1],user_id,mage[2],mage[3])#有價格跟備註
                except:
                    notice = edit_item(mage[1],user_id,mage[2],None)#有價格或有備註
            except:
                notice = edit_item(mage[1],user_id,None,None)#無價格、無備註
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=notice))
        elif 'del' == mage[0] or 'Del' == mage[0]:
            notice = del_item(mage[1],user_id)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=notice))
        elif 'list' == mage[0] or 'List' == mage[0]:
            item_list ,price_list, remark_list= search_sub(user_id)
            notice = '您訂閱的項目有:'
            for i in range(len(item_list)):
                notice+='\n'
                if remark_list[i] == None:
                    if price_list[i] == None:
                        notice=notice + str(i+1) + '.' + item_list[i] + '\n└' +str(0) + '\t'
                    else:
                        notice=notice + str(i+1) + '.' + item_list[i] + '\n└' +str(price_list[i])
                else:
                    if price_list[i] == None:
                        notice=notice + str(i+1) + '.' + item_list[i] + '\n└' +str(0) + '\t' + remark_list[i]
                    else:
                        notice=notice + str(i+1) + '.' + item_list[i] + '\n└' +str(price_list[i]) + '\t' + remark_list[i]
                #notice+='\n└----------'
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=notice))
        elif 'send' == mage[0] or 'Send' ==mage[0]:
            acc_token = get_notify_id(user_id)
            status = sent_message(mage[1],acc_token)
            if status == 200:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text='send OK!'))
        elif 'plt' == mage[0] or 'Plt' == mage[0]:
            acc_token = get_notify_id(user_id)
            item_id = pltshow(mage[1],acc_token, user_id)
            line_bot_api.reply_message(event.reply_token,ImageSendMessage(
                original_content_url='https://line.husan.cc/plt/'+item_id+'.png',
                preview_image_url='https://line.husan.cc/plt/'+item_id+'.png'
            ))
        elif 'url' == mage[0] or 'Url' == mage[0]:
            item_url = get_url(mage[1],user_id)
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text=item_url))
        elif 'check' == mage[0] or 'Check' == mage[0]:
            #app.logger.debug("Hello World")
            check_acc_status = check_account(user_id)
            if check_acc_status == None:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text='未註冊成功，請重新註冊。'))
            else:
                line_bot_api.reply_message(event.reply_token,TextSendMessage(text="註冊名稱:"+check_acc_status[0]))
        else:
            line_bot_api.reply_message(event.reply_token,TextSendMessage(
                text='請輸入指令:\nlist \n├查詢通知項目。\n└商品ID前數字即為商品號碼。\nadd 商品ID 價格 備註(不能有空格)\n├新增商品通知，低於設定價格時通知。\n├備註不能有空格。\n├輸入價格為0時，為能購買即通知。\n└EX:add DYAJID-A900AVJ4G 500 備註\ndel 商品ID or del 商品號碼\n├刪除商品通知。\n├EX:del DYAJID-A900AVJ4G\n└EX:del 5 \nedit 商品ID/商品號碼 價格 備註\n├修改商品通知，低於設定價格時通知。\n├EX:edit DYAJID-A900AVJ4G 500\n└EX:edit 5 299 蘋果\nplt 商品ID or plt 商品號碼\n├列出商品趨勢圖。\n├EX:plt DYAJID-A900AVJ4G\n└EX:plt 6\nurl 商品ID\n└回傳商品網址。'))
    except BaseException as e:
        #line_bot_api.reply_message(event.reply_token,TextSendMessage(text='指令錯誤，請重新確認!'))
        check_acc_status = check_account(user_id)
        if check_acc_status == None:
            current_app.logger.debug(user_id+' 指令錯誤函示，未註冊: ')
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='指令錯誤，請重新確認!\n未註冊成功，請重新註冊。'))
        else:
            current_app.logger.debug(user_id+' 已註冊: '+str(check_acc_status[0]))
            line_bot_api.reply_message(event.reply_token,TextSendMessage(text='指令錯誤，請重新確認!\n註冊名稱:'+check_acc_status[0]))
        current_app.logger.debug(user_id+' 指令錯誤: '+str(e))
        #print(e)
                                   
    # get user id when reply
    user_id = event.source.user_id
    #print("user_id =", user_id)
    
    profile = line_bot_api.get_profile(user_id)
    #print(profile.display_name)#帳號名稱
    #print(profile.user_id)#user_id
    #print(profile.picture_url)#帳號照片
    #print(profile.status_message)#none?
    

#notify註冊時會post至/register
@app.route("/register",methods=['POST']) #註冊事件
def register():
    if request.method == 'POST':
        code = request.form.get('code') #拿code去要access_token
        #print("code = ", code)
        state = request.form.get('state') #state = user_id 使用者id
        #print("user_id = ",state)
        profile = line_bot_api.get_profile(state)
        user_name = profile.display_name
        #print("username = ",user_name) #帳號名稱
        access_token = get_token(code) #取得access_token 發訊息給使用者的token
        #print("access_token = ",access_token)
        r_code = send_test_message(access_token)#發測試通知
    if r_code == 200:
        ifregister = check_account(state)#state = user_id 使用者id
        if ifregister == None:
            save_profile(user_name, code, state, access_token)#存入資料庫
            return '發送成功'
        else:
            return '已註冊過'
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
        "client_id":"", #notify client_id
        "client_secret":"" #notify client_secret
    }
    r = requests.post('https://notify-bot.line.me/oauth/token',headers=headers,params=params)
    source = json.loads(r.text)
    access_token = source['access_token']
    #print(access_token)
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
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database, charset="utf8mb4")
        if connection.is_connected():
            db_Info = connection.get_server_info()
            #print("資料庫版本：", db_Info)
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            #print("目前使用的資料庫：", record)

            #cursor.execute("SELECT * FROM user_info")
            current_app.logger.debug(user_id+' 註冊名稱: '+username)
            cursor.execute("INSERT INTO user_info (id, username, code, user_id, access_token) VALUES (null,'%s','%s','%s','%s')"%(username, code, user_id, access_token))
            connection.commit() #存檔
            cursor.execute("SELECT * FROM user_info")
            # 列出查詢使用者的資料
            #for i in cursor:
            #    print(i)

    except Error as e:
        current_app.logger.debug(user_id+' 註冊錯誤: '+str(e))
        #print("資料庫連接失敗0：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            #print("資料庫連線已關閉")
#新增訂閱項目
def add_item(item_id, user_id,w_price,remark):
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        if connection.is_connected():
            cursor = connection.cursor()
            #cursor.execute("select database();")
            #record = cursor.fetchone()#一定要有
            #print("目前使用的資料庫：", record)
            #cursor.execute("INSERT INTO")
            acc_token = get_notify_id(user_id)
            try:
                if remark == None: #有價格無註解
                    cursor.execute("INSERT INTO sub_list (item_id, w_price ,user_id, acc_token) VALUES ('%s','%d','%s','%s')"%(item_id, int(w_price) ,user_id, acc_token))
                else:#有價格有註解
                    cursor.execute("INSERT INTO sub_list (item_id, w_price, remark, user_id, acc_token) VALUES ('%s','%d','%s','%s','%s')"%(item_id, int(w_price),remark ,user_id, acc_token))
            except:#無價格有註解
                cursor.execute("INSERT INTO sub_list (item_id, remark, user_id, acc_token) VALUES ('%s','%s','%s','%s')"%(item_id ,w_price ,user_id, acc_token))
            connection.commit() #存檔          
        return 'Add Done!'
    
    except Error as e:
        current_app.logger.debug(user_id+' 新增訂閱項目錯誤: '+str(e))
        #print("資料庫連接失敗2：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            #print("資料庫連線已關閉")
#刪除訂閱項目
def del_item(item_id, user_id):
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        if connection.is_connected():
            cursor = connection.cursor()
            try:
                del_num = int(item_id)#取得整數商品編號
                cursor.execute("SELECT item_id FROM sub_list WHERE user_id LIKE '%s'"%(user_id))#取得使用者所有訂閱項目
                sub_item = cursor.fetchall()
                del_item = sub_item[del_num-1][0]#使用商品編號取得商品ID del_item=商品ID
                #print(del_item)
                cursor.execute("DELETE FROM sub_list WHERE item_id = '%s' AND user_id = '%s'"%(del_item,user_id))
                connection.commit()
                return 'Delete '+del_item
            except:
                cursor.execute("DELETE FROM sub_list WHERE item_id = '%s' AND user_id = '%s'"%(item_id,user_id))
                connection.commit() #存檔 
                return 'Delete Done!'
    except Error as e:
        current_app.logger.debug(user_id+' 刪除訂閱項目錯誤: '+str(e))
        #print("資料庫連接失敗3：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()


#編輯商品
def edit_item(item_id, user_id,w_price,remark):
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        if connection.is_connected():
            cursor = connection.cursor()
            acc_token = get_notify_id(user_id)#取得access_token   
            item_id = int_item_id2item_id(item_id,user_id)#轉換商品ID
            
            try:
                if remark == None: #有價格無註解
                    cursor.execute("UPDATE sub_list SET w_price='%d' ,remark='%s' WHERE user_id = '%s' AND item_id = '%s'"%(int(w_price),None , user_id, item_id))
                else:#有價格有註解
                    cursor.execute("UPDATE sub_list SET w_price='%d' ,remark='%s' WHERE user_id = '%s' AND item_id = '%s'"%(int(w_price), remark, user_id, item_id))
            except:#無價格有註解
                cursor.execute("UPDATE sub_list SET remark='%s' WHERE user_id = '%s' AND item_id = '%s'"%(remark, user_id, item_id))
            connection.commit() #存檔          
        return 'Edit Done!'
        
    except Error as e:
        current_app.logger.debug(user_id+' 編輯商品錯誤: '+str(e))
        #print("資料庫連接失敗2：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            #print("資料庫連線已關閉")           

#把商品編號&商品ID統一變成商品ID
def int_item_id2item_id(int_item_id,user_id):
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        if connection.is_connected():
            cursor = connection.cursor()
            try:
                del_num = int(int_item_id)#取得整數商品編號
                cursor.execute("SELECT item_id FROM sub_list WHERE user_id LIKE '%s'"%(user_id))#取得使用者所有訂閱項目
                sub_item = cursor.fetchall()
                item_id = sub_item[int(del_num)-1][0]#使用商品編號取得商品ID item_id=商品ID
                return item_id
            except Exception as e:
                current_app.logger.debug(user_id+' 不需商品編號轉ID: '+str(e))
                #print(e)
                return int_item_id
    except Error as e:
        current_app.logger.debug(user_id+' 商品編號轉ID錯誤1: '+str(e))
        #print("資料庫連接失敗3：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()

#確認是否註冊           
def check_account(user_id):
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        if connection.is_connected():
            cursor = connection.cursor()
            try:
                cursor.execute("SELECT username FROM user_info WHERE user_id LIKE '%s'"%(user_id))
                username = cursor.fetchall()
                if len(username) != 0:
                    username = username[0]
                    current_app.logger.debug(user_id+' 已註冊: '+str(username[0]))
                    return username
                else:
                    current_app.logger.debug(user_id+' 未註冊: ')
                    return None
            except Error as e:
                current_app.logger.debug(user_id+' 確認是否註冊錯誤: '+str(e))
                #print(e)
                return None
    except Error as e:
        current_app.logger.debug(user_id+' 確認是否註冊錯誤1: '+str(e))
        #print("資料庫連接失敗3：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()

#查詢訂閱項目            
def search_sub(user_id):
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT item_id , w_price , remark FROM sub_list WHERE user_id LIKE '%s'"%(user_id))
            sub_item = cursor.fetchall()
            price_list = [item[1] for item in sub_item]
            item_list = [item[0] for item in sub_item]
            remark_list = [item[2] for item in sub_item]
            return item_list,price_list,remark_list
    except Error as e:
        current_app.logger.debug(user_id+' 查詢訂閱項目錯誤: '+str(e))
        #print("資料庫連接失敗1：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
#取得notify_access_token
def get_notify_id(user_id):
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("select database();")
            record = cursor.fetchone()
            #print("目前使用的資料庫：", record)
            cursor.execute("SELECT access_token FROM user_info WHERE user_id LIKE '%s'"%(user_id))
            acc_token = cursor.fetchall() 
            #print(acc_token[0][0])
            return acc_token[0][0]
    except Error as e:
        current_app.logger.debug(user_id+' 取得notify_access_token錯誤: '+str(e))
        #print("資料庫連接失敗4：", e)

    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
            #print("資料庫連線已關閉")
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
    #print(r.status_code)
    return r.status_code

#用商品ID查詢商品名稱跟縮圖網址
def get_img_name(item_id):
    url = "https://ecapi.pchome.com.tw/ecshop/prodapi/v2/prod/"+item_id+"&fields=Seq,Id,Name,Nick,Price,Discount,Pic,Qty,Bonus,isPreOrder24h,isArrival24h&_callback=jsonp_prod"
    r = requests.get(url)
    r = re.split(",\"",r.text)
    current_app.logger.debug('商品名稱分割: '+str(r))
    name = re.split(":",r[2])
    name = json.loads(name[1],strict=False)
    pic = re.split(":",r[8])
    pic = re.sub(r"\\","",pic[2])
    pic = re.sub(r"\"","",pic)
    pic_url = "https://f.ecimg.tw"+ pic
    #print(pic_url)
    #print(name)
    return(name,pic_url)

#下載縮圖
def download_pic(item_id,pic_url):
    img = requests.get(pic_url)
    with open("/volume2/data/www/plt/"+item_id+"_n.jpg","wb") as f:
        f.write(img.content)
        f.close
#畫圖    
def pltshow(item_id,access_token, user_id):
    try:
        item_id_tmp = int(item_id)
        #print()
        item_id = get_num(item_id_tmp, user_id)
    except:
        item_id = item_id
    if '-000' not in item_id:
        item_id = item_id+'-000'
    current_app.logger.debug(user_id+' 畫圖: '+item_id)
    name,pic_url = get_img_name(item_id)#抓名子&圖片網址
    current_app.logger.debug(user_id+' 商品名稱: '+str(name)+' ,網址:'+str(pic_url))
    #print(name,pic_url)
    download_pic(item_id,pic_url)#下載縮圖
    #print(item_id)
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        cursor = connection.cursor()
        cursor.execute("SELECT price, qty, dtime FROM item_detail WHERE id LIKE '%s'"%(item_id))
        all_detail = cursor.fetchall()
    except Error as e:
        current_app.logger.debug(user_id+' 資料庫連接失敗7 '+str(e))
        #print("資料庫連接失敗4：", e)
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
    pr = []
    qt = []
    da = []
    for a in all_detail:
        pr.append(a[0])
        qt.append(a[1])
        da.append(a[2].strftime('%Y-%m-%d %H'))#%H:%M
    #print(len(pr),len(qt),len(da))
    plt.rcParams['font.sans-serif'] = ['Taipei Sans TC Beta']
    fig, (ax3,ax1) = plt.subplots(ncols=2,figsize=(10, 4),gridspec_kw={'width_ratios': [1, 3]})
    fig.suptitle(name+"\n"+item_id,fontsize=14,fontweight='bold')#標題
    ax2 = ax1.twinx()
    #價格
    ax1.set_ylabel('價格',color='tab:blue',rotation=0,labelpad=15)#價格文字
    ax1.plot(da,pr,'-', color='tab:blue')#價格畫線
    ax1.tick_params(axis='y', labelcolor='tab:blue')#左Y軸文字    
    texts = []
    tmp = 0
    for a,b in zip(da, pr):
        if tmp != b:
            tmp = b
            texts.append(ax1.annotate(b,xy=(a,b),xytext=(0,0),textcoords='offset pixels',color='darkblue'))
    adjust_text(texts,)   
    #數量
    ax2.set_ylabel('數量',color='tab:green',rotation=0,labelpad=15)#數量文字
    ax2.plot(da,qt,'--', color='limegreen')#數量畫線
    ax2.tick_params(axis='y', labelcolor='tab:green')#右Y軸文字
    ax2.yaxis.set_major_locator(MaxNLocator(integer=True))#右Y軸只顯示整數
    texts = []
    tmp=0
    for a,b in zip(da, qt):
        if tmp != b:
            tmp = b
            texts.append(ax2.annotate(b,xy=(a,b),xytext=(0,0),textcoords='offset pixels',color='darkgreen'))
    adjust_text(texts,)
    
    ax3.axis('off')
    img = Image.open("/volume2/data/www/plt/"+item_id+"_n.jpg")
    ax3.imshow(img)
    
    #調整X軸
    locator = mdates.AutoDateLocator(minticks=5, maxticks=15) #調整X軸間距
    ax2.xaxis.set_major_locator(locator)#調整X軸間距
    ax1.grid(linestyle='--')#背景虛線
    fig.autofmt_xdate()#X軸文字轉15度
    plt.savefig('/volume2/data/www/plt/'+item_id+'.png',dpi=300)#plt/'+item_id+'.jpg
    #re_img=open('/volume2/data/temp/plt/'+item_id+'.png')
    return item_id

#使用商品編號查詢商品ID
def get_num(in_num, user_id):
    try:
        connection = mariadb.connect(host=host, user=user, port=port, password=password, database=database)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT item_id FROM sub_list WHERE user_id LIKE '%s'"%(user_id))
            sub_item = cursor.fetchall()
            out_item = sub_item[int(in_num)-1][0]
            #print(out_item)
            return out_item
    except Error as e:
        current_app.logger.debug(user_id+' 資料庫連接失敗8 '+str(e))
        #print("資料庫連接失敗4：", e)
    finally:
        if (connection.is_connected()):
            cursor.close()
            connection.close()
        
#回傳商品網址        
def get_url(num,user_id):
    try:
        num_tmp = int(num)
        item_id = get_num(num,user_id)
    except:
        item_id = num
    return 'https://24h.pchome.com.tw/prod/'+item_id
        
if __name__ == "__main__":
    #handler = logging.FileHandler('flask.log')
    #app.logger.addHandler(handler)
    app.run('0.0.0.0',port=3000,debug = True)#, ssl_context='adhoc'
