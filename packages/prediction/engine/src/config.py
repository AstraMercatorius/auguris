import os

class Config:
    def __init__(self) -> None:
        self.port = int(os.getenv("PORT", 5900))
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.stream_name = os.getenv("STREAM_NAME", "prediction")
        self.model_storage = os.getenv("MODEL_STORAGE", "prediction-models")
        self.consumer_name = os.getenv("CONSUMER_NAME", "prediction-engine")
        self.raw_subject = os.getenv("RAW_SUBJECT", "market-data.processed.>")
        self.prediction_subject = os.getenv("PREDICTION_SUBJECT", "prediction")
        self.run_model_watcher = os.getenv("RUN_MODEL_WATCHER", "False").lower() in ('true', '1', 't')
