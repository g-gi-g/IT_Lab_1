import time
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
import os

import requests


class FolderSync:
    def __init__(self, api_url: str, token: str, local_folder: Path) -> None:
        self.api_url = api_url.rstrip('/')
        self.token = token
        self.local_folder = local_folder
        self.last_sync_time = 0
        self.file_hashes = {}  # Track file hashes to detect changes

    def headers(self):
        return {"Authorization": f"Bearer {self.token}"}

    def get_file_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file content"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception:
            return ""

    def get_remote_files(self) -> Dict[str, Any]:
        """Get list of remote files from server"""
        try:
            response = requests.get(f"{self.api_url}/files", headers=self.headers())
            if response.ok:
                files = response.json()
                return {file['name']: file for file in files}
        except Exception as e:
            print(f"Error fetching remote files: {e}")
        return {}

    def upload_file(self, file_path: Path) -> bool:
        """Upload a single file to server"""
        try:
            with open(file_path, 'rb') as f:
                response = requests.post(
                    f"{self.api_url}/files", 
                    headers=self.headers(), 
                    files={"file": (file_path.name, f)}
                )
                return response.ok
        except Exception as e:
            print(f"Error uploading {file_path.name}: {e}")
            return False

    def download_file(self, remote_file: Dict[str, Any], local_path: Path) -> bool:
        """Download a file from server"""
        try:
            response = requests.get(
                f"{self.api_url}/files/{remote_file['id']}/download", 
                headers=self.headers()
            )
            if response.ok:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            print(f"Error downloading {remote_file['name']}: {e}")
        return False

    def sync_upload_only(self) -> Dict[str, Any]:
        """Upload-only sync: upload new/changed local files to server"""
        results = {
            'uploaded': 0,
            'skipped': 0,
            'errors': 0,
            'files': []
        }
        
        if not self.local_folder.exists():
            print(f"Local folder {self.local_folder} does not exist")
            return results

        # Get remote files to check for conflicts
        remote_files = self.get_remote_files()
        
        for path in self.local_folder.glob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".py", ".jpg"}:
                continue
                
            # Check if file has changed
            current_hash = self.get_file_hash(path)
            if path.name in self.file_hashes and self.file_hashes[path.name] == current_hash:
                results['skipped'] += 1
                continue
                
            # Upload file
            if self.upload_file(path):
                self.file_hashes[path.name] = current_hash
                results['uploaded'] += 1
                results['files'].append(f"✅ Завантажено: {path.name}")
            else:
                results['errors'] += 1
                results['files'].append(f"❌ Помилка: {path.name}")
        
        return results

    def sync_download_only(self) -> Dict[str, Any]:
        """Download-only sync: download files from server to local folder"""
        results = {
            'downloaded': 0,
            'skipped': 0,
            'errors': 0,
            'files': []
        }
        
        # Create local folder if it doesn't exist
        self.local_folder.mkdir(parents=True, exist_ok=True)
        
        # Get remote files
        remote_files = self.get_remote_files()
        
        for name, remote_file in remote_files.items():
            local_path = self.local_folder / name
            
            # Skip if file already exists and is newer
            if local_path.exists():
                local_mtime = local_path.stat().st_mtime
                # Convert remote timestamp to local time
                try:
                    remote_mtime = remote_file.get('updated_at', 0)
                    if isinstance(remote_mtime, str):
                        # Parse ISO format timestamp
                        import datetime
                        remote_mtime = datetime.datetime.fromisoformat(remote_mtime.replace('Z', '+00:00')).timestamp()
                    
                    if local_mtime >= remote_mtime:
                        results['skipped'] += 1
                        continue
                except Exception:
                    pass  # If we can't compare, download anyway
            
            # Download file
            if self.download_file(remote_file, local_path):
                results['downloaded'] += 1
                results['files'].append(f"✅ Завантажено: {name}")
            else:
                results['errors'] += 1
                results['files'].append(f"❌ Помилка: {name}")
        
        return results

    def sync_bidirectional(self) -> Dict[str, Any]:
        """Bidirectional sync: upload local changes and download remote changes"""
        results = {
            'uploaded': 0,
            'downloaded': 0,
            'skipped': 0,
            'errors': 0,
            'files': []
        }
        
        # First, download remote files
        download_results = self.sync_download_only()
        results.update(download_results)
        
        # Then, upload local files
        upload_results = self.sync_upload_only()
        results['uploaded'] += upload_results['uploaded']
        results['skipped'] += upload_results['skipped']
        results['errors'] += upload_results['errors']
        results['files'].extend(upload_results['files'])
        
        return results

    def sync_once(self, mode: str = "upload_only") -> Dict[str, Any]:
        """Perform one-time sync with specified mode"""
        if mode == "upload_only":
            return self.sync_upload_only()
        elif mode == "download_only":
            return self.sync_download_only()
        elif mode == "bidirectional":
            return self.sync_bidirectional()
        else:
            return {"error": f"Unknown sync mode: {mode}"}

    def run_watch(self, interval_seconds: int = 5, mode: str = "upload_only"):
        """Run continuous sync in background"""
        while True:
            try:
                results = self.sync_once(mode)
                if results.get('uploaded', 0) > 0 or results.get('downloaded', 0) > 0:
                    print(f"Sync completed: {results}")
            except Exception as e:
                print(f"Sync error: {e}")
            time.sleep(interval_seconds)


