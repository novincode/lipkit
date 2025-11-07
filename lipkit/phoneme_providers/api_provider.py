"""
API-based phoneme provider for premium cloud service
"""

import json
from typing import List, Optional
from ..core import PhonemeProvider, LipSyncData, PhonemeData, NetworkError, ExtractionError, AudioFileError


class APIPhonemeProvider(PhonemeProvider):
    """
    Cloud API phoneme extraction service
    This is the PREMIUM option - requires API key and internet
    """
    
    def __init__(
        self, 
        api_key: str = "",
        endpoint: str = "https://api.lipkit.dev/v1/phonemes"
    ):
        """
        Initialize API provider
        
        Args:
            api_key: API key for authentication
            endpoint: API endpoint URL
        """
        self.api_key = api_key
        self.endpoint = endpoint
    
    @property
    def name(self) -> str:
        return "LipKit Cloud API (Premium)"
    
    @property
    def description(self) -> str:
        return "High-accuracy cloud-based phoneme extraction with multi-language support."
    
    def is_available(self) -> bool:
        """Check if API is available and key is valid"""
        if not self.api_key:
            return False
        
        # Would ping API health endpoint
        # For now, just check if key exists
        return len(self.api_key) > 0
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages from API"""
        # Premium API supports many languages
        return [
            "en", "en-US", "en-GB",
            "es", "fr", "de", "it", "pt",
            "ja", "ko", "zh", "ru"
        ]
    
    def extract_phonemes(
        self, 
        audio_path: str, 
        language: str = "en",
        **kwargs
    ) -> LipSyncData:
        """
        Extract phonemes using cloud API
        
        Args:
            audio_path: Path to audio file
            language: Language code
            **kwargs: Additional options (quality='high', model='whisper-large', etc.)
        """
        if not self.validate_audio(audio_path):
            raise AudioFileError(f"Audio file not found or invalid: {audio_path}")
        
        if not self.is_available():
            raise NetworkError("API key not configured or invalid")
        
        try:
            # Import requests only when needed (not always available in Blender)
            import requests
        except ImportError:
            raise NetworkError("requests library not available - cannot use API provider")
        
        # Prepare request
        quality = kwargs.get("quality", "high")
        model = kwargs.get("model", "auto")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                headers = {
                    'Authorization': f'Bearer {self.api_key}',
                    'User-Agent': 'LipKit-Blender/0.1.0'
                }
                params = {
                    'language': language,
                    'quality': quality,
                    'model': model,
                    'format': 'json'
                }
                
                response = requests.post(
                    self.endpoint,
                    files=files,
                    headers=headers,
                    params=params,
                    timeout=120  # 2 minute timeout
                )
            
            if response.status_code == 200:
                return self._parse_api_response(response.json())
            elif response.status_code == 401:
                raise NetworkError("Invalid API key")
            elif response.status_code == 429:
                raise NetworkError("API rate limit exceeded")
            elif response.status_code >= 500:
                raise NetworkError(f"API server error: {response.status_code}")
            else:
                raise NetworkError(f"API request failed: {response.status_code} - {response.text}")
        
        except requests.RequestException as e:
            raise NetworkError(f"Network error: {str(e)}")
        except Exception as e:
            raise ExtractionError(f"Failed to extract phonemes via API: {str(e)}")
    
    def _parse_api_response(self, data: dict) -> LipSyncData:
        """Parse API response into LipSyncData"""
        try:
            # Expected API response format:
            # {
            #     "phonemes": [...],
            #     "duration": 12.5,
            #     "language": "en",
            #     "phoneme_set": "arpabet",
            #     "confidence": 0.95,
            #     "metadata": {...}
            # }
            
            phonemes = []
            for p_data in data.get("phonemes", []):
                phoneme = PhonemeData(
                    phoneme=p_data["phoneme"],
                    start_time=p_data["start_time"],
                    end_time=p_data["end_time"],
                    confidence=p_data.get("confidence", 1.0),
                    metadata=p_data.get("metadata", {})
                )
                phonemes.append(phoneme)
            
            return LipSyncData(
                phonemes=phonemes,
                duration=data.get("duration", phonemes[-1].end_time if phonemes else 0.0),
                language=data.get("language", "en"),
                phoneme_set=data.get("phoneme_set", "arpabet"),
                metadata={
                    **data.get("metadata", {}),
                    "source": "api",
                    "api_confidence": data.get("confidence", 1.0)
                }
            )
        
        except (KeyError, IndexError, TypeError) as e:
            raise ExtractionError(f"Failed to parse API response: {str(e)}")


class CustomAPIProvider(PhonemeProvider):
    """
    Custom API endpoint provider
    Allows users to point to their own phoneme extraction service
    """
    
    def __init__(
        self, 
        endpoint: str,
        api_key: Optional[str] = None,
        headers: Optional[dict] = None
    ):
        """
        Initialize custom API provider
        
        Args:
            endpoint: Custom API endpoint URL
            api_key: Optional API key
            headers: Optional custom headers
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.headers = headers or {}
    
    @property
    def name(self) -> str:
        return "Custom API"
    
    @property
    def description(self) -> str:
        return "Connect to your own phoneme extraction API endpoint."
    
    def is_available(self) -> bool:
        """Check if custom endpoint is configured"""
        return bool(self.endpoint)
    
    def get_supported_languages(self) -> List[str]:
        """Languages depend on custom implementation"""
        return ["en"]  # Default to English
    
    def extract_phonemes(
        self, 
        audio_path: str, 
        language: str = "en",
        **kwargs
    ) -> LipSyncData:
        """Extract using custom API - similar to APIPhonemeProvider"""
        if not self.validate_audio(audio_path):
            raise AudioFileError(f"Audio file not found: {audio_path}")
        
        if not self.is_available():
            raise NetworkError("Custom API endpoint not configured")
        
        try:
            import requests
        except ImportError:
            raise NetworkError("requests library not available")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                headers = {**self.headers}
                
                if self.api_key:
                    headers['Authorization'] = f'Bearer {self.api_key}'
                
                params = {'language': language}
                
                response = requests.post(
                    self.endpoint,
                    files=files,
                    headers=headers,
                    params=params,
                    timeout=120
                )
            
            if response.status_code == 200:
                # Try to parse as LipSyncData JSON format
                return LipSyncData.from_dict(response.json())
            else:
                raise NetworkError(f"Custom API failed: {response.status_code}")
        
        except requests.RequestException as e:
            raise NetworkError(f"Network error: {str(e)}")
        except Exception as e:
            raise ExtractionError(f"Custom API error: {str(e)}")
