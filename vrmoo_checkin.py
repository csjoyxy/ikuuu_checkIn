import os
import time
import json
import requests
from urllib.parse import quote

BASE = "https://www.vrmoo.net"
LOGIN_URL = f"{BASE}/wp-json/jwt-auth/v1/token"
SIGN_URL = f"{BASE}/wp-json/b2/v1/userMission"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"

def push_plus(token, content):
    if not token:
        return
    url = f"http://www.pushplus.plus/send?token={token}&title={quote('VRMoo签到')}&content={quote(content)}"
    try:
        r = requests.post(url, timeout=10)
        print("推送成功" if r.status_code == 200 else f"推送失败：HTTP {r.status_code}")
    except Exception as e:
        print(f"推送异常：{e}")

def login_get_token(sess, email, password):
    headers = {
        "Origin": BASE,
        "Referer": f"{BASE}/",
        "User-Agent": UA,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    data = {
        "username": email,
        "password": password
    }
    r = sess.post(LOGIN_URL, headers=headers, data=data, timeout=15)
    j = r.json()
    token = j.get("token")
    if not token:
        raise RuntimeError(f"登录失败：{j}")
    print("登录成功")
    return token

def sign_in(sess, token):
    sess.headers.update({
        "Authorization": f"Bearer {token}",
        "User-Agent": UA,
        "Origin": BASE,
        "Referer": f"{BASE}/"
    })
    sess.cookies.set("b2_token", token, domain="www.vrmoo.net", path="/")
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    r = sess.post(SIGN_URL, headers=headers, json={}, timeout=15)
    text = r.text.strip()
    print(f"签到响应：{text}")
    try:
        res = r.json()
        if "credit" in res and "mission" in res:
            credit = res.get("credit", 0)
            my_credit = res["mission"].get("my_credit", "未知")
            date = res.get("date", "未知")
            return f"签到成功：+{credit}，总积分 {my_credit}（时间：{date}）"
        else:
            return res.get("msg") or res.get("message") or "今日已签到或无积分变化"
    except Exception:
        if text.isdigit():
            return f"今日已签到，获得积分：{text}"
        return f"签到完成（原始返回：{text[:100]})"

def check_in_one(email, password, push_token):
    sess = requests.Session()
    try:
        print(f"\n处理账户：{email}")
        token = login_get_token(sess, email, password)
        result = sign_in(sess, token)
        print(result)
        push_plus(push_token, result)
    except Exception as e:
        err = f"签到失败：{e}"
        print(err)
        push_plus(push_token, err)
    finally:
        sess.close()

def main():
    info = os.getenv("VRMOO_INFO", "").strip()
    if not info:
        print("❌ 未设置 VRMOO_INFO 环境变量")
        return
    users = [u for u in info.split(",") if u.strip()]
    for u in users:
        parts = [p.strip() for p in u.split("<split>")]
        if len(parts) < 2:
            print(f"格式错误：{u}")
            continue
        email, password = parts[0], parts[1]
        push_token = parts[2] if len(parts) > 2 else ""
        check_in_one(email, password, push_token)
        time.sleep(3)

if __name__ == "__main__":
    main()
