# Models Directory

This directory contains trained TensorFlow/Keras models for the TensorFlow Agent.

## Directory Structure

```
models/
├── README.md
├── image_classifier.keras      # CNN model for image classification
├── regression_model.keras       # Neural network for regression tasks
├── object_detector.keras        # YOLO/Faster R-CNN for object detection
├── sentiment_analyzer.keras     # LSTM/Transformer for sentiment analysis
└── time_series_forecaster.keras # LSTM/GRU for time series forecasting
```

## Adding Your Own Models

1. Train your TensorFlow/Keras model
2. Save it in `.keras` format: `model.save("models/your_model.keras")`
3. Reference it in your query: "Predict using your_model"

## Example Use Cases

- **Image Classification**: "Classify this image as cat or dog"
- **Object Detection**: "Detect objects in this image"
- **Sentiment Analysis**: "Analyze sentiment of this review"
- **Time Series Forecasting**: "Predict train ticket discount"
- **Churn Prediction**: "Predict customer churn"
- **Disease Detection**: "Detect disease from plant leaf image"

## Model Requirements

- Saved in `.keras` format (TensorFlow 2.x)
- Compatible with TensorFlow 2.x
- Include proper input/output shapes in model metadata

## Note

If TensorFlow is not installed, the agent will return mock predictions for demonstration purposes. To use actual models:

```bash
pip install tensorflow
```
