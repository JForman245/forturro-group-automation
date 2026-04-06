#!/usr/bin/env python3
import requests
import json

resp = requests.post('http://localhost:11434/api/generate', 
                    json={"model": "gemma2:2b", 
                          "prompt": "Write a 5-word real estate email subject", 
                          "stream": False})
data = resp.json()
print("Gemma2:2b response:", data['response'])