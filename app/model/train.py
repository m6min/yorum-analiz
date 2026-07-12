import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

CSV_DOSYASI = "data.csv"

def read_csv(dosya_adi: str) -> pd.DataFrame:
    """Yorumları ve puanlamaları içeren dosyayı okur

    Args:
        dosya_adi (str)

    Returns:
        pd.DataFrame
    """
    return pd.read_csv(dosya_adi, sep=";", encoding="utf-8")

def train(df: pd.DataFrame) -> tuple[Pipeline, pd.DataFrame, pd.DataFrame]:
    """Modeli eğitecek pipeline'ı tutar ve sonuc olarak pipeline'ı ve train/test verilerini döndürür

    Args:
        df (pd.DataFrame): _description_

    Returns:
        tuple: _description_
    """
    # Durum 2 (nötr) satırlarını almayalım:
    df_clean = df[df["Durum"] != 2]
    x = df_clean["Metin"]
    y = df_clean["Durum"]

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)
    model_pipeline = Pipeline([
        ("vectorizer", TfidfVectorizer(max_features=10000)),
        ("classifier", LogisticRegression())
    ])
    print("Model eğitiliyor..")
    model_pipeline.fit(x_train, y_train)
    return model_pipeline, x_test, y_test

def main():
    """_summary_
    """
    df = read_csv(CSV_DOSYASI)
    model_pipeline, x_test, y_test = train(df)
    model_skoru = model_pipeline.score(x_test, y_test)
    print(f"Model Başarısı: {model_skoru * 100:.2f}")
    joblib.dump(model_pipeline, "model.joblib")
    print("Model model.joblib dosyasına kaydedildi.")

if __name__=="__main__":
    main()
