"""
Mock services for testing dynamic API key claims and model inference
"""
import os
import json
import time
import random
from typing import Dict, Any, List, Optional
from flask import Flask, jsonify, request, Response

# Create a mock Flask app for the billing service
mock_app = Flask(__name__)

# In-memory store for mock data
mock_data = {
    "budgets": {
        "ak_tiered_model_exec": {"remaining_budget": 1000},
        "test-groq": {"remaining_budget": 500},
        "test-all": {"remaining_budget": 2000},
    },
    "models": {
        "Meta-Llama-3.1-8B-Instruct": {
            "responses": {
                "capital": "Paris is the capital of France.",
                "weather": "The weather depends on location and season. I don't have real-time weather data.",
                "default": "I'm a helpful assistant running in a mock service. How can I assist you today?"
            },
            "latency": {"min": 0.5, "max": 1.5}
        },
        "Meta-Llama-3.1-70B-Instruct": {
            "responses": {
                "capital": "Paris is the capital of France. It's located in the north-central part of the country and is known as the 'City of Light'.",
                "weather": "I don't have access to real-time weather data. To get current weather information, you would need to check a weather service or app.",
                "default": "I'm a helpful assistant powered by a simulated Llama 3.1 70B model. How can I assist you today?"
            },
            "latency": {"min": 1.0, "max": 2.5}
        },
        "default": {
            "responses": {
                "default": "This is a mock response from the Triton Inference Server."
            },
            "latency": {"min": 0.3, "max": 0.8}
        }
    }
}

@mock_app.route('/api/budget/<api_key_id>', methods=['GET'])
def get_budget(api_key_id):
    """Mock budget endpoint"""
    if api_key_id in mock_data["budgets"]:
        return jsonify(mock_data["budgets"][api_key_id])
    return jsonify({"remaining_budget": 0}), 404

@mock_app.route('/v2/models/<model_name>/generate', methods=['POST'])
def triton_generate(model_name):
    """
    Mock Triton Inference Server endpoint for text generation
    
    Simulates different Llama models with different response styles and latencies
    
    Example request:
    {
        "inputs": [{
            "name": "text_input",
            "shape": [1],
            "datatype": "BYTES",
            "data": ["<formatted prompt here>"]
        }],
        "parameters": {
            "temperature": 0.7,
            "max_tokens": 100
        }
    }
    """
    # Get request data
    data = request.json
    
    # Extract prompt from request
    prompt = ""
    if data and "inputs" in data and len(data["inputs"]) > 0:
        input_data = data["inputs"][0]
        if "data" in input_data and len(input_data["data"]) > 0:
            prompt = input_data["data"][0]
    
    # Get model configuration
    model_config = mock_data["models"].get(model_name, mock_data["models"]["default"])
    
    # Determine response based on prompt content
    response_text = model_config["responses"]["default"]
    for key, text in model_config["responses"].items():
        if key != "default" and key in prompt.lower():
            response_text = text
            break
    
    # Simulate processing time
    min_latency = model_config["latency"]["min"]
    max_latency = model_config["latency"]["max"]
    processing_time = random.uniform(min_latency, max_latency)
    time.sleep(processing_time)
    
    # Return Triton-style response
    return jsonify({
        "model_name": model_name,
        "model_version": "1",
        "outputs": [{
            "name": "text_output",
            "shape": [1],
            "datatype": "BYTES",
            "data": [response_text]
        }],
        "parameters": {
            "processing_time": processing_time
        }
    })

def start_mock_services(port=5001, debug=False):
    """
    Start the mock services for testing
    
    Args:
        port: Port number to run the server on
        debug: Whether to run in debug mode
    """
    # Use this in test fixtures to start mock services
    mock_app.run(host='0.0.0.0', port=port, debug=debug)
    
def get_mock_user_context(api_key_id: str = None) -> Dict[str, Any]:
    """
    Create a mock user context for testing dynamic claims
    
    Args:
        api_key_id: Optional API key ID to include
        
    Returns:
        Dict with user context variables for dynamic claim processing
    """
    return {
        "team_id": "admin-team",  # For testing permissions.get_team_permissions
        "api_key_id": api_key_id or "test-all",  # For testing API endpoints
        "user_id": "test-user"  # For testing user-specific logic
    }

def get_available_models() -> List[str]:
    """
    Get a list of available mock models
    
    Returns:
        List of model names that can be used with the mock Triton server
    """
    return list(mock_data["models"].keys())


if __name__ == "__main__":
    print("Starting mock services for API testing on http://127.0.0.1:5001")
    print("Press CTRL+C to stop the server")
    start_mock_services(port=5001)

"""

   curl -X POST http://192.168.1.25:5001/v2/models/Meta-Llama-3.1-8B-Instruct/generate \
     -H "Content-Type: application/json" \
     -d '{
       "inputs": [{
         "name": "text_input",
         "shape": [1],
         "datatype": "BYTES",
         "data": ["<|begin_of_text|><|start_header_id|>system<|end_header_id|>\nYou are a helpful assistant<|eot_id|>\n<|start_header_id|>user<|end_header_id|>\nWhat is the capital of France?<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>"]
       }],
       "parameters": {
         "temperature": 0.7,
         "max_tokens": 100
       }
     }'

"""