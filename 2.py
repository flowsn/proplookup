from flask import Flask, request, render_template_string, jsonify
import os
import requests
import json
import urllib.parse
from datetime import datetime

app = Flask(__name__)

# API keys
GEOCLIENT_KEY = '3bd5c70fec6f4c8f9a59821a303eeb72'  # Primary key
GEOCLIENT_SECONDARY_KEY = '107c23829655446a98802eeceb127c7b'  # Secondary key
GOOGLE_KEY = 'AIzaSyDBCR8XDh6aVnm0JaQGH4pLzG_KXy2Nsro'


# Helper to parse datetime strings
def parse_datetime(dt_str):
    try:
        return datetime.strptime(dt_str, '%m/%d/%Y %I:%M:%S %p')
    except:
        return datetime.min

# Build ACRIS document image URL
def generate_document_url(doc_id):
    return f"https://a836-acris.nyc.gov/DS/DocumentSearch/DocumentImageView?doc_id={doc_id}"

def get_bbl_from_address(street, borough):
    try:
        num, name = street.split(' ', 1)
    except ValueError:
        return None, None, None, None, None, None, {}
    headers = {'Ocp-Apim-Subscription-Key': GEOCLIENT_KEY}
    params = {'houseNumber': num, 'street': name, 'borough': borough}
    resp = requests.get('https://api.nyc.gov/geoclient/v2/address', params=params, headers=headers)
    if resp.status_code == 401 and GEOCLIENT_SECONDARY_KEY:
        headers['Ocp-Apim-Subscription-Key'] = GEOCLIENT_SECONDARY_KEY
        resp = requests.get('https://api.nyc.gov/geoclient/v2/address', params=params, headers=headers)
    raw = resp.json()
    a = raw.get('address', {})
    try:
        bc = a['bblBoroughCode']
        block = a['bblTaxBlock'].zfill(5)
        lot = a['bblTaxLot'].zfill(4)
        full_addr = f"{num} {name}, {borough}"
        lat = a.get('latitude')
        lon = a.get('longitude')
        return bc, block, lot, full_addr, lat, lon, raw
    except KeyError:
        return None, None, None, None, None, None, raw

def get_pip_docs(bc, block, lot):
    try:
        blk = str(int(block))
        lt = str(int(lot))
    except:
        return [], ''
    docs_data = []
    pip_raw = ''
    for rt in ('OTHER', 'SALES'):
        url = (
            'https://propertyinformationportal.nyc.gov/proxy/proxy.ashx?'
            'https://a836-acrissds.nyc.gov/AcrisDtm/AcrisDtmApi/AcrisDocuments'
            f'?returntype={rt}&borough={bc}&block={blk}&lot={lt}'
        )
        resp = requests.get(url)
        if resp.status_code != 200:
            continue
        try:
            raw = resp.json()
        except:
            continue
        if not pip_raw:
            pip_raw = json.dumps(raw, indent=2)
        docs_data.extend(raw.get('documents') or [])
    simplified = []
    for d in docs_data:
        simplified.append({
            'doc_id': d.get('doc_id', ''),
            'document_date': d.get('document_date', ''),
            'recorded_datetime': d.get('recorded_datetime', ''),
            'doc_type': d.get('doc_type', ''),
            'document_amt': d.get('document_amt', 0.0),
            'party1': [p.get('name') for p in d.get('party1', [])],
            'party2': [p.get('name') for p in d.get('party2', [])],
            'url': generate_document_url(d.get('doc_id', ''))
        })
    simplified.sort(key=lambda x: parse_datetime(x['recorded_datetime']), reverse=True)
    return simplified, pip_raw

def generate_tax_url(bc, block, lot):
    pin = f"{int(bc)}{block}{lot}"
    return f"https://a836-pts-access.nyc.gov/care/datalets/datalet.aspx?mode=profileall2&s&UseSearch=no&pin={pin}&jur=65"

@app.route('/')
def index():
    street = request.args.get('street')
    borough = request.args.get('borough')
    bbl = request.args.get('bbl')

    bc = block = lot = full_address = lat = lon = None
    geoclient_raw = None

    if bbl and not (street or borough):
        try:
            bc, block, lot = bbl.split('-')
            block = block.zfill(5)
            lot = lot.zfill(4)
            full_address = f"BBL {bbl}"
        except ValueError:
            return render_template_string(HTML_TEMPLATE, google_key=GOOGLE_KEY)
    elif street and borough:
        bc, block, lot, full_address, lat, lon, geoclient_raw = get_bbl_from_address(street, borough)
        if not bc:
            return render_template_string(HTML_TEMPLATE, google_key=GOOGLE_KEY)
    else:
        return render_template_string(HTML_TEMPLATE, google_key=GOOGLE_KEY)

    pip_docs, pip_raw = get_pip_docs(bc, block, lot)
    tax_url = generate_tax_url(bc, block, lot)

    return render_template_string(
        HTML_TEMPLATE,
        full_address=full_address,
        bc=bc,
        block=block,
        lot=lot,
        lat=lat,
        lon=lon,
        pip_docs=pip_docs,
        pip_raw=pip_raw,
        google_key=GOOGLE_KEY,
        geoclient_raw=geoclient_raw,
        tax_url=tax_url
    )

HTML_TEMPLATE = '''
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>NYC Property Lookup</title>
  <style>
    body { font-family: sans-serif; padding: 2rem; }
    .maps { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0; }
    table { border-collapse: collapse; width: 100%; font-size: 0.85rem; margin-top:1rem; }
    th, td { border: 1px solid #ccc; padding: 0.3rem 0.5rem; text-align: left; }
    th { background: #eaeaea; }
    .deed     { background: #d4f7d4; }
    .mortgage { background: #ffd1d1; }
    .tax-lien { background: #d0eaff; }
    .ucc      { background: #d3d3d3; }
    .other    { background: #f0f0f0; }
  </style>
</head>
<body>
  <h1>NYC Property Lookup</h1>
  <form method="get">
    <div>
      <label><strong>Search by Address:</strong></label><br>
      <input type="text" name="street" placeholder="123 Main St" style="width:300px;" value="">
      <select name="borough">
        <option value="Manhattan">Manhattan</option>
        <option value="Brooklyn" selected>Brooklyn</option>
        <option value="Queens">Queens</option>
        <option value="Bronx">Bronx</option>
        <option value="Staten Island">Staten Island</option>
      </select>
    </div>
    <div style="margin-top:1rem;">
      <label><strong>Or BBL:</strong></label><br>
      <input type="text" name="bbl" placeholder="1-00862-1274" style="width:300px;" value="">
    </div>
    <button type="submit" style="margin-top:1rem;">Search</button>
  </form>

  {% if full_address %}
    {% if lat and lon %}
      <div class="maps">
        <iframe width="100%" height="300" src="https://www.google.com/maps/embed/v1/streetview?key={{ google_key }}&location={{ lat }},{{ lon }}" allowfullscreen></iframe>
        <iframe width="100%" height="300" src="https://www.google.com/maps/embed/v1/place?key={{ google_key }}&q={{ lat }},{{ lon }}" allowfullscreen></iframe>
      </div>
    {% endif %}

    <h2>{{ full_address }} (BBL: {{ bc }}-{{ block }}-{{ lot }})</h2>
    <ul>
      {% if lat and lon %}
      <li><a href="https://roadview.planninglabs.nyc/view/{{ lon }}/{{ lat }}" target="_blank">Cyclomedia View</a></li>
      {% endif %}
      <li><a href="https://a836-acris.nyc.gov/bblsearch/bblsearch.asp?borough={{ bc }}&block={{ block }}&lot={{ lot }}" target="_blank">ACRIS</a></li>
      <li><a href="https://a810-bisweb.nyc.gov/bisweb/PropertyProfileOverviewServlet?boro={{ bc }}&block={{ block }}&lot={{ lot }}" target="_blank">DOB BIS</a></li>
      <li><a href="https://www.google.com/maps/place/{{ full_address|urlencode }}" target="_blank">Google Maps</a></li>
      <li><a href="https://propertyinformationportal.nyc.gov/parcels/parcel/{{ bc }}{{ block }}{{ lot }}" target="_blank">PIP</a></li>
      <li><a href="{{ tax_url }}" target="_blank">Tax Account</a></li>
    </ul>

    {% if pip_docs %}
      <h3>All Documents (Newest First)</h3>
      <table>
        <thead>
          <tr><th>CRFN</th><th>Lot</th><th>Doc Date</th><th>Recorded</th><th>Type</th><th>Party1</th><th>Party2</th><th>Amount</th></tr>
        </thead>
        <tbody>
          {% for doc in pip_docs %}
          <tr class="{{ 'tax-lien' if 'TAX LIEN' in doc.doc_type.upper() else 'ucc' if 'UCC' in doc.doc_type.upper() else 'deed' if 'DEED' in doc.doc_type.upper() else 'mortgage' }}">
            <td><a href="{{ doc.url }}" target="_blank">{{ doc.doc_id }}</a></td>
            <td>{{ lot }}</td>
            <td>{{ doc.document_date }}</td>
            <td>{{ doc.recorded_datetime }}</td>
            <td>{{ doc.doc_type }}</td>
            <td>{{ doc.party1|join(', ') }}</td>
            <td>{{ doc.party2|join(', ') }}</td>
            <td>{{ '{:,.2f}'.format(doc.document_amt) }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    {% else %}
      <p>No documents found.</p>
    {% endif %}

    <h3>AI Summary</h3>
    <div id="summary">Loading summary...</div>
    <script>
      document.addEventListener('DOMContentLoaded', async () => {
        const docs = {{ pip_docs|tojson }};
        const res = await fetch('/summary', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({docs})
        });
        const data = await res.json();
        const container = document.getElementById('summary');
        if (data.summary.length) {
          const tbl = document.createElement('table');
          tbl.style.width = '100%'; tbl.style.marginTop = '1rem';
          const tbody = document.createElement('tbody');
          data.summary.forEach(line => {
            const tr = document.createElement('tr');
            const td = document.createElement('td'); td.innerHTML = `<strong>${line}</strong>`;
            tr.appendChild(td); tbody.appendChild(tr);
          });
          tbl.appendChild(tbody);
          container.innerHTML = ''; container.appendChild(tbl);
        } else {
          container.textContent = '(No summary available)';
        }
      });
    </script>
  {% endif %}
</body>
</html>
'''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
