from flask import Flask, render_template, request, send_file
import pandas as pd
import io 

app = Flask(__name__)

# =========================
# FUNGSI SORT ICD
# =========================
def urut_icd(icd):
    try:
        bagian = icd.split('.')
        prefix = bagian[0]
        angka = int(bagian[1]) if len(bagian) > 1 else 0
        return (prefix, angka)
    except:
        return (icd, 0)


# =========================
# KELOMPOK UMUR 
# =========================
def kelompok_umur(umur, satuan=None):
    try:
        umur = int(umur)
    except:
        return "Tidak diketahui"

    satuan = str(satuan).lower() if satuan else "tahun"

    # JAM
    if satuan == 'jam':
        if umur < 1:
            return "<1 jam"
        else:
            return "1-23 jam"

    # HARI
    elif satuan == 'hari':
        if umur <= 7:
            return "1-7 hari"
        elif umur <= 28:
            return "8-28 hari"
        else:
            return "29 hari - <3 bulan"

    # BULAN
    elif satuan == 'bulan':
        if umur < 3:
            return "29 hari - <3 bulan"
        elif umur < 6:
            return "3 - <6 bulan"
        elif umur <= 11:
            return "6 - 11 bulan"

    # DEFAULT (TAHUN)
    if umur == 0:
        return "<1 tahun"
    elif umur <= 4:
        return "1-4 tahun"
    elif umur <= 9:
        return "5-9 tahun"
    elif umur <= 14:
        return "10-14 tahun"
    elif umur <= 19:
        return "15-19 tahun"
    elif umur <= 24:
        return "20-24 tahun"
    elif umur <= 29:
        return "25-29 tahun"
    elif umur <= 34:
        return "30-34 tahun"
    elif umur <= 39:
        return "35-39 tahun"
    elif umur <= 44:
        return "40-44 tahun"
    elif umur <= 49:
        return "45-49 tahun"
    elif umur <= 54:
        return "50-54 tahun"
    elif umur <= 59:
        return "55-59 tahun"
    elif umur <= 64:
        return "60-64 tahun"
    elif umur <= 69:
        return "65-69 tahun"
    elif umur <= 74:
        return "70-74 tahun"
    elif umur <= 79:
        return "75-79 tahun"
    elif umur <= 84:
        return "80-84 tahun"
    else:
        return ">=85 tahun"


# =========================
# ROUTE
# =========================
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['file']

        raw = pd.read_excel(file, header=None)

        header_row = None

        for i in range(len(raw)):
            baris = raw.iloc[i].astype(str).str.strip()

            if 'ICD 10' in baris.values:
                header_row = i
                break

        if header_row is None:
            return "Kolom ICD 10 tidak ditemukan"

        file.seek(0)

        df = pd.read_excel(file, header=header_row)

        # bersihin kolom
        df.columns = df.columns.str.strip()

        # normalisasi
        df['Gender'] = df['Gender'].astype(str).str.upper().str.strip()
        df['Jenis Kasus'] = df['Jenis Kasus'].astype(str).str.lower().str.strip()

        # satuan opsional
        if 'Satuan' in df.columns:
            df['Satuan'] = df['Satuan'].astype(str).str.lower().str.strip()
        else:
            df['Satuan'] = 'tahun'

        hasil = {}
   

        # =========================
        # URUTKAN ICD
        # =========================
        kode_icd = sorted(df['ICD 10'].dropna().unique(), key=urut_icd)

        urutan_umur = [
            "<1 jam","1-23 jam",
            "1-7 hari","8-28 hari","29 hari - <3 bulan",
            "3 - <6 bulan","6 - 11 bulan",
            "<1 tahun","1-4 tahun","5-9 tahun","10-14 tahun",
            "15-19 tahun","20-24 tahun","25-29 tahun",
            "30-34 tahun","35-39 tahun","40-44 tahun",
            "45-49 tahun","50-54 tahun","55-59 tahun",
            "60-64 tahun","65-69 tahun","70-74 tahun",
            "75-79 tahun","80-84 tahun",">=85 tahun"
        ]

        # =========================
        # LOOP PER ICD
        # =========================
        for kode in kode_icd:

            df_kode = df[df['ICD 10'] == kode]

            if df_kode.empty:
                continue

            # kasus baru
            df_baru = df_kode[df_kode['Jenis Kasus'].str.contains('baru', na=False)]

            if not df_baru.empty:
                df_baru = df_baru.copy()

                df_baru['kelompok_umur'] = df_baru.apply(
                    lambda x: kelompok_umur(x['Umur'], x['Satuan']),
                    axis=1
                )

                tabel = df_baru.groupby(['kelompok_umur', 'Gender']).size().unstack(fill_value=0)
            else:
                tabel = pd.DataFrame()

            # total semua
            total = df_kode.groupby('Gender').size()

            data_tabel = []

            for i, umur in enumerate(urutan_umur, start=1):

                laki = (
                    tabel.loc[umur]['L']
                    if not tabel.empty and 'L' in tabel.columns and umur in tabel.index
                    else 0
                )

                perempuan = (
                    tabel.loc[umur]['P']
                    if not tabel.empty and 'P' in tabel.columns and umur in tabel.index
                    else 0
                )

                data_tabel.append({
                    'no': i,
                    'umur': umur,
                    'laki': int(laki),
                    'perempuan': int(perempuan)
                })

            hasil[kode] = {
                'data': data_tabel,
                'jumlah_l': int(total.get('L', 0)),
                'jumlah_p': int(total.get('P', 0))
            }

        global hasil_global
        hasil_global = hasil

        return render_template('hasil.html', hasil=hasil)

    return render_template('index.html')

@app.route('/download/<kode>')
def download_excel(kode):

    data = hasil_global.get(kode)

    if not data:
        return "Data tidak ditemukan"

    # dataframe
    df_export = pd.DataFrame(data['data'])

    # rename kolom
    df_export.columns = [
        'No',
        'Golongan Umur',
        'Laki-laki',
        'Perempuan'
    ]

    # tambah jumlah pasien
    total_row = pd.DataFrame([{
        'No': '',
        'Golongan Umur': 'Jumlah Kunjungan Pasien',
        'Laki-laki': data['jumlah_l'],
        'Perempuan': data['jumlah_p']
    }])

    df_export = pd.concat([df_export, total_row], ignore_index=True)

    # simpan excel ke memory
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_export.to_excel(writer, index=False)

    output.seek(0)

    return send_file(
        output,
        download_name=f'RL51_{kode}.xlsx',
        as_attachment=True
    )    

# =========================
# RUN
# =========================
if __name__ == '__main__':
    app.run(debug=True)