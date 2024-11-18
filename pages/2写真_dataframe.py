import pandas as pd
from PIL import ExifTags
import streamlit as st
from PIL import Image
from io import BytesIO
import folium
from streamlit_folium import folium_static
import base64

# 画像データをDataFrameの列に表示するための関数
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# EXIFデータから位置情報を抽出する関数
def get_gps_info(exif_data):
    gps_info = {}
    if exif_data is not None:
        for tag, value in exif_data.items():
            decoded_tag = ExifTags.TAGS.get(tag)
            if decoded_tag == 'GPSInfo':
                gps_info = value
                break
    return gps_info

# EXIFデータから撮影時間を抽出する関数
def get_creation_time(exif_data):
    creation_time = "撮影時間情報なし"
    if exif_data is not None:
        for tag, value in exif_data.items():
            if ExifTags.TAGS.get(tag) == 'DateTime':
                creation_time = value
                break
    return creation_time

# EXIFのGPS情報を解析して緯度・経度を取得する関数
def get_lat_lon(gps_info):
    def convert_to_degrees(values):
        try:
            # 'IFDRational'オブジェクトを数値に変換
            d = float(values[0])
            m = float(values[1])
            s = float(values[2])
            return d + (m / 60.0) + (s / 3600.0)
        except (TypeError, IndexError, ValueError):
            return None  # 不正なデータの場合はNoneを返す

    if gps_info:
        lat = convert_to_degrees(gps_info.get(2)) if gps_info.get(2) else None
        lon = convert_to_degrees(gps_info.get(4)) if gps_info.get(4) else None

        # 緯度・経度がNoneの場合はスキップ
        if lat is None or lon is None:
            return None, None
        
        # 南緯・西経の処理
        if gps_info.get(1) == 'S':  # 南緯の場合
            lat = -lat
        if gps_info.get(3) == 'W':  # 西経の場合
            lon = -lon

        return lat, lon
    return None, None


if st.button("detaframeの作成"):
    
    if "data" not in st.session_state:
        st.session_state.data = []
        
    for file_name, file_content in st.session_state.resized_file_contents.items():
        try:
            # 画像を読み込む
            image = Image.open(BytesIO(file_content))
            
            # EXIFデータを取得
            exif_data = image._getexif()
            
            # 撮影時間とGPS情報を抽出
            creation_time = get_creation_time(exif_data)
            gps_info = get_gps_info(exif_data)
            lat, lon = get_lat_lon(gps_info)

            # データをリストに保存
            st.session_state.data.append({
                "ファイル名": file_name,
                "撮影時間": creation_time,
                "latitude": lat,
                "longitude": lon,
            })

        except Exception as e:
            st.write(f"エラーが発生しました: {e}")
            continue

    # DataFrameに変換
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df, use_container_width=True)
    
    # DataFrameに緯度と経度があれば地図を表示
    if not df.empty and 'latitude' in df.columns and 'longitude' in df.columns:
        valid_locations = df.dropna(subset=['latitude', 'longitude'])  # 緯度・経度が存在する行のみを使用
        if not valid_locations.empty:
            # 地図の中心を計算（平均位置に設定）
            map_center = [valid_locations['latitude'].mean(), valid_locations['longitude'].mean()]
            
            # Foliumで地図作成
            m = folium.Map(location=map_center, zoom_start=12)
            
            # 各地点にマーカーを追加
            for _, row in valid_locations.iterrows():
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=row.get('ファイル名', 'No File Name'),  # もしファイル名があれば、それをポップアップとして表示
                    icon=folium.Icon(color='blue')  # 青いマーカー
                ).add_to(m)
            
            # Streamlitに地図を表示
            folium_static(m)
        else:
            st.write("有効な緯度・経度が含まれていません")
    else:
        st.write("データがありません")
