from typing import Dict, List, Any


class MLCrew:
    def __init__(self):
        self.ml_algorithms = self.build_ml_algorithms()

    def run(self, query: str):
        # Analyze ML task
        task_type = self.detect_task_type(query)
        data_type = self.detect_data_type(query)
        requirements = self.extract_requirements(query)
        
        # Generate ML pipeline
        preprocessing = self.design_preprocessing(data_type, requirements)
        model_selection = self.select_model(task_type, data_type, requirements)
        training_strategy = self.design_training(task_type, requirements)
        evaluation_metrics = self.select_evaluation_metrics(task_type)
        deployment_strategy = self.design_deployment(task_type, requirements)
        
        crew_steps = [
            {"thought": "ML Agent: analyzing machine learning task", "output": f"Task type: {task_type}"},
            {"thought": "Data Engineer: designing preprocessing pipeline", "output": "Preprocessing designed"},
            {"thought": "Model Selector: choosing appropriate model", "output": f"Model: {model_selection['model']}"},
            {"thought": "Training Designer: planning training strategy", "output": "Training strategy defined"},
            {"thought": "Evaluator: selecting metrics", "output": f"Metrics: {', '.join(evaluation_metrics)}"},
            {"thought": "Deployment Architect: planning deployment", "output": "Deployment strategy designed"},
        ]
        
        return {
            "task_type": task_type,
            "data_type": data_type,
            "requirements": requirements,
            "preprocessing": preprocessing,
            "model_selection": model_selection,
            "training_strategy": training_strategy,
            "evaluation_metrics": evaluation_metrics,
            "deployment_strategy": deployment_strategy,
            "crew_steps": crew_steps,
        }

    @staticmethod
    def detect_task_type(query: str) -> str:
        """Detect the type of ML task from query."""
        query_lower = query.lower()
        
        task_patterns = {
            "classification": ["classification", "classify", "predict class", "categorize", "label"],
            "regression": ["regression", "predict value", "forecast", "price prediction", "house price"],
            "clustering": ["clustering", "cluster", "group", "segment", "unsupervised"],
            "nlp": ["nlp", "text", "sentiment", "language", "translation", "chatbot"],
            "computer_vision": ["image", "vision", "object detection", "classification image", "cnn"],
            "recommendation": ["recommend", "recommendation", "collaborative filtering", "suggest"],
            "time_series": ["time series", "forecast", "temporal", "sequence", "stock"],
            "anomaly_detection": ["anomaly", "outlier", "fraud", "detection"],
        }
        
        for task_type, patterns in task_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return task_type
        
        return "general_ml"

    @staticmethod
    def detect_data_type(query: str) -> str:
        """Detect the type of data from query."""
        query_lower = query.lower()
        
        if "image" in query_lower or "vision" in query_lower:
            return "image"
        elif "text" in query_lower or "nlp" in query_lower or "sentiment" in query_lower:
            return "text"
        elif "tabular" in query_lower or "csv" in query_lower or "structured" in query_lower:
            return "tabular"
        elif "time series" in query_lower or "temporal" in query_lower:
            return "time_series"
        elif "graph" in query_lower or "network" in query_lower:
            return "graph"
        
        return "tabular"

    @staticmethod
    def extract_requirements(query: str) -> Dict[str, Any]:
        """Extract ML requirements from query."""
        requirements = {
            "accuracy": None,
            "latency": None,
            "interpretability": False,
            "real_time": False,
            "constraints": []
        }
        
        query_lower = query.lower()
        
        if "high accuracy" in query_lower or "best accuracy" in query_lower:
            requirements["accuracy"] = "high"
        elif "fast" in query_lower or "low latency" in query_lower:
            requirements["latency"] = "low"
        
        if "interpretable" in query_lower or "explainable" in query_lower:
            requirements["interpretability"] = True
        
        if "real time" in query_lower or "real-time" in query_lower:
            requirements["real_time"] = True
        
        if "mobile" in query_lower or "edge" in query_lower:
            requirements["constraints"].append("edge_deployment")
        
        if "large dataset" in query_lower or "big data" in query_lower:
            requirements["constraints"].append("large_scale")
        
        return requirements

    def design_preprocessing(self, data_type: str, requirements: Dict) -> Dict[str, Any]:
        """Design preprocessing pipeline."""
        preprocessing_steps = {
            "tabular": ["Handle missing values", "Feature scaling", "Encoding categorical variables", "Feature selection"],
            "image": ["Resize images", "Normalization", "Data augmentation", "Color space conversion"],
            "text": ["Tokenization", "Stop word removal", "Stemming/Lemmatization", "Vectorization (TF-IDF/Embeddings)"],
            "time_series": ["Handle missing values", "Seasonal decomposition", "Stationarity check", "Feature engineering"],
        }
        
        return {
            "steps": preprocessing_steps.get(data_type, preprocessing_steps["tabular"]),
            "techniques": {
                "normalization": "StandardScaler/MinMaxScaler",
                "encoding": "One-Hot/Label Encoding",
                "feature_selection": "PCA/Feature Importance"
            }
        }

    def select_model(self, task_type: str, data_type: str, requirements: Dict) -> Dict[str, Any]:
        """Select appropriate ML model."""
        model_recommendations = {
            "classification": {
                "tabular": ["Random Forest", "Gradient Boosting (XGBoost/LightGBM)", "Logistic Regression", "SVM"],
                "text": ["BERT/RoBERTa", "LSTM/GRU", "Naive Bayes", "SVM with TF-IDF"],
                "image": ["CNN (ResNet/EfficientNet)", "Vision Transformer", "Transfer Learning"]
            },
            "regression": {
                "tabular": ["Gradient Boosting (XGBoost/LightGBM)", "Random Forest", "Linear Regression", "Neural Networks"],
                "time_series": ["ARIMA/SARIMA", "LSTM/GRU", "Prophet", "Transformer-based models"]
            },
            "clustering": {
                "tabular": ["K-Means", "DBSCAN", "Hierarchical Clustering", "Gaussian Mixture Models"],
                "text": ["K-Means on embeddings", "Topic Modeling (LDA)", "Hierarchical clustering"]
            },
            "nlp": {
                "text": ["BERT/GPT models", "T5", "Seq2Seq models", "Transformer-based"]
            },
            "computer_vision": {
                "image": ["CNN (ResNet/EfficientNet)", "YOLO (for detection)", "Vision Transformer", "U-Net (segmentation)"]
            }
        }
        
        models = model_recommendations.get(task_type, {}).get(data_type, ["Random Forest", "Neural Networks"])
        
        # Select best model based on requirements
        if requirements.get("interpretability"):
            best_model = models[0] if "Random Forest" in models[0] or "Linear" in models[0] else models[-1]
        elif requirements.get("real_time"):
            best_model = models[0]
        else:
            best_model = models[0]
        
        return {
            "model": best_model,
            "alternatives": models[1:],
            "reason": f"Selected {best_model} for task type {task_type} with data type {data_type}"
        }

    def design_training(self, task_type: str, requirements: Dict) -> Dict[str, Any]:
        """Design training strategy."""
        return {
            "validation": "K-Fold Cross Validation",
            "hyperparameter_tuning": "Grid Search / Random Search / Bayesian Optimization",
            "early_stopping": True,
            "regularization": "L1/L2 regularization, Dropout",
            "batch_size": "32/64/128",
            "epochs": "Early stopping based on validation loss",
            "optimizer": "Adam/SGD with momentum",
            "learning_rate": "Learning rate scheduling"
        }

    def select_evaluation_metrics(self, task_type: str) -> List[str]:
        """Select appropriate evaluation metrics."""
        metrics = {
            "classification": ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC", "Confusion Matrix"],
            "regression": ["MSE", "RMSE", "MAE", "R² Score", "Adjusted R²"],
            "clustering": ["Silhouette Score", "Davies-Bouldin Index", "Calinski-Harabasz Index"],
            "nlp": ["BLEU Score", "ROUGE", "Perplexity", "Accuracy"],
            "computer_vision": ["mAP", "IoU", "Accuracy", "Precision", "Recall"],
            "time_series": ["MAPE", "RMSE", "MAE", "Direction Accuracy"],
            "anomaly_detection": ["Precision", "Recall", "F1-Score", "AUC-ROC"]
        }
        
        return metrics.get(task_type, ["Accuracy", "F1-Score"])

    def design_deployment(self, task_type: str, requirements: Dict) -> Dict[str, Any]:
        """Design deployment strategy."""
        deployment = {
            "format": "ONNX / TensorFlow SavedModel / PyTorch TorchScript",
            "serving": "TensorFlow Serving / TorchServe / FastAPI",
            "scaling": "Horizontal scaling with load balancer",
            "monitoring": "Model performance monitoring, drift detection",
            "versioning": "MLflow / DVC for model versioning"
        }
        
        if requirements.get("real_time"):
            deployment["optimization"] = "Model quantization, pruning, TensorRT"
        
        if "edge_deployment" in requirements.get("constraints", []):
            deployment["format"] = "TFLite / ONNX Runtime / CoreML"
            deployment["serving"] = "On-device inference"
        
        return deployment

    def build_ml_algorithms(self) -> Dict[str, List[str]]:
        """Build ML algorithms database."""
        return {
            "supervised": ["Linear Regression", "Logistic Regression", "Decision Trees", "Random Forest", "Gradient Boosting", "SVM", "Neural Networks"],
            "unsupervised": ["K-Means", "DBSCAN", "Hierarchical Clustering", "PCA", "t-SNE", "Autoencoders"],
            "deep_learning": ["CNN", "RNN", "LSTM", "GRU", "Transformer", "GAN", "VAE"],
            "nlp": ["BERT", "GPT", "T5", "Word2Vec", "GloVe", "FastText"],
            "reinforcement_learning": ["Q-Learning", "DQN", "PPO", "A3C", "Actor-Critic"]
        }
