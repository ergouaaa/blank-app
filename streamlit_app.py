import streamlit as st
import requests
import time
from datetime import datetime, timezone, timedelta
import pandas as pd

# ==========================================
# 1. 页面基础配置
# ==========================================
st.set_page_config(page_title="白银费率监控", layout="wide")
st.title("Hyperliquid vs Binance 白银费率对比")
st.caption("🚀 已启用公共线路加速，无需配置本地代理")

# 硬编码币种信息
HL_COIN = "xyz:SILVER"
BN_SYMBOL = "XAGUSDT"

# ==========================================
# 2. 核心函数：获取币安数据 (使用公共中转)
# ==========================================
def get_binance_funding_rates_via_proxy(symbol):
    """
    通过公共 CORS 代理访问币安合约接口，绕过 Streamlit Cloud 的 IP 限制
    """
    # 目标：币安合约接口
    target_url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=50"
    
    # 技巧：使用 api.allorigins.win 作为跳板
    # 这样请求是由 allorigins 发出的，而不是美国的 Streamlit 服务器
    proxy_url = f"https://api.allorigins.win/raw?url={target_url}"
    
    try:
        # 添加一个随机参数防止缓存
        resp = requests.get(f"{proxy_url}&rand={int(time.time())}", timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            rates_map = {}
            if isinstance(data, list):
                for item in data:
                    ts = item["fundingTime"]
                    rate = float(item["fundingRate"]) * 10000
                    # 对齐到整小时
                    aligned_ts = (ts // 3600000) * 3600000 
                    rates_map[aligned_ts] = rate
            return rates_map
        else:
            print(f"Proxy returned status: {resp.status_code}")
            return {}
            
    except Exception as e:
        print(f"Binance Proxy Error: {e}")
        return {}

# ==========================================
# 3. 主程序逻辑
# ==========================================

# 自动运行，或者点击刷新
if st.button("🔄 刷新数据", type="primary"):
    
    # --- A. 获取 Hyperliquid 数据 (直连) ---
    st.info("正在拉取数据...")
    
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

    # --- B. 获取 Binance 数据 (通过中转) ---
    bn_map = get_binance_funding_rates_via_proxy(BN_SYMBOL)

    # --- C. 数据合并与展示 ---
    tz = timezone(timedelta(hours=8)) # 北京时间
    
    # 取最近 12 小时
    recent_hl_data = hl_data[-12:] 
    recent_hl_data.reverse() # 最新的在上面

    table_rows = []
    
    for x in recent_hl_data:
        # 时间
        hl_ts = x["time"]
        dt = datetime.fromtimestamp(hl_ts / 1000, tz)
        time_str = dt.strftime("%Y-%m-%d %H:00")
        
        # HL 费率
        hl_bps = float(x["fundingRate"]) * 10000
        
        # 币安 费率 (尝试匹配)
        aligned_ts = (hl_ts // 3600000) * 3600000
        
        if aligned_ts in bn_map:
            bn_val = f"{bn_map[aligned_ts]:.4f}"
            bn_num = bn_map[aligned_ts]
            
            # 计算差价 (Hyperliquid - Binance)
            diff = hl_bps - bn_num
            diff_str = f"{diff:.4f}"
        else:
            bn_val = "-"
            diff_str = "-"

        table_rows.append({
            "时间 (GMT+8)": time_str,
            "Hyperliquid (bps)": f"{hl_bps:.4f}",
            "Binance (bps)": bn_val,
            "差值 (H-B)": diff_str # 帮你算了个差值，方便看套利空间
        })

    # 渲染表格
    df = pd.DataFrame(table_rows)
    st.table(df)

else:
    st.write("点击上方按钮开始查询")
