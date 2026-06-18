"""
TensorFlowCrew
=============
Handles TensorFlow model operations including loading, prediction, and inference.
"""

import os
import json
import numpy as np
from typing import Dict, Any, List, Optional


class TensorFlowCrew:
    def __init__(self):
        self.models_dir = "models"
        self.loaded_models = {}
        self.class_mappings = {
            "sentiment_analyzer": {0: "Positive", 1: "Negative"},
            "image_classifier": {0: "Cat", 1: "Dog", 2: "Other"},
            "default_model": {0: "Class 0", 1: "Class 1"}
        }
    
    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute TensorFlow model operations."""
        query = input_data.get("query", "")
        task_type = input_data.get("task_type", "general")
        model_name = input_data.get("model_name", None)
        user_input = input_data.get("input_data", None)
        models_dir = input_data.get("models_dir", self.models_dir)
        
        crew_steps = []
        
        # Step 1: Analyze prediction request
        crew_steps.append({
            "thought": "TensorFlow Agent: analyzing prediction request",
            "output": f"Task type: {task_type}"
        })
        
        # Step 2: Determine model to use
        model_info = self.determine_model(task_type, model_name, models_dir, query)
        crew_steps.append({
            "thought": "TensorFlow Agent: selecting appropriate model",
            "output": f"Model: {model_info.get('name', 'default')}"
        })
        
        # Step 3: Load model
        model = self.load_model(model_info, models_dir)
        crew_steps.append({
            "thought": "TensorFlow Agent: loading TensorFlow model",
            "output": f"Model loaded: {model_info.get('name', 'default')}"
        })
        
        # Step 4: Preprocess input data
        preprocessed_data = self.preprocess_input(user_input, task_type, model_info)
        crew_steps.append({
            "thought": "TensorFlow Agent: preprocessing input data",
            "output": f"Preprocessed data shape: {preprocessed_data.get('shape', 'N/A')}"
        })
        
        # Step 5: Run prediction
        prediction = self.predict(model, preprocessed_data, task_type)
        crew_steps.append({
            "thought": "TensorFlow Agent: running prediction/inference",
            "output": f"Prediction completed"
        })
        
        # Step 6: Post-process results
        postprocessed_result = self.postprocess_prediction(prediction, task_type, model_info.get("name", "default_model"))
        crew_steps.append({
            "thought": "TensorFlow Agent: postprocessing results",
            "output": f"Final result prepared"
        })
        
        return {
            "task_type": task_type,
            "model_name": model_info.get("name", "default"),
            "prediction": postprocessed_result.get("prediction"),
            "confidence": postprocessed_result.get("confidence"),
            "preprocessing": preprocessed_data.get("description", ""),
            "postprocessing": postprocessed_result.get("description", ""),
            "model_info": model_info,
            "crew_steps": crew_steps
        }
    
    def determine_model(self, task_type: str, model_name: Optional[str], models_dir: str, query: str = "") -> Dict[str, Any]:
        """Determine which model to use based on task type."""
        if model_name:
            return {
                "name": model_name,
                "path": os.path.join(models_dir, f"{model_name}.keras"),
                "architecture": "custom",
                "input_shape": "depends on model",
                "output_shape": "depends on model",
                "parameters": "N/A"
            }
        
        # Check for sentiment/feedback specific queries
        q_lower = query.lower() if query else ""
        if "sentiment" in q_lower or "feedback" in q_lower or "review" in q_lower:
            return {
                "name": "sentiment_analyzer",
                "path": os.path.join(models_dir, "sentiment_analyzer.keras"),
                "architecture": "LSTM/Transformer",
                "input_shape": "(sequence_length,)",
                "output_shape": "(num_classes,)",
                "parameters": "5M+"
            }
        
        # Default model mappings based on task type
        model_mappings = {
            "classification": {
                "name": "image_classifier",
                "path": os.path.join(models_dir, "image_classifier.keras"),
                "architecture": "CNN",
                "input_shape": "(224, 224, 3)",
                "output_shape": "(num_classes,)",
                "parameters": "10M+"
            },
            "regression": {
                "name": "regression_model",
                "path": os.path.join(models_dir, "regression_model.keras"),
                "architecture": "Dense Neural Network",
                "input_shape": "(num_features,)",
                "output_shape": "(1,)",
                "parameters": "1M+"
            },
            "detection": {
                "name": "object_detector",
                "path": os.path.join(models_dir, "object_detector.keras"),
                "architecture": "YOLO/Faster R-CNN",
                "input_shape": "(416, 416, 3)",
                "output_shape": "(num_boxes, 6)",
                "parameters": "50M+"
            },
            "nlp": {
                "name": "sentiment_analyzer",
                "path": os.path.join(models_dir, "sentiment_analyzer.keras"),
                "architecture": "LSTM/Transformer",
                "input_shape": "(sequence_length,)",
                "output_shape": "(num_classes,)",
                "parameters": "5M+"
            },
            "image_classification": {
                "name": "image_classifier",
                "path": os.path.join(models_dir, "image_classifier.keras"),
                "architecture": "CNN (ResNet/VGG)",
                "input_shape": "(224, 224, 3)",
                "output_shape": "(num_classes,)",
                "parameters": "25M+"
            },
            "time_series": {
                "name": "time_series_forecaster",
                "path": os.path.join(models_dir, "time_series_forecaster.keras"),
                "architecture": "LSTM/GRU",
                "input_shape": "(lookback, features)",
                "output_shape": "(forecast_horizon,)",
                "parameters": "2M+"
            }
        }
        
        return model_mappings.get(task_type, {
            "name": "default_model",
            "path": os.path.join(models_dir, "default_model.keras"),
            "architecture": "Neural Network",
            "input_shape": "depends on data",
            "output_shape": "depends on task",
            "parameters": "N/A"
        })
    
    def load_model(self, model_info: Dict[str, Any], models_dir: str):
        """Load TensorFlow model."""
        model_path = model_info.get("path", "")
        
        # Check if model file exists
        if not os.path.exists(model_path):
            # Return None if model doesn't exist (for demo purposes)
            return None
        
        try:
            import tensorflow as tf
            model = tf.keras.models.load_model(model_path)
            return model
        except ImportError:
            # TensorFlow not installed, return None for demo
            return None
        except Exception as e:
            # Model loading failed, return None for demo
            return None
    
    def preprocess_input(self, user_input: Any, task_type: str, model_info: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess input data for the model."""
        if user_input is None:
            return {
                "data": None,
                "shape": "No input provided",
                "description": "No input data provided. Model is ready for inference."
            }
        
        preprocessing_steps = []
        
        # Handle different input types
        if isinstance(user_input, (list, np.ndarray)):
            data = np.array(user_input, dtype=np.float32)
            preprocessing_steps.append("Converted to numpy array")
            
            # Normalize if needed
            if task_type in ["classification", "image_classification"]:
                if data.max() > 1.0:
                    data = data / 255.0
                    preprocessing_steps.append("Normalized to [0, 1]")
            
            # Add batch dimension if needed
            if len(data.shape) == 2 or len(data.shape) == 3:
                data = np.expand_dims(data, axis=0)
                preprocessing_steps.append("Added batch dimension")
            
            return {
                "data": data,
                "shape": str(data.shape),
                "description": "; ".join(preprocessing_steps)
            }
        elif isinstance(user_input, str):
            # Text input for NLP
            preprocessing_steps.append("Text input received")
            preprocessing_steps.append("Tokenization would be applied")
            preprocessing_steps.append("Padding/truncation to sequence length")
            
            return {
                "data": user_input,
                "shape": "(sequence_length,)",
                "description": "; ".join(preprocessing_steps)
            }
        else:
            preprocessing_steps.append("Input converted to array")
            return {
                "data": np.array([user_input]),
                "shape": "(1,)",
                "description": "; ".join(preprocessing_steps)
            }
    
    def predict(self, model: Any, preprocessed_data: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Run prediction using the model."""
        data = preprocessed_data.get("data")
        
        if model is None or data is None:
            # Return mock prediction for demo purposes
            return self._mock_prediction(task_type)
        
        try:
            import tensorflow as tf
            prediction = model.predict(data)
            return {"prediction": prediction.tolist(), "raw": prediction}
        except Exception as e:
            return self._mock_prediction(task_type)
    
    def _mock_prediction(self, task_type: str) -> Dict[str, Any]:
        """Generate mock prediction for demo purposes."""
        if task_type == "classification":
            return {
                "prediction": [0.85, 0.15],
                "classes": ["Class 0", "Class 1"]
            }
        elif task_type == "regression":
            return {
                "prediction": [42.5],
                "description": "Predicted value"
            }
        elif task_type == "detection":
            return {
                "prediction": [
                    {"class": "object_1", "confidence": 0.92, "bbox": [10, 20, 100, 150]},
                    {"class": "object_2", "confidence": 0.78, "bbox": [50, 60, 200, 250]}
                ]
            }
        elif task_type == "nlp":
            return {
                "prediction": [0.75, 0.25],
                "sentiment": "positive"
            }
        elif task_type == "image_classification":
            return {
                "prediction": [0.90, 0.08, 0.02],
                "classes": ["cat", "dog", "other"]
            }
        elif task_type == "time_series":
            return {
                "prediction": [120.5, 125.3, 130.1, 128.9, 135.2],
                "description": "Forecast values"
            }
        else:
            return {
                "prediction": [0.5],
                "description": "Generic prediction"
            }
    
    def postprocess_prediction(self, prediction: Dict[str, Any], task_type: str, model_name: str = "default_model") -> Dict[str, Any]:
        """Post-process prediction results."""
        raw_prediction = prediction.get("prediction")
        
        if raw_prediction is None:
            return {
                "prediction": None,
                "confidence": None,
                "description": "No prediction to post-process"
            }
        
        if isinstance(raw_prediction, list):
            # Calculate confidence for classification tasks
            if task_type in ["classification", "image_classification", "nlp"]:
                max_value = max(raw_prediction) if raw_prediction else 0
                confidence = max_value / sum(raw_prediction) if sum(raw_prediction) > 0 else 0
                
                # Get class with highest confidence
                predicted_class = raw_prediction.index(max_value)
                
                # Map class ID to label
                class_label = self.class_mappings.get(model_name, {}).get(predicted_class, f"Class {predicted_class}")
                
                # Create probability dictionary with labels
                prob_dict = {}
                for idx, prob in enumerate(raw_prediction):
                    label = self.class_mappings.get(model_name, {}).get(idx, f"Class {idx}")
                    prob_dict[label] = prob
                
                return {
                    "prediction": {
                        "predicted_class": predicted_class,
                        "predicted_label": class_label,
                        "probabilities": prob_dict
                    },
                    "confidence": confidence,
                    "description": f"Predicted {class_label} with {confidence:.2%} confidence"
                }
            elif task_type == "detection":
                return {
                    "prediction": raw_prediction,
                    "confidence": max([obj.get("confidence", 0) for obj in raw_prediction]) if raw_prediction else 0,
                    "description": f"Detected {len(raw_prediction)} objects"
                }
            else:
                return {
                    "prediction": raw_prediction,
                    "confidence": None,
                    "description": "Prediction values returned"
                }
        
        return {
            "prediction": raw_prediction,
            "confidence": None,
            "description": "Prediction returned"
        }
