import os

class Config:
    def __init__(self) -> None:
        self.port = int(os.getenv("PORT", 5100))
        self.nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
        self.stream_name = os.getenv("STREAM_NAME", "market-data")
        self.consumer_name = os.getenv("CONSUMER_NAME", "feature-engineering")
        self.raw_subject = os.getenv("RAW_SUBJECT", "market-data.raw.>")
        self.processed_subject = os.getenv("PROCESSESD_SUBJECT", "market-data.processed")
