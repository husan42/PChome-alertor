# PChome-alertor

使用Line官方帳號訂閱PChome商品，當有貨or物品降價時發訊息通知。

體驗網址
https://lin.ee/7NQJJFg

## 使用說明

### 註冊
* 加入官方帳號後，傳送訊息"註冊"，會回傳一個網址，點選網址後註冊。
* 如有註冊成功會在line_notify收到"帳號連結成功"訊息。

<img align="left" src="https://github.com/husan42/Line-BOT-Pchome/blob/main/register.PNG"><img  src="https://github.com/husan42/Line-BOT-Pchome/blob/main/register_done.PNG">  
帳號連結成功

### 指令查詢

* 查詢使用指令＆教學
規則如下
```
help
```
<img src="https://github.com/husan42/Line-BOT-Pchome/blob/main/help.png">

### 訂閱商品
查詢物品ID
* PChome 商品連結中prod與?中間就是商品ID
<img src="https://github.com/husan42/Line-BOT-Pchome/blob/main/detail.png">


https://24h.pchome.com.tw/prod/DYAJID-A900AVJ62?fq=/S/DYAJID

* 官方帳號中傳送訊息訂閱商品

規則如下
```
add 商品ID 通知價格(0時為有貨時就通知) 備註(可不用)
範例:
add DGBJDE-1900AWVFF 9500 switch主機 
add DYAJID-A900AVJ62 15000
```

增加 此商品 價格低於9500時通知 備註為：switch主機

<img src="https://github.com/husan42/Line-BOT-Pchome/blob/main/add.png">

### 刪除訂閱

* 官方帳號中傳送訊息刪除訂閱商品

規則如下
```
del 商品ID or del 商品號碼
└刪除商品通知。
範例:
del DYAJID-A900AVJ4G
del 5
```

<img src="https://github.com/husan42/Line-BOT-Pchome/blob/main/del.png">

### 查詢訂閱清單

* 官方帳號中傳送訊息查詢訂閱清單

規則如下
```
list
```
<img src="https://github.com/husan42/Line-BOT-Pchome/blob/main/list.png">

### 查詢歷史價格

* 回傳商品歷史價格＆數量

規則如下
```
plt 商品ID or plt 商品號碼
└列出商品趨勢圖。
範例:
plt DYAJID-A900AVJ4G
plt 6
```
<img src="https://github.com/husan42/Line-BOT-Pchome/blob/main/plt.png">

###回傳商品網址

*回傳指定商品購買網址

規則如下
```
url 商品ID or url 商品號碼
└回傳商品網址。
範例:
url DYAJID-A900AVJ4G
url 6
```
<img src="https://github.com/husan42/Line-BOT-Pchome/blob/main/url.png">

### 訂閱通知

* 系統每10min會去爬商品資訊一次，
* 當訂閱商品 有貨 & 售價低於設定價格，就會傳送訊息至line_notify
<img src="https://github.com/husan42/Line-BOT-Pchome/blob/main/notify.PNG">

## 所使用到的工具

* python  
* line API
* flask
* mariadb
* domain name
* Let's Encrypt SSL
* Bash shell Crontab
