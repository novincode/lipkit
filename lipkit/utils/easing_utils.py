"""
Easing and animation utilities for smooth mouth transitions
"""

import math
from typing import List, Tuple


class EasingCurve:
    """Easing functions for smooth animation transitions"""
    
    @staticmethod
    def ease_in_out(t: float) -> float:
        """Ease in-out cubic curve (0-1 range)"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            p = 2 * t - 2
            return 0.5 * p * p * p + 1
    
    @staticmethod
    def ease_in(t: float) -> float:
        """Ease in cubic curve"""
        return t * t * t
    
    @staticmethod
    def ease_out(t: float) -> float:
        """Ease out cubic curve"""
        t = 1 - t
        return 1 - t * t * t
    
    @staticmethod
    def smooth(t: float) -> float:
        """Linear smooth transition"""
        return t
    
    @staticmethod
    def get_easing_function(easing_type: str):
        """Get easing function by name"""
        easing_map = {
            'ease_in_out': EasingCurve.ease_in_out,
            'ease_in': EasingCurve.ease_in,
            'ease_out': EasingCurve.ease_out,
            'smooth': EasingCurve.smooth,
        }
        return easing_map.get(easing_type, EasingCurve.ease_in_out)


def apply_easing_to_keyframes(
    keyframe_data: dict,
    easing_type: str = 'ease_in_out',
    easing_duration: float = 3.0
) -> dict:
    """
    Apply easing to keyframes by adding intermediate keyframes
    
    This creates smooth transitions between phoneme indices
    instead of instant jumps.
    
    Args:
        keyframe_data: Dict mapping frame -> phoneme_index
        easing_type: Type of easing function
        easing_duration: Number of frames for transition
        
    Returns:
        New keyframe dict with easing interpolation
    """
    if easing_duration < 1:
        return keyframe_data
    
    easing_fn = EasingCurve.get_easing_function(easing_type)
    
    # Sort frames
    sorted_frames = sorted(keyframe_data.keys())
    
    if len(sorted_frames) < 2:
        return keyframe_data
    
    eased_keyframes = {}
    duration_int = int(easing_duration)
    
    # For each pair of consecutive keyframes
    for i in range(len(sorted_frames) - 1):
        start_frame = sorted_frames[i]
        next_frame = sorted_frames[i + 1]
        start_index = keyframe_data[start_frame]
        next_index = keyframe_data[next_frame]
        
        # Add start keyframe
        eased_keyframes[start_frame] = start_index
        
        # If indices are different, create easing transition
        if start_index != next_index:
            index_diff = next_index - start_index
            
            # Create intermediate keyframes
            for step in range(1, duration_int):
                # Calculate normalized time (0-1)
                t = step / duration_int
                
                # Apply easing function
                eased_t = easing_fn(t)
                
                # Interpolate between indices
                eased_value = start_index + (index_diff * eased_t)
                
                # Interpolate frame position
                eased_frame = start_frame + (step / duration_int) * (next_frame - start_frame)
                eased_frame = round(eased_frame)
                
                # Avoid duplicate frames
                if eased_frame not in eased_keyframes and eased_frame < next_frame:
                    # Round value to nearest index or use float for driver
                    eased_keyframes[eased_frame] = round(eased_value, 2)
        
        # Add final keyframe from this pair
        if i == len(sorted_frames) - 2:
            eased_keyframes[next_frame] = next_index
    
    return eased_keyframes


def get_smooth_value(
    current_index: int,
    target_index: int,
    progress: float
) -> float:
    """
    Get smoothly interpolated value between two indices
    
    Args:
        current_index: Starting mouth shape index
        target_index: Target mouth shape index
        progress: Progress from 0 to 1
        
    Returns:
        Interpolated value
    """
    # Use ease-in-out by default
    eased_progress = EasingCurve.ease_in_out(progress)
    return current_index + (target_index - current_index) * eased_progress
