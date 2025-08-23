import requests
import json
import os
import time

session = requests.session()

# VRMoo网站URL
url = 'https://www.vrmoo.net'
login_url = f'{url}/wp-json/jwt-auth/v1/token'
check_url = f'{url}/wp-json/b2/v1/getUserMission'

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
        
        # 动态签到数据 - 尝试多个可能的count值
        today = time.strftime("%d", time.localtime())  # 获取今天是几号
        possible_counts = [str(int(today)), '10', '11', '12', '9']  # 多个可能的count值
        
        success = False
        for count_val in possible_counts:
            checkin_data = {
                'count': count_val,
                'paged': '1'
            }
            
            print(f'尝试签到参数 count={count_val}...')
            checkin_response = session.post(url=check_url, headers=auth_header, data=checkin_data)
            
            try:
                result = json.loads(checkin_response.text)
                # 检查是否有有效的mission数据
                if 'mission' in result and 'credit' in result['mission']:
                    mission = result['mission']
                    credit = mission.get('credit', '未知')
                    my_credit = mission.get('my_credit', '未知') 
                    always = mission.get('always', '未知')
                    date = mission.get('date', '未知')
                    content = f'VRMoo签到成功！获得积分: {credit}，当前总积分: {my_credit}，连续签到: {always}天，签到时间: {date}'
                    print(content)
                    success = True
                    break
                else:
                    print(f'count={count_val} 响应异常: {str(result)[:100]}')
                    continue
            except Exception as e:
                print(f'count={count_val} 解析失败: {e}')
                continue
        
        if not success:
            content = 'VRMoo签到失败：所有count参数都尝试过了'
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
