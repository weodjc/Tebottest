import requests
import random
import telebot
import json
import time
import os
import io
import re
import warnings
#频道 https://t.me/CrystaYUYE
# @cry5200   
admin_ids = [管理员]  

def is_admin(user_id):
    return int(user_id) in admin_ids

bot = telebot.TeleBot("7678335461:AAGVf3yYTaPNxaEYAa72iWMNCHflA4io40w")  

data_file = "user_data.json"
def load_user_data():
    try:
        with open(data_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_data(user_data):
    with open(data_file, "w") as f:
        json.dump(user_data, f, indent=4)

def is_member(user_id, user_data):
    return user_data.get(user_id, {}).get("is_member", False)

def is_admin_or_member(user_id, user_data):
    return int(user_id) in admin_ids or user_data[user_id]["is_member"]
def check_channel_member(user_id):
    try:
        chat_member = bot.get_chat_member(-频道id, user_id)
        return chat_member.status!= 'left'
    except telebot.apihelper.ApiTelegramException as e:
        print(f"获取频道成员信息时出错")
        return False

def check_sign_in(user_id, user_data):
    if user_data[user_id]["last_sign_in"] == 0:
        bot.send_message(user_id, "请先进行签到 /qd")
        return False
    return True

def extract_id_cards(response_text):
    id_cards = []
    data = response_text.strip('[]').split('},')
    for item in data:
        if '"idcard":"' in item:
            start_index = item.find('"idcard":"') + len('"idcard":"')
            end_index = item.find('"', start_index)
            id_card = item[start_index:end_index]
            id_cards.append(id_card)
    return id_cards

@bot.message_handler(commands=['start'])
def user_menu(message):
    user_id = message.from_user.id
    if not check_channel_member(user_id):
        keyboard = [
            [telebot.types.InlineKeyboardButton("加入频道", url='频道链接')]
        ]
        reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
        bot.send_message(message.chat.id, "请先加入频道，点击下方按钮", reply_markup=reply_markup)
        return

    keyboard = [
        [telebot.types.InlineKeyboardButton("使用说明", callback_data='usage')],
        [telebot.types.InlineKeyboardButton("联系客服", url='https://t.me/换')],
        [telebot.types.InlineKeyboardButton("充值", url='https://t.me/换')]
    ]
    reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
    bot.send_message(message.chat.id, "欢迎使用本机器人，Cry为您服务！\n\n基本指令\n\n/qd 签到\n/zt  个人", reply_markup=reply_markup)

@bot.callback_query_handler(func=lambda call: call.data == 'usage')
def show_usage(call):
    usage_text = "机器人功能如下\n"
    usage_text += "\n/jl 手机号 查询吉林脱敏信息\n"
    usage_text += "\n/lm 姓名 地区 性别：查询身份证信息\n"
    usage_text += "\n/qb 姓名 模糊身份用x或者*代替：模糊查询身份证信息\n"
    usage_text += "\n/2ys 姓名 身份证号码：进行二要素验证\n"
    usage_text += "\n直接发送 手机号 姓名 身份证号码：进行三要素验证\n"
    usage_text += "\n/qq QQ号码：查询QQ相关信息 维护...\n"
    usage_text += "\n/sjh 手机号码：查询手机号归属地及运营商\n"
    usage_text += "\n/sjh_1 姓名 手机号码：进行机主二要素验证（接口暂时维护中）\n"
    usage_text += "\n感谢大家支持 后续会添加各种功能..."
    bot.send_message(call.message.chat.id, usage_text)

@bot.message_handler(commands=['sjh_1'])
def sjh_1_handler(message):
    bot.reply_to(message, "接口暂时维护中")

@bot.message_handler(commands=['lm'])
def get_id_cards(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    if not check_channel_member(user_id):
        return
    if not check_sign_in(user_id, user_data):
        return
    parts = message.text.split()
    if len(parts) < 4:
        bot.reply_to(message, "正确格式:/lm 姓名 地区 性别")
        return
    name = parts[1]
    diqu = parts[2]
    gender = parts[3]
    token = "bd5ae5e25ea09f8c"
    url = 'http://api.hlkt.uk/api/liemo1/?name={}&diqu={}&sex={}&token={}'.format(name, diqu, gender, token)
    try:
        bot.send_message(message.chat.id, "正在执行猎魔，请稍候...")
        response = requests.get(url)
        response.raise_for_status()
        id_cards = extract_id_cards(response.text)
        if id_cards:
            result = ""
            for id_card in id_cards:
                result += id_card + "\n"
            if len(result) > 4096:  
                with open('猎魔.txt', 'w') as file:
                    file.write(result)
                with open('猎魔.txt', 'rb') as file:
                    bot.send_document(message.chat.id, file)
                os.remove('猎魔.txt')  
            else:
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1, text=f"```\n{result}\n```")
            if not is_admin(user_id) and not is_member(user_id, user_data) and user_data[user_id]["points"] > 0:
                user_data[user_id]["points"] -= 1
                save_user_data(user_data)
        else:
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1, text="未获取到身份证信息")
    except requests.exceptions.RequestException as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1, text=f"服务器出现问题 请联系管理员!")

@bot.message_handler(commands=['qb'])
def query_by_name_and_card(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    if not check_channel_member(user_id):
        return
    if not check_sign_in(user_id, user_data):
        return
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "正确格式为:/qb 姓名 模糊身份用 x 或者*代替")
        return
    name = parts[1]
    cardno = parts[2]

    url = f'http://api.hlkt.uk/api/kubu/?name={name}&cardno={cardno}&token=e12d8f8716a95a43'
    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.text
        id_cards = re.findall(r'\b\d{17}[\dXx]\b', result)
        if id_cards:
            result = '\n'.join(id_cards)
            if len(result) > 4096:  
                with open('库补.txt', 'w') as file:
                    file.write(result)
                with open('库补.txt', 'rb') as file:
                    bot.send_document(message.chat.id, file)
                os.remove('库补.txt')  
            else:
                bot.reply_to(message, result)
            if not is_admin(user_id) and not is_member(user_id, user_data) and user_data[user_id]["points"] > 0:
                user_data[user_id]["points"] -= 1
                save_user_data(user_data)
        else:
            bot.reply_to(message, "接口维护")
    except requests.exceptions.RequestException as e:
        bot.reply_to(message, f"请求出错:{e}")

@bot.message_handler(commands=['qd'])
def sign_in(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    if user_id not in user_data:
        user_data[user_id] = {
            "username": message.from_user.username,
            "user_id": user_id,
            "points": 0,
            "is_member": False,
            "last_sign_in": 0
        }
    current_time = time.time()
    if current_time - user_data[user_id]["last_sign_in"] > 86400:  
        user_data[user_id]["points"] += 3
        user_data[user_id]["last_sign_in"] = current_time
        save_user_data(user_data)
        bot.reply_to(message, f"签到成功获得 3 积分")
    else:
        bot.reply_to(message, "你已经签到过了!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    if not check_channel_member(user_id):
        return

    text = message.text.strip()
    parts = text.split()
    if not check_sign_in(user_id, user_data):
        return
    if len(parts) == 2: 
        name = parts[0]
        id_number = parts[1]
        if not re.match(r"^\d{17}[\dXx]$", id_number):
            bot.reply_to(message, "身份证号码格式错误,应为18位数字或17位数字加X/x")
            return
        if not name.strip():
            bot.reply_to(message, "姓名不能为空")
            return
        if is_admin(user_id) or is_member(user_id, user_data):
            result = two_factor_verification(name, id_number)
            bot.reply_to(message, result)
        else:
            if user_data[user_id]["points"] > 0:
                user_data[user_id]["points"] -= 1
                save_user_data(user_data)
                bot.send_message(message.chat.id, "正在执行二要素验证,请稍候...")
                result = two_factor_verification(name, id_number)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1, text=f"扣除1积分\n```\n{result}\n```")
            else:
                bot.reply_to(message, "你积分不足")
        return

    elif len(parts) >= 3:  
        phone = parts[0]
        name = " ".join(parts[1:-1]) 
        idCard = parts[-1]
        if not re.match(r"^\d{11}$", phone):
            bot.reply_to(message, "手机号格式错误,应为11位数字")
            return
        if not re.match(r"^\d{17}[\dXx]$", idCard):
            bot.reply_to(message, "身份证号码格式错误,应为18位数字或17位数字加X/x")
            return
        if not name.strip():
            bot.reply_to(message, "姓名不能为空")
            return
        if is_admin(user_id) or is_member(user_id, user_data):
            result = three_elements_verification(phone, name, idCard)
            bot.reply_to(message, result)
        else:
            if user_data[user_id]["points"] > 0:
                user_data[user_id]["points"] -= 1
                save_user_data(user_data)
                bot.send_message(message.chat.id, "正在执行三要素验证,请稍候...")
                result = three_elements_verification(phone, name, idCard)
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1, text=f"扣除1积分\n```\n{result}\n```")
            else:
                bot.reply_to(message, "你积分不足")
        return

    bot.reply_to(message, "输入格式错误,请按照以下格式输入:\n"
                          "1. 二要素验证:姓名 身份证\n"
                          "2. 三要素验证:手机号 姓名 身份证")

def two_factor_verification(name, id_number):
    url = "https://www.jxca.net/iset-core-test/auth/checkIdInfo"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    data = {
        "name": name,
        "idNum": id_number
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        response_data = response.json()
        if response_data["code"] == 0:
            return f"姓名:{name}\n身份证:{id_number}\n验证结果:提交的二要素一致🟢"
        else:
            return f"姓名:{name}\n身份证:{id_number}\n验证结果:提交的二要素不一致🔴"
    except requests.RequestException as e:
        return f"姓名:{name}\n身份证:{id_number}\n服务端出现错误 请联系管理员!"

def three_elements_verification(phone, name, idCard):
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "Origin": "https://www.jkjdsh.com",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.54(0x18003637) NetType/WIFI Language/zh_CN",
        "Referer": "https://www.jkjdsh.com/jiading/",
        "Connection": "keep-alive",
        "domainId": "645891443a3e44449323c6d8624549b8-1734949239737-domainId"
    }
    data = {
        "phone": phone,
        "jmId": "62a7f8e5bbd811efb6780242ac110004",
        "name": name,
        "idCard": idCard
    }
    url = "https://www.jkjdsh.com/api/gzdAPI/verifyIdentity/submitAuthInfo.service"

    response = requests.post(url, headers=headers, json=data)
    return response.json()

def three_elements_verification(phone, name, idCard):
    openId = "oU" + ''.join(random.choice("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(10))
    stationId = str(random.randint(5000, 99999))

    payload = json.dumps({
        "authType": "IdCard",
        "isUpdateIdCard": 1,
        "openId": openId,
        "roleCode": "recycler",
        "realName": name,
        "phone": phone,
        "cardNo": idCard,
        "pid": 209,
        "pname": "湖北省再生资源集团有限公司",
        "stationId": stationId,
        "stationName": "珞瑜路金鑫国际家居一楼德国菲斯曼店",
        "mid": None,
        "merchantId": None,
        "custId": "iKsYrfAbiI",
        "userId": "iKsYrfAbiI"
    })

    url = "https://gxhs.wtkj.site/dev-api/gxhs/front/make_auth"

    headers = {
        'User-Agent': "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.53(0x180032e) NetType/WIFI Language/zh_CN",
        "Accept-Encoding": "gzip,compress,br,deflate",
        "Content-Type": "application/json",
        "Authorization": "Bearer",
        "Referer": "https://servicewechat.com/wxe48112dad392793a/114/page-frame.html"
    }

    try:
        response = requests.post(url, data=payload, headers=headers)
        response_data = response.json()
        if response_data["code"] == 2000009:
            return f"{name}－{idCard}－{phone}－运营商核验一致✅"
        elif response_data["code"] == 2000050:
            return f"{name}－{idCard}－{phone}－运营商核验失败❌"
        elif "访问过于频繁" in response_data.get("msg", ""):
            return f"访问过于频繁,等待1秒后重试 {idCard}"
        else:
            return f"{name}－{idCard}－{phone}－运营商核验失败❌"
    except json.JSONDecodeError as e:
        print(f"解析JSON数据出错：{e}")
        print(f"服务器返回数据：{response.text}")
        return f"解析JSON数据出错：{e}"
    except requests.RequestException as e:
        print(f"请求出现问题：{e}")
        return f"请求出现问题：{e}"

@bot.message_handler(commands=['jl'])
def jl_command(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    if not check_channel_member(user_id):
        return
    if not check_sign_in(user_id, user_data):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "正确格式为:/jl 手机号")
        return
    phone_number = parts[1]
    if is_admin(user_id) or is_member(user_id, user_data):
        result = process_jl_command(phone_number)
        bot.reply_to(message, result)
    else:
        if user_data[user_id]["points"] >= 1:
            user_data[user_id]["points"] -= 1
            save_user_data(user_data)
            result = process_jl_command(phone_number)
            bot.send_message(message.chat.id, "正在执行吉林脱敏，请稍候...")
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1, text=f"扣除1积分\n{result}")
        else:
            bot.reply_to(message, "你积分不足")


def process_jl_command(phone_number):
    url = "https://jsb-mp.jilinxiangyun.com/api/v1/mini-program-natural/get-mask-info"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Device": "3",
        "Accept-Encoding": "gzip,compress,br,deflate",
    }
    data = {
        "loginNo": phone_number
    }
    try:
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        return f"服务端请求错误 请联系管理员！"

@bot.message_handler(commands=['qq'])
def qq_info(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    if not check_channel_member(user_id):
        return
    if not check_sign_in(user_id, user_data):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "正确格式:/qq QQ号")
        return
    qq_number = parts[1]
    if is_admin(user_id) or is_member(user_id, user_data):
        url = f'https://zy.xywlapi.cc/qqapi?qq={qq_number}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            formatted_result = f"QQ号: {qq_number}\n手机号: {data.get('phone', '')}"
            bot.reply_to(message, formatted_result)
        else:
            bot.reply_to(message, 'API 请求失败')
    else:
        if user_data[user_id]["points"] > 0:
            user_data[user_id]["points"] -= 1
            save_user_data(user_data)
            bot.send_message(message.chat.id, "正在执行qq查询，请稍候...")
            url = f'https://zy.xywlapi.cc/qqapi?qq={qq_number}'
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                formatted_result = f"QQ号: {qq_number}\n手机号: {data.get('phone', '')}"
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1, text=f"扣除1积分\n```\n{formatted_result}\n```")
            else:
                bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1, text='服务端请求错误 请联系管理员!')
        else:
            bot.reply_to(message, "你积分不足")

@bot.message_handler(commands=['sjh'])
def query_phone_info(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    if not check_channel_member(user_id):
        return
    if not check_sign_in(user_id, user_data):
        return
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "正确格式为:/sjh 手机号")
        return
    phone_number = parts[1]
    if is_admin(user_id) or is_member(user_id, user_data):
        result = get_phone_location(phone_number)
        bot.reply_to(message, f"手机号: {result['phone']}\n归属地: {result['location']}\n运营商: {result['operator']}")
    else:
        if user_data[user_id]["points"] > 0:
            user_data[user_id]["points"] -= 1
            save_user_data(user_data)
            bot.send_message(message.chat.id, "正在执行手机号，请稍候...")
            result = get_phone_location(phone_number)
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1, text=f"扣除1积分\n```\n手机号: {result['phone']}\n归属地: {result['location']}\n运营商: {result['operator']}\n```")
        else:
            bot.reply_to(message, "你积分不足")

def get_phone_location(mobile, retries=3):
    url = f"https://cx.shouji.360.cn/phonearea.php?number={mobile}"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Host": "cx.shouji.360.cn",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0"
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data['code'] == 0:
                province = data['data']['province']
                city = data['data']['city']
                operator = data['data']['sp']
                return {
                    "phone": mobile,
                    "location": f"{province}{city}",
                    "operator": operator
                }
            else:
                print("失败:", data['message'])
                return {
                    "phone": "",
                    "location": "",
                    "operator": ""
                }
        except requests.exceptions.RequestException as e:
            print("失败:", e)
            if attempt < retries - 1:
                time.sleep(2) 
            else:
                return {
                    "phone": "",
                    "location": "",
                    "operator": ""
                }

@bot.message_handler(commands=['zt'])
def user_info(message):
    user_id = str(message.from_user.id)
    user_data = load_user_data()
    if not check_channel_member(user_id):
        return
    if not check_sign_in(user_id, user_data):
        return
    info = f"用户 ID:{user_data[user_id]['user_id']}\n" \
           f"用户名:{user_data[user_id].get('username', '未知')}\n" \
           f"剩余积分:{user_data[user_id].get('points', 0)}\n" \
           f"是否会员:{'是' if user_data[user_id].get('is_member', False) else '否'}"
    bot.reply_to(message, info)

@bot.message_handler(commands=['gly'])
def admin_menu(message):
    if is_admin(message.from_user.id):
        bot.reply_to(message, "管理员菜单选项:\n/jjf - 为用户增加积分\n/jhy - 授权会员\n/sc - 删除会员")
    else:
        bot.reply_to(message, "你不是管理员,无权访问此菜单。")

@bot.message_handler(commands=['jjf'])
def add_points(message):
    if is_admin(message.from_user.id):
        parts = message.text.split()
        if len(parts) == 3:
            user_id = parts[1]
            points_to_add = int(parts[2])
            user_data = load_user_data()
            if user_id in user_data:
                user_data[user_id]["points"] += points_to_add
                save_user_data(user_data)
                bot.reply_to(message, f"已为用户 {user_id} 增加 {points_to_add} 积分,当前积分:{user_data[user_id]['points']}")
            else:
                bot.reply_to(message, f"未找到用户 ID 为 {user_id} 的用户")
        else:
            bot.reply_to(message, "命令格式错误,正确格式为:/jjf 用户id 积分数量")
    else:
        bot.reply_to(message, "你不是管理员,无权执行此操作")

@bot.message_handler(commands=['jhy'])
def authorize_member(message):
    if is_admin(message.from_user.id):
        user_id_to_authorize = int(message.text.split()[1])
        user_data = load_user_data()
        if str(user_id_to_authorize) in user_data:
            user_data[str(user_id_to_authorize)]["is_member"] = True
            save_user_data(user_data)
            bot.reply_to(message, f"已成功授权用户 {user_id_to_authorize} 为会员")
        else:
            bot.reply_to(message, f"未找到用户 ID 为 {user_id_to_authorize} 的用户")
    else:
        bot.reply_to(message, "你不是管理员,无权执行此操作")

@bot.message_handler(commands=['sc'])
def delete_member(message):
    if is_admin(message.from_user.id):
        user_id_to_delete = int(message.text.split()[1])
        user_data = load_user_data()
        if str(user_id_to_delete) in user_data:
            user_data[str(user_id_to_delete)]["is_member"] = False
            save_user_data(user_data)
            bot.reply_to(message, f"已成功删除用户 {user_id_to_delete} 的会员资格")
        else:
            bot.reply_to(message, f"未找到用户 ID 为 {user_id_to_delete} 的用户")
    else:
        bot.reply_to(message, "你不是管理员,无权执行此操作")

if __name__ == "__main__":
    while True:
        try:
            bot.polling()
        except Exception as e:
            print(f"遇到错误:{e},正在重新启动...")
            time.sleep(1)
