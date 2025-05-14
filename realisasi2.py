import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import os
import tempfile

# Set halaman dan layout sebagai perintah pertama
st.set_page_config(page_title="Dashboard Saham", layout="wide")

# Fungsi untuk memuat file CSS
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Muat file CSS
load_css("style.css")

# Daftar contoh kode saham yang umum digunakan
saham_list = ["AAPL", "MSFT", "GOOGL", "TSLA", "ASII.JK", "BBCA.JK", "TLKM.JK", "BBRI.JK", "UNVR.JK", "KO", "DIS", "WMT", "ICBP.JK"]

# Judul Aplikasi dengan warna yang menarik
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>Dashboard Saham Interaktif</h1>", unsafe_allow_html=True)

# Membuat kolom untuk input parameter di sidebar
st.sidebar.header("Parameter Saham")
symbol = st.sidebar.selectbox("Kode Saham", saham_list)
entry_price = st.sidebar.number_input("Harga Entry", value=0.0)
stop_loss = st.sidebar.number_input("Stop-Loss", value=0.0)
target_price = st.sidebar.number_input("Target Price", value=0.0)
period = st.sidebar.select_slider("Pilih Periode Data", options=['5d', '1mo', '3mo', '6mo', '1y'], value='5d')
submit = st.sidebar.button("Tampilkan")

# Fungsi untuk menyimpan hasil realisasi ke CSV secara otomatis
def autosave_to_csv(dataframe):
    temp_dir = tempfile.gettempdir()
    filename = os.path.join(temp_dir, "hasil_realisasi.csv")
    dataframe.to_csv(filename, index=False)
    return filename

# Informasi Saham di Sidebar
if symbol:
    st.sidebar.write("### Informasi Saham")
    try:
        stock_info = yf.Ticker(symbol)
        stock_details = stock_info.info
        st.sidebar.write(f"**Nama Perusahaan:** {stock_details.get('longName', 'Tidak Diketahui')}")
        st.sidebar.write(f"**Sektor:** {stock_details.get('sector', 'Tidak Diketahui')}")
        st.sidebar.write(f"**Harga Sekarang:** {stock_details.get('currentPrice', 'Tidak Diketahui')}")
        st.sidebar.write(f"**Kapitalisasi Pasar:** {stock_details.get('marketCap', 'Tidak Diketahui')}")
    except Exception as e:
        st.sidebar.error(f"Tidak dapat mengambil informasi untuk kode saham {symbol}. Error: {e}")

# Membuat Dashboard dengan Tabs
if submit:
    tabs = st.tabs(["Overview", "Grafik", "Hasil Realisasi"])
    stock_data = yf.download(symbol, period=period, interval='1d')

    if stock_data.empty:
        st.error("Tidak ada data yang ditemukan. Periksa kode saham yang dimasukkan.")
    else:
        # **Tab 1: Overview**
        with tabs[0]:
            st.markdown("<h2 style='color: #4CAF50;'>Overview Saham</h2>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)

            # Menghitung perubahan harian
            daily_change = stock_data['Close'].pct_change().dropna()

            # Memastikan ada nilai untuk perubahan harian
            if not daily_change.empty:
                last_daily_change = daily_change.iloc[-1] * 100  # Mengonversi ke persen
                daily_change_str = f"{float(last_daily_change):.2f}%"  # Pastikan ini adalah float
            else:
                daily_change_str = "Tidak Tersedia"

            # Tampilkan metrik
            col1.metric("Harga Saat Ini", stock_data['Close'].iloc[-1])
            col2.metric("Perubahan Harian", daily_change_str)
            col3.metric("Volume", stock_data['Volume'].iloc[-1])

        # **Tab 2: Grafik**
        with tabs[1]:
            st.markdown("<h2 style='color: #4CAF50;'>Grafik Wall</h2>", unsafe_allow_html=True)
            
            # Debug: Tampilkan beberapa data untuk memastikan ada yang ditampilkan
            st.write(stock_data.head())  # Tampilkan 5 baris pertama untuk memeriksa data
            
            if not stock_data.empty and len(stock_data) > 1:
                fig = go.Figure(data=[
                    go.Bar(
                        x=stock_data.index,
                        y=stock_data['Close'],  # Menggunakan harga penutupan untuk grafik batang
                        marker_color='blue'  # Warna batang
                    )
                ])
                fig.update_layout(
                    title=f'Grafik Wall Saham {symbol}',
                    yaxis_title='Harga',
                    xaxis_title='Tanggal',
                    height=600,
                    template="plotly_dark"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("Tidak ada data yang cukup untuk ditampilkan dalam grafik.")

        # **Tab 3: Hasil Realisasi**
        with tabs[2]:
            st.markdown("<h2 style='color: #4CAF50;'>Hasil Realisasi Prediksi</h2>", unsafe_allow_html=True)
            realizations = []
            for index, row in stock_data.iterrows():
                high = row['High']
                low = row['Low']
                date = index.date() + timedelta(days=1)  # Tambahkan satu hari
                current_price = row['Close']

                # Menghitung persentase perubahan harga
                if entry_price != 0:
                    price_change_percent = ((current_price - entry_price) / entry_price) * 100
                else:
                    price_change_percent = 0

                result = "❗ Belum mencapai target atau stop-loss"
                low_value = float(low)  # Ambil nilai float
                high_value = float(high)  # Ambil nilai float

                if low_value < stop_loss:
                    result = f"⚠️ Stop-loss tercapai dengan harga {low_value}"
                if high_value >= target_price:
                    result = f"✅ Target tercapai dengan harga {high_value}"

                realizations.append({
                    "Tanggal": date,
                    "Hasil": result,
                    "Harga Entry": float(entry_price),
                    "Harga Sekarang": float(current_price),
                    "Persentase Perubahan": "{:.2f}%".format(float(price_change_percent))  # Memastikan format ke string
                })
                
            result_df = pd.DataFrame(realizations)
            csv_filename = autosave_to_csv(result_df)
            st.table(result_df)
            csv_data = result_df.to_csv(index=False)
            st.download_button(
                label="Download Hasil Realisasi CSV",
                data=csv_data,
                file_name='hasil_realisasi.csv',
                mime='text/csv'
            )

# Footer dengan informasi
st.markdown("<br><hr><div style='text-align: center;'>© 2024 Dashboard Saham Interaktif</div>", unsafe_allow_html=True)