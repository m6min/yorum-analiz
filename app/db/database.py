import os

from dotenv import load_dotenv
from pymongo import AsyncMongoClient

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL", "Link bulunamadi")

client = AsyncMongoClient(MONGO_URL)
db = client["analiz_db"]
yorumlar_koleksiyonu = db["yorumlar"]

islem_durumlari_koleksiyonu = db["islem_durumlari"]

analiz_sonuclari_koleksiyonu = db["analiz_sonuclari"]
