import pandas as pd
import numpy as np
from sklearn.feature_extraction import DictVectorizer
import predict
from datetime import datetime

test_data = {"date":1751328000000,"ticker":"NVDA","alpha":0.0003783764,"beta":2.1460832908,
             "month_index":24,"index_avg":0.0024422721,"historical_vol":0.0153780249,
             "eom_10yr":4.24,"10yr_avg":4.3833333333,"spread":0.52,"vix_avg":18.2150001526,
             "sector":"Technology"}
new_data = pd.DataFrame([test_data])
# test prepare_features
# new_data contains all features needed, 
# data type
def test_prepare_features():
    training_data = pd.read_json('tests/unit/test.json')
    training_data['date'] = pd.to_datetime(training_data['date'])
    vectorizer = DictVectorizer(sparse=False)
    categorical = ['sector']
    numerical = ['month_index', 'index_avg', 'alpha', 'beta', 'historical_vol', 'eom_10yr',
                 '10yr_avg', 'spread', 'vix_avg']
    vectorizer.fit(training_data[numerical+categorical].to_dict(orient='records'))
    new_data_dict = new_data[numerical+categorical].to_dict(orient='records')
    expected_output = vectorizer.transform(new_data_dict)
    actual_output = predict.prepare_features(new_data, vectorizer)

    np.testing.assert_array_almost_equal(actual_output, expected_output, decimal=6)


# test prediction
def test_predict():
    actual_output = predict.predict(new_data)
    expected_output = new_data
    expected_output['predicted_1m_return'] = 0.026805
    expected_output['model_version'] = 'f085545033ee42e48ab356df6f8ef03e'
    expected_output['date'] = pd.to_datetime(expected_output['date'])
    numerical = ['month_index', 'index_avg', 'alpha', 'beta', 'historical_vol', 'eom_10yr',
                 '10yr_avg', 'spread', 'vix_avg']
    print ('actual_output is: ', actual_output.to_dict(orient='records'))
    print ('expected_output is: ', expected_output.to_dict(orient='records'))
    assert (actual_output['date'] == expected_output['date']).all()
    np.testing.assert_array_almost_equal(actual_output[numerical], 
                                         expected_output[numerical], decimal=6)
