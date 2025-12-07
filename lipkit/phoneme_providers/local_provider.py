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
    Uses local tool installation for offline phoneme extraction.
    
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
        progress_callback=None,
        **kwargs
    ) -> LipSyncData:
        """
        Extract phonemes using Rhubarb Lip Sync tool
        
        Args:
            audio_path: Path to audio file (MP3, M4A, OGG, WAV, etc.)
            language: Language code (Rhubarb supports en, de, fr, pt)
            progress_callback: Optional callback(message) for progress updates
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
        
        # Convert to WAV if necessary
        wav_path = audio_path
        from ..utils.audio_utils import convert_audio_to_wav
        
        if not audio_path.lower().endswith('.wav'):
            print(f"📦 Audio format conversion required")
            success, result = convert_audio_to_wav(audio_path)
            
            if not success:
                raise ExtractionError(
                    f"Cannot process audio format. {result}\n\n"
                    f"Supported formats: WAV, MP3, M4A, OGG, FLAC, AAC\n"
                    f"Install ffmpeg to enable format conversion."
                )
            
            wav_path = result
        
        # Run the extraction tool
        try:
            if progress_callback:
                progress_callback(0, "🎵 Processing audio file...")
            result = self._run_rhubarb(wav_path, language, progress_callback)
            if progress_callback:
                progress_callback(100, "📊 Parsing results...")
            return self._parse_rhubarb_output(result, audio_path)
        except Exception as e:
            raise ExtractionError(f"Phoneme extraction failed: {str(e)}")
        finally:
            # Clean up converted file if we created one
            if wav_path != audio_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                    print(f"✨ Cleaned up temporary WAV file")
                except:
                    pass
    
    def _run_rhubarb(self, audio_path: str, language: str, progress_callback=None) -> str:
        """Run Rhubarb Lip Sync tool with real-time progress tracking
        
        Rhubarb command format:
        rhubarb [options] <input file>
        
        Args:
            audio_path: Path to audio file
            language: Language code
            progress_callback: Optional callback(percent, message) for progress updates
        
        Returns JSON to stdout by default
        """
        import threading
        
        cmd = [
            self.tool_path,
            "-f", "json",  # JSON output format
            "-r", "pocketSphinx",  # Recognizer (pocketSphinx is most accurate)
            "--machineReadable",  # Enable machine-readable progress output!
            audio_path  # Input audio file
        ]
        
        print(f"🎤 Running Rhubarb: {' '.join(cmd)}")
        if progress_callback:
            progress_callback(0, "🎤 Starting Rhubarb analysis...")
        
        try:
            # Use Popen for real-time output monitoring
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1  # Line buffered
            )
            
            # Monitor stderr in background thread for progress (Rhubarb outputs progress to stderr)
            stderr_lines = []
            last_percent = 0
            stderr_done = threading.Event()
            
            def monitor_stderr():
                """Monitor Rhubarb stderr for machine-readable progress messages"""
                nonlocal last_percent
                try:
                    for line in process.stderr:
                        line = line.strip()
                        if not line:
                            continue
                        
                        stderr_lines.append(line)
                        
                        # Try to parse machine-readable JSON output
                        try:
                            event = json.loads(line)
                            event_type = event.get("type", "")
                            
                            if event_type == "progress":
                                # value is 0.0 to 1.0
                                value = event.get("value", 0)
                                percent = int(value * 100)
                                last_percent = percent
                                if progress_callback:
                                    progress_callback(percent, f"🔄 Processing: {percent}%")
                                print(f"Rhubarb: {percent}%")
                                
                            elif event_type == "start":
                                if progress_callback:
                                    progress_callback(0, "📂 Loading audio file...")
                                print("Rhubarb: Starting...")
                                
                            elif event_type == "failure":
                                reason = event.get("reason", "Unknown error")
                                print(f"Rhubarb ERROR: {reason}")
                                
                            elif event_type == "success":
                                if progress_callback:
                                    progress_callback(100, "✅ Analysis complete!")
                                print("Rhubarb: Success!")
                                
                        except json.JSONDecodeError:
                            # Not JSON, just log it
                            print(f"Rhubarb: {line}")
                            
                except Exception as e:
                    print(f"Rhubarb stderr monitor error: {e}")
                finally:
                    stderr_done.set()
            
            # Start stderr monitoring thread
            stderr_thread = threading.Thread(target=monitor_stderr, daemon=True)
            stderr_thread.start()
            
            # Read stdout (the JSON result) - with timeout
            print("Rhubarb: Waiting for stdout...")
            stdout_data = ""
            try:
                stdout_data, _ = process.communicate(timeout=600)  # 10 minute timeout
                print(f"Rhubarb: communicate() returned, stdout length: {len(stdout_data)}")
            except subprocess.TimeoutExpired:
                print("Rhubarb: TIMEOUT! Killing process...")
                process.kill()
                stdout_data, _ = process.communicate()
                raise ExtractionError("Rhubarb timed out after 10 minutes")
            
            # Wait for stderr thread to finish (with timeout!)
            print("Rhubarb: Waiting for stderr thread...")
            stderr_done.wait(timeout=5)
            stderr_thread.join(timeout=2)
            print("Rhubarb: stderr thread done")
            
            # Check result
            if process.returncode != 0:
                error_msg = '\n'.join(stderr_lines) or stdout_data or "Unknown error"
                print(f"❌ Rhubarb error output:\n{error_msg}")
                raise ExtractionError(f"Rhubarb failed with code {process.returncode}:\n{error_msg}")
            
            # Check if we got JSON output
            output = stdout_data.strip()
            if not output or not output.startswith('{'):
                stderr_msg = '\n'.join(stderr_lines)
                raise ExtractionError(f"Rhubarb didn't return JSON. Output:\n{output}\nStderr:\n{stderr_msg}")
            
            print(f"✅ Rhubarb succeeded - received {len(output)} bytes of JSON")
            if progress_callback:
                progress_callback(100, "✅ Rhubarb analysis complete")
            
            return output
            
        except subprocess.TimeoutExpired:
            process.kill()
            raise ExtractionError("Rhubarb timed out after 10 minutes")
    
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
