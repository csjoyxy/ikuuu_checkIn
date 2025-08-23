import requests
import json
import os
import time

session = requests.session()

# VRMoo网站URL
url = 'https://www.vrmoo.net'
login_url = f'{url}/wp-json/jwt-auth/v1/token'
check_url = f'{url}/wp-json/b2/v1/userMission'  # 修正为真正的签到接口

msg_template = 'http://www.pushplus.plus/send?token={}&title=VRMoo签到&content={}'

header = {
    'origin': 'https://www.vrmoo.net',
    'referer': 'https://www.vrmoo.net/gold',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'x-requested-with': 'XMLHttpRequest',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty'
}

def checkIn(email, passwd, SCKEY):
    # 登录数据，根据抓包信息构造
    login_data = {
        'nickname': '',
        'username': email,
        'password': passwd,
        'code': '',
        'img_code': '',
        'invitation_code': '',
        'token': '',
        'smsToken': '',
        'luoToken': '',
        'confirmPassword': '',
        'loginType': ''
    }
    
    try:
        print(f'账户【{email}】进行登录...')
        
        # 执行登录，获取JWT token
        login_response = session.post(url=login_url, headers=header, data=login_data)
        
        # 解析登录响应
        try:
            login_result = json.loads(login_response.text)
            if 'token' in login_result:
                jwt_token = login_result['token']
                print('登录成功，获取到token')
                
                # 为签到请求添加Authorization头
                auth_header = header.copy()
                auth_header['Authorization'] = f'Bearer {jwt_token}'
                
            else:
                print(f'登录失败，未获取到token: {login_result}')
                content = '登录失败'
                if SCKEY and SCKEY != '':
                    push_url = msg_template.format(SCKEY, content)
                    requests.post(url=push_url)
                return
                
        except json.JSONDecodeError:
            print(f'登录响应解析失败: {login_response.text[:200]}')
            content = '登录响应解析失败'
            if SCKEY and SCKEY != '':
                push_url = msg_template.format(SCKEY, content)
                requests.post(url=push_url)
            return
        
        # 等待一下再签到
        time.sleep(1)
        
        # 进行签到 - 真正的签到接口不需要参数
        print('开始签到...')
        checkin_response = session.post(url=check_url, headers=auth_header)  # 不传递data参数
        print(f'签到响应: {checkin_response.text}')
        
        # 解析签到结果
        try:
            result = json.loads(checkin_response.text)
            # 新的响应结构：根级别有credit，mission里有详细信息
            if 'mission' in result and 'credit' in result:
                credit = result.get('credit', '未知')
                mission = result.get('mission', {})
                my_credit = mission.get('my_credit', '未知')
                always = mission.get('always', '未知')
                date = result.get('date', '未知')
                content = f'VRMoo签到成功！获得积分: {credit}，当前总积分: {my_credit}，连续签到: {always}天，签到时间: {date}'
            else:
                # 检查是否有错误信息
                error_msg = result.get('msg', result.get('message', ''))
                if error_msg:
                    content = f'VRMoo签到失败: {error_msg}'
                else:
                    content = f'VRMoo签到响应异常: {str(result)[:200]}'
            print(content)
        except Exception as e:
            content = '签到请求已发送，但响应解析失败'
            if '成功' in checkin_response.text or 'success' in checkin_response.text.lower():
                content = '签到成功'
            elif '已签' in checkin_response.text or '已完成' in checkin_response.text:
                content = '今日已签到'
            elif 'error' in checkin_response.text.lower():
                content = '签到失败'
            print(f'响应解析失败: {e}')
            print(content)
        
        # 进行推送
        if SCKEY and SCKEY != '':
            push_url = msg_template.format(SCKEY, content)
            push_response = requests.post(url=push_url)
            print('推送成功' if push_response.status_code == 200 else '推送可能失败')
        
        # 清理session
        session.cookies.clear()
            
    except Exception as e:
        content = f'签到失败: {str(e)}'
        print(content)
        if SCKEY and SCKEY != '':
            push_url = msg_template.format(SCKEY, content)
            requests.post(url=push_url)
        
        # 清理session
        session.cookies.clear()

if __name__ == '__main__':
    # 环境变量格式: email1<split>password1<split>sckey1,email2<split>password2<split>sckey2
    info = os.environ.get('VRMOO_INFO', '')
    if not info:
        print('未找到VRMOO_INFO环境变量，请设置用户信息')
        exit(1)
    
    split = info.split(',')
    for user in split:
        user_split = user.split('<split>')
        if len(user_split) >= 2:
            email = user_split[0].strip()
            password = user_split[1].strip()
            sckey = user_split[2].strip() if len(user_split) > 2 else ''
            
            print(f'\n处理用户: {email}')
            checkIn(email, password, sckey)
            time.sleep(3)  # 增加间隔时间避免请求过快
        else:
            print(f'用户信息格式错误: {user}')
