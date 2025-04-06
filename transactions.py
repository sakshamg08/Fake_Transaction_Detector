import pandas as pd
import joblib
import json
from flask import Flask, request, jsonify
#from flask_cors import CORS # type: ignore
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from web3 import Web3

# 1. Load and preprocess dataset
df = pd.read_csv(r"C:\Users\Saksham\OneDrive\Desktop\AIML Lab\Mini Project\Datasets\modified_data2.csv")

features = ['Income', 'Transaction_amount']
scaler = MinMaxScaler()
df[features] = scaler.fit_transform(df[features])

X = df[features]
y = df['Fraud']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# Print model performance
print("\nConfusion Matrix:")
print(confusion_matrix(y_test, model.predict(X_test)))
print("\nClassification Report:")
print(classification_report(y_test, model.predict(X_test)))

# Save model and preprocessing tools
joblib.dump(model, 'fraud_model.pkl')
joblib.dump(scaler, 'scaler.pkl')
joblib.dump(features, 'model_columns.pkl')
print("Model, scaler, and column layout saved.")

# 2. Set up Flask app
app = Flask(__name__)
#CORS(app)  # Enable CORS if frontend is on another port

model = joblib.load("fraud_model.pkl")
scaler = joblib.load("scaler.pkl")
model_columns = joblib.load("model_columns.pkl")

# 3. Connect to Ganache
ganache_url = "http://127.0.0.1:8545"
web3 = Web3(Web3.HTTPProvider(ganache_url))

if not web3.is_connected():
    raise ConnectionError("Failed to connect to Ganache")

web3.eth.default_account = web3.eth.accounts[0]

# 4. Load smart contract
with open("build/contracts/FraudLogger.json", "r") as file:
    contract_json = json.load(file)
    contract_abi = contract_json['abi']

contract_address = "0x49c7D03f57fD8DA05FE28c34B1e1748Ec6aE412b"
contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# 5. Routes
@app.route('/')
def home():
    return "Fraud Detection API with Blockchain Logger"

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True)

        # Validate input
        required_fields = ['Income', 'Transaction_amount', 'transactionHash', 'paymentMethod']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        # Prepare and scale input
        input_df = pd.DataFrame([{col: float(data[col]) if col in ['Income', 'Transaction_amount'] else data[col]
                                  for col in model_columns}])
        input_df[model_columns] = scaler.transform(input_df[model_columns])

        # Predict
        prediction = model.predict(input_df)[0]
        result = "Fraud" if prediction == 1 else "Legit"
        response = {"prediction": result}

        # Log to blockchain if legit
        if result == "Legit":
            scaled_amount = int(float(data['Transaction_amount']) * 1e6)  # Convert to int for Solidity
            tx_hash = contract.functions.storeLog(
                data["transactionHash"],
                scaled_amount,
                data["paymentMethod"],
                result
            ).transact()

            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            response["blockchain_tx"] = tx_hash.hex()
        else:
            response["flagged"] = "Fraudulent transaction detected and not stored on blockchain."

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 6. Run the app
if __name__ == '__main__':
    app.run(debug=True)
