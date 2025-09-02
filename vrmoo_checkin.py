import os
import time
import requests
from urllib.parse import quote

BASE = "https://www.vrmoo.net"
LOGIN_URL = f"{BASE}/wp-json/jwt-auth/v1/token"
SIGN_URL = f"{BASE}/wp-json/b2/v1/userMission"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0"

def push_plus(token, content):
    if not token:
        return
    url = f"http://www.pushplus.plus/send?token={token}&title={quote('VRMoo签到')}&content={quote(content)}"
    try:
        r = requests.post(url, timeout=10)
        print("推送成功" if r.status_code == 200 else f"推送失败：HTTP {r.status_code}")
    except Exception as e:
        print(f"推送异常：{e}")

def login_and_get_cookies(email, password):
    sess = requests.Session()
    headers_login = {
        "Origin": BASE,
        "Referer": f"{BASE}/",
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    data = {"username": email, "password": password}
    r = sess.post(LOGIN_URL, headers=headers_login, data=data, timeout=15)
    try:
        j = r.json()
    except Exception:
        raise RuntimeError(f"登录返回异常：{r.text}")

    if "token" not in j:
        raise RuntimeError(f"登录失败：{j}")

    print("登录成功")

    # 从响应和会话中提取所有 Cookie
    cookie_dict = requests.utils.dict_from_cookiejar(sess.cookies)
    cookie_header = "; ".join([f"{k}={v}" for k, v in cookie_dict.items()])
    return cookie_header

def check_in(cookie_header, push_token):
    headers_sign = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json; charset=UTF-8",
        "Cookie": cookie_header
    }
    r = requests.post(SIGN_URL, headers=headers_sign, json={}, timeout=15)
    print(f"签到响应：{r.text}")
    try:
        res = r.json()
        if "credit" in res and int(res.get("credit", 0)) > 0:
            content = f"签到成功，本次 +{res['credit']}，总积分 {res['mission']['my_credit']}"
        else:
            content = res.get("msg") or res.get("message") or "今日已签到或无积分变化"
    except Exception:
        text = r.text.strip().strip('"')
        if text.isdigit():
            content = f"今日已签到，获得积分：{text}"
        else:
            content = f"签到完成（原始返回：{text[:100]})"

    print(content)
    push_plus(push_token, content)

if __name__ == "__main__":
    info = os.environ.get("VRMOO_INFO", "").strip()
    if not info:
        print("未设置 VRMOO_INFO 环境变量")
        exit(1)
    for u in info.split(","):
        parts = [p.strip() for p in u.split("<split>")]
        if len(parts) < 2:
            print(f"格式错误：{u}")
            continue
        email, password = parts[0], parts[1]
        push_token = parts[2] if len(parts) > 2 else ""
        print(f"\n处理账户：{email}")
        try:
            cookie_header = login_and_get_cookies(email, password)
            check_in(cookie_header, push_token)
        except Exception as e:
            err = f"签到失败：{e}"
            print(err)
            push_plus(push_token, err)
        time.sleep(3)
