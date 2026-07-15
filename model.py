"""
model.py — PyTorch LSTM for 7-day price prediction.
Trains on historical prices and forecasts the next week.
"""

from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler

MODEL_PATH = Path(__file__).parent / "price_model.pt"

SEQ_LEN = 10       # look-back window
PRED_DAYS = 7      # forecast horizon
HIDDEN_SIZE = 64
NUM_LAYERS = 2
EPOCHS = 80
LEARNING_RATE = 0.01
MIN_DATA_POINTS = 20


class PriceLSTM(nn.Module):
    """LSTM network that maps a price sequence to a 7-day forecast."""

    def __init__(self, input_size=1, hidden_size=HIDDEN_SIZE, num_layers=NUM_LAYERS, output_size=PRED_DAYS):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # x shape: (batch, seq_len, 1)
        out, _ = self.lstm(x)
        # Use last time-step hidden state
        out = self.fc(out[:, -1, :])
        return out


def _generate_synthetic_prices(n: int = 40, base: float = 50000.0) -> list:
    """
    Generate a realistic-looking synthetic price series for demo / training
    when real history is too short.
    """
    rng = np.random.default_rng(42)
    prices = [base]
    for _ in range(n - 1):
        # Random walk with slight downward bias (simulates deals)
        change = rng.normal(-50, 400)
        next_price = max(prices[-1] + change, base * 0.7)
        prices.append(float(next_price))
    return prices


def _prepare_sequences(scaled: np.ndarray, seq_len: int = SEQ_LEN, pred_days: int = PRED_DAYS):
    """
    Build (X, y) sliding-window sequences for supervised LSTM training.
    X: last `seq_len` prices  |  y: next `pred_days` prices
    """
    X, y = [], []
    for i in range(len(scaled) - seq_len - pred_days + 1):
        X.append(scaled[i : i + seq_len])
        y.append(scaled[i + seq_len : i + seq_len + pred_days].flatten())
    return np.array(X), np.array(y)


def train_model(prices: list):
    """
    Train an LSTM on the given historical price list.
    If fewer than 20 points exist, pads with synthetic data for demo.
    Saves the trained weights to price_model.pt and returns (model, scaler).
    """
    try:
        price_list = list(prices) if prices else []

        if len(price_list) < MIN_DATA_POINTS:
            print(
                f"[model] Only {len(price_list)} data points — "
                "generating synthetic data for training demo."
            )
            base = float(price_list[-1]) if price_list else 50000.0
            synthetic = _generate_synthetic_prices(n=40, base=base)
            # Keep real prices at the end so recent values matter more
            price_list = synthetic[:-len(price_list)] + price_list if price_list else synthetic

        data = np.array(price_list, dtype=np.float32).reshape(-1, 1)

        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled = scaler.fit_transform(data)

        X, y = _prepare_sequences(scaled)
        if len(X) == 0:
            print("[model] Not enough sequences to train. Aborting.")
            return None, None

        X_tensor = torch.tensor(X, dtype=torch.float32)
        y_tensor = torch.tensor(y, dtype=torch.float32)

        model = PriceLSTM()
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

        model.train()
        for epoch in range(1, EPOCHS + 1):
            optimizer.zero_grad()
            output = model(X_tensor)
            loss = criterion(output, y_tensor)
            loss.backward()
            optimizer.step()
            if epoch % 20 == 0 or epoch == 1:
                print(f"[model] Epoch {epoch}/{EPOCHS} — loss: {loss.item():.6f}")

        # Persist weights + scaler params for later prediction
        torch.save(
            {
                "model_state": model.state_dict(),
                "scaler_min": scaler.min_,
                "scaler_scale": scaler.scale_,
                "data_min": scaler.data_min_,
                "data_max": scaler.data_max_,
            },
            MODEL_PATH,
        )
        print(f"[model] Model saved to {MODEL_PATH}")
        return model, scaler

    except Exception as exc:
        print(f"[model] Training failed: {exc}")
        return None, None


def _load_scaler_from_checkpoint(checkpoint) -> MinMaxScaler:
    """Rebuild a MinMaxScaler from values stored in the checkpoint."""
    scaler = MinMaxScaler(feature_range=(0, 1))
    # Minimal fit so sklearn attributes exist, then overwrite
    scaler.fit([[0.0], [1.0]])
    scaler.min_ = checkpoint["scaler_min"]
    scaler.scale_ = checkpoint["scaler_scale"]
    scaler.data_min_ = checkpoint["data_min"]
    scaler.data_max_ = checkpoint["data_max"]
    return scaler


def predict_next_7_days(prices: list) -> list:
    """
    Predict the next 7 daily prices from the latest historical series.
    Trains (or retrains) the model as needed, then returns a list of 7 floats.
    """
    try:
        price_list = list(prices) if prices else []

        # Ensure we have enough history (synthetic fallback handled in train_model)
        model, scaler = train_model(price_list)
        if model is None or scaler is None:
            print("[model] Prediction aborted — model unavailable.")
            return []

        # Use last SEQ_LEN prices; pad with synthetic if needed
        if len(price_list) < SEQ_LEN:
            base = float(price_list[-1]) if price_list else 50000.0
            pad = _generate_synthetic_prices(n=SEQ_LEN, base=base)
            seq = pad[-SEQ_LEN:]
            if price_list:
                seq = pad[-(SEQ_LEN - len(price_list)) :] + price_list
                seq = seq[-SEQ_LEN:]
        else:
            seq = price_list[-SEQ_LEN:]

        arr = np.array(seq, dtype=np.float32).reshape(-1, 1)
        scaled = scaler.transform(arr)

        x = torch.tensor(scaled, dtype=torch.float32).unsqueeze(0)  # (1, SEQ_LEN, 1)

        model.eval()
        with torch.no_grad():
            pred_scaled = model(x).numpy().flatten()

        # Inverse-transform each predicted day independently
        pred_prices = scaler.inverse_transform(pred_scaled.reshape(-1, 1)).flatten()
        result = [round(float(p), 2) for p in pred_prices]
        print(f"[model] 7-day forecast: {result}")
        return result

    except Exception as exc:
        print(f"[model] Prediction failed: {exc}")
        return []


if __name__ == "__main__":
    # Standalone test with synthetic series
    demo = _generate_synthetic_prices(30)
    print("Training on demo prices...")
    forecast = predict_next_7_days(demo)
    print("Forecast:", forecast)
