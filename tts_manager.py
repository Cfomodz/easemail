#!/usr/bin/env python3
"""
Text-to-Speech Manager for Email Triage System
Supports multiple TTS providers including ElevenLabs Flash v2.5
"""

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import time
import queue
import io

# Optional imports - graceful degradation if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    import pygame
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

try:
    import playsound
    HAS_PLAYSOUND = True
except ImportError:
    HAS_PLAYSOUND = False


class TTSManager:
    """Manages text-to-speech functionality with multiple provider support"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get('enable_tts', True)
        self.provider = config.get('tts_provider', 'pyttsx3')
        
        # Initialize providers
        self.pyttsx3_engine = None
        self.elevenlabs_session = None
        
        # Interruption and streaming control
        self.interrupt_flag = threading.Event()
        self.current_playback_thread = None
        self.audio_queue = queue.Queue()
        self.is_playing = threading.Event()
        
        if self.enabled:
            self._init_providers()
    
    def _init_providers(self):
        """Initialize available TTS providers"""
        # Initialize pyttsx3 as fallback
        if HAS_PYTTSX3:
            try:
                self.pyttsx3_engine = pyttsx3.init()
                self.pyttsx3_engine.setProperty('rate', 180)
                self.pyttsx3_engine.setProperty('volume', 0.9)
                
                # Try to set a better voice if available
                voices = self.pyttsx3_engine.getProperty('voices')
                if voices:
                    # Prefer female voices or voices with "english" in the name
                    for voice in voices:
                        if 'english' in voice.name.lower() or 'female' in voice.name.lower():
                            self.pyttsx3_engine.setProperty('voice', voice.id)
                            break
                
                print("✅ pyttsx3 TTS initialized")
            except Exception as e:
                print(f"⚠️  pyttsx3 initialization failed: {e}")
                self.pyttsx3_engine = None
        
        # Initialize ElevenLabs
        if HAS_REQUESTS and self.config.get('elevenlabs_api_key'):
            try:
                self.elevenlabs_session = requests.Session()
                self.elevenlabs_session.headers.update({
                    'xi-api-key': self.config['elevenlabs_api_key'],
                    'Content-Type': 'application/json'
                })
                
                # Test the API key
                response = self.elevenlabs_session.get('https://api.elevenlabs.io/v1/user')
                if response.status_code == 200:
                    print("✅ ElevenLabs TTS initialized")
                else:
                    print(f"⚠️  ElevenLabs API test failed: {response.status_code}")
                    self.elevenlabs_session = None
            except Exception as e:
                print(f"⚠️  ElevenLabs initialization failed: {e}")
                self.elevenlabs_session = None
        
        # Initialize audio playback
        if HAS_PYGAME:
            try:
                pygame.mixer.init()
                print("✅ pygame audio initialized")
            except Exception as e:
                print(f"⚠️  pygame initialization failed: {e}")
    
    def speak(self, text: str, priority: str = "normal", interruptible: bool = True) -> bool:
        """
        Speak text using the configured TTS provider
        
        Args:
            text: Text to speak
            priority: "high", "normal", or "low" - affects processing
            interruptible: Whether this speech can be interrupted
            
        Returns:
            bool: True if speech was successful
        """
        if not self.enabled or not text.strip():
            return False
        
        # Interrupt any current playback if this is interruptible
        if interruptible:
            self.interrupt_current_speech()
        
        # Clean up text for better speech
        clean_text = self._clean_text_for_speech(text)
        
        # Choose provider based on configuration and availability
        if self.provider == "elevenlabs" and self.elevenlabs_session:
            return self._speak_elevenlabs_streaming(clean_text, priority, interruptible)
        elif self.provider == "pyttsx3" and self.pyttsx3_engine:
            return self._speak_pyttsx3(clean_text, interruptible)
        else:
            # Fallback to any available provider
            if self.elevenlabs_session:
                return self._speak_elevenlabs_streaming(clean_text, priority, interruptible)
            elif self.pyttsx3_engine:
                return self._speak_pyttsx3(clean_text, interruptible)
            else:
                print(f"🔊 TTS: {clean_text}")  # Text fallback
                return True
    
    def interrupt_current_speech(self):
        """Interrupt any currently playing speech"""
        self.interrupt_flag.set()
        
        # Stop pygame if playing
        if HAS_PYGAME and self.is_playing.is_set():
            try:
                pygame.mixer.music.stop()
            except:
                pass
        
        # Wait for current playback to stop
        if self.current_playback_thread and self.current_playback_thread.is_alive():
            self.current_playback_thread.join(timeout=0.5)
        
        # Clear the interrupt flag for next use
        self.interrupt_flag.clear()
        self.is_playing.clear()
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text to make it more suitable for speech"""
        # Remove or replace problematic characters
        replacements = {
            '@': ' at ',
            '#': ' number ',
            '&': ' and ',
            '%': ' percent ',
            '$': ' dollars ',
            '€': ' euros ',
            '£': ' pounds ',
            '→': ' goes to ',
            '←': ' comes from ',
            '✅': ' success ',
            '❌': ' error ',
            '⚠️': ' warning ',
            '🔊': '',
            '📧': ' email ',
            '🗑️': ' trash ',
            '⏰': ' later ',
            '⚡': ' action needed ',
            '🤖': ' AI ',
        }
        
        clean_text = text
        for old, new in replacements.items():
            clean_text = clean_text.replace(old, new)
        
        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())
        
        # Limit length for better performance
        if len(clean_text) > 500:
            clean_text = clean_text[:497] + "..."
        
        return clean_text
    
    def _speak_elevenlabs_streaming(self, text: str, priority: str = "normal", interruptible: bool = True) -> bool:
        """Speak using ElevenLabs API with streaming"""
        try:
            voice_id = self.config.get('elevenlabs_voice_id', 'Z9hrfEHGU3dykHntWvIY')
            model = self.config.get('elevenlabs_model', 'eleven_flash_v2_5')
            
            # Prepare request data for streaming
            data = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.2,
                    "use_speaker_boost": True
                }
            }
            
            # Add optimization settings for Flash v2.5
            if model == "eleven_flash_v2_5":
                data["voice_settings"]["optimize_streaming_latency"] = 4  # Max optimization
                data["voice_settings"]["output_format"] = "mp3_44100_128"
            
            # Use streaming endpoint
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
            
            # Make streaming request
            response = self.elevenlabs_session.post(url, json=data, stream=True)
            
            if response.status_code == 200:
                return self._play_streaming_audio(response, interruptible)
            else:
                print(f"⚠️  ElevenLabs streaming error: {response.status_code}")
                # Fallback to non-streaming
                return self._speak_elevenlabs_fallback(text, priority, interruptible)
                
        except Exception as e:
            print(f"⚠️  ElevenLabs streaming error: {e}")
            return self._speak_pyttsx3(text, interruptible)  # Fallback
    
    def _speak_elevenlabs_fallback(self, text: str, priority: str = "normal", interruptible: bool = True) -> bool:
        """Non-streaming ElevenLabs fallback"""
        try:
            voice_id = self.config.get('elevenlabs_voice_id', 'Z9hrfEHGU3dykHntWvIY')
            model = self.config.get('elevenlabs_model', 'eleven_flash_v2_5')
            
            data = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.2,
                    "use_speaker_boost": True
                }
            }
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            response = self.elevenlabs_session.post(url, json=data)
            
            if response.status_code == 200:
                # Save audio to temporary file
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                    temp_file.write(response.content)
                    temp_path = temp_file.name
                
                # Play audio with interruption support
                success = self._play_audio_file_interruptible(temp_path, interruptible)
                
                # Clean up
                try:
                    os.unlink(temp_path)
                except:
                    pass
                
                return success
            else:
                print(f"⚠️  ElevenLabs API error: {response.status_code}")
                return self._speak_pyttsx3(text, interruptible)
                
        except Exception as e:
            print(f"⚠️  ElevenLabs fallback error: {e}")
            return self._speak_pyttsx3(text, interruptible)
    
    def _speak_pyttsx3(self, text: str, interruptible: bool = True) -> bool:
        """Speak using pyttsx3"""
        if not self.pyttsx3_engine:
            print(f"🔊 TTS: {text}")  # Text fallback
            return True
        
        try:
            if interruptible:
                # For interruptible speech, we need to check periodically
                def speak_with_interrupt():
                    self.pyttsx3_engine.say(text)
                    self.pyttsx3_engine.runAndWait()
                
                self.current_playback_thread = threading.Thread(target=speak_with_interrupt, daemon=True)
                self.current_playback_thread.start()
                
                # Wait for completion or interruption
                while self.current_playback_thread.is_alive():
                    if self.interrupt_flag.is_set():
                        try:
                            self.pyttsx3_engine.stop()
                        except:
                            pass
                        break
                    time.sleep(0.1)
            else:
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
            
            return True
        except Exception as e:
            print(f"⚠️  pyttsx3 TTS error: {e}")
            print(f"🔊 TTS: {text}")  # Text fallback
            return True
    
    def _play_streaming_audio(self, response, interruptible: bool = True) -> bool:
        """Play streaming audio from ElevenLabs"""
        try:
            # Create a temporary file to buffer the stream
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name
                
                # Stream audio data and write to file
                for chunk in response.iter_content(chunk_size=1024):
                    if interruptible and self.interrupt_flag.is_set():
                        break
                    if chunk:
                        temp_file.write(chunk)
                
                # If we were interrupted during streaming, don't play
                if interruptible and self.interrupt_flag.is_set():
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    return False
            
            # Play the buffered audio
            success = self._play_audio_file_interruptible(temp_path, interruptible)
            
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return success
            
        except Exception as e:
            print(f"⚠️  Streaming audio error: {e}")
            return False
    
    def _play_audio_file_interruptible(self, file_path: str, interruptible: bool = True) -> bool:
        """Play audio file with interruption support"""
        def play_audio():
            self.is_playing.set()
            try:
                if HAS_PYGAME:
                    pygame.mixer.music.load(file_path)
                    pygame.mixer.music.play()
                    
                    # Wait for playback to complete or interruption
                    while pygame.mixer.music.get_busy():
                        if interruptible and self.interrupt_flag.is_set():
                            pygame.mixer.music.stop()
                            break
                        time.sleep(0.1)
                else:
                    # Fallback to system command
                    if os.name == 'posix':
                        os.system(f"mpg123 -q '{file_path}' 2>/dev/null &")
                    elif os.name == 'nt':
                        os.system(f'start /min "" "{file_path}"')
            except Exception as e:
                print(f"⚠️  Audio playback error: {e}")
            finally:
                self.is_playing.clear()
        
        if interruptible:
            self.current_playback_thread = threading.Thread(target=play_audio, daemon=True)
            self.current_playback_thread.start()
            
            # Wait for completion or interruption
            self.current_playback_thread.join()
        else:
            play_audio()
        
        return True
    
    def _play_audio_file(self, file_path: str) -> bool:
        """Play audio file using available audio library"""
        # Try pygame first
        if HAS_PYGAME:
            try:
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                return True
            except Exception as e:
                print(f"⚠️  pygame playback error: {e}")
        
        # Try playsound as fallback
        if HAS_PLAYSOUND:
            try:
                playsound.playsound(file_path)
                return True
            except Exception as e:
                print(f"⚠️  playsound error: {e}")
        
        # System command fallback
        try:
            if os.name == 'posix':  # Linux/macOS
                os.system(f"mpg123 -q '{file_path}' 2>/dev/null || ffplay -nodisp -autoexit -v quiet '{file_path}' 2>/dev/null")
            elif os.name == 'nt':  # Windows
                os.system(f'start /min "" "{file_path}"')
            return True
        except Exception as e:
            print(f"⚠️  System audio playback error: {e}")
            return False
    
    def speak_async(self, text: str, priority: str = "normal"):
        """Speak text asynchronously (non-blocking)"""
        if not self.enabled:
            return
        
        def speak_thread():
            self.speak(text, priority)
        
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
    
    def set_voice_settings(self, **kwargs):
        """Update voice settings for ElevenLabs"""
        if 'voice_id' in kwargs:
            self.config['elevenlabs_voice_id'] = kwargs['voice_id']
        if 'model' in kwargs:
            self.config['elevenlabs_model'] = kwargs['model']
        if 'stability' in kwargs:
            self.config['elevenlabs_stability'] = kwargs['stability']
        if 'similarity_boost' in kwargs:
            self.config['elevenlabs_similarity_boost'] = kwargs['similarity_boost']
    
    def list_available_voices(self) -> Dict[str, Any]:
        """List available voices from ElevenLabs"""
        if not self.elevenlabs_session:
            return {"error": "ElevenLabs not initialized"}
        
        try:
            response = self.elevenlabs_session.get('https://api.elevenlabs.io/v1/voices')
            if response.status_code == 200:
                voices_data = response.json()
                return {
                    "voices": [
                        {
                            "voice_id": voice["voice_id"],
                            "name": voice["name"],
                            "category": voice.get("category", "unknown"),
                            "description": voice.get("description", "")
                        }
                        for voice in voices_data.get("voices", [])
                    ]
                }
            else:
                return {"error": f"API error: {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def test_speech(self):
        """Test TTS functionality"""
        test_messages = [
            "Email triage system is ready.",
            "Testing ElevenLabs Flash version 2.5 integration.",
            "This is a test of the text to speech functionality."
        ]
        
        print("🎤 Testing TTS functionality...")
        
        for i, message in enumerate(test_messages, 1):
            print(f"Test {i}: {message}")
            success = self.speak(message)
            if success:
                print(f"✅ Test {i} successful")
            else:
                print(f"❌ Test {i} failed")
            time.sleep(1)  # Brief pause between tests


def main():
    """Test the TTS manager"""
    # Load config
    config_path = Path("./triage_data/config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = json.load(f)
    else:
        config = {
            "enable_tts": True,
            "tts_provider": "elevenlabs",
            "elevenlabs_api_key": "sk_43882f16b26beacf077728e663c54fd2f72bd86b6765df56",
            "elevenlabs_voice_id": "pNInz6obpgDQGcFmaJgB",
            "elevenlabs_model": "eleven_flash_v2_5"
        }
    
    # Initialize TTS manager
    tts = TTSManager(config)
    
    # List available voices
    print("🎵 Available ElevenLabs voices:")
    voices = tts.list_available_voices()
    if "voices" in voices:
        for voice in voices["voices"][:5]:  # Show first 5
            print(f"  • {voice['name']} ({voice['voice_id']})")
    else:
        print(f"  Error: {voices.get('error', 'Unknown error')}")
    
    # Test speech
    tts.test_speech()


if __name__ == "__main__":
    main()
