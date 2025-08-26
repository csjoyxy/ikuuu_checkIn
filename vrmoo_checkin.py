import os
import json
import requests

def sign_in(info):
    name = info.get("name", "未知用户")
    jwt_url = "https://vrmoo.com/api/user/jwt"
    signin_url = "https://vrmoo.com/api/mission/checkin"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json"
    }

    # 登录获取 JWT
    r = requests.post(jwt_url, json={"email": info["email"], "password": info["password"]}, headers=headers)
    if r.status_code != 200 or "token" not in r.json():
        return f"{name} 登录失败"

    token = r.json()["token"]
    headers["Authorization"] = f"Bearer {token}"

    # 发起签到请求
    r = requests.get(signin_url, headers=headers)
    try:
        res = r.json()
    except Exception:
        res = r.text.strip().strip('"')
        if res.isdigit():
            return f"{name} 今日已签到，获得积分：{res}"
        return f"{name} 签到完成（原始返回：{res[:100]})"

    if isinstance(res, dict) and "credit" in res and "mission" in res:
        return f"{name} 签到成功，获得积分：{res['credit']}，任务：{res['mission']}"
    return f"{name} 签到完成（返回内容异常）"

def pushplus(content):
    token = os.getenv("PUSHPLUS_TOKEN")
    if not token:
        return
    requests.post("http://www.pushplus.plus/send", json={
        "token": token,
        "title": "VRMoo 签到结果",
        "content": content
    })

def main():
    raw = os.getenv("VRMOO_INFO")
    if not raw:
        print("未设置 VRMOO_INFO")
        return

    try:
        accounts = json.loads(raw)
    except Exception:
        print("VRMOO_INFO 格式错误")
        return

    if not isinstance(accounts, list):
        accounts = [accounts]

    results = []
    for info in accounts:
        result = sign_in(info)
        print(result)
        results.append(result)

    pushplus("\n".join(results))

if __name__ == "__main__":
    main()
