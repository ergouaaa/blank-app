import streamlit as st
import requests
import time
from datetime import datetime, timezone, timedelta
import pandas as pd

# 1. 设置网页标题
st.title("Hyperliquid 资金费率查询")

# 2. 输入框 (保留你的默认值)
coin = st.text_input("请输入币种代码", "xyz:SILVER")

# 3. 按钮触发
if st.button("查询最新费率"):
    url = "https://api.hyperliquid.xyz/info"
    now = int(time.time() * 1000)

    # 这里查询过去24小时的数据，足够覆盖8条
    payload = {
        "type": "fundingHistory",
        "coin": coin,
        "startTime": now - 24 * 60 * 60 * 1000 
    }

    with st.spinner('正在请求数据...'):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
        except Exception as e:
            st.error(f"请求失败: {e}")
            st.stop()

    if not isinstance(data, list) or len(data) == 0:
        st.warning(f"未找到数据: {data}")
        st.stop()

    tz = timezone(timedelta(hours=8))  # GMT+8
    
    result_list = []
    
    # -------------------------------------------------------
    # 🔴 关键修改在这里：把 [-3:] 改成了 [-8:]
    # -------------------------------------------------------
    # 这表示取列表里的 "最后8个" 数据
    recent_data = data[-8:] 

    # 为了浏览方便，如果你想把 "最新" 的时间显示在表格最上面，
    # 可以把下面这行注释取消掉（即去掉 # 号）：
    # recent_data = reversed(recent_data)

    for x in recent_data:
        dt = datetime.fromtimestamp(x["time"] / 1000, tz)
        bps = float(x["fundingRate"]) * 10000
        
        result_list.append({
            "时间 (GMT+8)": dt.strftime("%Y-%m-%d %H:00"),
            "费率 (bps)": f"{bps:.2f} bps"
        })

    # 显示表格
    st.table(result_list)
