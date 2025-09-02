import os
import requests
from urllib.parse import quote

BASE = "https://www.vrmoo.net"
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

def check_in(cookie_str, push_token):
    headers = {
        "User-Agent": UA,
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json; charset=UTF-8",
        "Cookie": cookie_str
    }
    try:
        r = requests.post(SIGN_URL, headers=headers, json={}, timeout=15)
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

    except Exception as e:
        err = f"签到失败：{e}"
        print(err)
        push_plus(push_token, err)

if __name__ == "__main__":
    cookie_str = os.environ.get("VRMOO_COOKIE", "").strip()
    push_token = os.environ.get("PUSHPLUS_TOKEN", "").strip()

    if not cookie_str:
        print("❌ 未设置 VRMOO_COOKIE 环境变量")
        exit(1)

    check_in(cookie_str, push_token)
