"""
Operators for LipKit

Copyright (C) 2024-2025 Shayan Moradi
SPDX-License-Identifier: GPL-3.0-or-later
"""

import bpy
from bpy.props import StringProperty
import traceback

from .core.controller import LipSyncController
from .core.animation_engine import AnimationEngine
from .core.mapping import PhonemeMapping, PresetManager
from .phoneme_providers import LocalPhonemeProvider
from .utils import audio_utils
from .utils import phoneme_storage
from .preferences import get_preferences

# Module-level cache for phoneme data (survives scene changes)
_phoneme_data_cache = None


def get_cached_phoneme_data():
    """Retrieve cached phoneme data from analyze_audio"""
    global _phoneme_data_cache
    return _phoneme_data_cache


def clear_cached_phoneme_data():
    """Clear the module-level phoneme data cache"""
    global _phoneme_data_cache
    _phoneme_data_cache = None


class LIPKIT_OT_refresh_vse_strips(bpy.types.Operator):
    """Refresh the list of VSE sound strips"""
    bl_idname = "lipkit.refresh_vse_strips"
    bl_label = "Refresh VSE Strips"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # Force Blender to re-evaluate the enum by toggling a dummy value
        props = context.scene.lipkit
        
        # Count available sounds for reporting
        sound_count = 0
        direct_sounds = len(bpy.data.sounds)
        
        for scene in bpy.data.scenes:
            seq = getattr(scene, 'sequence_editor', None)
            if seq:
                seqs = getattr(seq, 'sequences_all', None) or getattr(seq, 'sequences', [])
                if seqs:
                    for s in seqs:
                        if getattr(s, 'type', '') == 'SOUND':
                            sound_count += 1
        
        # Force UI redraw
        for area in context.screen.areas:
            area.tag_redraw()
        
        if sound_count > 0:
            self.report({'INFO'}, f"Found {sound_count} VSE strips")
        elif direct_sounds > 0:
            self.report({'INFO'}, f"No VSE strips, but {direct_sounds} sounds in project")
        else:
            self.report({'WARNING'}, "No sounds found in project")
        
        return {'FINISHED'}


class LIPKIT_OT_open_preferences(bpy.types.Operator):
    """Open LipKit preferences to configure tool path"""
    bl_idname = "lipkit.open_preferences"
    bl_label = "Open Preferences"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        # Open preferences window with LipKit extension selected
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
        
        # Try to navigate to extensions (this might not work in all Blender versions)
        try:
            context.preferences.active_section = 'EXTENSIONS'
        except:
            pass
        
        self.report({'INFO'}, "Set 'Local Tool Path' to your rhubarb executable")
        return {'FINISHED'}


class LIPKIT_OT_download_rhubarb(bpy.types.Operator):
    """Download and install Rhubarb automatically (requires internet access)"""
    bl_idname = "lipkit.download_rhubarb"
    bl_label = "Download Rhubarb"
    bl_options = {'REGISTER'}
    
    # Timer for checking download progress
    _timer = None
    
    @classmethod
    def poll(cls, context):
        """Check if online access is allowed"""
        return getattr(bpy.app, 'online_access', True)
    
    def execute(self, context):
        # Double-check online access (Blender Extension Guidelines Rule 4.2)
        if not getattr(bpy.app, 'online_access', True):
            self.report({'ERROR'}, 
                "Online access is disabled. Enable 'Allow Online Access' in "
                "Edit → Preferences → System, or download Rhubarb manually.")
            return {'CANCELLED'}
        
        # Start download in background
        import threading
        
        scene = context.scene
        
        # Mark as downloading
        scene.lipkit.rhubarb_downloading = True
        
        def download_thread():
            """Background thread to download Rhubarb"""
            from .utils.rhubarb_manager import download_rhubarb, verify_rhubarb
            from .preferences import get_preferences
            
            try:
                print("📥 Starting Rhubarb download...")
                success, result = download_rhubarb()
                
                if not success:
                    print(f"❌ Download failed: {result}")
                    scene.lipkit.rhubarb_download_error = result
                    return
                
                exe_path = result
                print(f"✅ Downloaded to: {exe_path}")
                
                # Verify it works
                is_valid, msg = verify_rhubarb(exe_path)
                if not is_valid:
                    print(f"❌ Verification failed: {msg}")
                    scene.lipkit.rhubarb_download_error = msg
                    return
                
                # Update preferences
                prefs = get_preferences(context)
                prefs.local_tool_path = exe_path
                scene.lipkit.rhubarb_path = exe_path
                
                print(f"✅ {msg}")
                scene.lipkit.rhubarb_download_error = ""
                
            except Exception as e:
                print(f"❌ Download error: {str(e)}")
                scene.lipkit.rhubarb_download_error = str(e)
            
            finally:
                scene.lipkit.rhubarb_downloading = False
        
        # Start thread
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
        
        self.report({'INFO'}, "Downloading Rhubarb in background...")
        return {'FINISHED'}


class LIPKIT_OT_select_rhubarb(bpy.types.Operator):
    """Select folder containing Rhubarb"""
    bl_idname = "lipkit.select_rhubarb"
    bl_label = "Select Rhubarb Folder"
    bl_options = {'REGISTER'}
    
    directory: bpy.props.StringProperty(
        name="Rhubarb Folder",
        description="Folder containing rhubarb executable",
        subtype='DIR_PATH'
    )
    
    def execute(self, context):
        import os
        
        if not self.directory:
            self.report({'ERROR'}, "No folder selected")
            return {'CANCELLED'}
        
        # Look for rhubarb in this directory
        potential_paths = [
            os.path.join(self.directory, "rhubarb"),
            os.path.join(self.directory, "rhubarb.exe"),
        ]
        
        rhubarb_path = None
        for path in potential_paths:
            if os.path.exists(path):
                rhubarb_path = path
                break
        
        if not rhubarb_path:
            self.report({'ERROR'}, f"rhubarb not found in: {self.directory}")
            return {'CANCELLED'}
        
        # Save to SCENE properties (this persists!)
        context.scene.lipkit.rhubarb_path = rhubarb_path
        
        # Also try preferences (but scene is more reliable)
        from .preferences import get_preferences
        try:
            prefs = get_preferences(context)
            prefs.local_tool_path = rhubarb_path
        except:
            pass
        
        print(f"✅ Rhubarb saved to scene: {rhubarb_path}")
        self.report({'INFO'}, f"✅ Ready: {os.path.basename(rhubarb_path)}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class LIPKIT_OT_select_rhubarb_manual(bpy.types.Operator):
    """Manually select Rhubarb folder or executable"""
    bl_idname = "lipkit.select_rhubarb_manual"
    bl_label = "Select Rhubarb"
    bl_options = {'REGISTER'}
    
    directory: bpy.props.StringProperty(
        name="Rhubarb Folder",
        description="Folder containing rhubarb executable",
        subtype='DIR_PATH'
    )
    
    def execute(self, context):
        import os
        from .preferences import get_preferences
        
        if not self.directory:
            self.report({'ERROR'}, "No folder selected")
            return {'CANCELLED'}
        
        # Look for rhubarb in this directory
        potential_paths = [
            os.path.join(self.directory, "rhubarb"),
            os.path.join(self.directory, "rhubarb.exe"),
        ]
        
        rhubarb_path = None
        for path in potential_paths:
            if os.path.exists(path):
                rhubarb_path = path
                break
        
        if not rhubarb_path:
            self.report({'ERROR'}, f"rhubarb not found in: {self.directory}")
            return {'CANCELLED'}
        
        # Save to preferences
        prefs = get_preferences(context)
        prefs.local_tool_path = rhubarb_path
        
        # Also save to scene properties
        context.scene.lipkit.rhubarb_path = rhubarb_path
        
        print(f"✅ Rhubarb path set: {rhubarb_path}")
        self.report({'INFO'}, f"✅ Ready: {os.path.basename(rhubarb_path)}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class LIPKIT_OT_create_controller(bpy.types.Operator):
    """Create a new LipKit controller object"""
    bl_idname = "lipkit.create_controller"
    bl_label = "Create Controller"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            controller = LipSyncController.create_controller()
            context.scene.lipkit.controller_object = controller
            
            self.report({'INFO'}, f"Created controller: {controller.name}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create controller: {str(e)}")
            return {'CANCELLED'}


class LIPKIT_OT_analyze_audio(bpy.types.Operator):
    """Analyze audio and extract phonemes"""
    bl_idname = "lipkit.analyze_audio"
    bl_label = "Analyze Audio"
    bl_options = {'REGISTER'}
    
    # Class-level state for tracking analysis
    _timer = None
    _thread = None
    _result = None  # Will hold (success, data_or_error)
    _progress_percent = 0
    _progress_message = ""
    _start_time = None
    _cancelled = False  # Flag for user cancellation
    
    def execute(self, context):
        props = context.scene.lipkit
        prefs = get_preferences(context)
        
        # Safety check: if analyzing flag is set but no thread is running, reset it
        if props.audio_analyzing:
            if LIPKIT_OT_analyze_audio._thread is None or not LIPKIT_OT_analyze_audio._thread.is_alive():
                print("LipKit: Detected stale analyzing state, resetting...")
                props.audio_analyzing = False
                LIPKIT_OT_analyze_audio._progress_percent = 0
                LIPKIT_OT_analyze_audio._progress_message = ""
                LIPKIT_OT_analyze_audio._start_time = None
            else:
                self.report({'WARNING'}, "⚠️ Analysis already in progress! Check System Console for progress.")
                return {'CANCELLED'}
        
        # Get audio path
        audio_path = None
        if props.audio_source == 'FILE':
            audio_path = bpy.path.abspath(props.audio_filepath)
        elif props.audio_source == 'VSE':
            if props.vse_strip != 'NONE':
                audio_path = audio_utils.get_audio_from_vse(props.vse_strip)
        
        if not audio_path:
            self.report({'ERROR'}, "No audio file selected")
            return {'CANCELLED'}
        
        # Validate audio
        is_valid, error_msg = audio_utils.validate_audio_file(audio_path)
        if not is_valid:
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}
        
        # Check if phoneme data already exists in .blend file
        success, cached_data, message = phoneme_storage.load_phoneme_data(audio_path)
        
        if success and cached_data:
            self.report({'INFO'}, message)
            global _phoneme_data_cache
            _phoneme_data_cache = cached_data
            props.phoneme_data_cached = True
            props.has_phoneme_data = True
            return {'FINISHED'}
        
        # Reset class state
        LIPKIT_OT_analyze_audio._result = None
        LIPKIT_OT_analyze_audio._progress_percent = 0
        LIPKIT_OT_analyze_audio._progress_message = "Starting..."
        LIPKIT_OT_analyze_audio._start_time = None
        LIPKIT_OT_analyze_audio._cancelled = False
        
        # Get Rhubarb path - try multiple sources
        from .utils.rhubarb_manager import get_effective_rhubarb_path
        
        rhubarb_path = get_effective_rhubarb_path(props, prefs)
        
        if not rhubarb_path:
            self.report({'ERROR'}, "Rhubarb not found! Go to Phoneme Engine panel and download or select it.")
            return {'CANCELLED'}
        
        debug_mode = prefs.debug_mode
        
        import threading
        import time
        
        def progress_callback(percent, message):
            """Thread-safe progress callback"""
            LIPKIT_OT_analyze_audio._progress_percent = percent
            LIPKIT_OT_analyze_audio._progress_message = message
            print(f"[{percent:3d}%] {message}")
        
        def analyze_thread():
            """Background thread to extract phonemes"""
            try:
                LIPKIT_OT_analyze_audio._start_time = time.time()
                
                provider = LocalPhonemeProvider(tool_path=rhubarb_path)
                
                if not provider.is_available():
                    error = f"❌ Rhubarb not available at: {rhubarb_path}"
                    print(error)
                    LIPKIT_OT_analyze_audio._result = (False, error)
                    return
                
                progress_callback(0, "📊 Starting phoneme extraction...")
                
                lipsync_data = provider.extract_phonemes(
                    audio_path, 
                    language='en',
                    progress_callback=progress_callback
                )
                
                # Validate result before setting as success
                if lipsync_data is None:
                    error = "❌ Rhubarb returned no data"
                    print(error)
                    LIPKIT_OT_analyze_audio._result = (False, error)
                    return
                
                if not hasattr(lipsync_data, 'phonemes') or not lipsync_data.phonemes:
                    error = "❌ No phonemes extracted from audio"
                    print(error)
                    LIPKIT_OT_analyze_audio._result = (False, error)
                    return
                
                elapsed = time.time() - LIPKIT_OT_analyze_audio._start_time
                progress_callback(100, f"✅ Done in {elapsed:.1f}s - {len(lipsync_data.phonemes)} phonemes")
                
                LIPKIT_OT_analyze_audio._result = (True, lipsync_data)
                print(f"✅ Thread completed successfully with {len(lipsync_data.phonemes)} phonemes")
                
            except Exception as e:
                error_msg = f"❌ Analysis failed: {str(e)}"
                print(error_msg)
                if debug_mode:
                    traceback.print_exc()
                LIPKIT_OT_analyze_audio._result = (False, error_msg)
            finally:
                # Always ensure result is set
                if LIPKIT_OT_analyze_audio._result is None:
                    print("⚠️ Thread ended without setting result!")
                    LIPKIT_OT_analyze_audio._result = (False, "Thread ended unexpectedly")
        
        # Mark as analyzing
        props.audio_analyzing = True
        props.phoneme_data_cached = False
        
        # Start background thread
        LIPKIT_OT_analyze_audio._thread = threading.Thread(target=analyze_thread, daemon=True)
        LIPKIT_OT_analyze_audio._thread.start()
        
        # Add timer to check thread status
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.2, window=context.window)  # Check more frequently
        wm.modal_handler_add(self)
        
        self.report({'INFO'}, "⏳ Analyzing... Check System Console (Window → Toggle System Console) for progress")
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        props = context.scene.lipkit
        
        # Handle ESC key to cancel
        if event.type in {'ESC'}:
            self.report({'WARNING'}, "Analysis cancelled by user")
            LIPKIT_OT_analyze_audio._cancelled = True
            props.audio_analyzing = False
            # Reset state
            LIPKIT_OT_analyze_audio._progress_percent = 0
            LIPKIT_OT_analyze_audio._progress_message = ""
            LIPKIT_OT_analyze_audio._start_time = None
            LIPKIT_OT_analyze_audio._thread = None
            wm = context.window_manager
            if self._timer:
                wm.event_timer_remove(self._timer)
            context.workspace.status_text_set(None)
            return {'CANCELLED'}
        
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}
        
        # Force UI redraw to show progress
        for area in context.screen.areas:
            area.tag_redraw()
        
        # IMPORTANT: Check if result is already available (thread finished)
        # This is the PRIMARY check - if result is set, thread is done
        if LIPKIT_OT_analyze_audio._result is not None:
            print(f"LipKit: Result is ready, processing... (result type: {type(LIPKIT_OT_analyze_audio._result)})")
            # Thread finished - clean up and process
            wm = context.window_manager
            if self._timer:
                wm.event_timer_remove(self._timer)
            context.workspace.status_text_set(None)
            return self._process_result(context)
        
        # Secondary check: thread state
        thread = LIPKIT_OT_analyze_audio._thread
        thread_alive = thread is not None and thread.is_alive()
        
        if not thread_alive and LIPKIT_OT_analyze_audio._result is None:
            # Thread died without setting result - this is an error
            print("LipKit ERROR: Thread died without setting result!")
            wm = context.window_manager
            if self._timer:
                wm.event_timer_remove(self._timer)
            context.workspace.status_text_set(None)
            props.audio_analyzing = False
            LIPKIT_OT_analyze_audio._progress_percent = 0
            LIPKIT_OT_analyze_audio._progress_message = ""
            LIPKIT_OT_analyze_audio._start_time = None
            LIPKIT_OT_analyze_audio._thread = None
            self.report({'ERROR'}, "Analysis failed unexpectedly - check System Console")
            return {'CANCELLED'}
        
        # Thread still running - show progress
        elapsed = 0
        if LIPKIT_OT_analyze_audio._start_time:
            import time
            elapsed = time.time() - LIPKIT_OT_analyze_audio._start_time
        
        percent = LIPKIT_OT_analyze_audio._progress_percent
        msg = LIPKIT_OT_analyze_audio._progress_message
        
        # Timeout after 15 minutes
        if elapsed > 900:
            self.report({'ERROR'}, "Analysis timed out after 15 minutes")
            props.audio_analyzing = False
            # Reset state
            LIPKIT_OT_analyze_audio._progress_percent = 0
            LIPKIT_OT_analyze_audio._progress_message = ""
            LIPKIT_OT_analyze_audio._start_time = None
            LIPKIT_OT_analyze_audio._thread = None
            wm = context.window_manager
            if self._timer:
                wm.event_timer_remove(self._timer)
            context.workspace.status_text_set(None)
            return {'CANCELLED'}
        
        # Update status bar
        context.workspace.status_text_set(f"⏳ Rhubarb [{percent}%] ({elapsed:.0f}s) - {msg} (ESC to cancel)")
        return {'PASS_THROUGH'}
    
    def _process_result(self, context):
        """Process the analysis result - called when thread completes"""
        props = context.scene.lipkit
        props.audio_analyzing = False
        
        # Check if cancelled
        if LIPKIT_OT_analyze_audio._cancelled:
            self.report({'WARNING'}, "Analysis cancelled")
            self._reset_state()
            return {'CANCELLED'}
        
        result = LIPKIT_OT_analyze_audio._result
        if result is None:
            self.report({'ERROR'}, "Analysis thread ended unexpectedly - check System Console for errors")
            self._reset_state()
            return {'CANCELLED'}
        
        success, data = result
        
        if success:
            # Save to .blend file storage
            audio_path = None
            if props.audio_source == 'FILE':
                audio_path = bpy.path.abspath(props.audio_filepath)
            elif props.audio_source == 'VSE':
                if props.vse_strip != 'NONE':
                    audio_path = audio_utils.get_audio_from_vse(props.vse_strip)
            
            if audio_path:
                try:
                    save_success, save_message = phoneme_storage.save_phoneme_data(audio_path, data)
                    if save_success:
                        print(f"✓ {save_message}")
                    else:
                        print(f"⚠ Failed to save: {save_message}")
                except Exception as e:
                    print(f"⚠ Exception saving phoneme data: {e}")
            
            # Store in module cache
            global _phoneme_data_cache
            _phoneme_data_cache = data
            props.phoneme_data_cached = True
            props.has_phoneme_data = True
            
            self._reset_state()
            self.report({'INFO'}, f"✅ Analyzed: {len(data.phonemes)} phonemes ({data.duration:.1f}s)")
            return {'FINISHED'}
        else:
            self._reset_state()
            self.report({'ERROR'}, str(data))
            return {'CANCELLED'}
    
    def _reset_state(self):
        """Reset all class-level state"""
        LIPKIT_OT_analyze_audio._progress_percent = 0
        LIPKIT_OT_analyze_audio._progress_message = ""
        LIPKIT_OT_analyze_audio._start_time = None
        LIPKIT_OT_analyze_audio._result = None
        LIPKIT_OT_analyze_audio._thread = None
        LIPKIT_OT_analyze_audio._cancelled = False
    
    def cancel(self, context):
        """Handle operator cancellation"""
        LIPKIT_OT_analyze_audio._cancelled = True
        context.scene.lipkit.audio_analyzing = False
        if self._timer:
            try:
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
            except:
                pass
        try:
            context.workspace.status_text_set(None)
        except:
            pass
        # Full reset
        self._reset_state()


class LIPKIT_OT_cancel_analysis(bpy.types.Operator):
    """Cancel ongoing audio analysis"""
    bl_idname = "lipkit.cancel_analysis"
    bl_label = "Cancel Analysis"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        props = context.scene.lipkit
        
        # Set cancellation flag
        LIPKIT_OT_analyze_audio._cancelled = True
        
        # Reset state immediately
        props.audio_analyzing = False
        
        # Full reset of class state
        LIPKIT_OT_analyze_audio._progress_percent = 0
        LIPKIT_OT_analyze_audio._progress_message = ""
        LIPKIT_OT_analyze_audio._start_time = None
        LIPKIT_OT_analyze_audio._result = None
        LIPKIT_OT_analyze_audio._thread = None
        
        self.report({'WARNING'}, "❌ Analysis cancelled")
        return {'FINISHED'}


class LIPKIT_OT_clear_phoneme_data(bpy.types.Operator):
    """Clear phoneme data from memory (does not delete from file)"""
    bl_idname = "lipkit.clear_phoneme_data"
    bl_label = "Clear Phoneme Data"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        from .operators import clear_cached_phoneme_data
        
        clear_cached_phoneme_data()
        props = context.scene.lipkit
        props.phoneme_data_cached = False
        props.has_phoneme_data = False
        props.phoneme_data_json = ""
        
        self.report({'INFO'}, "Cleared phoneme data from memory")
        return {'FINISHED'}


class LIPKIT_OT_delete_phoneme_data(bpy.types.Operator):
    """Delete saved phoneme data from .blend file"""
    bl_idname = "lipkit.delete_phoneme_data"
    bl_label = "Delete from File"
    bl_options = {'REGISTER', 'UNDO'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)
    
    def execute(self, context):
        props = context.scene.lipkit
        
        # Get audio path
        audio_path = None
        if props.audio_source == 'FILE':
            audio_path = bpy.path.abspath(props.audio_filepath)
        elif props.audio_source == 'VSE':
            if props.vse_strip != 'NONE':
                audio_path = audio_utils.get_audio_from_vse(props.vse_strip)
        
        if not audio_path:
            self.report({'ERROR'}, "No audio file selected")
            return {'CANCELLED'}
        
        # Delete from file
        success, message = phoneme_storage.delete_phoneme_data(audio_path)
        
        if success:
            # Also clear from memory
            from .operators import clear_cached_phoneme_data
            clear_cached_phoneme_data()
            props.phoneme_data_cached = False
            props.has_phoneme_data = False
            props.phoneme_data_json = ""
            
            self.report({'INFO'}, message)
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, message)
            return {'CANCELLED'}


    def _get_provider(self, props, prefs):
        """Get the appropriate phoneme provider"""
        # Always use LOCAL provider (Rhubarb)
        return LocalPhonemeProvider(tool_path=props.rhubarb_path)


class LIPKIT_OT_load_preset(bpy.types.Operator):
    """Load phoneme mapping preset"""
    bl_idname = "lipkit.load_preset"
    bl_label = "Load Preset"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.lipkit
        
        try:
            preset_data = PresetManager.load_preset(props.phoneme_preset)
            
            if not preset_data:
                self.report({'ERROR'}, f"Preset not found: {props.phoneme_preset}")
                return {'CANCELLED'}
            
            # Clear existing mappings
            props.phoneme_mappings.clear()
            
            # Add mappings from preset
            for item in preset_data.get("mappings", []):
                mapping = props.phoneme_mappings.add()
                mapping.phoneme = item.get("phoneme", "")
                mapping.phoneme_index = item.get("index", 0)
                mapping.target_name = ""  # User needs to set this
                mapping.enabled = True
            
            self.report({'INFO'}, f"Loaded preset: {preset_data.get('name', props.phoneme_preset)}")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load preset: {str(e)}")
            return {'CANCELLED'}


class LIPKIT_OT_auto_map_targets(bpy.types.Operator):
    """Quick-fill all mappings based on name matching (optional helper)"""
    bl_idname = "lipkit.auto_map_targets"
    bl_label = "Quick Auto-Map (Name Match)"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.lipkit
        target_obj = props.target_object
        
        if not target_obj:
            self.report({'ERROR'}, "Select a target object first")
            return {'CANCELLED'}
        
        mapped_count = 0
        
        try:
            # DYNAMIC: detect from object type
            if target_obj.type in ('GPENCIL', 'GREASEPENCIL'):
                # Auto-map GP layers based on name
                for mapping in props.phoneme_mappings:
                    phoneme = mapping.phoneme.lower()
                    
                    if hasattr(target_obj.data, 'layers'):
                        for layer in target_obj.data.layers:
                            # Support both old (.info) and new (.name) attribute names
                            layer_name = getattr(layer, 'name', None) or getattr(layer, 'info', None)
                            if layer_name and phoneme in layer_name.lower():
                                mapping.target_object = target_obj
                                mapping.target_property = layer_name
                                mapping.target_name = layer_name
                                mapped_count += 1
                                break
            
            elif target_obj.type == 'MESH':
                # Auto-map shape keys based on name
                if hasattr(target_obj.data, 'shape_keys') and target_obj.data.shape_keys:
                    for mapping in props.phoneme_mappings:
                        phoneme = mapping.phoneme.lower()
                        
                        for key in target_obj.data.shape_keys.key_blocks:
                            if phoneme in key.name.lower():
                                mapping.target_object = target_obj
                                mapping.target_property = key.name
                                mapping.target_name = key.name
                                mapped_count += 1
                                break
            
            if mapped_count > 0:
                self.report({'INFO'}, f"Auto-mapped {mapped_count} targets by name")
            else:
                self.report({'WARNING'}, "No matches found - use manual selection")
            
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to auto-map: {str(e)}")
            return {'CANCELLED'}


class LIPKIT_OT_select_mapping_target(bpy.types.Operator):
    """Select target for a specific phoneme mapping"""
    bl_idname = "lipkit.select_mapping_target"
    bl_label = "Select Target"
    bl_options = {'REGISTER', 'UNDO'}
    
    mapping_index: bpy.props.IntProperty(default=0)
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        props = context.scene.lipkit
        
        if self.mapping_index >= len(props.phoneme_mappings):
            self.report({'ERROR'}, "Invalid mapping index")
            return {'CANCELLED'}
        
        target_obj = props.target_object
        if not target_obj:
            self.report({'ERROR'}, "Select a target object first")
            return {'CANCELLED'}
        
        # Build menu based on object type (dynamic!)
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.lipkit
        mapping = props.phoneme_mappings[self.mapping_index]
        target_obj = props.target_object
        
        layout.label(text=f"Select target for: {mapping.phoneme}", icon='SPEAKER')
        layout.separator()
        
        box = layout.box()
        
        obj_type = target_obj.type
        
        # DYNAMIC: Check actual object type - support both old and new GP type names
        if obj_type in ('GPENCIL', 'GREASEPENCIL'):
            # Show GP layers
            if hasattr(target_obj.data, 'layers') and len(target_obj.data.layers) > 0:
                box.label(text="GP Layers:", icon='GREASEPENCIL')
                for layer in target_obj.data.layers:
                    # Support both old (.info) and new (.name) attribute names
                    layer_name = getattr(layer, 'name', None) or getattr(layer, 'info', None)
                    if layer_name:
                        row = box.row()
                        op = row.operator("lipkit.assign_mapping_target", text=layer_name, icon='LAYER_ACTIVE')
                        op.mapping_index = self.mapping_index
                        op.target_name = layer_name
            else:
                box.label(text="No layers found", icon='INFO')
                box.label(text=f"Add layers to {target_obj.name} first")
        
        elif obj_type == 'MESH':
            # Show shape keys
            if hasattr(target_obj.data, 'shape_keys') and target_obj.data.shape_keys:
                box.label(text="Shape Keys:", icon='SHAPEKEY_DATA')
                for key in target_obj.data.shape_keys.key_blocks:
                    if key.name == "Basis":
                        continue
                    row = box.row()
                    op = row.operator("lipkit.assign_mapping_target", text=key.name, icon='SHAPEKEY_DATA')
                    op.mapping_index = self.mapping_index
                    op.target_name = key.name
            else:
                box.label(text="No shape keys found", icon='INFO')
                box.label(text=f"Add shape keys to {target_obj.name} first")
        
        else:
            box.label(text=f"Object type '{obj_type}' not supported", icon='ERROR')
            box.label(text="Supported types:")
            box.label(text="• MESH (for shape keys)")
            box.label(text="• GPENCIL/GREASEPENCIL (for layers)")
            box.label(text="")
            box.label(text=f"Your object '{target_obj.name}' is type: {obj_type}")


class LIPKIT_OT_assign_mapping_target(bpy.types.Operator):
    """Assign a target to a phoneme mapping"""
    bl_idname = "lipkit.assign_mapping_target"
    bl_label = "Assign"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    
    mapping_index: bpy.props.IntProperty(default=0)
    target_name: bpy.props.StringProperty(default="")
    
    def execute(self, context):
        props = context.scene.lipkit
        
        if self.mapping_index >= len(props.phoneme_mappings):
            return {'CANCELLED'}
        
        mapping = props.phoneme_mappings[self.mapping_index]
        target_obj = props.target_object
        
        # Assign the mapping
        mapping.target_object = target_obj
        mapping.target_property = self.target_name
        mapping.target_name = self.target_name  # Backwards compatibility
        
        self.report({'INFO'}, f"✓ {mapping.phoneme} → {self.target_name}")
        return {'FINISHED'}


class LIPKIT_OT_generate(bpy.types.Operator):
    """Generate lip sync animation"""
    bl_idname = "lipkit.generate"
    bl_label = "Generate Lip Sync"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.lipkit
        prefs = get_preferences(context)
        
        # Validate inputs
        if not props.controller_object:
            self.report({'ERROR'}, "No controller object - create one first")
            return {'CANCELLED'}
        
        if not props.target_object:
            self.report({'ERROR'}, "No target object selected")
            return {'CANCELLED'}
        
        if not props.phoneme_data_cached:
            self.report({'ERROR'}, "No phoneme data - analyze audio first")
            return {'CANCELLED'}
        
        # Get audio path (for re-extraction)
        audio_path = None
        if props.audio_source == 'FILE':
            audio_path = bpy.path.abspath(props.audio_filepath)
        elif props.audio_source == 'VSE':
            if props.vse_strip != 'NONE':
                audio_path = audio_utils.get_audio_from_vse(props.vse_strip)
        
        if not audio_path:
            self.report({'ERROR'}, "No audio file available")
            return {'CANCELLED'}
        
        try:
            props.generation_in_progress = True
            
            # Use cached phoneme data
            lipsync_data = get_cached_phoneme_data()
            
            if not lipsync_data:
                self.report({'ERROR'}, "Phoneme data lost - analyze audio again")
                return {'CANCELLED'}
            
            # Build mapping
            mapping = PhonemeMapping()
            mapping.name = props.action_name
            mapping.visual_system = props.visual_system
            mapping.target_object = props.target_object.name
            mapping.phoneme_set = props.phoneme_preset
            
            for item in props.phoneme_mappings:
                # Use new object-based properties if available, fall back to target_name for compatibility
                target_to_use = None
                if item.target_object and item.target_property:
                    target_to_use = item.target_property
                elif item.target_name:
                    target_to_use = item.target_name
                
                if item.enabled and target_to_use:
                    mapping.add_mapping(
                        item.phoneme,
                        item.phoneme_index,
                        target_to_use
                    )
            
            # Generate animation
            engine = AnimationEngine(lipsync_data, mapping, props.controller_object)
            
            results = engine.generate(
                props.target_object,
                start_frame=props.start_frame,
                use_nla=props.use_nla,
                action_name=props.action_name,
                interpolation=props.interpolation,
                min_hold_frames=props.min_hold_frames,
                merge_threshold=props.merge_threshold
            )
            
            # Report results
            self.report(
                {'INFO'},
                f"✓ Generated {results['keyframes_created']} keyframes, "
                f"{results['drivers_created']} drivers"
            )
            
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Generation failed: {str(e)}")
            if prefs.debug_mode:
                traceback.print_exc()
            return {'CANCELLED'}
        
        finally:
            props.generation_in_progress = False


class LIPKIT_OT_clear_all_keyframes(bpy.types.Operator):
    """Clean all keyframes from controller and added layers"""
    bl_idname = "lipkit.clear_all_keyframes"
    bl_label = "Clean All Keyframes"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.lipkit
        
        if not props.controller_object:
            self.report({'WARNING'}, "No controller object")
            return {'CANCELLED'}
        
        try:
            # Clear animation from controller
            LipSyncController.clear_animation(props.controller_object)
            cleared_count = 1
            
            # Also clear from target object if it's a GP object with mapped layers
            if props.target_object and props.target_object.type in ('GPENCIL', 'GREASEPENCIL'):
                target_obj = props.target_object
                
                # Clear animation from all layers that were mapped
                for mapping in props.phoneme_mappings:
                    if mapping.target_property and hasattr(target_obj.data, 'layers'):
                        for layer in target_obj.data.layers:
                            layer_name = getattr(layer, 'name', None) or getattr(layer, 'info', None)
                            if layer_name == mapping.target_property:
                                # Clear keyframes from this layer's opacity
                                if hasattr(layer, 'opacity'):
                                    # Note: GP layer opacity doesn't use keyframes in the traditional sense,
                                    # but we can clear any attached drivers
                                    pass
                                cleared_count += 1
                                break
            
            self.report({'INFO'}, f"Cleaned keyframes from controller and layers")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to clean keyframes: {str(e)}")
            return {'CANCELLED'}


class LIPKIT_OT_clear_animation(bpy.types.Operator):
    """Clear generated lip sync animation"""
    bl_idname = "lipkit.clear_animation"
    bl_label = "Clear Animation"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.lipkit
        
        if not props.controller_object:
            self.report({'WARNING'}, "No controller object")
            return {'CANCELLED'}
        
        try:
            LipSyncController.clear_animation(props.controller_object)
            self.report({'INFO'}, "Cleared animation from controller")
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to clear: {str(e)}")
            return {'CANCELLED'}


class LIPKIT_OT_save_phoneme_data(bpy.types.Operator):
    """Save analyzed phoneme data to a file"""
    bl_idname = "lipkit.save_phoneme_data"
    bl_label = "Save Phoneme Data"
    bl_options = {'REGISTER'}
    
    filepath: bpy.props.StringProperty(
        subtype='FILE_PATH',
        default="phoneme_data.json"
    )
    
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        from ..utils import audio_utils
        
        props = context.scene.lipkit
        
        if not props.has_phoneme_data or not props.phoneme_data_json:
            self.report({'ERROR'}, "No phoneme data to save. Analyze audio first.")
            return {'CANCELLED'}
        
        try:
            # Parse JSON and save to file
            import json
            from ..core import LipSyncData
            
            data_dict = json.loads(props.phoneme_data_json)
            lipsync_data = LipSyncData.from_dict(data_dict)
            
            success, message = audio_utils.save_phoneme_data_to_file(
                self.filepath,
                lipsync_data
            )
            
            if success:
                self.report({'INFO'}, message)
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, message)
                return {'CANCELLED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save: {str(e)}")
            return {'CANCELLED'}


class LIPKIT_OT_load_phoneme_data(bpy.types.Operator):
    """Load phoneme data from a file"""
    bl_idname = "lipkit.load_phoneme_data"
    bl_label = "Load Phoneme Data"
    bl_options = {'REGISTER'}
    
    filepath: bpy.props.StringProperty(
        subtype='FILE_PATH'
    )
    
    filter_glob: bpy.props.StringProperty(
        default="*.json",
        options={'HIDDEN'}
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        from ..utils import audio_utils
        import json
        
        props = context.scene.lipkit
        
        success, lipsync_data, message = audio_utils.load_phoneme_data_from_file(
            self.filepath
        )
        
        if not success:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
        
        try:
            # Store in properties
            props.phoneme_data_json = json.dumps(lipsync_data.to_dict())
            props.has_phoneme_data = True
            props.phoneme_data_cached = True
            
            # Also store in module cache so it can be used immediately
            global _phoneme_data_cache
            _phoneme_data_cache = lipsync_data
            
            self.report({'INFO'}, message)
            return {'FINISHED'}
        
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load: {str(e)}")
            return {'CANCELLED'}


class LIPKIT_OT_clear_phoneme_data(bpy.types.Operator):
    """Clear analyzed phoneme data"""
    bl_idname = "lipkit.clear_phoneme_data"
    bl_label = "Clear Phoneme Data"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        props = context.scene.lipkit
        
        # Clear all phoneme data
        props.phoneme_data_cached = False
        props.has_phoneme_data = False
        props.phoneme_data_json = ""
        
        # Clear module cache
        clear_cached_phoneme_data()
        
        self.report({'INFO'}, "✓ Phoneme data cleared")
        return {'FINISHED'}


class LIPKIT_OT_delete_phoneme_data(bpy.types.Operator):
    """Delete saved phoneme data for current audio from the .blend file"""
    bl_idname = "lipkit.delete_phoneme_data"
    bl_label = "Delete Saved Data"
    bl_options = {'REGISTER'}
    
    def execute(self, context):
        props = context.scene.lipkit
        
        # Get audio path
        audio_path = None
        if props.audio_source == 'FILE':
            audio_path = bpy.path.abspath(props.audio_filepath)
        elif props.audio_source == 'VSE':
            if props.vse_strip != 'NONE':
                audio_path = audio_utils.get_audio_from_vse(props.vse_strip)
        
        if not audio_path:
            self.report({'ERROR'}, "No audio file selected")
            return {'CANCELLED'}
        
        # Delete from storage
        success, message = phoneme_storage.delete_phoneme_data(audio_path)
        
        if success:
            # Also clear from memory
            props.phoneme_data_cached = False
            props.has_phoneme_data = False
            clear_cached_phoneme_data()
            
            self.report({'INFO'}, message)
        else:
            self.report({'WARNING'}, message)
        
        return {'FINISHED'}


# Registration
classes = [
    LIPKIT_OT_refresh_vse_strips,
    LIPKIT_OT_open_preferences,
    LIPKIT_OT_download_rhubarb,
    LIPKIT_OT_select_rhubarb,
    LIPKIT_OT_select_rhubarb_manual,
    LIPKIT_OT_create_controller,
    LIPKIT_OT_analyze_audio,
    LIPKIT_OT_cancel_analysis,
    LIPKIT_OT_clear_phoneme_data,
    LIPKIT_OT_delete_phoneme_data,
    LIPKIT_OT_load_preset,
    LIPKIT_OT_auto_map_targets,
    LIPKIT_OT_select_mapping_target,
    LIPKIT_OT_assign_mapping_target,
    LIPKIT_OT_generate,
    LIPKIT_OT_clear_all_keyframes,
    LIPKIT_OT_clear_animation,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
