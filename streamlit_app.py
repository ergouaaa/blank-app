import requests
import streamlit as st
import time

# ==========================================
# 改造后的函数：获取币安资金费率 (带重试和代理)
# ==========================================
def get_binance_funding_rates(symbol, proxies=None):
    """
    尝试从多个节点获取币安合约资金费率
    """
    # 币安合约(Futures)的节点列表
    # 注意：合约主要就是 fapi.binance.com，其他节点不如现货多，但我们可以尝试主备
    base_urls = [
        "https://fapi.binance.com", 
        "https://fapi.binance.vision", # 偶尔可用，但也可能被墙
    ]
    
    endpoint = "/fapi/v1/fundingRate"
    params = {"symbol": symbol, "limit": 50}

    for base_url in base_urls:
        full_url = base_url + endpoint
        try:
            # 发送请求 (如果设置了代理，这里会自动使用)
            resp = requests.get(full_url, params=params, proxies=proxies, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                # 数据处理逻辑
                rates_map = {}
                if isinstance(data, list):
                    for item in data:
                        ts = item["fundingTime"]
                        rate = float(item["fundingRate"]) * 10000
                        aligned_ts = (ts // 3600000) * 3600000
                        rates_map[aligned_ts] = rate
                return rates_map # 成功获取，直接返回
            
            elif resp.status_code == 403:
                # 403 通常意味着 IP 被墙
                print(f"节点 {base_url} 返回 403 (被墙)，尝试下一个...")
                continue
                
        except Exception as e:
            print(f"节点 {base_url} 连接失败: {e}")
            continue # 尝试下一个节点
            
    # 如果所有节点都失败
    st.error("所有币安节点均连接失败，请检查代理设置或服务器地区。")
    return {}
