"""
Local phoneme provider - uses local tools for phoneme extraction
"""

import subprocess
import json
import os
from typing import List
from ..core import PhonemeProvider, LipSyncData, PhonemeData, AudioFileError, ExtractionError


class LocalPhonemeProvider(PhonemeProvider):
    """
    Local phoneme extraction using external tools like Rhubarb or Allosaurus
    This is the FREE option - no API calls required
    """
    
    def __init__(self, tool_path: str = ""):
        """
        Initialize local provider
        
        Args:
            tool_path: Path to phoneme extraction tool executable
        """
        self.tool_path = tool_path
        self._available = None
    
    @property
    def name(self) -> str:
        return "Local (Free)"
    
    @property
    def description(self) -> str:
        return "Local phoneme extraction using Rhubarb or custom tools. No internet required."
    
    def is_available(self) -> bool:
        """Check if local tool is available"""
        if self._available is not None:
            return self._available
        
        # Check if tool exists
        if not self.tool_path or not os.path.exists(self.tool_path):
            self._available = False
            return False
        
        # Try to run tool with --version or --help
        try:
            subprocess.run(
                [self.tool_path, "--version"],
                capture_output=True,
                timeout=5
            )
            self._available = True
        except (subprocess.SubprocessError, FileNotFoundError):
            self._available = False
        
        return self._available
    
    def get_supported_languages(self) -> List[str]:
        """Get supported languages"""
        # Most local tools support English primarily
        return ["en", "en-US", "en-GB"]
    
    def extract_phonemes(
        self, 
        audio_path: str, 
        language: str = "en",
        **kwargs
    ) -> LipSyncData:
        """
        Extract phonemes using local tool
        
        Args:
            audio_path: Path to audio file
            language: Language code
            **kwargs: Additional options (e.g., recognizer='pocketsphinx')
        """
        if not self.validate_audio(audio_path):
            raise AudioFileError(f"Audio file not found or invalid: {audio_path}")
        
        if not self.is_available():
            # If no tool available, return mock data for development
            return self._generate_mock_data(audio_path)
        
        # Run the extraction tool
        try:
            result = self._run_extraction_tool(audio_path, language, **kwargs)
            return self._parse_tool_output(result, audio_path)
        except Exception as e:
            raise ExtractionError(f"Failed to extract phonemes: {str(e)}")
    
    def _run_extraction_tool(self, audio_path: str, language: str, **kwargs) -> str:
        """Run external phoneme extraction tool"""
        # Example: rhubarb -f json -o output.json audio.wav
        # This will vary based on the actual tool being used
        
        output_format = kwargs.get("output_format", "json")
        
        cmd = [
            self.tool_path,
            "-f", output_format,
            audio_path
        ]
        
        # Add language if supported
        if language != "en":
            cmd.extend(["--language", language])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            raise ExtractionError(f"Tool failed: {result.stderr}")
        
        return result.stdout
    
    def _parse_tool_output(self, output: str, audio_path: str) -> LipSyncData:
        """Parse tool output into LipSyncData"""
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            raise ExtractionError(f"Failed to parse tool output: {str(e)}")
        
        # Parse based on Rhubarb-style output format
        # Adjust this based on actual tool output format
        phonemes = []
        
        if "mouthCues" in data:
            # Rhubarb format
            for cue in data["mouthCues"]:
                phoneme = PhonemeData(
                    phoneme=cue["value"],
                    start_time=cue["start"],
                    end_time=cue["end"] if "end" in cue else cue["start"] + 0.1,
                    confidence=1.0
                )
                phonemes.append(phoneme)
        elif "phonemes" in data:
            # Generic format
            for p in data["phonemes"]:
                phoneme = PhonemeData.from_dict(p)
                phonemes.append(phoneme)
        
        duration = data.get("duration", phonemes[-1].end_time if phonemes else 0.0)
        
        return LipSyncData(
            phonemes=phonemes,
            duration=duration,
            language=data.get("language", "en"),
            phoneme_set=data.get("phoneme_set", "arpabet"),
            metadata={"source": "local_tool", "tool_path": self.tool_path}
        )
    
    def _generate_mock_data(self, audio_path: str) -> LipSyncData:
        """
        Generate mock phoneme data for development/testing
        This allows the addon to work even without a phoneme extraction tool installed
        """
        # Get audio duration (simplified - would need actual audio library)
        duration = 5.0  # Mock duration
        
        # Generate sample phonemes - Preston Blair 9-shape pattern
        mock_phonemes = [
            PhonemeData("REST", 0.0, 0.5, 1.0),
            PhonemeData("M", 0.5, 0.7, 1.0),
            PhonemeData("AH", 0.7, 1.0, 1.0),
            PhonemeData("EE", 1.0, 1.3, 1.0),
            PhonemeData("REST", 1.3, 1.5, 1.0),
            PhonemeData("OH", 1.5, 1.8, 1.0),
            PhonemeData("OO", 1.8, 2.1, 1.0),
            PhonemeData("L", 2.1, 2.3, 1.0),
            PhonemeData("REST", 2.3, 3.0, 1.0),
        ]
        
        return LipSyncData(
            phonemes=mock_phonemes,
            duration=duration,
            language="en",
            phoneme_set="preston_blair",
            metadata={
                "source": "mock_data",
                "warning": "Using mock data - install phoneme extraction tool for real results"
            }
        )
