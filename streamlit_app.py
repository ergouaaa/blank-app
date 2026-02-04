import streamlit as st
import requests
import time
from datetime import datetime, timezone, timedelta
import pandas as pd

# ---------------------------------------------------------
# 1. 页面基础设置
# ---------------------------------------------------------
st.set_page_config(page_title="白银资金费率监控", layout="wide")
st.title("Hyperliquid vs Binance 白银费率对比")

# 硬编码写死币种，不需要手动输入
HL_COIN = "xyz:SILVER"
BN_SYMBOL = "XAGUSDT"

# ---------------------------------------------------------
# 2. 获取币安数据的函数
# ---------------------------------------------------------
def get_binance_funding_rates(symbol):
    """获取币安最近的资金费率"""
    try:
        # 币安 U本位合约 历史资金费率接口
        url = "https://fapi.binance.vision/fapi/v1/fundingRate"
        # limit=50 足够覆盖最近几天
        params = {"symbol": symbol, "limit": 50} 
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        
        rates_map = {}
        if isinstance(data, list):
            for item in data:
                ts = item["fundingTime"]
                rate = float(item["fundingRate"]) * 10000 # 转为 bps
                
                # 将时间戳对齐到整小时（去掉毫秒级误差），方便后续对比
                aligned_ts = (ts // 3600000) * 3600000 
                rates_map[aligned_ts] = rate
        return rates_map
    except Exception as e:
        st.error(f"币安接口连接失败: {e}")
        return {}

# ---------------------------------------------------------
# 3. 主程序逻辑
# ---------------------------------------------------------
if st.button("刷新最新费率"):
    
    # --- A. 获取 Hyperliquid 数据 ---
    url = "https://api.hyperliquid.xyz/info"
    now = int(time.time() * 1000)
    
    # 查过去24小时数据
    payload = {
        "type": "fundingHistory",
        "coin": HL_COIN,
        "startTime": now - 24 * 60 * 60 * 1000
    }

    with st.spinner('正在同步双边数据...'):
        # 并行获取两边的数据
        try:
            hl_resp = requests.post(url, json=payload, timeout=10)
            hl_data = hl_resp.json()
        except Exception as e:
            st.error(f"Hyperliquid 请求失败: {e}")
            st.stop()

        bn_map = get_binance_funding_rates(BN_SYMBOL)

    if not isinstance(hl_data, list) or len(hl_data) == 0:
        st.warning("未获取到 Hyperliquid 数据")
        st.stop()

    # --- B. 数据对齐与展示 ---
    tz = timezone(timedelta(hours=8))  # 北京时间 GMT+8
    
    # 只取最后 12 条数据（最近12小时），你可以改为 8 或 24
    recent_hl_data = hl_data[-12:] 
    
    # 倒序：最新的时间显示在最上面
    recent_hl_data.reverse()

    table_rows = []
    
    for x in recent_hl_data:
        # Hyperliquid 的时间戳
        hl_ts = x["time"]
        dt = datetime.fromtimestamp(hl_ts / 1000, tz)
        time_str = dt.strftime("%Y-%m-%d %H:00")
        
        # Hyperliquid 费率
        hl_bps = float(x["fundingRate"]) * 10000
        
        # 寻找对应的币安费率
        # 逻辑：检查当前这个小时，币安有没有结算记录
        aligned_ts = (hl_ts // 3600000) * 3600000
        
        if aligned_ts in bn_map:
            # 如果币安在这个时间点有数据，就显示
            bn_val = f"{bn_map[aligned_ts]:.4f}"
        else:
            # 如果没有（比如币安还没到4小时/8小时结算点），就留空
            bn_val = "" 

        table_rows.append({
            "时间 (GMT+8)": time_str,
            "Hyperliquid (bps)": f"{hl_bps:.4f}",
            "Binance (bps)": bn_val  # 有值则显示，无值则空
        })

    # --- C. 渲染表格 ---
    df = pd.DataFrame(table_rows)
    
    # 使用 st.table 展示，清晰整齐
    st.table(df)
