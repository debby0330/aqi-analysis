from pyproj import Transformer

def test_twd97_conversion():
    # 台北車站 WGS84 坐標
    taipei_wgs84 = (25.0478, 121.5170)
    
    # 測試幾個測站坐標
    test_stations = [
        ("台北車站", 25.0478, 121.5170),
        ("基隆測站", 25.129167, 121.760056),
        ("新店測站", 24.949028, 121.383528),
        ("淡水測站", 25.164444, 121.446111)
    ]
    
    # 創建坐標轉換器
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3826")
    
    print("坐標轉換測試:")
    print("=" * 60)
    
    # 轉換台北車站
    taipei_x, taipei_y = transformer.transform(taipei_wgs84[0], taipei_wgs84[1])
    print(f"台北車站 WGS84: ({taipei_wgs84[0]}, {taipei_wgs84[1]})")
    print(f"台北車站 TWD97: ({taipei_x:.2f}, {taipei_y:.2f})")
    print()
    
    # 轉換測站並計算距離
    for name, lat, lon in test_stations:
        try:
            x, y = transformer.transform(lat, lon)
            distance = ((x - taipei_x)**2 + (y - taipei_y)**2)**0.5 / 1000
            
            print(f"{name}:")
            print(f"  WGS84: ({lat}, {lon})")
            print(f"  TWD97: ({x:.2f}, {y:.2f})")
            print(f"  距離台北車站: {distance:.2f} 公里")
            print()
        except Exception as e:
            print(f"{name} 轉換錯誤: {e}")

if __name__ == "__main__":
    test_twd97_conversion()
