# EduAGI - Accessibility-First Educational AI

An inclusive educational AI system designed to accommodate diverse learning needs and disabilities.

## Accessibility Engine (Phase 1)

### Core Features

**🎯 AccessibilityProfile**
- Stores comprehensive user accessibility needs
- Supports visual, hearing, cognitive, and motor impairments
- Auto-detects patterns and suggests accommodations
- Severity-aware configuration (mild/moderate/severe)

**🗣️ VoiceOnlyMode**
- Complete learning flow without visual UI
- Math-to-speech conversion (equations → spoken language)
- Diagram descriptions and spatial content adaptation
- Interactive voice-based lessons for blind students

**📝 SimplifiedLanguageProcessor**
- Auto-simplifies complex explanations
- Shorter sentences, simpler vocabulary
- More examples and concrete concepts
- Cognitive load reduction for learning disabilities

**⏳ PatienceMode**
- Configurable response timeouts
- No time pressure learning environment
- Adaptive timeouts based on user patterns
- Encouraging feedback and progress celebration

**🔧 Configuration Classes**
- **SpeechConfig**: Rate, pitch, pause duration control
- **HighContrastConfig**: WCAG AA compliant visual settings
- **DyslexiaFriendlyConfig**: Typography and spacing optimization

**🕵️ AccessibilityDetector**
- Analyzes typing speed patterns → suggests voice input
- Detects frequent errors → recommends simplified mode
- Monitors response times → enables patience mode
- Machine learning approach to accessibility needs

### Disability-Aware FSRS

**🧠 Cognitive Memory Profiles**
- ADHD: Reduced stability, frequent reviews, shorter sessions
- Dyslexia: Slower consolidation, difficulty ceiling, hints enabled  
- Autism: Enhanced positive reinforcement, clear progress indicators
- Intellectual Disabilities: Maximum support with micro-learning
- Working Memory Deficits: Reduced interference, frequent breaks

**📊 Adaptive Scheduling**
- Different memory curves per cognitive profile
- Longer intervals adjusted for learning disabilities
- Encouragement reviews for confidence building
- Dynamic difficulty ceiling based on success rates

**💪 Encouragement System**
- Profile-specific motivational messages
- Success celebration adapted to user needs
- Progress visualization for different learning styles
- Mistake normalization and growth mindset reinforcement

## Usage Example

```python
from accessibility_engine import AccessibilityEngine, ImpairmentType, SeverityLevel
from disability_aware_fsrs import DisabilityAwareFSRS

# Initialize systems
engine = AccessibilityEngine()
fsrs = DisabilityAwareFSRS()

# Create user profile
profile = engine.create_profile("student_123")
profile.add_impairment(ImpairmentType.COGNITIVE, "dyslexia", SeverityLevel.MODERATE)
profile.add_impairment(ImpairmentType.VISUAL, "low_vision", SeverityLevel.MILD)

# Register with FSRS
fsrs.register_cognitive_profile("student_123", profile)

# Process educational content
content = "This demonstrates complex photosynthetic mechanisms."
accessible_content = engine.process_content("student_123", content)
# Output: "This shows how plants make food. For example: A tree uses sunlight."

# Get UI configuration
ui_config = engine.get_ui_config("student_123")
# Returns: High contrast + dyslexia-friendly settings

# Schedule learning with adaptive FSRS
card = fsrs.schedule_new_card("student_123", initial_difficulty=4.0)
# Automatically limited to appropriate difficulty ceiling

# Handle review with encouragement
updated_card = fsrs.schedule_review("student_123", card, ReviewOutcome.GOOD)
encouragement = fsrs.get_encouragement_message("student_123", updated_card, ReviewOutcome.GOOD)
# Returns: "Great effort! You're making progress!"
```

## Testing

Run comprehensive tests:

```bash
pip install -r requirements.txt
python -m pytest src/test_accessibility_modules.py -v
```

## Architecture Principles

1. **Inclusive by Design**: Accessibility considered from ground up
2. **Adaptive Learning**: System learns user needs and adjusts automatically  
3. **Evidence-Based**: Uses research on cognitive science and special education
4. **Configurable**: Fine-grained control over all accessibility features
5. **Encouraging**: Emphasizes progress, effort, and growth mindset

## Next Phases

- [ ] Phase 2: Advanced voice synthesis with emotional inflection
- [ ] Phase 3: Computer vision for gesture-based interaction
- [ ] Phase 4: Real-time cognitive load monitoring
- [ ] Phase 5: Peer learning with accessibility matching