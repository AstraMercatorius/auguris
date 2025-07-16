import logging
import os

import numpy as np
from numpy.typing import NDArray
from pandas import DataFrame
from NNModel_lib import NNModel

TMP_DIR = "/tmp/neural-trade/models"
logger = logging.getLogger(__name__)

class InferenceEngine:
    def __init__(self) -> None:
        self.models = []
        logger.info("loading models")
    
    def __load_models(self):
        models_already_loaded = len(self.models) > 0

        if models_already_loaded:
            return

        for file in os.listdir(TMP_DIR):
            if file.endswith(".h5"):
                modelPath = os.path.join(TMP_DIR, file)
                logger.info(f"loading model {modelPath}")
                model = NNModel(0, 3)
                model.load(modelPath)
                self.models.append(model)

    async def predict(self, df: DataFrame) -> NDArray:
        self.__load_models()
        predictions = np.array([model.predict(df) for model in self.models])
        aggregated_predictions = np.apply_along_axis(lambda x: np.bincount(x).argmax(), axis=0, arr=predictions)
        return aggregated_predictions - 1
