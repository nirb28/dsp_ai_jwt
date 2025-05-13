"""
Mock services for testing dynamic API key claims
"""
import os
import json
from typing import Dict, Any
from flask import Flask, jsonify, request

# Create a mock Flask app for the billing service
mock_app = Flask(__name__)

# In-memory store for mock data
mock_data = {
    "budgets": {
        "ak_tiered_model_exec": {"remaining_budget": 1000},
        "test-groq": {"remaining_budget": 500},
        "test-all": {"remaining_budget": 2000},
    }
}

@mock_app.route('/api/budget/<api_key_id>', methods=['GET'])
def get_budget(api_key_id):
    """Mock budget endpoint"""
    if api_key_id in mock_data["budgets"]:
        return jsonify(mock_data["budgets"][api_key_id])
    return jsonify({"remaining_budget": 0}), 404

def start_mock_services(port=5001):
    """Start the mock services for testing"""
    # Use this in test fixtures to start mock services
    mock_app.run(host='127.0.0.1', port=port)
    
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
        "user_id": "test-user"
    }


if __name__ == "__main__":
    print("Starting mock services for API testing on http://127.0.0.1:5001")
    print("Press CTRL+C to stop the server")
    start_mock_services(port=5001)
