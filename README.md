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

### 訂閱商品
查詢物品ID
* PChome 商品連結中prod與?中間就是商品ID

https://24h.pchome.com.tw/prod/DYAJID-A900AVJ62?fq=/S/DYAJID

* 官方帳號中傳送訊息訂閱商品

規則如下
```
add 商品ID 通知價格
範例:
add DYAJID-A900AVJ62 15000
```

增加 此商品 價格低於15000時通知

<img src="https://github.com/husan42/Line-BOT-Pchome/blob/main/add.PNG">

### 刪除訂閱

* 官方帳號中傳送訊息刪除訂閱商品

規則如下
```
del 物品ID
範例:
del DYAJID-A900AVJ62
```

<img src="https://github.com/husan42/Line-BOT-Pchome/blob/main/del.PNG">

### 查詢訂閱清單

* 官方帳號中傳送訊息查詢訂閱清單

規則如下
```
list
```
圖片同上

### 訂閱通知

* 系統每15min會去爬商品資訊一次，
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
