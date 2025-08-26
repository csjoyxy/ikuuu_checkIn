import os
import requests

# 登录函数：获取 JWT Token
def login_and_get_token(username, password):
    url = "https://www.vrmoo.net/wp-json/b2/v1/login"
    payload = {
        "username": username,
        "password": password
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200 and "token" in response.json():
        print("✅ 登录成功")
        return response.json()["token"]
    else:
        print("❌ 登录失败，请检查账号密码")
        print("响应内容：", response.text)
        exit(1)

# 签到函数
def check_in(jwt_token):
    url = "https://www.vrmoo.net/wp-json/b2/v1/userMission"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        result = response.json()
        if result.get("mission"):
            print("🎉 签到成功：", result["mission"])
        else:
            print("⚠️ 已签到或无任务：", result)
    else:
        print("❌ 签到失败")
        print("响应内容：", response.text)

# 主函数
def main():
    username = os.getenv("VRMOO_USERNAME")
    password = os.getenv("VRMOO_PASSWORD")

    if not username or not password:
        print("❌ 缺少账号或密码，请设置环境变量 VRMOO_USERNAME 和 VRMOO_PASSWORD")
        exit(1)

    jwt_token = login_and_get_token(username, password)
    check_in(jwt_token)

if __name__ == "__main__":
    main()
