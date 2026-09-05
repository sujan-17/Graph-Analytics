import os
import uuid
import shutil
import pandas as pd
from app.core.config import settings

class StorageService:
    @staticmethod
    def save_dataset_file(user_id: str, filename: str, content: bytes) -> tuple[str, str]:
        """
        Saves uploaded dataset CSV to backend storage.
        Returns (dataset_id, storage_path).
        """
        dataset_id = str(uuid.uuid4())
        user_dir = os.path.join(settings.DATASETS_DIR, user_id)
        os.makedirs(user_dir, exist_ok=True)
        
        file_path = os.path.join(user_dir, f"{dataset_id}.csv")
        with open(file_path, "wb") as f:
            f.write(content)
            
        return dataset_id, file_path

    @staticmethod
    def load_dataset_dataframe(file_path: str) -> pd.DataFrame:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found at {file_path}")
        return pd.read_csv(file_path)

storage_service = StorageService()
