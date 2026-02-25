import pandas as pd
import os

def check_csv_distances():
    # 找到最新的 CSV 檔案
    csv_files = [f for f in os.listdir('outputs') if f.startswith('aqi_data_') and f.endswith('.csv')]
    if not csv_files:
        print("找不到 CSV 檔案")
        return
    
    latest_csv = max(csv_files)
    csv_path = os.path.join('outputs', latest_csv)
    
    print(f"檢查檔案: {csv_path}")
    print("=" * 50)
    
    try:
        # 讀取 CSV 檔案
        df = pd.read_csv(csv_path, encoding='utf-8-sig')
        
        # 顯示基本資訊
        print(f"總記錄數: {len(df)}")
        print(f"欄位: {list(df.columns)}")
        print()
        
        # 檢查距離欄位
        if '距離台北車站(公里)' in df.columns:
            distances = df['距離台北車站(公里)']
            print(f"距離統計:")
            print(f"  最小值: {distances.min()}")
            print(f"  最大值: {distances.max()}")
            print(f"  平均值: {distances.mean():.2f}")
            print(f"  零值數量: {(distances == 0).sum()}")
            print()
            
            # 顯示前10筆記錄
            print("前10筆記錄:")
            print(df[['測站名稱', '縣市', 'AQI', '距離台北車站(公里)']].head(10).to_string(index=False))
            print()
            
            # 顯示有距離的記錄
            non_zero = df[distances > 0]
            if len(non_zero) > 0:
                print(f"非零距離記錄 ({len(non_zero)} 筆):")
                print(non_zero[['測站名稱', '縣市', '距離台北車站(公里)']].head(10).to_string(index=False))
            else:
                print("所有距離都是0！")
        else:
            print("找不到 '距離台北車站(公里)' 欄位")
            
    except Exception as e:
        print(f"讀取 CSV 檔案時發生錯誤: {e}")

if __name__ == "__main__":
    check_csv_distances()
