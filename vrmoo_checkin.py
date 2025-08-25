#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
import requests
from urllib.parse import urlparse

DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/127.0.0.0 Safari/537.36"
)

def build_session(user_agent: str) -> requests.Session:
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": user_agent or DEFAULT_UA,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
    })
    return sess

def set_b2_token_cookie(sess: requests.Session, base_url: str, jwt_token: str):
    host = urlparse(base_url).netloc or "www.vrmoo.net"
    # 和抓包一致：把 JWT 同时放到 Cookie 的 b2_token
    sess.cookies.set("b2_token", jwt_token, domain=host, path="/")

def sign_in(sess: requests.Session, base_url: str, jwt_token: str, timeout: int = 15):
    url = base_url.rstrip("/") + "/api/mission/userMission"

    headers_sign = {
        "Content-Type": "application/json; charset=UTF-8",
        "Authorization": f"Bearer {jwt_token}",
        "Origin": base_url.rstrip("/"),
        "Referer": base_url.rstrip("/") + "/",
        # User-Agent 由 session 统一设置
    }

    # body 为空 JSON，和抓包保持一致
    resp = sess.post(url, headers=headers_sign, json={}, timeout=timeout)
    return resp

def pretty_print_response(resp: requests.Response):
    print(f"HTTP {resp.status_code}")
    ct = resp.headers.get("Content-Type", "")
    if "application/json" in ct:
        try:
            data = resp.json()
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            print(resp.text)
    else:
        # 有时接口异常会返回纯文本或数字
        print(resp.text)

def main():
    parser = argparse.ArgumentParser(
        description="VRMOO 每日签到脚本（还原抓包：Authorization + b2_token + JSON 空体）"
    )
    parser.add_argument("--jwt", dest="jwt_token", type=str, default=os.getenv("JWT_TOKEN"),
                        help="JWT Token（可用环境变量 JWT_TOKEN）")
    parser.add_argument("--base-url", dest="base_url", type=str, default=os.getenv("VRMOO_BASE_URL", "https://www.vrmoo.net"),
                        help="站点根地址，默认 https://www.vrmoo.net")
    parser.add_argument("--ua", dest="user_agent", type=str, default=os.getenv("UA", DEFAULT_UA),
                        help="User-Agent，可不改")
    parser.add_argument("--timeout", dest="timeout", type=int, default=int(os.getenv("TIMEOUT", "15")),
                        help="请求超时时间（秒），默认 15")
    args = parser.parse_args()

    if not args.jwt_token:
        print("错误：缺少 JWT Token。请使用参数 --jwt 或设置环境变量 JWT_TOKEN。", file=sys.stderr)
        print("提示：JWT 可从你已登录网页的网络请求中复制 Authorization 里的 Bearer 值。", file=sys.stderr)
        sys.exit(1)

    sess = build_session(args.user_agent)
    set_b2_token_cookie(sess, args.base_url, args.jwt_token)

    try:
        resp = sign_in(sess, args.base_url, args.jwt_token, timeout=args.timeout)
    except requests.RequestException as e:
        print(f"请求失败：{e}", file=sys.stderr)
        sys.exit(2)

    pretty_print_response(resp)

    # 简单判定：如果是 JSON 且包含 mission/credit 字段，基本可认为成功
    try:
        data = resp.json()
        keys = set(map(str.lower, data.keys())) if isinstance(data, dict) else set()
        if any(k in keys for k in ["mission", "credit", "data", "msg"]):
            print("签到流程已完成（以 JSON 返回判断）。")
        else:
            print("已返回 JSON，但字段不含常见结果，请人工确认。")
    except Exception:
        print("返回非 JSON（可能是接口未触发或认证不足）。请核对 Token 与 Cookie。")

if __name__ == "__main__":
    main()
