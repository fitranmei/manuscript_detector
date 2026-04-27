/* Builds the IEEE two-column Word manuscript from structured content.
 *
 * Output: manuscript.docx in the project root.
 *
 * Layout decisions (approximating the IEEE conference template):
 *   - US Letter page, margins 0.75" top/bottom, 0.625" left/right.
 *   - Section 1 (single column): title, authors, affiliation.
 *   - Section 2 (continuous, two columns): abstract, index terms, body,
 *     references. Column gap 0.17" (roughly 240 DXA).
 *   - Times New Roman throughout. Body 10pt, section heading 10pt bold
 *     small-caps, subsection 10pt italic, caption 8pt.
 */

const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun,
  AlignmentType, PageOrientation, SectionType,
  HeadingLevel, LevelFormat, LineRuleType,
  BorderStyle, TabStopType,
  Table, TableRow, TableCell, WidthType, ShadingType,
} = require("docx");

const FIG = (name) =>
  fs.readFileSync(path.join(__dirname, "figures", name));

// ---------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------

const font = "Times New Roman";

function p(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [new TextRun({ text, font, size: opts.size ?? 20 })];
  return new Paragraph({
    alignment: opts.align ?? AlignmentType.JUSTIFIED,
    spacing: { after: opts.after ?? 0, line: 240, lineRule: LineRuleType.AUTO },
    indent: opts.indent ?? (opts.noIndent ? undefined : { firstLine: 180 }),
    children: runs,
  });
}

function body(text, opts = {}) {
  // Plain justified body paragraph, first-line indent.
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 60, line: 240, lineRule: LineRuleType.AUTO },
    indent: opts.noIndent ? undefined : { firstLine: 180 },
    children: [new TextRun({ text, font, size: 20 })],
  });
}

function sectionHeading(label) {
  // IEEE section headings: centered, 10pt bold small-caps, Roman numeral.
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 120, line: 240 },
    children: [new TextRun({ text: label, font, size: 20, bold: true, smallCaps: true })],
  });
}

function subHeading(label) {
  // IEEE subsection headings: italic, left-aligned, 10pt.
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { before: 120, after: 60 },
    children: [new TextRun({ text: label, font, size: 20, italics: true })],
  });
}

function abstractPara(intro, rest) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 80, line: 240 },
    children: [
      new TextRun({ text: intro, font, size: 18, bold: true, italics: true }),
      new TextRun({ text: rest, font, size: 18, italics: true }),
    ],
  });
}

function keywordsPara(intro, rest) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 160, line: 240 },
    children: [
      new TextRun({ text: intro, font, size: 18, bold: true, italics: true }),
      new TextRun({ text: rest, font, size: 18, italics: true }),
    ],
  });
}

function figureImage(filename, caption, { widthPx = 340 } = {}) {
  const data = FIG(filename);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 40 },
      children: [
        new ImageRun({
          type: "png",
          data,
          transformation: { width: widthPx, height: Math.round(widthPx * 0.5) },
          altText: { title: caption, description: caption, name: filename },
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 0, after: 140 },
      children: [new TextRun({ text: caption, font, size: 16 })],
    }),
  ];
}

function figureImageSquare(filename, caption, { widthPx = 260 } = {}) {
  const data = FIG(filename);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 40 },
      children: [
        new ImageRun({
          type: "png",
          data,
          transformation: { width: widthPx, height: Math.round(widthPx * 0.82) },
          altText: { title: caption, description: caption, name: filename },
        }),
      ],
    }),
    new Paragraph({
      alignment: AlignmentType.JUSTIFIED,
      spacing: { before: 0, after: 140 },
      children: [new TextRun({ text: caption, font, size: 16 })],
    }),
  ];
}

function eq(num, text) {
  // Display equation as a tab-separated line: centered equation, right (n)
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 80, after: 80 },
    tabStops: [{ type: TabStopType.RIGHT, position: 5040 }],
    children: [
      new TextRun({ text, font, size: 20, italics: true }),
      new TextRun({ text: `\t(${num})`, font, size: 20 }),
    ],
  });
}

function ref(n, text) {
  return new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 40, line: 220 },
    indent: { left: 240, hanging: 240 },
    children: [new TextRun({ text: `[${n}]  ${text}`, font, size: 16 })],
  });
}

// ---------------------------------------------------------------------
// Header section (single column)
// ---------------------------------------------------------------------

const title = new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 120 },
  children: [
    new TextRun({
      text: "Sistem Deteksi Pelanggaran Lawan Arah Kendaraan Menggunakan YOLO26 dan Analisis Vektor Pergerakan Berbasis Tracking Objek",
      font, size: 44, bold: true,
    }),
  ],
});

const authors = new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 40 },
  children: [new TextRun({ text: "Nama Penulis Pertama, Nama Penulis Kedua", font, size: 22 })],
});

const affil = new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 160 },
  children: [
    new TextRun({
      text: "Program Studi Teknik Informatika, Universitas [•]\npenulis1@email.ac.id, penulis2@email.ac.id",
      font, size: 20, italics: true,
      break: 0,
    }),
  ],
});

const affilLine2 = new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 40 },
  children: [new TextRun({ text: "Program Studi Teknik Informatika, Universitas [•]", font, size: 20, italics: true })],
});

const affilLine3 = new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 200 },
  children: [new TextRun({ text: "penulis1@email.ac.id, penulis2@email.ac.id", font, size: 20, italics: true })],
});

const headerChildren = [title, authors, affilLine2, affilLine3];

// ---------------------------------------------------------------------
// Body section (two columns)
// ---------------------------------------------------------------------

const bodyChildren = [
  // ----- Abstract + Index Terms -----
  abstractPara(
    "Abstrak—",
    "Pelanggaran lawan arah merupakan salah satu perilaku berkendara paling berisiko di jalan perkotaan, namun pemantauannya masih sangat bergantung pada pengamatan manual terhadap rekaman CCTV. Sebagian besar sistem pemantauan berbasis computer vision yang ada saat ini berhenti pada tahap deteksi objek: kendaraan dikenali dengan akurat, tetapi arah pergerakannya tidak dianalisis secara kuantitatif. Penelitian ini mengusulkan pipeline deteksi pelanggaran lawan arah yang memadukan detektor objek modern YOLO26 dengan pelacakan objek multi-target (BoT-SORT/ByteTrack) dan analisis vektor pergerakan berbasis centroid. Untuk setiap kendaraan yang terlacak, arah pergerakan diestimasi dari perpindahan centroid pada jendela frame yang dihaluskan, lalu dibandingkan dengan vektor arah referensi jalur. Kendaraan diklasifikasikan melanggar hanya apabila sudut antara vektor gerak dan vektor referensi melampaui ambang (default 135°) dan bertahan lebih lama dari durasi minimum (default 0,6 detik). Mekanisme histeresis ini dirancang untuk menekan false positive dari kendaraan berhenti, berbelok, atau sedikit menyimpang. Makalah ini memaparkan arsitektur sistem, justifikasi matematis, konfigurasi eksperimen, serta rencana evaluasi kuantitatif terhadap baseline yang hanya mengandalkan deteksi objek. Implementasi referensi tersedia dalam Python dengan biaya komputasi yang sesuai untuk pemrosesan real-time pada CCTV jalan raya."
  ),
  keywordsPara(
    "Kata Kunci—",
    "YOLO26; deteksi kendaraan; object tracking; BoT-SORT; ByteTrack; motion vector; pelanggaran lawan arah; computer vision lalu lintas."
  ),

  // ----- I. PENDAHULUAN -----
  sectionHeading("I. Pendahuluan"),
  body("Kepadatan lalu lintas perkotaan dan keterbatasan sumber daya manusia menjadikan pemantauan pelanggaran lalu lintas secara manual pada rekaman kamera CCTV semakin tidak praktis. Salah satu bentuk pelanggaran yang paling berbahaya namun sulit ditangkap tepat waktu adalah mengemudi berlawanan dengan arah jalur yang diizinkan. Insiden semacam ini berkontribusi terhadap kecelakaan frontal dengan tingkat fatalitas tinggi, sehingga deteksi otomatis yang cepat, akurat, dan stabil memiliki nilai praktis yang besar."),
  body("Perkembangan detektor objek berbasis deep learning dalam beberapa tahun terakhir, khususnya keluarga YOLO, telah memungkinkan pengenalan kendaraan pada rekaman lalu lintas secara real-time dengan akurasi yang kompetitif. YOLO26, varian terbaru yang dirilis Ultralytics pada awal 2026, memperkenalkan sejumlah penyempurnaan arsitektural, di antaranya penghapusan Distribution Focal Loss (DFL), inferensi end-to-end tanpa NMS, loss function ProgLoss+STAL, serta optimizer hybrid MuSGD yang bersama-sama menghasilkan laju inferensi CPU hingga 43% lebih cepat dibandingkan YOLO11 pada ukuran model yang setara [1], [2]."),
  body("Meskipun demikian, pengembangan sistem deteksi pelanggaran arah tidak cukup hanya dengan meningkatkan kualitas detektor. Berbagai studi sebelumnya [3], [4] menunjukkan bahwa sistem yang hanya berhenti pada deteksi cenderung mengalami dua kelemahan utama: (i) kendaraan yang terdeteksi namun tidak dilacak identitasnya lintas frame sulit untuk diinterpretasikan arah geraknya, dan (ii) sistem sering gagal membedakan antara pelanggaran sesungguhnya dengan pergerakan transien seperti berbelok, mundur untuk parkir, atau tracking yang pecah. Penambahan modul tracking memang mulai diadopsi [5], namun informasi pergerakan yang dihasilkan tracker sering tidak dieksploitasi secara kuantitatif; vektor perpindahan centroid, misalnya, jarang dibandingkan secara eksplisit terhadap vektor referensi jalur."),
  body("Berdasarkan celah tersebut, penelitian ini mengusulkan suatu pipeline deteksi pelanggaran lawan arah yang mengintegrasikan deteksi objek YOLO26 dengan pelacakan multi-target dan analisis vektor pergerakan berbasis sudut. Kontribusi utama makalah ini adalah:"),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    numbering: { reference: "enum-contrib", level: 0 },
    spacing: { after: 40, line: 240 },
    children: [new TextRun({ text: "Rancangan pipeline end-to-end yang memanfaatkan modul tracking bawaan YOLO26 (BoT-SORT/ByteTrack) untuk menjaga identitas kendaraan lintas frame tanpa menambah kompleksitas pasca-pemrosesan.", font, size: 20 })],
  }),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    numbering: { reference: "enum-contrib", level: 0 },
    spacing: { after: 40, line: 240 },
    children: [new TextRun({ text: "Perumusan matematis yang sederhana namun efektif untuk menurunkan vektor gerak dari jejak centroid, menghitung sudut terhadap arah referensi jalur, dan menghasilkan keputusan pelanggaran.", font, size: 20 })],
  }),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    numbering: { reference: "enum-contrib", level: 0 },
    spacing: { after: 40, line: 240 },
    children: [new TextRun({ text: "Mekanisme histeresis berbasis durasi (state machine tiga-keadaan) yang menekan false positive akibat kendaraan berhenti, berbelok, maupun ganguan sesaat dari tracker.", font, size: 20 })],
  }),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    numbering: { reference: "enum-contrib", level: 0 },
    spacing: { after: 80, line: 240 },
    children: [new TextRun({ text: "Protokol evaluasi lengkap—mencakup dataset, metrik, baseline, dan skenario ablasi—yang memungkinkan reproduksi dan pembandingan di kemudian hari.", font, size: 20 })],
  }),
  body("Sisa makalah ini disusun sebagai berikut. Bab II membahas pekerjaan terkait. Bab III memaparkan metode yang diusulkan, mencakup arsitektur sistem, formulasi vektor pergerakan, dan logika pelanggaran. Bab IV mendeskripsikan perancangan eksperimen. Bab V menyajikan hasil yang diharapkan beserta analisis awal, dan Bab VI menutup dengan kesimpulan serta rencana pengembangan selanjutnya."),

  // ----- II. KAJIAN PUSTAKA -----
  sectionHeading("II. Kajian Pustaka"),
  subHeading("A. Evolusi Detektor YOLO untuk Lalu Lintas"),
  body("YOLO (You Only Look Once) yang diperkenalkan oleh Redmon dkk. [8] menandai pergeseran paradigma dari pendekatan detektor dua tahap menjadi regresi bounding box satu tahap yang jauh lebih cepat. Sejak itu, varian YOLO terus berkembang dengan penyempurnaan backbone, neck, dan head, serta strategi training yang lebih modern. YOLO26 merupakan iterasi terbaru yang fokus pada efisiensi perangkat tepi: penghapusan DFL menyederhanakan ekspor ke berbagai runtime; head one-to-one menghapus NMS pasca-pemrosesan; loss ProgLoss dengan komponen STAL meningkatkan akurasi terutama pada objek kecil; dan optimizer MuSGD yang menggabungkan SGD dengan Muon mempercepat konvergensi [1], [2], [10]. Pada COCO val, YOLO26-n melaporkan mAP@50-95 sebesar 40,9 dengan inferensi ONNX CPU 38,9 ms, sedangkan YOLO26-s melaporkan 48,6 dengan 87,2 ms [1]. Karakteristik ini menjadikan YOLO26 kandidat yang tepat untuk sistem CCTV yang dituntut bekerja secara real-time dengan latency rendah."),

  subHeading("B. Deteksi Pelanggaran Lawan Arah"),
  body("Rahman dkk. [3] memperkenalkan pipeline tiga tahap—deteksi YOLO, tracking centroid berbasis region of interest, dan pengujian arah lintasan—untuk mendeteksi pelanggaran lawan arah pada rekaman CCTV jalan. Kendati efektif pada kondisi yang relatif bersih, pendekatan tersebut mengandalkan aturan ambang perpindahan sederhana sehingga rentan terhadap jitter deteksi dan mis-tracking. Wee dkk. [4] mengombinasikan YOLOv4 dengan optical flow Lucas–Kanade untuk memperoleh estimasi arah. Pendekatan ini menangkap aliran piksel yang kaya, tetapi biaya komputasinya relatif tinggi dan perlu penyelarasan ROI yang cermat. Studi lain seperti You dkk. [5] berfokus pada peningkatan kualitas tracking (CDS-YOLOv8 + ByteTrack terkalibrasi); meskipun memperbaiki stabilitas identitas, logika pelanggaran spesifik tidak menjadi fokus utama. Celah yang konsisten di seluruh literatur adalah minimnya analisis vektor gerak terhadap vektor referensi jalur yang eksplisit dan bersifat kuantitatif."),

  subHeading("C. Multi-Object Tracking"),
  body("ByteTrack [6] menunjukkan bahwa memanfaatkan deteksi dengan skor rendah dalam tahap asosiasi kedua dapat menjaga identitas objek pada kondisi oklusi; BoT-SORT [7] memperpanjang ide tersebut dengan kompensasi gerakan kamera serta re-identifikasi untuk pelacakan yang lebih tangguh pada konteks multi-kamera. Pustaka Ultralytics memaketkan kedua tracker tersebut langsung di dalam metode .track(), sehingga integrasinya dengan YOLO26 tidak memerlukan implementasi eksternal. Penelitian ini memanfaatkan integrasi tersebut, sekaligus memperlihatkan bahwa modul tracking off-the-shelf—jika dipadukan dengan analisis vektor yang terstruktur—sudah mencukupi untuk kasus pelanggaran lawan arah."),

  // ----- III. METODE YANG DIUSULKAN -----
  sectionHeading("III. Metode yang Diusulkan"),
  subHeading("A. Arsitektur Sistem"),
  body("Gambar 1 memperlihatkan arsitektur pipeline yang diusulkan. Setiap frame video CCTV diproses secara berurutan melalui enam tahap: (1) inferensi YOLO26 untuk memperoleh bounding box kendaraan, (2) asosiasi lintas-frame oleh BoT-SORT/ByteTrack yang menghasilkan identitas unik per track, (3) estimasi vektor pergerakan berbasis centroid, (4) pemetaan posisi kendaraan ke jalur berdasarkan konfigurasi polygon, (5) uji sudut antara vektor pergerakan dan vektor referensi jalur, dan (6) state machine pelanggaran yang hanya menandai kendaraan setelah kondisi lawan arah bertahan dalam durasi tertentu. Keluaran pipeline adalah video teranotasi serta berkas CSV yang berisi catatan setiap pelanggaran."),
  ...figureImage("fig1_pipeline.png", "Gambar 1. Diagram blok pipeline deteksi pelanggaran lawan arah yang diusulkan."),

  subHeading("B. Deteksi Kendaraan dengan YOLO26"),
  body("Pipeline memanfaatkan varian YOLO26-n (model nano) sebagai pilihan default karena mampu mempertahankan laju inferensi tinggi pada CPU sekaligus mencapai akurasi yang memadai pada kelas kendaraan umum. Filter kelas dibatasi pada indeks kelas kendaraan dari dataset COCO, yaitu {2: car, 3: motorcycle, 5: bus, 7: truck}, sehingga objek non-kendaraan tidak ikut masuk ke tahap tracking. Parameter default yang digunakan mengikuti rekomendasi Ultralytics [1]: ukuran input 640×640, threshold confidence 0,35, dan threshold IoU NMS 0,5 (walaupun YOLO26 bersifat NMS-free pada head end-to-end, IoU tetap relevan untuk filter redundansi pada mode tertentu)."),

  subHeading("C. Multi-Object Tracking"),
  body("Modul tracking diaktifkan melalui panggilan tunggal model.track(source, persist=True, tracker=\"bytetrack.yaml\"). Parameter persist=True memberi isyarat kepada Ultralytics agar mempertahankan state tracker antar pemanggilan, sehingga setiap panggilan frame lanjutan dapat mempertahankan ID kendaraan yang sama. Identitas track ini kemudian menjadi kunci asosiasi untuk seluruh analisis selanjutnya: jejak centroid, riwayat sudut, dan state pelanggaran seluruhnya diindeks berdasarkan track_id."),

  subHeading("D. Analisis Vektor Pergerakan"),
  body("Untuk setiap kendaraan yang terlacak, pipeline menghitung bottom-center dari bounding box sebagai estimator kasar titik kontak kendaraan dengan permukaan jalan. Pilihan bottom-center—alih-alih centroid geometris—mengurangi pengaruh variasi ukuran bounding box akibat perubahan sudut pandang. Titik tersebut disimpan dalam ring buffer berukuran W=10 frame (default). Pada setiap frame, vektor gerak diestimasi sebagai selisih antara titik terbaru dan titik tertua dalam buffer:"),
  eq(1, "v_motion = p_t  −  p_{t−W+1}"),
  body("Pendekatan selisih end-to-end ini bekerja sebagai smoothing window: jitter deteksi satu-frame tidak merusak estimasi arah. Jika magnitudo vektor lebih kecil daripada ambang ||v_motion|| < d_min (default 4 piksel), kendaraan dianggap diam dan tidak dievaluasi terhadap ambang sudut—kendaraan yang berhenti sejenak di lampu merah, misalnya, tidak pernah memasuki state lawan arah."),

  subHeading("E. Klasifikasi Pelanggaran Lawan Arah"),
  body("Konfigurasi pengguna mendefinisikan sejumlah jalur berbentuk polygon pada ruang piksel kamera, masing-masing disertai vektor unit v_ref yang merepresentasikan arah legal. Saat bottom-center suatu kendaraan berada di dalam polygon tertentu, sudut antara vektor geraknya dan vektor referensi jalur dihitung melalui persamaan standar:"),
  eq(2, "θ = arccos( (v_motion · v_ref) / ( ||v_motion|| · ||v_ref|| ) )"),
  body("Kendaraan dinyatakan OPPOSING pada frame tersebut bila θ ≥ θ_th (default 135°), yang setara dengan kerucut toleransi ±45° di sekitar arah berlawanan. Gambar 2 memvisualisasikan geometri sudut ini."),
  ...figureImageSquare("fig2_angle_geometry.png", "Gambar 2. Sudut antara vektor gerak kendaraan dan arah referensi jalur."),
  body("Keputusan akhir pelanggaran dihasilkan oleh state machine tiga-keadaan (NORMAL → OPPOSING → VIOLATING) yang diperlihatkan pada Gambar 3. State NORMAL berpindah ke OPPOSING ketika θ ≥ θ_th pada satu frame. State OPPOSING naik ke VIOLATING hanya bila streak opposing berlangsung paling sedikit N_min frame berturut-turut (default 15 frame, setara 0,6 detik pada 25 FPS). Untuk mentoleransi glitch tracker, sebuah reset_tolerance τ (default 3 frame) menunda pembatalan streak ketika muncul frame non-opposing sesaat. Setelah masuk ke VIOLATING, state dipertahankan hingga track keluar dari frame, agar kendaraan yang sudah divonis melanggar tidak di-‘unflag’ saat memperbaiki arah; hal ini konsisten dengan perilaku penegakan hukum lalu lintas."),
  ...figureImage("fig3_state_machine.png", "Gambar 3. State machine pelanggaran dengan histeresis berbasis durasi."),
  body("Kombinasi ambang sudut yang luas (135°) dan syarat durasi ini penting karena dua hal. Pertama, kerucut toleransi ±45° mengakomodasi kendaraan yang sedang berpindah lajur tanpa benar-benar melawan arah. Kedua, ambang durasi menyaring transien pendek seperti mundur parkir dan belokan U yang sebagian kecil segmennya tampak opposing."),

  // ----- IV. PERANCANGAN EKSPERIMEN -----
  sectionHeading("IV. Perancangan Eksperimen"),
  subHeading("A. Dataset dan Skenario Pengujian"),
  body("Evaluasi akan dilakukan pada tiga tipe data. (i) Rekaman CCTV jalan dua arah yang dikumpulkan sendiri (minimum 4 jam total, minimal 30 kejadian pelanggaran lawan arah yang dianotasi manual) untuk mengukur kinerja end-to-end. (ii) Rekaman publik lalu lintas perkotaan yang tersedia terbuka (mis. UA-DETRAC, MIO-TCD) sebagai sumber kendaraan non-pelanggar untuk mengukur false positive rate. (iii) Sekuens sintetis yang disusun dari klip-klip pendek berisi skenario ambigu (kendaraan parkir, memutar balik, belok di persimpangan) untuk mengevaluasi robustness ambang histeresis. Setiap pelanggaran dianotasi dalam bentuk first_frame, last_frame, lane sesuai kontrak format pada evaluate.py."),

  subHeading("B. Lingkungan Implementasi"),
  body("Implementasi referensi ditulis dalam Python dan menggunakan pustaka Ultralytics v8.3.200+, OpenCV 4.9, serta NumPy 1.26. Pengujian direncanakan pada dua konfigurasi perangkat: (a) GPU NVIDIA RTX 3060 (12 GB) untuk menyimulasikan server pemantauan; dan (b) CPU Intel Core i5-12400 untuk merepresentasikan deployment edge tanpa akselerator. Latensi per-frame, laju inferensi rata-rata (FPS), dan penggunaan memori akan dicatat untuk setiap varian YOLO26-n/s/m."),

  subHeading("C. Metrik Evaluasi"),
  body("Empat metrik utama dilaporkan. Precision, recall, dan F1-score dihitung terhadap pasangan (track_id, lane) dengan toleransi temporal Δ=30 frame antara first_frame ground-truth dan flagged_frame prediksi. Detection latency dihitung sebagai selisih frame antara timbulnya pelanggaran dalam ground-truth dan pertama kalinya state naik ke VIOLATING—ukuran praktis yang menunjukkan seberapa cepat sistem akan menghasilkan alarm. Throughput diukur dalam FPS end-to-end termasuk rendering overlay."),

  subHeading("D. Baseline Perbandingan"),
  body("Empat baseline akan dibandingkan terhadap metode yang diusulkan: (B1) YOLO26-only: kendaraan yang terdeteksi pada jalur yang salah berdasarkan lookup polygon saja, tanpa informasi arah; (B2) YOLO26 + tracking + aturan perpindahan centroid sederhana mengikuti [3]; (B3) YOLO26 + optical flow Lucas–Kanade pada ROI jalur, mengikuti [4]; (B4) metode penuh yang diusulkan. Ablasi dilakukan dengan menonaktifkan salah satu komponen: (A1) tanpa smoothing window (W=1), (A2) tanpa state machine (keputusan instan), (A3) tanpa ambang min_displacement (semua track dievaluasi)."),
  ...figureImage("fig4_lane_example.png", "Gambar 4. Ilustrasi frame teranotasi yang memperlihatkan polygon jalur, vektor referensi (hijau), dan pelanggaran lawan arah (merah)."),

  // ----- V. HASIL YANG DIHARAPKAN -----
  sectionHeading("V. Hasil yang Diharapkan dan Pembahasan Awal"),
  body("Bagian ini merumuskan hipotesis hasil yang akan diuji ketika dataset telah terkumpul dan dianotasi. Hipotesis disusun berbasis karakteristik arsitektural dan parameter default yang telah ditetapkan."),
  subHeading("A. Hipotesis Kinerja Deteksi"),
  body("Baseline B1 diperkirakan menghasilkan recall tinggi namun precision rendah karena kendaraan yang secara sah melintas di jalur terdekat selama perpindahan lajur akan terflag sebagai pelanggaran. Baseline B2 diharapkan memperbaiki precision namun masih menderita dari jitter centroid. Metode B4 yang diusulkan diharapkan mencapai F1-score paling tinggi dengan recall ≥ 0,90 dan precision ≥ 0,90 pada dataset primer. Perbaikan terbesar diharapkan pada false positive rate: skenario mundur untuk parkir dan belokan U seharusnya ditolak sepenuhnya oleh kombinasi ambang sudut 135° dan durasi 15 frame."),
  subHeading("B. Hipotesis Latensi Deteksi"),
  body("Dengan N_min=15 frame pada 25 FPS, latensi deteksi teoritis berada di sekitar 0,6 detik setelah kendaraan mulai bergerak lawan arah. Nilai ini dianggap dapat diterima untuk alarm operator dan jauh lebih cepat dari pemantauan manual."),
  subHeading("C. Hipotesis Throughput"),
  body("Untuk YOLO26-n pada resolusi 640 dengan GPU RTX 3060, throughput end-to-end (termasuk tracking, analisis vektor, dan rendering) diperkirakan mencapai ≥ 60 FPS. Pada CPU, throughput varian nano diperkirakan ≥ 20 FPS, masih memenuhi batas kasar real-time untuk CCTV 15 FPS."),
  subHeading("D. Keterbatasan yang Diantisipasi"),
  body("Sistem saat ini mengasumsikan kamera tetap (stasioner) dan kalibrasi jalur yang dilakukan manual. Kondisi malam hari yang ekstrem atau hujan lebat dapat menurunkan akurasi deteksi dan—secara tidak langsung—akurasi estimasi vektor karena tracker lebih sering kehilangan identitas. Homografi piksel-ke-dunia juga tidak dilakukan dalam versi referensi, sehingga ambang kecepatan (yang bergantung pada satuan piksel) perlu disesuaikan per kamera."),

  // ----- VI. KESIMPULAN -----
  sectionHeading("VI. Kesimpulan dan Rencana Kerja Selanjutnya"),
  body("Makalah ini merumuskan dan mengimplementasikan pipeline deteksi pelanggaran lawan arah yang menggabungkan detektor YOLO26, tracking BoT-SORT/ByteTrack, dan analisis vektor pergerakan berbasis sudut. Dengan state machine tiga-keadaan dan kriteria durasi minimum, sistem dirancang agar hanya menandai pelanggaran yang memenuhi kriteria sudut dan temporal secara bersamaan, sehingga kendaraan berhenti, berbelok, dan gangguan tracking transien tidak menghasilkan alarm palsu. Rencana kerja selanjutnya mencakup: (i) pengumpulan dan anotasi dataset primer, (ii) evaluasi kuantitatif lengkap terhadap empat baseline dan tiga ablasi, (iii) integrasi homografi piksel-ke-dunia untuk menetapkan ambang kecepatan yang bermakna fisik, dan (iv) eksplorasi varian YOLO26-s/m untuk sensor dengan beban tinggi. Implementasi referensi dipublikasikan bersama makalah ini untuk memudahkan reproduksi dan pembandingan."),

  // ----- REFERENSI -----
  sectionHeading("Referensi"),
  ref(1, "Ultralytics, “Ultralytics YOLO26,” Ultralytics Documentation, 2026. [Online]. Available: https://docs.ultralytics.com/models/yolo26/."),
  ref(2, "R. Sapkota et al., “Ultralytics YOLO Evolution: An Overview of YOLO26, YOLO11, YOLOv8 and YOLOv5 Object Detectors for Computer Vision and Pattern Recognition,” arXiv preprint arXiv:2510.09653, 2026."),
  ref(3, "Z. Rahman, A. M. Ami, and M. A. Ullah, “A Real-Time Wrong-Way Vehicle Detection Based on YOLO and Centroid Tracking,” in Proc. IEEE Region 10 Symp. (TENSYMP), 2020, pp. 916–920."),
  ref(4, "M. C. Wee, K. Connie, and K. M. Goh, “Wrong-Way Driving Detection for Enhanced Road Safety using Computer Vision and Machine Learning Techniques,” Int. J. Adv. Sci. Eng. Inf. Technol., vol. 14, no. 6, pp. 2100–2109, Dec. 2024."),
  ref(5, "S. You, Y. Chen, X. Xiao, Y. Sun, and X. Li, “Multi-Object Vehicle Detection and Tracking Algorithm Based on Improved YOLOv8 and ByteTrack,” Electronics, vol. 13, no. 15, Art. 3033, Aug. 2024."),
  ref(6, "Y. Zhang, P. Sun, Y. Jiang, D. Yu, F. Weng, Z. Yuan, P. Luo, W. Liu, and X. Wang, “ByteTrack: Multi-Object Tracking by Associating Every Detection Box,” in Proc. European Conf. Comput. Vis. (ECCV), 2022, pp. 1–21."),
  ref(7, "N. Aharon, R. Orfaig, and B.-Z. Bobrovsky, “BoT-SORT: Robust Associations Multi-Pedestrian Tracking,” arXiv preprint arXiv:2206.14651, 2022."),
  ref(8, "J. Redmon, S. Divvala, R. Girshick, and A. Farhadi, “You Only Look Once: Unified, Real-Time Object Detection,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), 2016, pp. 779–788."),
  ref(9, "T.-Y. Lin et al., “Microsoft COCO: Common Objects in Context,” in Proc. European Conf. Comput. Vis. (ECCV), 2014, pp. 740–755."),
  ref(10, "R. Khanam and M. Hussain, “YOLO26: Key Architectural Enhancements and Performance Benchmarking for Real-Time Object Detection,” arXiv preprint arXiv:2509.25164, 2026."),
];

// ---------------------------------------------------------------------
// Document
// ---------------------------------------------------------------------

const doc = new Document({
  creator: "Claude (auto-generated draft)",
  title: "Sistem Deteksi Pelanggaran Lawan Arah Kendaraan",
  styles: {
    default: { document: { run: { font, size: 20 } } },
  },
  numbering: {
    config: [{
      reference: "enum-contrib",
      levels: [{
        level: 0, format: LevelFormat.DECIMAL, text: "%1)",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 420, hanging: 240 } } },
      }],
    }],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 }, // US Letter
          margin: { top: 1080, bottom: 1440, left: 900, right: 900 }, // IEEE-ish
        },
        column: { count: 1 },
      },
      children: headerChildren,
    },
    {
      properties: {
        type: SectionType.CONTINUOUS,
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1080, bottom: 1440, left: 900, right: 900 },
        },
        column: { count: 2, space: 360, equalWidth: true, separate: false },
      },
      children: bodyChildren,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(path.join(__dirname, "manuscript.docx"), buf);
  console.log("Wrote manuscript.docx (" + buf.length + " bytes)");
});
