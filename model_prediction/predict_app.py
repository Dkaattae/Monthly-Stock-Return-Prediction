"""Flask API for serving machine learning predictions."""
import pandas as pd
from flask import Flask, request, jsonify
from predict import predict

app = Flask("monthly_stock_return_prediction")


@app.route("/predict", methods=["POST"])
def predict_endpoint():
    '''
    handle post request for model prediction
    '''
    new_data = request.get_json()
    new_data_df = pd.DataFrame(new_data)
    prediction = predict(new_data_df)

    columns_to_return = ["ticker", "date", "predicted_1m_return", "model_version"]
    result = prediction[columns_to_return].to_dict(orient="records")

    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9696)
