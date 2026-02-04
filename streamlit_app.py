import streamlit as st
import requests
import time
from datetime import datetime, timezone, timedelta

# 1. 设置页面布局为 "居中" (Centered)
st.set_page_config(page_title="Hyperliquid 费率查询", layout="centered")

st.title("Hyperliquid 资金费率查询")

# 2. 输入框 & 刷新按钮
# 使用 columns 让输入框和按钮排得好看一点
col1, col2 = st.columns([3, 1]) 
with col1:
    coin = st.text_input("请输入币种代码", "xyz:SILVER", label_visibility="collapsed")
with col2:
    # 这个按钮点击后会触发页面重跑，从而实现刷新，不需要写逻辑
    st.button("🔄 刷新")

# 3. 核心逻辑 (直接运行，不需要 if st.button)
url = "https://api.hyperliquid.xyz/info"
now = int(time.time() * 1000)

payload = {
    "type": "fundingHistory",
    "coin": coin,
    "startTime": now - 24 * 60 * 60 * 1000 
}

# 显示加载圈
with st.spinner('正在获取最新数据...'):
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

# 取最后 8 条数据
recent_data = data[-8:] 

# 建议：既然你是要看“最新”，通常把最新的时间放在第一行比较方便
# 我把下面这行注释解开了，这样最新的时间会在最上面 (如果你不喜欢，可以再把这行注释掉)
recent_data = reversed(recent_data)

result_list = []

for x in recent_data:
    dt = datetime.fromtimestamp(x["time"] / 1000, tz)
    bps = float(x["fundingRate"]) * 10000
    
    result_list.append({
        "时间 (GMT+8)": dt.strftime("%Y-%m-%d %H:00"),
        "费率 (bps)": f"{bps:.2f} bps"
    })

# 显示表格 (Stremalit 默认就会居中显示这个表格)
st.table(result_list)
