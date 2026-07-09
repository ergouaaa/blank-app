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
    coin = st.text_input("请输入币种代码", "SKHX", label_visibility="collapsed").strip()
with col2:
    # 这个按钮点击后会触发页面重跑，从而实现刷新，不需要写逻辑
    st.button("🔄 刷新")

if not coin:
    st.warning("请输入币种代码")
    st.stop()


def fetch_funding_history(query_coin):
    url = "https://api.hyperliquid.xyz/info"
    now = int(time.time() * 1000)
    payload = {
        "type": "fundingHistory",
        "coin": query_coin,
        "startTime": now - 24 * 60 * 60 * 1000
    }

    resp = requests.post(url, json=payload, timeout=10)
    return resp.json()


def get_candidate_coins(raw_coin):
    candidates = [raw_coin]

    # SKHX 这类 xyz 市场在 API 里需要带上 dex 前缀，用户输入时可以省略。
    if ":" not in raw_coin:
        xyz_coin = f"xyz:{raw_coin.upper()}"
        if xyz_coin not in candidates:
            candidates.append(xyz_coin)

    return candidates


# 3. 核心逻辑 (直接运行，不需要 if st.button)
data = None
last_error = None
tried_coins = []

# 显示加载圈
with st.spinner('正在获取最新数据...'):
    for query_coin in get_candidate_coins(coin):
        tried_coins.append(query_coin)
        try:
            data = fetch_funding_history(query_coin)
        except Exception as e:
            last_error = e
            continue

        if isinstance(data, list) and len(data) > 0:
            break

if last_error and (not isinstance(data, list) or len(data) == 0):
    st.error(f"请求失败: {last_error}")
    st.stop()

if not isinstance(data, list) or len(data) == 0:
    st.warning(f"未找到数据: {data}，已尝试: {', '.join(tried_coins)}")
    st.stop()

tz = timezone(timedelta(hours=8))  # GMT+8

# 取最后 24 条数据
recent_data = data[-24:]

# 建议：既然你是要看“最新”，通常把最新的时间放在第一行比较方便
# 我把下面这行注释解开了，这样最新的时间会在最上面 (如果你不喜欢，可以再把这行注释掉)
recent_data = reversed(recent_data)

result_list = []
total_bps = 0

for x in recent_data:
    dt = datetime.fromtimestamp(x["time"] / 1000, tz)
    bps = float(x["fundingRate"]) * 10000
    total_bps += bps

    result_list.append({
        "时间 (GMT+8)": dt.strftime("%Y-%m-%d %H:00"),
        "费率 (bps)": f"{bps:.2f} bps"
    })

# 显示表格 (Streamlit 默认就会居中显示这个表格)
st.table(result_list)

st.metric("最近 24 条费率合计", f"{total_bps:.2f} bps")
