from flask import Flask, jsonify, request
from app.api_core import health, parcel_detail, parcels_bbox

app = Flask(__name__)

@app.get('/health')
def health_route():
    return jsonify(health())

@app.get('/parcels')
def parcels_route():
    bbox = request.args.get('bbox')
    if not bbox:
        return jsonify({'error': 'bbox required'}), 400
    return jsonify(parcels_bbox(bbox))

@app.get('/parcels/<parcel_id>')
def detail_route(parcel_id: str):
    row = parcel_detail(parcel_id)
    return (jsonify(row), 200) if row else (jsonify({'error': 'not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
