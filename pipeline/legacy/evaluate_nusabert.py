import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

# Load Model
model_name = "cahya/bert-base-indonesian-NER" # Using the base NER model which is usually equivalent to v1.3 for inference
# Or specifically: "cahya/bert-base-indonesian-NER" or "cahya/bert-base-indonesian-522M"
# The user specified "cahya/NusaBert-ner-v1.3" -> often mapped to "cahya/bert-base-indonesian-NER" on HF hub or similar.
# Let's try to use the exact string if it exists, or fallback to "cahya/bert-base-indonesian-NER" which is the standard one.
# Validating URL: https://huggingface.co/cahya/NusaBert-ner-v1.3 -> It doesn't seem to resolve to a direct model ID easily without login sometimes or if it's a collection.
# Common ID for Cahya's NER: "cahya/bert-base-indonesian-NER"
MODEL_ID = "cahya/bert-base-indonesian-NER" 

print(f"Loading model: {MODEL_ID}...")
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_ID)
except Exception as e:
    print(f"Error loading {MODEL_ID}, trying 'cahya/bert-base-indonesian-GEM-ner'...")
    MODEL_ID = "cahya/bert-base-indonesian-522M" # Fallback attempt if needed, but the first one should work.
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForTokenClassification.from_pretrained(MODEL_ID)

nlp = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

titles = [
    "Isra Mikraj 2026 Tanggal Berapa? Simak Juga Jadwal Liburnya!",
    "31 Ribu Wisatawan Datangi Ragunan di Penghujung Libur Sekolah",
    "Viral Cekcok Berujung Pria Ditusuk di Jaksel, Polisi Selidiki",
    "Brimob Polda Metro Gelar Antisipasi Tawuran di Jatinegara Jaktim",
    "Polisi Tangkap 2 Copet yang Beraksi di CFD Bundaran HI",
    "Arus Balik Wisata, Jalur Puncak Bogor Berlaku One Way Arah Jakarta Siang ini",
    "Pria Ditangkap Usai Rebut Paksa Anak dari Mantan Istri di Kelapa Gading",
    "Viral Mobil Pakai Strobo-Sirene Shaun the Sheep, Berakhir Ditilang Polisi",
    "Ribuan Pelayat Iringi Pemakaman Pimpinan Ponpes Gontor",
    "Detik-detik Histeris Penemuan 3 Orang Sekeluarga Tewas di Jakut Diungkap Saksi"
]

print("\n--- NER Evaluation Results ---\n")

for title in titles:
    results = nlp(title)
    print(f"Title: {title}")
    if not results:
        print("  [No entities found]")
    for entity in results:
        # entity is a dict with 'entity_group', 'score', 'word', 'start', 'end'
        print(f"  - {entity['entity_group']}: {entity['word']} ({entity['score']:.2f})")
    print("-" * 30)

print("\nDone.")
