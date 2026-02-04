import streamlit as st
import requests
import time
from datetime import datetime, timezone, timedelta
import pandas as pd

# 1. 设置网页标题
st.title("Hyperliquid 资金费率查询")

# 2. 添加一个输入框，默认是你的 xyz:SILVER，但也可以查别的
coin = st.text_input("请输入币种代码", "xyz:SILVER")

# 3. 添加一个按钮，点击才开始查询
if st.button("查询最新费率"):
    url = "https://api.hyperliquid.xyz/info"
    now = int(time.time() * 1000)

    payload = {
        "type": "fundingHistory",
        "coin": coin,
        "startTime": now - 24 * 60 * 60 * 1000
    }

    # 添加加载提示
    with st.spinner('正在请求数据...'):
        try:
            resp = requests.post(url, json=payload, timeout=10)
            data = resp.json()
        except Exception as e:
            st.error(f"请求失败: {e}")
            st.stop() # 停止后续代码运行

    # 4. 逻辑判断：如果没有数据
    if not isinstance(data, list) or len(data) == 0:
        st.warning(f"未找到数据: {data}") # 用 warning 比 print 更显眼
        st.stop() # 替代 exit()

    tz = timezone(timedelta(hours=8))  # GMT+8
    
    # 5. 处理数据并展示
    # 创建一个列表来存处理好的数据，为了最后显示表格
    result_list = []
    
    for x in data[-8:]:
        dt = datetime.fromtimestamp(x["time"] / 1000, tz)
        bps = float(x["fundingRate"]) * 10000
        
        # 存入列表
        result_list.append({
            "时间 (GMT+8)": dt.strftime("%Y-%m-%d %H:00"),
            "费率 (bps)": f"{bps:.2f} bps"
        })

    # 6. 直接显示为表格，比 print 更好看
    st.table(result_list)
    
    # 如果你还是喜欢原来的文本格式，也可以保留下面的代码：
    # for item in result_list:
    #     st.write(item["时间 (GMT+8)"], item["费率 (bps)"])
