"""
Interruption detection for real-time voice interactions.
Detects speech onset during agent output and handles graceful interruption with context preservation.
"""

import logging
import numpy as np
import struct
import time
from collections import deque
from typing import Optional, Dict, Any, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class SensitivityLevel(Enum):
    """Interruption detection sensitivity levels."""
    LOW = "low"
    MEDIUM = "medium"  
    HIGH = "high"


class AudioFeatures:
    """Audio feature extraction for speech detection."""
    
    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate
        self.frame_size = 320  # 20ms at 16kHz
        self.energy_window = deque(maxlen=10)  # 200ms window
        self.zero_crossing_window = deque(maxlen=10)
        
    def extract_energy(self, audio_chunk: bytes) -> float:
        """Calculate RMS energy of audio chunk."""
        if len(audio_chunk) < 2:
            return 0.0
            
        # Convert bytes to int16 samples
        samples = struct.unpack(f"<{len(audio_chunk)//2}h", audio_chunk)
        
        # Calculate RMS energy
        energy = np.sqrt(np.mean(np.square(samples)))
        self.energy_window.append(energy)
        
        return energy
    
    def extract_zero_crossings(self, audio_chunk: bytes) -> int:
        """Calculate zero crossing rate."""
        if len(audio_chunk) < 4:
            return 0
            
        samples = struct.unpack(f"<{len(audio_chunk)//2}h", audio_chunk)
        
        # Count zero crossings
        crossings = 0
        for i in range(1, len(samples)):
            if (samples[i-1] * samples[i]) < 0:
                crossings += 1
        
        zcr = crossings / len(samples)
        self.zero_crossing_window.append(zcr)
        
        return crossings
    
    def get_average_energy(self) -> float:
        """Get average energy over recent window."""
        if not self.energy_window:
            return 0.0
        return sum(self.energy_window) / len(self.energy_window)
    
    def get_average_zcr(self) -> float:
        """Get average zero crossing rate over recent window."""
        if not self.zero_crossing_window:
            return 0.0
        return sum(self.zero_crossing_window) / len(self.zero_crossing_window)


class InterruptionDetector:
    """Detects speech onset during agent output for barge-in functionality."""
    
    def __init__(self, sensitivity: SensitivityLevel = SensitivityLevel.MEDIUM):
        self.sensitivity = sensitivity
        self.sample_rate = 16000
        self.features = AudioFeatures(self.sample_rate)
        
        # Detection parameters per sensitivity level
        self.thresholds = {
            SensitivityLevel.LOW: {
                "energy_multiplier": 3.0,
                "min_energy": 800,
                "zcr_threshold": 0.05,
                "consecutive_frames": 5,
                "cooldown_ms": 1000
            },
            SensitivityLevel.MEDIUM: {
                "energy_multiplier": 2.5,
                "min_energy": 600,
                "zcr_threshold": 0.04,
                "consecutive_frames": 3,
                "cooldown_ms": 800
            },
            SensitivityLevel.HIGH: {
                "energy_multiplier": 2.0,
                "min_energy": 400,
                "zcr_threshold": 0.03,
                "consecutive_frames": 2,
                "cooldown_ms": 600
            }
        }
        
        # State tracking
        self.baseline_energy = 100.0  # Background noise level
        self.speech_frames = 0
        self.last_interruption_time = 0
        self.is_speech_active = False
        self.interruption_context = ""
        
        # Adaptive background noise estimation
        self.noise_samples = deque(maxlen=50)  # 1 second of background
        self.last_adaptation_time = time.time()
        
    def set_sensitivity(self, sensitivity: str) -> None:
        """Set detection sensitivity level."""
        try:
            self.sensitivity = SensitivityLevel(sensitivity.lower())
            logger.info(f"Interruption sensitivity set to: {self.sensitivity.value}")
        except ValueError:
            logger.warning(f"Invalid sensitivity level: {sensitivity}")
    
    def detect_speech_onset(self, audio_chunk: bytes) -> bool:
        """
        Detect if speech has started in the audio chunk.
        Returns True if interruption should be triggered.
        """
        current_time = time.time() * 1000  # Convert to milliseconds
        
        # Cooldown check
        threshold = self.thresholds[self.sensitivity]
        if current_time - self.last_interruption_time < threshold["cooldown_ms"]:
            return False
        
        # Extract audio features
        energy = self.features.extract_energy(audio_chunk)
        zcr_count = self.features.extract_zero_crossings(audio_chunk)
        zcr_rate = zcr_count / (len(audio_chunk) // 2) if len(audio_chunk) > 2 else 0
        
        # Update background noise estimate
        self._update_baseline(energy)
        
        # Speech detection logic
        is_speech_frame = self._is_speech_frame(energy, zcr_rate)
        
        if is_speech_frame:
            self.speech_frames += 1
            
            # Check if we have enough consecutive speech frames
            if self.speech_frames >= threshold["consecutive_frames"]:
                if not self.is_speech_active:
                    self.is_speech_active = True
                    self.last_interruption_time = current_time
                    self._capture_interruption_context()
                    
                    logger.info(f"Speech onset detected - Energy: {energy:.1f}, "
                              f"Baseline: {self.baseline_energy:.1f}, ZCR: {zcr_rate:.3f}")
                    return True
        else:
            # Reset speech frame counter if we don't detect speech
            if self.speech_frames > 0:
                self.speech_frames = max(0, self.speech_frames - 1)
            
            # Reset speech active state if energy drops significantly
            if energy < self.baseline_energy * 1.5:
                self.is_speech_active = False
        
        return False
    
    def _is_speech_frame(self, energy: float, zcr_rate: float) -> bool:
        """Determine if current frame contains speech."""
        threshold = self.thresholds[self.sensitivity]
        
        # Energy-based detection
        energy_threshold = max(
            self.baseline_energy * threshold["energy_multiplier"],
            threshold["min_energy"]
        )
        
        energy_check = energy > energy_threshold
        zcr_check = zcr_rate > threshold["zcr_threshold"]
        
        # Both energy and ZCR should indicate speech
        return energy_check and zcr_check
    
    def _update_baseline(self, energy: float) -> None:
        """Update baseline noise level adaptively."""
        current_time = time.time()
        
        # Only update baseline when not detecting speech
        if not self.is_speech_active and energy < self.baseline_energy * 2:
            self.noise_samples.append(energy)
            
            # Update baseline every 5 seconds
            if current_time - self.last_adaptation_time > 5.0:
                if len(self.noise_samples) >= 10:
                    # Use 75th percentile to be robust against brief noise spikes
                    sorted_samples = sorted(self.noise_samples)
                    percentile_75 = sorted_samples[int(len(sorted_samples) * 0.75)]
                    
                    # Smooth adaptation
                    self.baseline_energy = (self.baseline_energy * 0.7 + percentile_75 * 0.3)
                    logger.debug(f"Updated baseline energy: {self.baseline_energy:.1f}")
                
                self.last_adaptation_time = current_time
    
    def _capture_interruption_context(self) -> None:
        """Capture context information at interruption point."""
        current_time = time.time()
        
        # Simple context - in a full implementation, this would capture:
        # - Current TTS position/sentence
        # - Conversation state
        # - Key resumption points
        self.interruption_context = f"interrupted_at_{int(current_time)}"
        
        logger.debug(f"Captured interruption context: {self.interruption_context}")
    
    def get_interruption_context(self) -> str:
        """Get context information from last interruption."""
        return self.interruption_context
    
    def reset_state(self) -> None:
        """Reset detection state (e.g., when starting new conversation)."""
        self.speech_frames = 0
        self.is_speech_active = False
        self.interruption_context = ""
        self.features.energy_window.clear()
        self.features.zero_crossing_window.clear()
        
        logger.debug("Interruption detector state reset")
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get current detection statistics."""
        avg_energy = self.features.get_average_energy()
        avg_zcr = self.features.get_average_zcr()
        threshold = self.thresholds[self.sensitivity]
        
        return {
            "sensitivity": self.sensitivity.value,
            "baseline_energy": self.baseline_energy,
            "current_energy": avg_energy,
            "energy_ratio": avg_energy / self.baseline_energy if self.baseline_energy > 0 else 0,
            "zero_crossing_rate": avg_zcr,
            "speech_frames": self.speech_frames,
            "is_speech_active": self.is_speech_active,
            "energy_threshold": max(
                self.baseline_energy * threshold["energy_multiplier"],
                threshold["min_energy"]
            ),
            "zcr_threshold": threshold["zcr_threshold"],
            "last_interruption": self.last_interruption_time
        }


class InterruptionManager:
    """Manages interruption handling and recovery strategies."""
    
    def __init__(self):
        self.interruption_history = deque(maxlen=100)  # Keep last 100 interruptions
        self.recovery_strategies = {
            "resume_from_key_point": self._resume_from_key_point,
            "contextual_restart": self._contextual_restart,
            "acknowledge_and_continue": self._acknowledge_and_continue
        }
    
    def handle_interruption(self, context: str, conversation_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an interruption event and determine recovery strategy.
        
        Args:
            context: Interruption context from detector
            conversation_state: Current conversation state
            
        Returns:
            Recovery strategy and parameters
        """
        interruption_data = {
            "timestamp": time.time(),
            "context": context,
            "conversation_state": conversation_state.copy(),
            "strategy": "resume_from_key_point"  # Default strategy
        }
        
        self.interruption_history.append(interruption_data)
        
        # Determine best recovery strategy based on context
        strategy = self._select_recovery_strategy(interruption_data)
        
        return {
            "strategy": strategy,
            "recovery_point": self._find_recovery_point(conversation_state),
            "acknowledgment": self._generate_acknowledgment(context),
            "context_preserved": True
        }
    
    def _select_recovery_strategy(self, interruption_data: Dict[str, Any]) -> str:
        """Select the best recovery strategy based on interruption context."""
        # Simple strategy selection - in practice, this could be more sophisticated
        recent_interruptions = [
            int_data for int_data in self.interruption_history
            if time.time() - int_data["timestamp"] < 30  # Last 30 seconds
        ]
        
        if len(recent_interruptions) > 3:
            return "acknowledge_and_continue"  # User seems impatient
        elif "urgent" in interruption_data.get("context", "").lower():
            return "contextual_restart"
        else:
            return "resume_from_key_point"
    
    def _find_recovery_point(self, conversation_state: Dict[str, Any]) -> str:
        """Find the best point to resume conversation."""
        # In a real implementation, this would analyze the conversation
        # and find logical resumption points (end of sentences, key concepts, etc.)
        return conversation_state.get("last_complete_thought", "beginning")
    
    def _generate_acknowledgment(self, context: str) -> str:
        """Generate appropriate acknowledgment for the interruption."""
        acknowledgments = [
            "I understand you want to add something.",
            "Yes, go ahead.",
            "What would you like to say?",
            "I'm listening."
        ]
        
        # Simple selection - could be more contextual
        import random
        return random.choice(acknowledgments)
    
    def _resume_from_key_point(self, recovery_data: Dict[str, Any]) -> str:
        """Resume conversation from a key logical point."""
        return f"Let me continue from where we were discussing {recovery_data['recovery_point']}..."
    
    def _contextual_restart(self, recovery_data: Dict[str, Any]) -> str:
        """Restart with context acknowledgment."""
        return f"I see this is important. Let me address your point about {recovery_data['recovery_point']}..."
    
    def _acknowledge_and_continue(self, recovery_data: Dict[str, Any]) -> str:
        """Simply acknowledge and continue."""
        return recovery_data["acknowledgment"]
    
    def get_interruption_stats(self) -> Dict[str, Any]:
        """Get statistics about interruption patterns."""
        if not self.interruption_history:
            return {"total_interruptions": 0}
        
        recent_count = len([
            int_data for int_data in self.interruption_history
            if time.time() - int_data["timestamp"] < 300  # Last 5 minutes
        ])
        
        return {
            "total_interruptions": len(self.interruption_history),
            "recent_interruptions": recent_count,
            "average_gap": self._calculate_average_gap(),
            "most_common_strategy": self._most_common_strategy()
        }
    
    def _calculate_average_gap(self) -> float:
        """Calculate average time between interruptions."""
        if len(self.interruption_history) < 2:
            return 0.0
        
        gaps = []
        for i in range(1, len(self.interruption_history)):
            gap = (self.interruption_history[i]["timestamp"] - 
                   self.interruption_history[i-1]["timestamp"])
            gaps.append(gap)
        
        return sum(gaps) / len(gaps) if gaps else 0.0
    
    def _most_common_strategy(self) -> str:
        """Get the most commonly used recovery strategy."""
        if not self.interruption_history:
            return "none"
        
        strategies = [int_data["strategy"] for int_data in self.interruption_history]
        return max(set(strategies), key=strategies.count)