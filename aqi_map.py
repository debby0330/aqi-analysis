#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台灣即時 AQI 地圖顯示程式
串接環境部 API 獲取全台即時 AQI 數據並使用 Folium 在地圖上標示
"""

import os
import requests
import folium
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
import json
from geopy.distance import geodesic
import csv
import math
from pyproj import Transformer

# 載入環境變數
load_dotenv()

class AQIMapGenerator:
    def __init__(self):
        self.api_key = os.getenv('AQI_API_KEY')
        if not self.api_key:
            raise ValueError("請在 .env 檔案中設定 AQI_API_KEY")
        
        self.api_url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
        self.aqi_data = None
        self.taipei_station_wgs84 = (25.0478, 121.5170)  # 台北車站 WGS84 坐標
        self.taipei_station_twd97 = self.wgs84_to_twd97(*self.taipei_station_wgs84)  # 轉換為 TWD97
        
    def fetch_aqi_data(self):
        """獲取環境部 AQI 數據"""
        try:
            params = {
                'api_key': self.api_key,
                'format': 'json',
                'limit': 1000
            }
            
            print("正在獲取 AQI 數據...")
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if isinstance(data, list):
                self.aqi_data = data
            elif isinstance(data, dict) and 'value' in data:
                self.aqi_data = data['value']
            else:
                raise ValueError("API 回應格式錯誤")
                
            print(f"成功獲取 {len(self.aqi_data)} 個測站數據")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"API 請求錯誤: {e}")
            return False
        except Exception as e:
            print(f"數據處理錯誤: {e}")
            return False
    
    def get_aqi_color(self, aqi_value):
        """根據 AQI 數值返回對應顏色"""
        try:
            aqi = int(aqi_value)
        except (ValueError, TypeError):
            return '#808080'  # 灰色（無效數據）
        
        if aqi <= 50:
            return '#00E400'  # 綠色
        elif aqi <= 100:
            return '#FFFF00'  # 黃色
        else:
            return '#FF0000'  # 紅色
    
    def get_aqi_level(self, aqi_value):
        """根據 AQI 數值返回等級描述"""
        try:
            aqi = int(aqi_value)
        except (ValueError, TypeError):
            return '數據異常'
        
        if aqi <= 50:
            return '良好'
        elif aqi <= 100:
            return '普通'
        else:
            return '不健康'
    
    def wgs84_to_twd97(self, lat, lon):
        """將 WGS84 坐標轉換為 TWD97 坐標"""
        try:
            # 定義坐標轉換器：WGS84 (EPSG:4326) -> TWD97 (EPSG:3826)
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:3826")
            x, y = transformer.transform(lat, lon)  # 注意順序：先緯度，後經度
            return (x, y)  # 返回 (x, y) 坐標（公尺）
        except Exception as e:
            print(f"坐標轉換錯誤: {e}")
            return None
    
    def calculate_distance_twd97(self, lat, lon):
        """使用 TWD97 坐標系統計算到台北車站的距離（公里）"""
        try:
            # 將測站 WGS84 坐標轉換為 TWD97
            station_twd97 = self.wgs84_to_twd97(lat, lon)
            if station_twd97 is None:
                return None
            
            # 使用歐幾里得距離公式計算平面距離
            distance_meters = math.sqrt(
                (station_twd97[0] - self.taipei_station_twd97[0])**2 + 
                (station_twd97[1] - self.taipei_station_twd97[1])**2
            )
            
            # 轉換為公里並四捨五入
            distance_km = distance_meters / 1000
            return round(distance_km, 2)
        except Exception as e:
            print(f"距離計算錯誤: {e}")
            return None
    
    def export_to_csv(self, filename=None):
        """將 AQI 數據匯出為 CSV 檔案"""
        if not self.aqi_data:
            print("沒有 AQI 數據可以匯出")
            return False
        
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'outputs/aqi_data_{timestamp}.csv'
        
        try:
            # 確保 outputs 目錄存在
            os.makedirs('outputs', exist_ok=True)
            
            # 準備 CSV 數據
            csv_data = []
            for station in self.aqi_data:
                try:
                    lat = station.get('latitude', 0)
                    lon = station.get('longitude', 0)
                    distance = self.calculate_distance_twd97(lat, lon)  # 使用 TWD97 計算距離
                    
                    csv_data.append({
                        '測站名稱': station.get('sitename', '未知測站'),
                        '縣市': station.get('county', '未知縣市'),
                        'AQI': station.get('aqi', 'N/A'),
                        '等級': self.get_aqi_level(station.get('aqi', 'N/A')),
                        '狀態': station.get('status', 'N/A'),
                        '主要污染物': station.get('pollutant', 'N/A'),
                        '緯度': lat,
                        '經度': lon,
                        '距離台北車站(公里)': distance,  # TWD97 計算的距離
                        '更新時間': station.get('publishtime', 'N/A')
                    })
                except Exception as e:
                    print(f"處理測站數據時發生錯誤: {e}")
                    continue
            
            # 寫入 CSV 檔案
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                if csv_data:
                    fieldnames = csv_data[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(csv_data)
            
            print(f"數據已匯出至 {filename}，共 {len(csv_data)} 筆記錄")
            return True
            
        except Exception as e:
            print(f"匯出 CSV 時發生錯誤: {e}")
            return False
    
    def create_map(self):
        """創建 AQI 地圖"""
        if not self.aqi_data:
            print("沒有 AQI 數據，請先執行 fetch_aqi_data()")
            return None
        
        # 台灣中心座標
        taiwan_center = [23.8, 121.0]
        
        # 創建地圖
        m = folium.Map(
            location=taiwan_center,
            zoom_start=7,
            tiles='OpenStreetMap'
        )
        
        # 添加簡化的 AQI 圖例
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 180px; height: 120px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <h4>AQI 等級圖例</h4>
        <p><i class="fa fa-circle" style="color:#00E400"></i> 0-50 良好</p>
        <p><i class="fa fa-circle" style="color:#FFFF00"></i> 51-100 普通</p>
        <p><i class="fa fa-circle" style="color:#FF0000"></i> 101+ 不健康</p>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
        
        # 添加測站標記
        valid_stations = 0
        for station in self.aqi_data:
            try:
                # 獲取座標
                lat = float(station.get('latitude', 0))
                lon = float(station.get('longitude', 0))
                
                if lat == 0 or lon == 0:
                    continue
                
                # 獲取 AQI 數值
                aqi = station.get('aqi', 'N/A')
                site_name = station.get('sitename', '未知測站')
                county = station.get('county', '未知縣市')
                pollutant = station.get('pollutant', 'N/A')
                status = station.get('status', 'N/A')
                
                # 獲取顏色和等級
                color = self.get_aqi_color(aqi)
                level = self.get_aqi_level(aqi)
                
                # 創建簡化的彈出視窗內容
                popup_content = f"""
                <div style="font-size: 14px; min-width: 200px;">
                <h4 style="margin: 5px 0; color: #333;">{site_name}</h4>
                <p style="margin: 3px 0;"><b>所在地:</b> {county}</p>
                <p style="margin: 3px 0;"><b>即時 AQI:</b> <span style="color: {color}; font-weight: bold;">{aqi}</span></p>
                <p style="margin: 3px 0;"><b>等級:</b> {level}</p>
                </div>
                """
                
                # 添加圓形標記
                folium.CircleMarker(
                    location=[lat, lon],
                    radius=10,
                    popup=folium.Popup(popup_content, max_width=250),
                    color='black',
                    weight=1,
                    fillColor=color,
                    fillOpacity=0.8,
                    tooltip=f"{site_name}: AQI {aqi}"
                ).add_to(m)
                
                valid_stations += 1
                
            except (ValueError, KeyError) as e:
                print(f"處理測站數據時發生錯誤: {e}")
                continue
        
        print(f"地圖上已標示 {valid_stations} 個有效測站")
        
        # 添加標題
        title_html = '''
        <h3 align="center" style="font-size:16px"><b>台灣即時 AQI 監測地圖</b></h3>
        '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        return m
    
    def save_map(self, map_obj, filename='aqi_map.html'):
        """儲存地圖為 HTML 檔案"""
        if map_obj is None:
            print("無法儲存地圖：地圖物件為 None")
            return False
        
        try:
            map_obj.save(filename)
            print(f"地圖已儲存為 {filename}")
            return True
        except Exception as e:
            print(f"儲存地圖時發生錯誤: {e}")
            return False
    
    def run(self):
        """執行完整流程"""
        print("=" * 50)
        print("台灣即時 AQI 地圖生成器")
        print("=" * 50)
        
        # 獲取數據
        if not self.fetch_aqi_data():
            print("無法獲取 AQI 數據，程式終止")
            return False
        
        # 創建地圖
        aqi_map = self.create_map()
        if aqi_map is None:
            print("無法創建地圖")
            return False
        
        # 儲存地圖
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        map_filename = f'outputs/aqi_map_{timestamp}.html'
        
        # 確保 outputs 目錄存在
        os.makedirs('outputs', exist_ok=True)
        
        if self.save_map(aqi_map, map_filename):
            print(f"地圖已儲存為 {map_filename}")
        
        # 匯出 CSV 數據
        csv_filename = f'outputs/aqi_data_{timestamp}.csv'
        if self.export_to_csv(csv_filename):
            print(f"數據已匯出為 {csv_filename}")
        
        print(f"\n任務完成！")
        print(f"- 地圖檔案: {map_filename}")
        print(f"- 數據檔案: {csv_filename}")
        return True

def main():
    """主程式"""
    try:
        generator = AQIMapGenerator()
        success = generator.run()
        
        if success:
            print("\n程式執行成功！")
        else:
            print("\n程式執行失敗，請檢查錯誤訊息")
            
    except Exception as e:
        print(f"程式執行時發生未預期的錯誤: {e}")

if __name__ == "__main__":
    main()
