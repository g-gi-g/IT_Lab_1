from flask import Flask, render_template_string, request, redirect, jsonify, flash
import os
import requests
import sys
from pathlib import Path

# Add parent directory to path to import sync module
sys.path.append(str(Path(__file__).parent.parent))
from client_desktop.sync import FolderSync

API_URL = os.environ.get("API_URL", "http://127.0.0.1:5000")

app = Flask(__name__)
app.secret_key = 'dev-secret-key'

TPL = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Mini Drive Web</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css" rel="stylesheet" />
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial, sans-serif; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .auth-section { display: flex; gap: 20px; margin-bottom: 20px; }
        .auth-form { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); flex: 1; }
        .auth-form h3 { margin-bottom: 15px; color: #333; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #0056b3; }
        .btn-danger { background: #dc3545; }
        .btn-danger:hover { background: #c82333; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        
        .files-section { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .controls { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; align-items: center; }
        .controls select, .controls input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .file-list { display: grid; gap: 10px; }
        .file-item { display: flex; align-items: center; justify-content: space-between; padding: 15px; background: #f8f9fa; border-radius: 4px; border: 1px solid #e9ecef; }
        .file-info { flex: 1; }
        .file-name { font-weight: bold; color: #333; }
        .file-meta { color: #666; font-size: 0.9em; margin-top: 5px; }
        .file-actions { display: flex; gap: 10px; }
        
        .preview-section { margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        .preview-content { max-height: 400px; overflow-y: auto; }
        .preview-text { background: white; padding: 15px; border-radius: 4px; font-family: monospace; white-space: pre-wrap; }
        .preview-image { max-width: 100%; max-height: 400px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        
        /* Syntax highlighting styles */
        .preview-content pre {
            background: #f8f8f8;
            border: 1px solid #e1e1e1;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
            margin: 0;
        }
        
        .preview-content code {
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .upload-area { border: 2px dashed #007bff; border-radius: 8px; padding: 40px; text-align: center; margin-bottom: 20px; background: #f8f9fa; }
        .upload-area.dragover { background: #e3f2fd; border-color: #1976d2; }
        
        .hidden { display: none; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .success { color: #155724; background: #d4edda; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📁 Mini Drive Web</h1>
        </div>

        {% if not token %}
        <div class="auth-section">
            <div class="auth-form">
                <h3>🔐 Вхід</h3>
<form method="post" action="/login">
                    <div class="form-group">
                        <label>Користувач:</label>
                        <input name="username" placeholder="Введіть ім'я користувача" required />
                    </div>
                    <div class="form-group">
                        <label>Пароль:</label>
                        <input name="password" placeholder="Введіть пароль" type="password" required />
                    </div>
                    <button type="submit" class="btn">Увійти</button>
                </form>
            </div>

            <div class="auth-form">
                <h3>📝 Реєстрація</h3>
                <form method="post" action="/register">
                    <div class="form-group">
                        <label>Користувач:</label>
                        <input name="username" placeholder="Введіть ім'я користувача" required />
                    </div>
                    <div class="form-group">
                        <label>Пароль:</label>
                        <input name="password" placeholder="Введіть пароль" type="password" required />
                    </div>
                    <button type="submit" class="btn btn-success">Зареєструватися</button>
</form>
            </div>
        </div>
        {% endif %}

{% if token %}
        <div class="files-section">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3>📂 Мої файли</h3>
                <form method="post" action="/logout" style="margin: 0;">
                    <button type="submit" class="btn btn-danger">🚪 Вийти</button>
                </form>
            </div>
            
            <!-- Upload Area -->
            <div class="upload-area" onclick="document.getElementById('file-input').click()">
                <p>📤 Перетягніть файли сюди або натисніть для вибору</p>
                <input type="file" id="file-input" multiple style="display: none;" onchange="uploadFiles(this.files)">
            </div>

            <!-- Controls -->
            <div class="controls">
                <button class="btn" onclick="refreshFiles()">🔄 Оновити</button>
                <select id="filter-type" onchange="refreshFiles()">
                    <option value="all">Всі файли</option>
                    <option value="py">Python (.py)</option>
                    <option value="jpg">Зображення (.jpg)</option>
    </select>
                <select id="sort-order" onchange="refreshFiles()">
                    <option value="asc">Сортування: А-Я</option>
                    <option value="desc">Сортування: Я-А</option>
    </select>
            </div>

            <!-- Sync Section -->
            <div class="sync-section" style="margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f9f9f9;">
                <h4 style="margin-top: 0;">🔄 Синхронізація папки</h4>
                <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
                    <input type="file" id="folder-input" webkitdirectory directory multiple style="display: none;" onchange="selectSyncFolder(this)">
                    <button class="btn" onclick="document.getElementById('folder-input').click()">📁 Вибрати папку</button>
                    <span id="sync-folder-info" style="color: #666; font-size: 14px;"></span>
                    <button class="btn btn-success" onclick="syncUploadOnly()" disabled id="sync-upload-btn">⬆️ Завантажити</button>
                    <button class="btn btn-primary" onclick="syncDownloadOnly()" disabled id="sync-download-btn">⬇️ Завантажити</button>
                    <button class="btn btn-info" onclick="syncBidirectional()" disabled id="sync-bidirectional-btn">🔄 Синхронізувати</button>
                </div>
                <div id="sync-results" style="margin-top: 10px; display: none;"></div>
            </div>

            <!-- File List -->
            <div class="file-list" id="file-list">
                <!-- Files will be loaded here -->
            </div>

            <!-- Preview Section -->
            <div class="preview-section hidden" id="preview-section">
                <h4>👁️ Превʼю файлу</h4>
                <div class="preview-content" id="preview-content"></div>
            </div>
        </div>
        {% endif %}

        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="error">{{ message }}</div>
    {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <script>
        let currentFiles = [];
        
        function refreshFiles() {
            const filterType = document.getElementById('filter-type').value;
            const sortOrder = document.getElementById('sort-order').value;
            
            fetch(`/api/files?type=${filterType}&order=${sortOrder}`)
                .then(response => response.json())
                .then(files => {
                    currentFiles = files;
                    renderFiles(files);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Помилка завантаження файлів');
                });
        }

        function renderFiles(files) {
            const fileList = document.getElementById('file-list');
            fileList.innerHTML = '';
            
            if (files.length === 0) {
                fileList.innerHTML = '<p style="text-align: center; color: #666; padding: 40px;">Файли не знайдено</p>';
                return;
            }

            files.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item';
                fileItem.innerHTML = `
                    <div class="file-info">
                        <div class="file-name">${escapeHtml(file.name)}</div>
                        <div class="file-meta">
                            ${file.extension} • Завантажив: ${escapeHtml(file.uploader || 'Невідомо')} • 
                            ${new Date(file.created_at).toLocaleString('uk-UA')}
                        </div>
                    </div>
                    <div class="file-actions">
                        ${canPreview(file.extension) ? `<button class="btn" onclick="previewFile(${file.id})">👁️ Превʼю</button>` : ''}
                        <button class="btn btn-success" onclick="downloadFile(${file.id}, '${escapeHtml(file.name)}')">⬇️ Скачати</button>
                        <button class="btn btn-danger" onclick="deleteFile(${file.id})">🗑️ Видалити</button>
                    </div>
                `;
                fileList.appendChild(fileItem);
            });
        }

        function canPreview(extension) {
            return extension === '.py' || extension === '.jpg';
        }

        function previewFile(fileId) {
            const file = currentFiles.find(f => f.id === fileId);
            const previewSection = document.getElementById('preview-section');
            const previewContent = document.getElementById('preview-content');
            
            if (file.extension === '.py') {
                // For Python files, get JSON response
                fetch(`/api/files/${fileId}/preview`)
                    .then(response => {
                        console.log('Response status:', response.status);
                        console.log('Response headers:', response.headers);
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log('Preview data received:', data);
                        if (data.content) {
                            previewContent.innerHTML = `<pre><code class="language-python">${escapeHtml(data.content)}</code></pre>`;
                            // Apply syntax highlighting
                            if (window.Prism) {
                                Prism.highlightAll();
                            }
                            previewSection.classList.remove('hidden');
                            previewSection.scrollIntoView({ behavior: 'smooth' });
                        } else {
                            console.error('No content in response:', data);
                            alert('Файл порожній або не містить контенту');
                        }
                    })
                    .catch(error => {
                        console.error('Error loading preview:', error);
                        alert('Помилка завантаження превʼю: ' + error.message);
                    });
            } else if (file.extension === '.jpg') {
                // For JPG files, display image directly
                previewContent.innerHTML = `<img src="/api/files/${fileId}/preview" class="preview-image" alt="Preview" onload="document.getElementById('preview-section').classList.remove('hidden'); document.getElementById('preview-section').scrollIntoView({ behavior: 'smooth' });">`;
            }
        }

        function downloadFile(fileId, filename) {
            window.open(`/api/files/${fileId}/download`, '_blank');
        }

        function deleteFile(fileId) {
            if (!confirm('Ви впевнені, що хочете видалити цей файл?')) {
                return;
            }
            
            fetch(`/api/files/${fileId}`, { method: 'DELETE' })
                .then(response => {
                    if (response.ok) {
                        refreshFiles();
                        alert('Файл видалено');
                    } else {
                        alert('Помилка видалення файлу');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Помилка видалення файлу');
                });
        }

        function uploadFiles(files) {
            Array.from(files).forEach(file => {
                const formData = new FormData();
                formData.append('file', file);
                
                fetch('/api/files', {
                    method: 'POST',
                    body: formData
                })
                .then(response => {
                    if (response.ok) {
                        refreshFiles();
                        alert(`Файл "${file.name}" завантажено`);
                    } else {
                        alert(`Помилка завантаження файлу "${file.name}"`);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert(`Помилка завантаження файлу "${file.name}"`);
                });
            });
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        // Sync functions
        let selectedSyncFolder = null;

        function selectSyncFolder(input) {
            if (input.files && input.files.length > 0) {
                selectedSyncFolder = input.files;
                const folderName = input.files[0].webkitRelativePath.split('/')[0];
                document.getElementById('sync-folder-info').textContent = `Папка: ${folderName} (${input.files.length} файлів)`;
                
                // Enable sync buttons
                document.getElementById('sync-upload-btn').disabled = false;
                document.getElementById('sync-download-btn').disabled = false;
                document.getElementById('sync-bidirectional-btn').disabled = false;
            }
        }

        function syncUploadOnly() {
            if (!selectedSyncFolder) {
                alert('Спочатку виберіть папку');
                return;
            }
            performSync('upload_only');
        }

        function syncDownloadOnly() {
            if (!selectedSyncFolder) {
                alert('Спочатку виберіть папку');
                return;
            }
            performSync('download_only');
        }

        function syncBidirectional() {
            if (!selectedSyncFolder) {
                alert('Спочатку виберіть папку');
                return;
            }
            performSync('bidirectional');
        }

        function performSync(mode) {
            const resultsDiv = document.getElementById('sync-results');
            resultsDiv.style.display = 'block';
            resultsDiv.innerHTML = '<div style="color: #666;">⏳ Виконується синхронізація...</div>';

            // Create FormData with files
            const formData = new FormData();
            formData.append('mode', mode);
            
            // Add all files to FormData
            for (let i = 0; i < selectedSyncFolder.length; i++) {
                const file = selectedSyncFolder[i];
                // Only sync .py and .jpg files
                if (file.name.endsWith('.py') || file.name.endsWith('.jpg')) {
                    formData.append('files', file);
                }
            }

            fetch('/api/sync', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                displaySyncResults(data);
            })
            .catch(error => {
                console.error('Error:', error);
                resultsDiv.innerHTML = `<div style="color: red;">❌ Помилка синхронізації: ${error.message}</div>`;
            });
        }

        function displaySyncResults(results) {
            const resultsDiv = document.getElementById('sync-results');
            const totalOps = (results.uploaded || 0) + (results.downloaded || 0);
            const totalErrors = results.errors || 0;
            const totalSkipped = results.skipped || 0;

            let html = `<div style="background: white; padding: 10px; border-radius: 4px; border: 1px solid #ddd;">
                <strong>Синхронізація завершена:</strong><br>
                ✅ Оброблено: ${totalOps} файлів<br>
                ⏭️ Пропущено: ${totalSkipped} файлів<br>
                ❌ Помилок: ${totalErrors}`;

            if (results.files && results.files.length > 0) {
                html += '<br><br><strong>Деталі:</strong><ul style="margin: 5px 0; padding-left: 20px;">';
                results.files.slice(0, 10).forEach(file => {
                    html += `<li>${file}</li>`;
                });
                if (results.files.length > 10) {
                    html += `<li>... та ще ${results.files.length - 10} файлів</li>`;
                }
                html += '</ul>';
            }

            html += '</div>';
            resultsDiv.innerHTML = html;

            // Refresh file list
            refreshFiles();
        }

        // Drag and drop functionality
        const uploadArea = document.querySelector('.upload-area');
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            uploadFiles(e.dataTransfer.files);
        });

        // Load files on page load
        {% if token %}
        refreshFiles();
{% endif %}
    </script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
</body>
</html>
"""

TOKEN = None

@app.route("/", methods=["GET"])
def index():
    return render_template_string(TPL, token=TOKEN)


@app.route("/login", methods=["POST"])
def login():
    global TOKEN
    r = requests.post(f"{API_URL}/auth/login", json={"username": request.form.get('username'), "password": request.form.get('password')})
    if r.ok:
        TOKEN = r.json()["access_token"]
        flash("Успішний вхід!", "success")
    else:
        flash("Невірні облікові дані", "error")
    return redirect("/")


@app.route("/register", methods=["POST"])
def register():
    r = requests.post(f"{API_URL}/auth/register", json={"username": request.form.get('username'), "password": request.form.get('password')})
    if r.ok:
        flash("Реєстрація успішна! Тепер увійдіть.", "success")
    else:
        flash("Помилка реєстрації. Можливо, користувач вже існує.", "error")
    return redirect("/")


@app.route("/logout", methods=["POST"])
def logout():
    global TOKEN
    TOKEN = None
    flash("Ви вийшли з системи", "success")
    return redirect("/")


# API endpoints for AJAX
@app.route("/api/files", methods=["GET"])
def api_get_files():
    if not TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    
    ftype = request.args.get("type", "all")
    order = request.args.get("order", "desc")
    
    r = requests.get(f"{API_URL}/files", headers={"Authorization": f"Bearer {TOKEN}"}, params={"type": ftype, "sort_by": "uploader", "order": order})
    if r.ok:
        return jsonify(r.json())
    return jsonify({"error": "Failed to fetch files"}), 500


@app.route("/api/files", methods=["POST"])
def api_upload_file():
    if not TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Forward the file to the API server
    files = {'file': (file.filename, file.stream, file.content_type)}
    r = requests.post(f"{API_URL}/files", headers={"Authorization": f"Bearer {TOKEN}"}, files=files)
    
    if r.ok:
        return jsonify(r.json())
    return jsonify({"error": "Upload failed"}), 500


@app.route("/api/files/<int:file_id>/preview", methods=["GET"])
def api_preview_file(file_id):
    if not TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        r = requests.get(f"{API_URL}/files/{file_id}/preview", headers={"Authorization": f"Bearer {TOKEN}"})
        print(f"Server response status: {r.status_code}")
        print(f"Server response headers: {r.headers}")
        
        if r.ok:
            # Check if it's an image
            content_type = r.headers.get('content-type', '')
            if 'image' in content_type:
                # Return the image directly
                from flask import Response
                return Response(r.content, mimetype=content_type)
            else:
                # Return JSON for text files
                try:
                    json_data = r.json()
                    print(f"JSON data: {json_data}")
                    return jsonify(json_data)
                except Exception as e:
                    print(f"Error parsing JSON: {e}")
                    print(f"Response text: {r.text}")
                    return jsonify({"error": "Invalid JSON response"}), 500
        else:
            print(f"Server error: {r.status_code} - {r.text}")
            return jsonify({"error": f"Server error: {r.status_code}"}), r.status_code
    except Exception as e:
        print(f"Request error: {e}")
        return jsonify({"error": f"Request failed: {str(e)}"}), 500


@app.route("/api/files/<int:file_id>/download", methods=["GET"])
def api_download_file(file_id):
    if not TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    
    r = requests.get(f"{API_URL}/files/{file_id}/download", headers={"Authorization": f"Bearer {TOKEN}"})
    if r.ok:
        from flask import Response
        return Response(r.content, mimetype='application/octet-stream', headers={
            'Content-Disposition': f'attachment; filename="{file_id}"'
        })
    return jsonify({"error": "Download failed"}), 500


@app.route("/api/files/<int:file_id>", methods=["DELETE"])
def api_delete_file(file_id):
    if not TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    
    r = requests.delete(f"{API_URL}/files/{file_id}", headers={"Authorization": f"Bearer {TOKEN}"})
    if r.ok:
        return jsonify({"message": "File deleted"})
    return jsonify({"error": "Delete failed"}), 500


@app.route("/api/sync", methods=["POST"])
def api_sync():
    if not TOKEN:
        return jsonify({"error": "Unauthorized"}), 401
    
    mode = request.form.get('mode', 'upload_only')
    files = request.files.getlist('files')
    
    if not files:
        return jsonify({"error": "No files provided"}), 400
    
    try:
        # Create temporary directory for sync
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Save uploaded files to temp directory
            for file in files:
                if file.filename and (file.filename.endswith('.py') or file.filename.endswith('.jpg')):
                    file.save(temp_path / file.filename)
            
            # Create FolderSync instance
            sync = FolderSync(API_URL, TOKEN, temp_path)
            
            # Perform sync based on mode
            if mode == "upload_only":
                results = sync.sync_upload_only()
            elif mode == "download_only":
                results = sync.sync_download_only()
            elif mode == "bidirectional":
                results = sync.sync_bidirectional()
            else:
                return jsonify({"error": f"Unknown sync mode: {mode}"}), 400
            
            return jsonify(results)
            
    except Exception as e:
        print(f"Sync error: {e}")
        return jsonify({"error": f"Sync failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(port=8000, debug=True)
