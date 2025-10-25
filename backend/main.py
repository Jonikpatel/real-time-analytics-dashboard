from fastapi import FastAPI
from kafka import KafkaConsumer, KafkaProducer
import pandas as pd
from sklearn.ensemble import IsolationForest
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import threading
import datetime

load_dotenv()
app = FastAPI()
producer = KafkaProducer(bootstrap_servers=[os.getenv('KAFKA_BROKER')])
consumer = KafkaConsumer('sensor-data', bootstrap_servers=[os.getenv('KAFKA_BROKER')], auto_offset_reset='earliest')
engine = create_engine(os.getenv('DATABASE_URL'))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SensorData(Base):
    __tablename__ = "sensor_data"
    id = Column(Integer, primary_key=True, index=True)
    temperature = Column(Float)
    pressure = Column(Float)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

model = IsolationForest(contamination=0.1)

@app.post("/ingest-data")
def ingest_data(data: dict):
    producer.send('sensor-data', json.dumps(data).encode('utf-8'))
    db = SessionLocal()
    db.add(SensorData(temperature=data.get('temperature'), pressure=data.get('pressure')))
    db.commit()
    db.close()
    return {"status": "Data ingested"}

@app.get("/analytics")
def get_analytics():
    db = SessionLocal()
    records = db.query(SensorData).all()
    db.close()
    df = pd.DataFrame([{'temperature': r.temperature, 'pressure': r.pressure} for r in records])
    if not df.empty:
        predictions = model.fit_predict(df)
        anomalies = sum(predictions == -1)
    else:
        anomalies = 0
    return {"total_records": len(records), "anomalies": anomalies, "data": df.to_dict() if not df.empty else {}}

# Background consumer
def consume_messages():
    for message in consumer:
        data = json.loads(message.value.decode('utf-8'))
        db = SessionLocal()
        db.add(SensorData(temperature=data.get('temperature'), pressure=data.get('pressure')))
        db.commit()
        db.close()

threading.Thread(target=consume_messages, daemon=True).start()
