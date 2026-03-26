from loguru import logger
import pandas as pd
from typing import Dict, Optional

from core.feature_builder import FeatureBuilder
from models.ml_randomforest import RandomForestModel
# Import other models like XGBoost, LSTM as they are created

class MLEngine:
    """
    Orchestrates the machine learning workflow, including feature building,
    training, and prediction.
    """
    def __init__(self, config: Dict):
        self.config = config
        self.ml_config = config.get("ml_config", {}).get("ml_config", {})
        self.feature_builder = FeatureBuilder(config)
        self.model = self._get_model()

    def _get_model(self):
        """Initializes the ML model based on the configuration."""
        model_name = self.ml_config.get("active_model", "ml_randomforest")
        model_path = self.ml_config.get("model_paths", {}).get(model_name)

        logger.info(f"Initializing ML model: {model_name}")

        if model_name == "ml_randomforest":
            # Pass hyperparameters from config to the model
            params = self.ml_config.get("training", {}).get("random_forest_params", {})
            return RandomForestModel(model_path=model_path, **params)
            
        elif model_name == "ml_xgboost":
            from models.ml_xgboost import XGBoostModel
            params = self.ml_config.get("training", {}).get("xgboost_params", {})
            return XGBoostModel(config=self.config)
            
        elif model_name == "ml_lstm":
            from models.ml_lstm import LSTMModel
            params = self.ml_config.get("training", {}).get("lstm_params", {})
            return LSTMModel(config=self.config)

        # Add logic for other models (XGBoost, etc.) here
        else:
            logger.error(f"Unsupported ML model '{model_name}' specified in config.")
            return RandomForestModel(model_path=model_path) # Fallback

    def train_model(
        self,
        price_data: pd.DataFrame,
        gann_levels: Optional[Dict],
        astro_events: Optional[pd.DataFrame]
    ):
        """
        Builds features and trains the ML model.
        """
        logger.info("--- Starting ML Model Training Workflow ---")
        # 1. Build features
        features_df = self.feature_builder.build_features(price_data, gann_levels, astro_events)

        if features_df.empty:
            logger.error("Feature building resulted in an empty DataFrame. Aborting training.")
            return

        # 2. Train model
        accuracy, report = self.model.train(features_df)

        print("\n--- Model Evaluation Report ---")
        print(f"Test Set Accuracy: {accuracy:.4f}")
        print(report)
        print("-------------------------------")
        print("MODEL PATH:", self.ml_config.get("model_paths"))
        print("ML CONFIG:", self.ml_config)
        logger.info("--- ML Model Training Workflow Finished ---")

    def get_predictions(
        self,
        price_data: pd.DataFrame,
        gann_levels: Optional[Dict],
        astro_events: Optional[pd.DataFrame]
    ) -> Optional[pd.DataFrame]:
        """
        Builds features for the latest data and returns model predictions.
        """
        logger.info("Generating ML predictions...")

        # 1. Load model
        try:
            self.model.load_model()
            if self.model.model is None:
                logger.warning("Model not available — skip prediction")
                return None

        except Exception as e:
            logger.warning(f"No model path — skipping ML ({e})")
            return None

        # Tambahan validasi FIT
        if not hasattr(self.model.model, "n_estimators"):
            logger.warning("Model not fitted — skipping ML")
            return None

        # 2. Check model availability
        if self.model is None or self.model.model is None:
            logger.warning("ML disabled — no trained model")
            return None

        # 3. Build features
        features_df = self.feature_builder.build_features(
            price_data,
            gann_levels,
            astro_events
        )

        if features_df is None or features_df.empty:
            logger.warning("No features available for ML prediction")
            return None

        # 4. Prepare input (remove target)
        X = features_df.drop(columns=['target'], errors='ignore')

        if X is None or len(X) == 0:
            logger.warning("Feature set empty after processing")
            return None

        # 5. Validate model compatibility
        if not hasattr(self.model.model, "predict"):
            logger.error("Model does not support prediction")
            return None

        # OPTIONAL: kalau model sudah pernah di-train dengan feature_names
        if hasattr(self.model.model, "feature_names_in_"):
            try:
                X = X[self.model.model.feature_names_in_]
            except Exception as e:
                logger.warning(f"Feature mismatch: {e}")
                return None

        # 6. Predict
        try:
            predictions = self.model.model.predict(X)
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None

        # 7. Convert to DataFrame
        predictions_df = pd.DataFrame(
            predictions,
            index=X.index,
            columns=["prediction"]
        )

        logger.success(f"Generated {len(predictions_df)} ML predictions")

        return predictions_df
