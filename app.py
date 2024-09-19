import streamlit as st
import zipfile
from PIL import Image, ExifTags
from datetime import datetime
from io import BytesIO

st.set_page_config(layout="wide")

def process_zip(uploaded_zip):
    # メモリ内でZIPファイルを読み込み
    with zipfile.ZipFile(uploaded_zip, 'r') as zip_ref:
        file_contents = {}
        for file_name in zip_ref.namelist():
            file_data = zip_ref.read(file_name)
            file_contents[file_name] = file_data
    
    # セッションステートにファイル内容を保存
    st.session_state.file_contents = file_contents

# アップロードされたZIPファイルを処理
uploaded_zip = st.file_uploader("ZIPファイルを選択してください", type="zip")

if uploaded_zip is not None:
    process_zip(uploaded_zip)

# 解凍された内容を表示
if 'file_contents' in st.session_state:
    file_contents = st.session_state.file_contents
    
    # Streamlitで列レイアウトを使用
    col1, col2, col3 = st.columns([2, 2, 3])
    
    with col1:
        st.write("写真")
    
    with col2:
        st.write("ファイル名")
    
    with col3:
        st.write("ファイル容量 (KB) - 撮影時間")
    
    for file_name, file_content in file_contents.items():
        if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
            # 画像の読み込み
            image = Image.open(BytesIO(file_content))
            
            # EXIFデータから撮影時間を取得
            exif_data = image._getexif()
            if exif_data is not None:
                for tag, value in exif_data.items():
                    if ExifTags.TAGS.get(tag) == 'DateTime':
                        creation_time = value
                        break
                else:
                    creation_time = "撮影時間情報なし"
            else:
                creation_time = "EXIFデータなし"
            
            # 撮影時間がなければデフォルトメッセージを表示
            try:
                formatted_time = datetime.strptime(creation_time, '%Y:%m:%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                formatted_time = creation_time

            # ファイル情報
            file_size = len(file_content) / 1024  # サイズをKB単位に変換
            
            # Streamlitで画像と情報を表示
            col1, col2, col3 = st.columns([2, 2, 3])
            
            with col1:
                st.image(image, use_column_width=True)
            
            with col2:
                st.write(file_name)
            
            with col3:
                st.write(f"{file_size:.2f} KB - {formatted_time}")

