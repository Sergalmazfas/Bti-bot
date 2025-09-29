import os
import json
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import requests
from google.cloud import storage, secretmanager
from google.auth import default

logger = logging.getLogger(__name__)

class ForgeService:
    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.bucket_name = "btibot-processed"
        self._load_credentials()
        self._init_gcs_client()
    
    def _load_credentials(self):
        """Загружает секреты из Google Secret Manager"""
        try:
            client = secretmanager.SecretManagerServiceClient()
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'talkhint')
            
            # Получаем ForgeClientID
            name_id = f"projects/{project_id}/secrets/ForgeClientID/versions/latest"
            response_id = client.access_secret_version(request={"name": name_id})
            self.client_id = response_id.payload.data.decode("UTF-8")
            
            # Получаем ForgeClientSecret
            name_secret = f"projects/{project_id}/secrets/ForgeClientSecret/versions/latest"
            response_secret = client.access_secret_version(request={"name": name_secret})
            self.client_secret = response_secret.payload.data.decode("UTF-8")
            
            logger.info("Forge credentials loaded successfully")
            logger.info(f"Client ID: {self.client_id[:10]}...")
        except Exception as e:
            logger.error(f"Failed to load Forge credentials: {e}")
            raise
    
    def _init_gcs_client(self):
        """Инициализирует клиент Google Cloud Storage"""
        try:
            self.gcs_client = storage.Client()
            logger.info("GCS client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GCS client: {e}")
            raise
    
    def _get_access_token(self) -> str:
        """Получает access token для Forge API"""
        if self.access_token:
            return self.access_token
            
        try:
            logger.info("Requesting Forge access token...")
            url = "https://developer.api.autodesk.com/authentication/v2/token"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials',
                'scope': 'data:read data:write data:create bucket:create bucket:read'
            }
            
            logger.info(f"Authentication URL: {url}")
            logger.info(f"Client ID: {self.client_id[:10]}...")
            
            response = requests.post(url, data=data, timeout=30)
            logger.info(f"Authentication response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                raise Exception(f"Authentication failed: {response.status_code}")
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)
            
            logger.info(f"Forge access token obtained, expires in {expires_in} seconds")
            return self.access_token
            
        except Exception as e:
            logger.error(f"Failed to get Forge access token: {e}")
            raise
    
    def _create_bucket(self, bucket_name: str) -> bool:
        """Создает bucket в Forge если не существует"""
        try:
            token = self._get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Checking if bucket {bucket_name} exists...")
            
            # Проверяем существование bucket
            url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}"
            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"Bucket check response: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"Bucket {bucket_name} already exists")
                return True
            
            # Создаем bucket
            logger.info(f"Creating bucket {bucket_name}...")
            url = "https://developer.api.autodesk.com/oss/v2/buckets"
            data = {
                'bucketKey': bucket_name,
                'policyKey': 'temporary'
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            logger.info(f"Bucket creation response: {response.status_code}")
            
            if response.status_code == 201:
                logger.info(f"Bucket {bucket_name} created successfully")
                return True
            else:
                logger.error(f"Failed to create bucket: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            return False
    
    def upload_file_to_forge(self, file_path: str, object_name: str) -> Optional[str]:
        """Загружает файл в Forge OSS"""
        try:
            token = self._get_access_token()
            bucket_name = "btibot-forge-bucket"
            
            logger.info(f"Uploading file {file_path} to Forge bucket {bucket_name}")
            
            # Создаем bucket если нужно
            if not self._create_bucket(bucket_name):
                logger.error("Failed to create or access bucket")
                return None
            
            # Получаем URL для загрузки
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/octet-stream'
            }
            
            url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{object_name}"
            logger.info(f"Upload URL: {url}")
            
            # Загружаем файл
            with open(file_path, 'rb') as f:
                file_content = f.read()
                logger.info(f"File size: {len(file_content)} bytes")
                
                upload_response = requests.put(url, data=file_content, headers=headers, timeout=60)
                logger.info(f"Upload response: {upload_response.status_code}")
                
                if upload_response.status_code not in [200, 201]:
                    logger.error(f"Upload failed: {upload_response.status_code} - {upload_response.text}")
                    return None
            
            object_urn = f"urn:adsk.objects:os.object:{bucket_name}:{object_name}"
            logger.info(f"File uploaded successfully: {object_urn}")
            return object_urn
            
        except Exception as e:
            logger.error(f"Failed to upload file to Forge: {e}")
            return None
    
    def convert_ifc_to_dwg(self, object_urn: str) -> Optional[str]:
        """Конвертирует IFC в DWG через Model Derivative API"""
        try:
            token = self._get_access_token()
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            logger.info(f"Starting conversion for URN: {object_urn}")
            
            # Начинаем конвертацию
            url = "https://developer.api.autodesk.com/modelderivative/v2/designdata/job"
            data = {
                'input': {
                    'urn': object_urn
                },
                'output': {
                    'destination': {
                        'region': 'us'
                    },
                    'formats': [
                        {
                            'type': 'dwg',
                            'views': ['2d']
                        }
                    ]
                }
            }
            
            logger.info(f"Conversion request URL: {url}")
            logger.info(f"Conversion request data: {json.dumps(data, indent=2)}")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            logger.info(f"Conversion response: {response.status_code}")
            
            if response.status_code not in [200, 201, 202]:
                logger.error(f"Conversion request failed: {response.status_code} - {response.text}")
                return None
            
            job_id = response.headers.get('X-Resource-Id')
            logger.info(f"Conversion job started: {job_id}")
            
            # Ждем завершения конвертации
            return self._wait_for_conversion_completion(object_urn, token)
            
        except Exception as e:
            logger.error(f"Failed to convert IFC to DWG: {e}")
            return None
    
    def _wait_for_conversion_completion(self, object_urn: str, token: str, max_wait_time: int = 300) -> Optional[str]:
        """Ждет завершения конвертации"""
        try:
            headers = {'Authorization': f'Bearer {token}'}
            url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{object_urn}/manifest"
            
            logger.info(f"Waiting for conversion completion, max wait: {max_wait_time}s")
            
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                logger.info(f"Checking conversion status... ({int(time.time() - start_time)}s elapsed)")
                
                response = requests.get(url, headers=headers, timeout=30)
                logger.info(f"Manifest check response: {response.status_code}")
                
                if response.status_code == 200:
                    manifest = response.json()
                    status = manifest.get('status')
                    logger.info(f"Conversion status: {status}")
                    
                    if status == 'success':
                        logger.info("Conversion completed successfully")
                        return self._download_converted_file(object_urn, token)
                    elif status == 'failed':
                        logger.error("Conversion failed")
                        logger.error(f"Manifest: {json.dumps(manifest, indent=2)}")
                        return None
                    elif status == 'inprogress':
                        logger.info("Conversion in progress, waiting...")
                    else:
                        logger.warning(f"Unknown status: {status}")
                
                time.sleep(10)  # Ждем 10 секунд перед следующей проверкой
            
            logger.error("Conversion timeout")
            return None
            
        except Exception as e:
            logger.error(f"Error waiting for conversion: {e}")
            return None
    
    def _download_converted_file(self, object_urn: str, token: str) -> Optional[str]:
        """Скачивает конвертированный файл"""
        try:
            headers = {'Authorization': f'Bearer {token}'}
            url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{object_urn}/manifest"
            
            logger.info(f"Downloading converted file from: {url}")
            
            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"Manifest download response: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Failed to get manifest: {response.status_code} - {response.text}")
                return None
            
            manifest = response.json()
            logger.info(f"Manifest: {json.dumps(manifest, indent=2)}")
            
            derivatives = manifest.get('derivatives', [])
            logger.info(f"Found {len(derivatives)} derivatives")
            
            for derivative in derivatives:
                output_type = derivative.get('outputType')
                logger.info(f"Checking derivative with outputType: {output_type}")
                
                if output_type == 'dwg':
                    children = derivative.get('children', [])
                    logger.info(f"Found {len(children)} children in DWG derivative")
                    
                    for child in children:
                        child_urn = child.get('urn')
                        if child_urn:
                            logger.info(f"Downloading child: {child_urn}")
                            return self._download_and_save_to_gcs(child_urn, token)
            
            logger.error("No DWG file found in conversion result")
            return None
            
        except Exception as e:
            logger.error(f"Failed to download converted file: {e}")
            return None
    
    def _download_and_save_to_gcs(self, download_urn: str, token: str) -> Optional[str]:
        """Скачивает файл и сохраняет в GCS"""
        try:
            logger.info(f"Downloading and saving to GCS: {download_urn}")
            
            # Получаем URL для скачивания
            headers = {'Authorization': f'Bearer {token}'}
            url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{download_urn}/manifest"
            
            response = requests.get(url, headers=headers, timeout=30)
            logger.info(f"Download manifest response: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Failed to get download manifest: {response.status_code} - {response.text}")
                return None
            
            manifest = response.json()
            logger.info(f"Download manifest: {json.dumps(manifest, indent=2)}")
            
            # Скачиваем файл
            download_url = manifest.get('urn')
            if not download_url:
                logger.error("No download URL found in manifest")
                return None
            
            logger.info(f"Downloading file from: {download_url}")
            file_response = requests.get(download_url, timeout=60)
            logger.info(f"File download response: {file_response.status_code}")
            
            if file_response.status_code != 200:
                logger.error(f"Failed to download file: {file_response.status_code} - {file_response.text}")
                return None
            
            # Сохраняем в GCS
            current_date = datetime.now().strftime('%Y-%m-%d')
            file_name = f"converted_{int(time.time())}.dwg"
            gcs_path = f"processed/{current_date}/{file_name}"
            
            logger.info(f"Saving to GCS: gs://{self.bucket_name}/{gcs_path}")
            
            bucket = self.gcs_client.bucket(self.bucket_name)
            blob = bucket.blob(gcs_path)
            blob.upload_from_string(file_response.content, content_type='application/dwg')
            
            gcs_url = f"gs://{self.bucket_name}/{gcs_path}"
            logger.info(f"File saved to GCS: {gcs_url}")
            return gcs_url
            
        except Exception as e:
            logger.error(f"Failed to download and save to GCS: {e}")
            return None

def upload_ifc_to_forge_and_get_dwg(file_path: str) -> Optional[str]:
    """
    Основная функция для загрузки IFC файла в Forge и получения DWG
    
    Args:
        file_path: Путь к IFC файлу
        
    Returns:
        URL файла в GCS или None в случае ошибки
    """
    try:
        logger.info(f"Starting IFC to DWG conversion for file: {file_path}")
        
        forge_service = ForgeService()
        
        # Генерируем уникальное имя для объекта
        object_name = f"ifc_{int(time.time())}.ifc"
        logger.info(f"Generated object name: {object_name}")
        
        # Загружаем файл в Forge
        logger.info("Step 1: Uploading file to Forge...")
        object_urn = forge_service.upload_file_to_forge(file_path, object_name)
        if not object_urn:
            logger.error("Failed to upload file to Forge")
            return None
        
        logger.info(f"File uploaded successfully: {object_urn}")
        
        # Конвертируем IFC в DWG
        logger.info("Step 2: Converting IFC to DWG...")
        gcs_url = forge_service.convert_ifc_to_dwg(object_urn)
        if not gcs_url:
            logger.error("Failed to convert IFC to DWG")
            return None
        
        logger.info(f"Successfully processed IFC file: {gcs_url}")
        return gcs_url
        
    except Exception as e:
        logger.error(f"Error in upload_ifc_to_forge_and_get_dwg: {e}")
        return None
