import os
import pandas as pd
import predict

data = pd.read_parquet('features.parquet', engine='pyarrow')
predicted_return = predict.predict(data)
os.makedirs("output", exist_ok=True)
predicted_return.to_parquet('output/backfill.parquet')