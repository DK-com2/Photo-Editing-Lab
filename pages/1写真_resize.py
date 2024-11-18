import streamlit as st
from PIL import Image, ExifTags
from io import BytesIO
import zipfile

# セッションステートからファイルを読み込み
if 'file_contents' in st.session_state:
    file_contents = st.session_state.file_contents

# リサイズされたファイルを新しいセッションステートに保存
if 'resized_file_contents' not in st.session_state:
    st.session_state.resized_file_contents = {}

# リサイズの縮小率をスライダーで選択
resize_factor = st.slider("リサイズの縮小率 (%)", 10, 100, 80) / 100  # %で指定し、内部では小数で扱う

def resize_image(image, resize_factor):
    # EXIF情報を抽出
    exif_data = image.info.get('exif')

    # 画像の解像度を縮小
    width, height = image.size
    new_size = (int(width * resize_factor), int(height * resize_factor))
    image = image.resize(new_size)

    # JPEGとして保存するためにRGBAをRGBに変換
    if image.mode == 'RGBA':
        image = image.convert('RGB')

    # 新しいサイズの画像を保存
    buffer = BytesIO()

    # exif_dataが存在する場合のみ設定
    if exif_data:
        image.save(buffer, format="JPEG", exif=exif_data)
    else:
        image.save(buffer, format="JPEG")
    
    buffer.seek(0)
    return buffer



# 圧縮ボタンの設置
if st.button("圧縮を実行"):
    # プログレスバーの初期化
    progress_bar = st.progress(0)
    total_files = len(st.session_state.file_contents)
    
    # 圧縮されたファイルで file_contents を置き換える
    for idx, (file_name, file_content) in enumerate(st.session_state.file_contents.items()):
        if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
            # 元の画像を読み込む
            image = Image.open(BytesIO(file_content))
            
            # 画像を圧縮
            resized_image_buffer = resize_image(image, resize_factor)
            
            # 圧縮された画像をファイル内容に置き換える
            st.session_state.resized_file_contents[file_name] = resized_image_buffer.getvalue()

        # プログレスバーの更新
        progress = (idx + 1) / total_files  # 進捗を計算
        progress_bar.progress(progress)
    
    st.success("画像の圧縮が完了しました。")
    progress_bar.empty()

# リサイズされたファイルがセッションステートにあるか確認
if 'resized_file_contents' in st.session_state:
    resized_file_contents = st.session_state.resized_file_contents
    
    # ZIPファイルを作成してダウンロード可能にする
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_name, file_content in resized_file_contents.items():
            zip_file.writestr(file_name, file_content)
    
    zip_buffer.seek(0)
    
    # ZIPファイルのダウンロードボタン
    st.download_button(
        label="リサイズされた画像をまとめてダウンロード (ZIP)",
        data=zip_buffer,
        file_name="resized_images.zip",
        mime="application/zip"
    )
    
# 2列のレイアウトで画像と情報を表示
cols_per_row = 2  # 1行あたりの列数
items = list(resized_file_contents.items())

for i in range(0, len(items), cols_per_row):
    cols = st.columns(cols_per_row)
    
    for j, (file_name, file_content) in enumerate(items[i:i + cols_per_row]):
        with cols[j]:
            # 画像データをPILで読み込む
            image = Image.open(BytesIO(file_content))
            
            # 画像を表示
            st.image(image, use_column_width=True)

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
            
            # ファイルサイズの計算
            file_size = len(file_content) / 1024
            
            # ファイル名をクリック可能なダウンロードボタンとして表示
            st.download_button(
                label=f"{file_name}",
                data=file_content,
                file_name=file_name,
                mime="image/jpeg"
            )
            st.write(f"{file_size:.2f} KB - {creation_time}")
else:
    st.write("リサイズされた画像がまだありません。")

