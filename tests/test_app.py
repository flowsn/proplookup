import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location('app_module', Path(__file__).resolve().parents[1] / '1.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
app = mod.app
generate_tax_url = mod.generate_tax_url

def test_generate_tax_url():
    url = generate_tax_url('3', '12345', '1001')
    assert url == (
        "https://a836-pts-access.nyc.gov/care/datalets/datalet.aspx"
        "?mode=profileall2&UseSearch=no&pin=3123451001&jur=65"
    )

def test_summary_endpoint():
    client = app.test_client()
    docs = [{"doc_type": "DEED", "recorded_datetime": "01/01/2024"}]
    resp = client.post('/summary', json={'docs': docs})
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["summary"] == ["01/01/2024 - DEED"]
