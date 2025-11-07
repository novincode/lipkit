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
    Local phoneme extraction using external tools like Rhubarb Lip Sync
    This is the FREE option - no API calls required, but needs tool installed
    
    Download Rhubarb: https://github.com/DanielSWolf/rhubarb-lip-sync
    """
    
    def __init__(self, tool_path: str = ""):
        """
        Initialize local provider
        
        Args:
            tool_path: Path to phoneme extraction tool executable (e.g., rhubarb)
        """
        self.tool_path = tool_path
        self._available = None
    
    @property
    def name(self) -> str:
        return "Local (Rhubarb)"
    
    @property
    def description(self) -> str:
        return "Local phoneme extraction using Rhubarb Lip Sync. Download from: github.com/DanielSWolf/rhubarb-lip-sync"
    
    def is_available(self) -> bool:
        """Check if local tool is available"""
        if self._available is not None:
            return self._available
        
        # If no tool path set, NOT available
        if not self.tool_path:
            self._available = False
            return False
        
        # Check if tool exists
        if not os.path.exists(self.tool_path):
            self._available = False
            return False
        
        # Try to run tool with --version or --help
        try:
            result = subprocess.run(
                [self.tool_path, "--version"],
                capture_output=True,
                timeout=5
            )
            self._available = result.returncode == 0
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
        Extract phonemes using Rhubarb Lip Sync tool
        
        Args:
            audio_path: Path to audio file
            language: Language code (Rhubarb supports en, de, fr, pt)
            **kwargs: Additional options
        
        Raises:
            ExtractionError: If tool is not available or extraction fails
        """
        if not self.validate_audio(audio_path):
            raise AudioFileError(f"Audio file not found or invalid: {audio_path}")
        
        # FAIL CLEARLY if no tool
        if not self.tool_path:
            raise ExtractionError(
                "No phoneme extraction tool configured.\n\n"
                "To use local phoneme extraction:\n"
                "1. Download Rhubarb Lip Sync from:\n"
                "   https://github.com/DanielSWolf/rhubarb-lip-sync/releases\n"
                "2. Extract the archive\n"
                "3. Go to Edit → Preferences → Extensions → LipKit\n"
                "4. Set 'Local Tool Path' to the rhubarb executable\n"
                "5. Try again"
            )
        
        # Check tool exists
        if not os.path.exists(self.tool_path):
            raise ExtractionError(
                f"Phoneme extraction tool not found at:\n{self.tool_path}\n\n"
                f"Please check the path in LipKit preferences."
            )
        
        # Run the extraction tool
        try:
            result = self._run_rhubarb(audio_path, language)
            return self._parse_rhubarb_output(result, audio_path)
        except Exception as e:
            raise ExtractionError(f"Phoneme extraction failed: {str(e)}")
    
    def _run_rhubarb(self, audio_path: str, language: str) -> str:
        """Run Rhubarb Lip Sync tool"""
        # Rhubarb command: rhubarb -f json audio.wav
        # Output format: JSON with mouthCues array
        
        cmd = [
            self.tool_path,
            "-f", "json",  # JSON output format
            audio_path
        ]
        
        # Add recognizer (default is pocketsphinx)
        # Rhubarb has 'pocketsphinx' (better) or 'phonetic' (faster but less accurate)
        cmd.extend(["--recognizer", "pocketsphinx"])
        
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown error"
            raise ExtractionError(f"Rhubarb failed: {error_msg}")
        
        return result.stdout
    
    def _parse_rhubarb_output(self, output: str, audio_path: str) -> LipSyncData:
        """Parse Rhubarb JSON output into LipSyncData
        
        Rhubarb outputs Preston Blair mouth shapes:
        A, B, C, D, E, F, G, H, X (9 shapes total)
        """
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            raise ExtractionError(f"Failed to parse Rhubarb output: {str(e)}")
        
        phonemes = []
        
        # Rhubarb format: {"mouthCues": [{"start": 0.0, "end": 0.5, "value": "X"}, ...]}
        if "mouthCues" in data:
            for i, cue in enumerate(data["mouthCues"]):
                # Get end time from next cue or use small duration
                if i < len(data["mouthCues"]) - 1:
                    end_time = data["mouthCues"][i + 1]["start"]
                else:
                    end_time = cue["start"] + 0.1
                
                phoneme = PhonemeData(
                    phoneme=cue["value"],  # A, B, C, D, E, F, G, H, X
                    start_time=cue["start"],
                    end_time=end_time,
                    confidence=1.0
                )
                phonemes.append(phoneme)
        else:
            raise ExtractionError("Invalid Rhubarb output format - no mouthCues found")
        
        if not phonemes:
            raise ExtractionError("No phonemes extracted from audio")
        
        duration = phonemes[-1].end_time if phonemes else 0.0
        
        return LipSyncData(
            phonemes=phonemes,
            duration=duration,
            language="en",
            phoneme_set="rhubarb",  # Rhubarb uses its own Preston Blair set
            metadata={
                "source": "rhubarb",
                "tool_path": self.tool_path,
                "mouth_shapes": "A, B, C, D, E, F, G, H, X (Preston Blair)"
            }
        )
