# Backend Server - Medical Blockchain

This directory contains the Python backend server for the Medical Blockchain project. The server provides multiple critical functionalities:

- **Analytics**: Computing blockchain performance metrics (throughput, latency) via smart contract interactions
- **Biometrics Verification**: Facial recognition-based authentication using machine learning models
- **Classification**: AI-powered doctor specialization classification with hierarchical access code assignment

## Setup Instructions

Follow these steps to configure and run the analytics server locally:

### 1. Navigate to the server directory

```bash
cd server
```

### 2. Configure Environment Variables

Rename the sample environment config file and update the required fields:

```bash
mv sample_config.env config.env
```

Open `config.env` and fill in the following:

- `PRIVATE_KEY` - Private key of the Admin account
- `NETWORK_PROVIDER` - RPC URL (e.g., <http://127.0.0.1:8545> for local Hardhat)
- `CONTRACT_ABI` - ABI of the deployed Analytics contract.  
  Before adding it here, convert the ABI to a **single-line JSON string** using [this tool](https://www.text-utils.com/json-formatter/).
- `CONTRACT_ADDRESS` - Address of the deployed Analytics contract
- `GROQ_API_KEY` - Groq API key for AI-powered classification features (required for doctor specialization classification)

### 4. Run the Server

Once the configuration is complete, start the server:

```bash
python main.py
```

### 5. Save the server URL

Once the server is running, it will be accessible at a local URL (e.g., `http://127.0.0.1:5000` by default).  

Make sure to save this URL — it will be required in the frontend (`client`) for:

- Analytics logging
- Biometric verification
- Doctor specialization classification
