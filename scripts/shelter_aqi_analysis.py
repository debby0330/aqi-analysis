import pandas as pd
import numpy as np
from math import radians, sin, cos, sqrt, atan2

def haversine_distance(lat1, lon1, lat2, lon2):
    """計算兩點間的距離（公里）"""
    R = 6371.0
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def shelter_aqi_risk_analysis():
    """避難收容所 AQI 風險分析（含情境模擬）"""
    
    print("進行避難收容所 AQI 風險分析...")
    
    # 讀取資料
    shelters_df = pd.read_csv("outputs/避難收容處所_SHP過濾.csv", encoding='utf-8-sig')
    aqi_df = pd.read_csv("outputs/aqi_data_20260225_115446.csv", encoding='utf-8-sig')
    
    print(f"避難收容所: {len(shelters_df)} 筆")
    print(f"AQI 測站: {len(aqi_df)} 筆")
    
    # 情境模擬：將某些測站的 AQI 設為高值
    print("\n進行情境模擬...")
    aqi_simulated = aqi_df.copy()
    
    # 選擇幾個測站模擬高 AQI 值
    high_aqi_stations = ['基隆', '汐止', '新店', '土城', '林口']
    for station in high_aqi_stations:
        mask = aqi_simulated['測站名稱'] == station
        if mask.any():
            aqi_simulated.loc[mask, 'AQI'] = 150
            aqi_simulated.loc[mask, '狀態'] = '不健康'
    
    print(f"模擬 {len(high_aqi_stations)} 個測站 AQI = 150")
    
    # 為每個避難收容所找到最近的 AQI 測站
    print("\n計算最近 AQI 測站...")
    results = []
    
    for idx, shelter in shelters_df.iterrows():
        shelter_lat = shelter['緯度']
        shelter_lon = shelter['經度']
        
        min_distance = float('inf')
        nearest_station = None
        nearest_aqi = None
        
        # 找到最近的 AQI 測站
        for _, aqi_station in aqi_simulated.iterrows():
            if pd.notna(aqi_station['緯度']) and pd.notna(aqi_station['經度']):
                distance = haversine_distance(
                    shelter_lat, shelter_lon,
                    aqi_station['緯度'], aqi_station['經度']
                )
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_station = aqi_station
                    nearest_aqi = aqi_station['AQI']
        
        # 風險標記
        risk_label = "Low Risk"
        if nearest_aqi > 100:
            risk_label = "High Risk"
        elif nearest_aqi > 50 and not shelter['is_indoor']:
            risk_label = "Warning"
        
        # 記錄結果
        result = {
            '避難收容處所名稱': shelter['避難收容處所名稱'],
            '縣市': shelter['縣市及鄉鎮市區'],
            '地址': shelter['避難收容處所地址'],
            '緯度': shelter_lat,
            '經度': shelter_lon,
            'is_indoor': shelter['is_indoor'],
            '最近AQI測站': nearest_station['測站名稱'] if nearest_station is not None else None,
            '最近AQI測站距離_km': round(min_distance, 2) if min_distance != float('inf') else None,
            '最近AQI值': nearest_aqi,
            'AQI狀態': nearest_station['狀態'] if nearest_station is not None else None,
            '風險標記': risk_label
        }
        
        results.append(result)
    
    # 轉換為 DataFrame
    results_df = pd.DataFrame(results)
    
    # 統計結果
    print(f"\n風險分析結果:")
    print(f"High Risk: {(results_df['風險標記'] == 'High Risk').sum()} 筆")
    print(f"Warning: {(results_df['風險標記'] == 'Warning').sum()} 筆")
    print(f"Low Risk: {(results_df['風險標記'] == 'Low Risk').sum()} 筆")
    
    # 顯示 High Risk 範例
    high_risk = results_df[results_df['風險標記'] == 'High Risk']
    if len(high_risk) > 0:
        print(f"\nHigh Risk 範例 (前5個):")
        for i, (_, row) in enumerate(high_risk.head().iterrows(), 1):
            print(f"{i}. {row['避難收容處所名稱']} - AQI: {row['最近AQI值']} ({row['最近AQI測站']})")
    
    # 保存結果
    output_file = "outputs/shelter_aqi_analysis.csv"
    results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n結果已保存至: {output_file}")
    
    return results_df

if __name__ == "__main__":
    result = shelter_aqi_risk_analysis()
