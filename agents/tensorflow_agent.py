import os
import numpy as np
from typing import Any
from agents.base_agent import BaseAgent
from tools.tot_planner import ToTPlanner
from crews.tensorflow_crew import TensorFlowCrew


class TensorFlowAgent(BaseAgent):
    name = "TensorFlowAgent"
    agent_type = "TensorFlow"
    rag_category = "ml"

    def __init__(self):
        self.tot = ToTPlanner()
        self.crew = TensorFlowCrew()
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")

    def run(self, query: str, input_data=None, model_name=None, task_type=None):
        tasks = [
            "Analyze prediction request",
            "Determine task type (classification, regression, detection, etc.)",
            "Load appropriate TensorFlow model",
            "Preprocess input data",
            "Run prediction/inference",
            "Post-process results",
            "Format output for user"
        ]
        
        thoughts = self.tot.create_thoughts(self.agent_type, query, tasks, max_thoughts=10)
        
        # Determine task type from query
        if task_type is None:
            task_type = self._infer_task_type(query)
        
        # Prepare data for crew
        crew_input = {
            "query": query,
            "input_data": input_data,
            "model_name": model_name,
            "task_type": task_type,
            "models_dir": self.models_dir
        }
        
        crew_result = self.crew.run(crew_input)
        crew_thoughts = [s["thought"] for s in crew_result["crew_steps"]]
        
        answer = self.build_tensorflow_answer(crew_result)
        
        return self.response(
            query,
            thoughts + crew_thoughts,
            answer,
            {"crew_result": crew_result}
        )
    
    def _infer_task_type(self, query: str) -> str:
        """Infer the type of ML task from the query."""
        q = query.lower()
        
        if "classify" in q or "class" in q or "category" in q:
            return "classification"
        elif "predict" in q or "forecast" in q or "regression" in q:
            return "regression"
        elif "detect" in q or "object detection" in q or "find" in q:
            return "detection"
        elif "sentiment" in q or "nlp" in q or "text" in q:
            return "nlp"
        elif "image" in q or "visual" in q or "photo" in q:
            return "image_classification"
        elif "time series" in q or "temporal" in q or "sequence" in q:
            return "time_series"
        else:
            return "general"
    
    def build_tensorflow_answer(self, crew_result: dict):
        """Build the TensorFlow prediction answer."""
        task_type = crew_result.get("task_type", "unknown")
        model_name = crew_result.get("model_name", "unknown")
        prediction = crew_result.get("prediction", None)
        confidence = crew_result.get("confidence", None)
        preprocessing = crew_result.get("preprocessing", "")
        postprocessing = crew_result.get("postprocessing", "")
        model_info = crew_result.get("model_info", {})
        
        # Extract input text from query if it's a sentiment/feedback analysis
        input_text = self._extract_input_text(crew_result.get("query", ""))
        
        answer = (
            "**TensorFlow Agent** — Deep Learning Prediction\n\n"
        )
        
        # Add input text if available
        if input_text:
            answer += f"**Input:**\n{input_text}\n\n"
        
        # Add prediction results with labels
        if prediction is not None:
            answer += "**Prediction Results:**\n"
            
            if isinstance(prediction, dict):
                # Check if we have a predicted_label (from class mapping)
                if "predicted_label" in prediction:
                    label = prediction["predicted_label"]
                    answer += f"**Prediction:** {label}\n\n"
                    
                    if confidence is not None:
                        answer += f"**Confidence:** {confidence:.1%}\n\n"
                    
                    # Add probabilities if available
                    if "probabilities" in prediction and isinstance(prediction["probabilities"], dict):
                        answer += "**Probabilities:**\n"
                        for label, prob in prediction["probabilities"].items():
                            answer += f"- {label}: {prob:.1%}\n"
                        answer += "\n"
                else:
                    # Fallback to original format
                    for key, value in prediction.items():
                        answer += f"- {key}: {value}\n"
                    
                    if confidence is not None:
                        answer += f"\nConfidence: {confidence:.2%}\n"
            else:
                answer += f"- Prediction: {prediction}\n"
                if confidence is not None:
                    answer += f"- Confidence: {confidence:.2%}\n"
            
            answer += "\n"
        
        # Add explanation using LLM
        explanation = self._generate_explanation(prediction, confidence, input_text, task_type)
        if explanation:
            answer += "**Explanation:**\n"
            answer += f"{explanation}\n\n"
        
        # Add model information (collapsed)
        if model_info:
            answer += "**Model Information:**\n"
            if "architecture" in model_info:
                answer += f"- Architecture: {model_info['architecture']}\n"
            if "parameters" in model_info:
                params = model_info['parameters']
                if isinstance(params, (int, float)):
                    answer += f"- Parameters: {params:,}\n"
                else:
                    answer += f"- Parameters: {params}\n"
            answer += "\n"
        
        # Add usage examples
        answer += "**Example Use Cases:**\n"
        answer += "- Image classification (cat/dog, plant disease detection)\n"
        answer += "- Text sentiment analysis\n"
        answer += "- Time series forecasting\n"
        answer += "- Customer churn prediction\n"
        answer += "- Object detection in images\n"
        
        return answer
    
    def _extract_input_text(self, query: str) -> str:
        """Extract input text from query for sentiment/feedback analysis."""
        # Look for quoted text in the query
        import re
        quoted_text = re.search(r'"([^"]+)"', query)
        if quoted_text:
            return quoted_text.group(1)
        
        # Look for text after "sentiment:" or similar
        if "sentiment:" in query.lower():
            parts = query.split("sentiment:", 1)
            if len(parts) > 1:
                return parts[1].strip().strip('"')
        
        if "analyze:" in query.lower():
            parts = query.split("analyze:", 1)
            if len(parts) > 1:
                return parts[1].strip().strip('"')
        
        return ""
    
    def _generate_explanation(self, prediction: Any, confidence: float, input_text: str, task_type: str) -> str:
        """Generate an explanation for the prediction using LLM-like reasoning."""
        if prediction is None or input_text is None:
            return ""
        
        if isinstance(prediction, dict) and "predicted_label" in prediction:
            label = prediction["predicted_label"]
            conf_percent = confidence * 100 if confidence else 0
            
            # Generate explanation based on task type and prediction
            if task_type == "nlp" or "sentiment" in task_type.lower():
                if label == "Positive":
                    return (
                        f"The sentiment is **{label}** with {conf_percent:.1f}% confidence. "
                        f"The text contains positive language and expressions that indicate satisfaction or approval."
                    )
                elif label == "Negative":
                    return (
                        f"The sentiment is **{label}** with {conf_percent:.1f}% confidence. "
                        f"The text contains negative language or expressions that indicate dissatisfaction or criticism."
                    )
            elif task_type == "image_classification":
                return (
                    f"The image is classified as **{label}** with {conf_percent:.1f}% confidence. "
                    f"The model identified visual features characteristic of this class."
                )
            else:
                return (
                    f"The prediction is **{label}** with {conf_percent:.1f}% confidence. "
                    f"The model analyzed the input features and determined this classification."
                )
        
        return ""
