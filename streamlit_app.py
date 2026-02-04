import streamlit as st
import requests
import time
from datetime import datetime, timezone, timedelta
import pandas as pd
import random

# ==========================================
# 1. 页面基础配置
# ==========================================
st.set_page_config(page_title="白银费率监控", layout="wide")
st.title("Hyperliquid vs Binance 白银费率对比")
st.caption("🚀 使用前端模拟协议，尝试绕过区域限制")

# 硬编码币种信息
HL_COIN = "xyz:SILVER"
BN_SYMBOL = "XAGUSDT"

# ==========================================
# 2. 核心函数：伪装成浏览器获取币安数据
# ==========================================
def get_binance_funding_rates_stealth(symbol):
    """
    尝试使用币安前端API（非公开API）并进行浏览器伪装
    """
    # 这里的 URL 是币安网页版图表背后使用的接口，通常比公开 API (fapi) 存活率高
    # 我们尝试用 www.binance.com 的主站接口
    url = "https://www.binance.com/fapi/v1/fundingRate"
    
    params = {
        "symbol": symbol,
        "limit": 50
    }
    
    # 伪装请求头，让服务器以为是真实用户在用 Chrome 浏览器访问
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    }

    # 备用节点列表 (如果主站不通，尝试其他节点)
    endpoints = [
        "https://fapi.binance.com/fapi/v1/fundingRate",
        "https://www.binance.com/fapi/v1/fundingRate", 
        "https://fapi.binance.vision/fapi/v1/fundingRate" # Vision 有时对 IP 宽松
    ]

    for base_url in endpoints:
        try:
            # st.write(f"正在尝试节点: {base_url} ...") # 调试用，生产环境可注释
            resp = requests.get(base_url, params=params, headers=headers, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                rates_map = {}
                if isinstance(data, list):
                    for item in data:
                        ts = item["fundingTime"]
                        rate = float(item["fundingRate"]) * 10000
                        aligned_ts = (ts // 3600000) * 3600000 
                        rates_map[aligned_ts] = rate
                return rates_map
            
        except Exception as e:
            continue # 失败就试下一个

    return {}

# ==========================================
# 3. 主程序逻辑
# ==========================================

if st.button("🔄 刷新数据 (深度穿透)", type="primary"):
    
    # --- A. 获取 Hyperliquid 数据 ---
    st.info("正在从 Hyperliquid 获取数据...")
    
    hl_url = "https://api.hyperliquid.xyz/info"
    now = int(time.time() * 1000)
    payload = {
        "type": "fundingHistory",
        "coin": HL_COIN,
        "startTime": now - 24 * 60 * 60 * 1000
    }

    try:
        hl_resp = requests.post(hl_url, json=payload, timeout=5)
        hl_data = hl_resp.json()
    except Exception as e:
        st.error(f"Hyperliquid 连接失败: {e}")
        st.stop()

    if not isinstance(hl_data, list) or len(hl_data) == 0:
        st.warning("Hyperliquid 暂无数据")
        st.stop()

    # --- B. 获取 Binance 数据 (使用伪装模式) ---
    st.info("正在尝试连接币安 (可能需要几秒钟)...")
    bn_map = get_binance_funding_rates_stealth(BN_SYMBOL)

    # --- C. 数据合并与展示 ---
    tz = timezone(timedelta(hours=8)) 
    
    recent_hl_data = hl_data[-12:] 
    recent_hl_data.reverse() 

    table_rows = []
    
    # 检查是否成功获取到了币安数据
    binance_online = len(bn_map) > 0
    
    if not binance_online:
        st.warning("⚠️ 提示: 币安所有节点均拒绝了连接 (美国IP限制)。建议在本地运行或使用日本VPS。")

    for x in recent_hl_data:
        hl_ts = x["time"]
        dt = datetime.fromtimestamp(hl_ts / 1000, tz)
        time_str = dt.strftime("%Y-%m-%d %H:00")
