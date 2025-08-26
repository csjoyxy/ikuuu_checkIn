def vrmoo_checkin(sess, token):
    SIGN_URL = "https://www.vrmoo.net/wp-json/b2/v1/userMission"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=UTF-8",
        "Origin": "https://www.vrmoo.net",
        "Referer": "https://www.vrmoo.net/",
        "User-Agent": "Mozilla/5.0 (Linux; Android 15; Mobile) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36"
    }

    # 设置 Cookie（必须）
    sess.cookies.set("b2_token", token, domain="www.vrmoo.net", path="/")

    try:
        r = sess.post(SIGN_URL, headers=headers, json={}, timeout=15)
        r.raise_for_status()
        data = r.json()

        if "mission" in data and "credit" in data:
            print(f"✅ 签到成功！获得积分：{data['credit']}，当前总积分：{data['my_credit']}")
            print(f"📅 签到日期：{data['mission']['date']}，连续签到：{data['mission']['mission']['days']} 天")
        elif isinstance(data, str) and data == "1":
            print("⚠️ 返回 '1'，但未真正签到成功。可能请求体格式不对或 Cookie 未设置。")
        else:
            print("⚠️ 请求成功但未触发签到逻辑，可能已经签到过了或 token 无效")
            print("返回内容：", data)

    except Exception as e:
        print("❌ 签到失败：", str(e))
