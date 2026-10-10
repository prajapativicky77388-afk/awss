# FloodSense AI
- frontend-live/index.html : main app (open in browser). Real map, live rain, routing, CSV retraining.
- frontend-live/sample_training_format.csv : CSV format for training.
- backend-aws/ : handler.py + template.yaml (sam build && sam deploy --guided).
- demo-offline.html : simple schematic demo, works without internet.
Run: cd frontend-live && python3 -m http.server 8000, then open localhost:8000
