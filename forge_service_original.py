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
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'swiftchair')
            
            # Получаем ForgeClientID
            name_id = f"projects/{project_id}/secrets/ForgeClientID/versions/latest"
            response_id = client.access_secret_version(request={"name": name_id})
            self.client_id = response_id.payload.data.decode("UTF-8")
            
            # Получаем ForgeClientSecret
            name_secret = f"projects/{project_id}/secrets/ForgeClientSecret/versions/latest"
            response_secret = client.access_secret_version(request={"name": name_secret})
            self.client_secret = response_secret.payload.data.decode("UTF-8")
            
            logger.info("Forge credentials loaded successfully")
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
            url = "https://developer.api.autodesk.com/authentication/v1/authenticate"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'client_credentials',
                'scope': 'data:read data:write data:create bucket:create bucket:read'
            }
            
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            logger.info("Forge access token obtained")
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
            
            # Проверяем существование bucket
            url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Bucket {bucket_name} already exists")
                return True
            
            # Создаем bucket
            url = "https://developer.api.autodesk.com/oss/v2/buckets"
            data = {
                'bucketKey': bucket_name,
                'policyKey': 'temporary'
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Bucket {bucket_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create bucket {bucket_name}: {e}")
            return False
    
    def upload_file_to_forge(self, file_path: str, object_name: str) -> Optional[str]:
        """Загружает файл в Forge OSS"""
        try:
            token = self._get_access_token()
            bucket_name = "btibot-forge-bucket"
            
            # Создаем bucket если нужно
            self._create_bucket(bucket_name)
            
            # Получаем URL для загрузки
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            url = f"https://developer.api.autodesk.com/oss/v2/buckets/{bucket_name}/objects/{object_name}"
            
            # Загружаем файл
            with open(file_path, 'rb') as f:
                upload_response = requests.put(url, data=f, headers=headers, timeout=60)
                upload_response.raise_for_status()
            
            logger.info(f"File uploaded to Forge: {object_name}")
            return f"urn:adsk.objects:os.object:{bucket_name}:{object_name}"
            
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
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
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
            
            start_time = time.time()
            while time.time() - start_time < max_wait_time:
                response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    manifest = response.json()
                    if manifest.get('status') == 'success':
                        logger.info("Conversion completed successfully")
                        return self._download_converted_file(object_urn, token)
                    elif manifest.get('status') == 'failed':
                        logger.error("Conversion failed")
                        return None
                
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
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            manifest = response.json()
            derivatives = manifest.get('derivatives', [])
            
            for derivative in derivatives:
                if derivative.get('outputType') == 'dwg':
                    # Получаем URL для скачивания
                    download_url = derivative.get('children', [{}])[0].get('urn')
                    if download_url:
                        return self._download_and_save_to_gcs(download_url, token)
            
            logger.error("No DWG file found in conversion result")
            return None
            
        except Exception as e:
            logger.error(f"Failed to download converted file: {e}")
            return None
    
    def _download_and_save_to_gcs(self, download_urn: str, token: str) -> Optional[str]:
        """Скачивает файл и сохраняет в GCS"""
        try:
            # Получаем URL для скачивания
            headers = {'Authorization': f'Bearer {token}'}
            url = f"https://developer.api.autodesk.com/modelderivative/v2/designdata/{download_urn}/manifest"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Скачиваем файл
            download_url = response.json().get('urn')
            if not download_url:
                logger.error("No download URL found")
                return None
            
            file_response = requests.get(download_url, timeout=60)
            file_response.raise_for_status()
            
            # Сохраняем в GCS
            current_date = datetime.now().strftime('%Y-%m-%d')
            file_name = f"converted_{int(time.time())}.dwg"
            gcs_path = f"processed/{current_date}/{file_name}"
            
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
        forge_service = ForgeService()
        
        # Генерируем уникальное имя для объекта
        object_name = f"ifc_{int(time.time())}.ifc"
        
        # Загружаем файл в Forge
        object_urn = forge_service.upload_file_to_forge(file_path, object_name)
        if not object_urn:
            logger.error("Failed to upload file to Forge")
            return None
        
        # Конвертируем IFC в DWG
        gcs_url = forge_service.convert_ifc_to_dwg(object_urn)
        if not gcs_url:
            logger.error("Failed to convert IFC to DWG")
            return None
        
        logger.info(f"Successfully processed IFC file: {gcs_url}")
        return gcs_url
        
    except Exception as e:
        logger.error(f"Error in upload_ifc_to_forge_and_get_dwg: {e}")
        return None
