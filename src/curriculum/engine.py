"""
CurriculumEngine: Core curriculum management for East African education systems.

Manages subject hierarchies, grade levels, and learning progression across
Uganda (Primary 1-7, Senior 1-6) and Kenya (Form 1-4) education systems.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime


class Country(Enum):
    UGANDA = "uganda"
    KENYA = "kenya"


class Subject(Enum):
    MATHEMATICS = "mathematics"
    SCIENCE = "science"
    ENGLISH = "english"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    ICT = "ict"


class DifficultyLevel(Enum):
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3
    EXPERT = 4


@dataclass
class GradeLevel:
    """Represents a grade level with country-specific naming."""
    level: int
    country: Country
    display_name: str
    age_range: Tuple[int, int]
    
    def __post_init__(self):
        if self.country == Country.UGANDA:
            if 1 <= self.level <= 7:
                self.cycle = "primary"
            elif 8 <= self.level <= 13:  # Senior 1-6 mapped to 8-13
                self.cycle = "secondary"
            else:
                raise ValueError(f"Invalid Uganda grade level: {self.level}")
        elif self.country == Country.KENYA:
            if 1 <= self.level <= 8:
                self.cycle = "primary"
            elif 9 <= self.level <= 12:  # Form 1-4 mapped to 9-12
                self.cycle = "secondary"
            else:
                raise ValueError(f"Invalid Kenya grade level: {self.level}")


@dataclass
class LearningObjective:
    """Specific learning objective within a topic."""
    id: str
    description: str
    difficulty: DifficultyLevel
    assessment_criteria: List[str] = field(default_factory=list)
    estimated_hours: float = 1.0


@dataclass
class Topic:
    """Curriculum topic with learning objectives and prerequisites."""
    id: str
    name: str
    description: str
    subject: Subject
    grade_level: int
    country: Country
    learning_objectives: List[LearningObjective] = field(default_factory=list)
    prerequisites: Set[str] = field(default_factory=set)
    difficulty_progression: List[DifficultyLevel] = field(default_factory=list)
    estimated_weeks: int = 2
    
    def add_objective(self, objective: LearningObjective):
        """Add a learning objective to this topic."""
        self.learning_objectives.append(objective)
    
    def add_prerequisite(self, topic_id: str):
        """Add a prerequisite topic."""
        self.prerequisites.add(topic_id)


class CurriculumEngine:
    """
    Main curriculum management engine for East African education systems.
    
    Handles subject hierarchies, grade progressions, and learning pathways
    across Uganda and Kenya education standards.
    """
    
    def __init__(self):
        self.topics: Dict[str, Topic] = {}
        self.grade_levels: Dict[Country, Dict[int, GradeLevel]] = {}
        self.subject_trees: Dict[Subject, Dict[Country, Dict[int, List[str]]]] = {}
        self._initialize_grade_levels()
        self._initialize_curriculum_data()
    
    def _initialize_grade_levels(self):
        """Initialize grade level structures for Uganda and Kenya."""
        # Uganda grade levels
        uganda_grades = {}
        for i in range(1, 8):  # Primary 1-7
            uganda_grades[i] = GradeLevel(
                level=i,
                country=Country.UGANDA,
                display_name=f"Primary {i}",
                age_range=(i + 5, i + 6)
            )
        for i in range(8, 14):  # Senior 1-6 (mapped to 8-13)
            senior_level = i - 7
            uganda_grades[i] = GradeLevel(
                level=i,
                country=Country.UGANDA,
                display_name=f"Senior {senior_level}",
                age_range=(i + 5, i + 6)
            )
        self.grade_levels[Country.UGANDA] = uganda_grades
        
        # Kenya grade levels
        kenya_grades = {}
        for i in range(1, 9):  # Standard 1-8
            kenya_grades[i] = GradeLevel(
                level=i,
                country=Country.KENYA,
                display_name=f"Standard {i}",
                age_range=(i + 5, i + 6)
            )
        for i in range(9, 13):  # Form 1-4 (mapped to 9-12)
            form_level = i - 8
            kenya_grades[i] = GradeLevel(
                level=i,
                country=Country.KENYA,
                display_name=f"Form {form_level}",
                age_range=(i + 5, i + 6)
            )
        self.grade_levels[Country.KENYA] = kenya_grades
    
    def _initialize_curriculum_data(self):
        """Initialize curriculum topics for all subjects and grade levels."""
        self._initialize_mathematics()
        self._initialize_science()
        self._initialize_english()
        self._initialize_history()
        self._initialize_geography()
        self._initialize_ict()
    
    def _initialize_mathematics(self):
        """Initialize mathematics curriculum topics."""
        math_topics = {
            # Primary Level Topics
            1: ["Numbers 1-10", "Shapes and Patterns", "Counting Games", "Basic Addition", "Size Comparison", 
                "Colors and Numbers", "Simple Sorting", "Number Recognition", "Basic Subtraction", "Time Concepts"],
            2: ["Numbers 1-100", "Addition Facts", "Subtraction Facts", "Place Value", "2D Shapes", 
                "Money Counting", "Measurement Basics", "Simple Fractions", "Number Patterns", "Data Collection"],
            3: ["Multiplication Tables", "Division Basics", "Fractions Half Quarter", "3D Shapes", "Time Reading",
                "Length Measurement", "Mass and Volume", "Number Lines", "Problem Solving", "Mental Math"],
            4: ["Long Multiplication", "Long Division", "Equivalent Fractions", "Decimals Introduction", "Area Perimeter",
                "Angles Basics", "Data Graphs", "Factors Multiples", "Word Problems", "Estimation"],
            5: ["Fraction Operations", "Decimal Operations", "Percentage Basics", "Ratio Introduction", "Coordinate Geometry",
                "Circle Properties", "Statistics Basics", "Algebraic Thinking", "Scale Drawing", "Speed Distance Time"],
            6: ["Algebra Equations", "Advanced Fractions", "Percentage Problems", "Ratio Proportion", "3D Geometry",
                "Probability Basics", "Scientific Notation", "Graphing Functions", "Trigonometry Intro", "Financial Math"],
            7: ["Linear Equations", "Quadratic Introduction", "Advanced Geometry", "Statistics Analysis", "Trigonometry",
                "Logarithms Basics", "Set Theory", "Mathematical Proof", "Optimization Problems", "Mathematical Modeling"]
        }
        
        # Secondary Level Topics  
        secondary_topics = {
            8: ["Functions Graphs", "Systems of Equations", "Geometric Proofs", "Advanced Statistics", "Calculus Introduction",
                "Matrix Operations", "Complex Numbers", "Sequences Series", "Mathematical Induction", "Optimization"],
            9: ["Differential Calculus", "Integral Calculus", "Analytical Geometry", "Advanced Trigonometry", "Probability Theory",
                "Linear Programming", "Numerical Methods", "Mathematical Modeling", "Statistics Inference", "Graph Theory"],
            10: ["Multivariable Calculus", "Differential Equations", "Abstract Algebra", "Real Analysis", "Combinatorics",
                 "Game Theory", "Topology Basics", "Number Theory", "Mathematical Logic", "Research Methods"]
        }
        
        all_math_topics = {**math_topics, **secondary_topics}
        self._create_subject_topics(Subject.MATHEMATICS, all_math_topics)
    
    def _initialize_science(self):
        """Initialize science curriculum topics."""
        science_topics = {
            1: ["Living Things", "Plants Animals", "Body Parts", "Weather Changes", "Day and Night",
                "Clean Dirty", "Hot Cold", "Floating Sinking", "Push Pull", "Sound Making"],
            2: ["Animal Homes", "Plant Growth", "Human Body", "Weather Seasons", "Materials Properties",
                "Light Shadow", "Sound Travel", "Simple Machines", "Water Cycle", "Health Hygiene"],
            3: ["Life Cycles", "Plant Parts", "Body Systems", "States of Matter", "Forces Motion",
                "Heat Temperature", "Electricity Basics", "Earth Moon Sun", "Rocks Soil", "Ecosystem Basics"],
            4: ["Photosynthesis", "Human Nutrition", "Digestion System", "Chemical Changes", "Energy Forms",
                "Simple Circuits", "Solar System", "Weather Climate", "Conservation", "Scientific Method"],
            5: ["Cell Structure", "Reproduction", "Respiratory System", "Acids Bases", "Motion Laws",
                "Magnetism", "Earth Structure", "Natural Resources", "Pollution", "Experiments"],
            6: ["Genetics Basics", "Circulatory System", "Chemical Reactions", "Atomic Structure", "Wave Properties",
                "Electromagnetic Spectrum", "Plate Tectonics", "Evolution", "Biotechnology", "Research Skills"],
            7: ["Advanced Genetics", "Endocrine System", "Organic Chemistry", "Nuclear Physics", "Modern Physics",
                "Quantum Mechanics", "Climate Change", "Molecular Biology", "Environmental Science", "Data Analysis"]
        }
        
        self._create_subject_topics(Subject.SCIENCE, science_topics)
    
    def _initialize_english(self):
        """Initialize English curriculum topics."""
        english_topics = {
            1: ["Alphabet Letters", "Phonics Sounds", "Simple Words", "Picture Stories", "Listening Skills",
                "Speaking Practice", "Handwriting", "Rhyming Words", "Story Time", "Basic Grammar"],
            2: ["Reading Comprehension", "Vocabulary Building", "Sentence Structure", "Creative Writing", "Spelling",
                "Grammar Rules", "Poetry", "Dialogues", "Book Reports", "Presentation Skills"],
            3: ["Literature Analysis", "Essay Writing", "Advanced Grammar", "Research Skills", "Public Speaking",
                "Critical Thinking", "Media Literacy", "Drama Performance", "Language Arts", "Writing Process"],
            4: ["Literary Genres", "Argumentative Writing", "Language Structure", "Communication Skills", "Creative Expression",
                "Text Analysis", "Oral Literature", "Technical Writing", "Language History", "Cultural Studies"],
            5: ["World Literature", "Academic Writing", "Linguistics", "Rhetoric", "Comparative Literature",
                "Language Variation", "Digital Literacy", "Professional Communication", "Literary Criticism", "Research Methods"],
            6: ["Contemporary Literature", "Advanced Composition", "Sociolinguistics", "Discourse Analysis", "Translation Studies",
                "Publishing", "Multimedia Communication", "Language Teaching", "Literary Theory", "Independent Study"]
        }
        
        self._create_subject_topics(Subject.ENGLISH, english_topics)
    
    def _initialize_history(self):
        """Initialize history curriculum topics."""
        history_topics = {
            1: ["Family History", "Community Helpers", "Traditional Stories", "Local Customs", "Important Days",
                "Past Present", "Old New Things", "Heroes Stories", "Cultural Practices", "Time Concepts"],
            2: ["East Africa History", "Traditional Kingdoms", "Colonial Period", "Independence Movements", "National Heroes",
                "Cultural Heritage", "Archaeological Sites", "Trade Routes", "Social Changes", "Historical Timeline"],
            3: ["African Civilizations", "World History", "Industrial Revolution", "World Wars", "Decolonization",
                "Global Connections", "Historical Analysis", "Primary Sources", "Historiography", "Research Methods"]
        }
        
        self._create_subject_topics(Subject.HISTORY, history_topics)
    
    def _initialize_geography(self):
        """Initialize geography curriculum topics."""
        geography_topics = {
            1: ["My School Environment", "Home Surroundings", "Maps Directions", "Weather Observation", "Land Water",
                "Animals Plants", "Transport Modes", "Communication", "Safety Rules", "Environmental Care"],
            2: ["East African Geography", "Physical Features", "Climate Patterns", "Natural Resources", "Population Distribution",
                "Economic Activities", "Transportation Networks", "Urban Rural", "Environmental Issues", "GIS Basics"],
            3: ["World Geography", "Global Systems", "Climate Change", "Sustainable Development", "Geopolitics",
                "Remote Sensing", "Spatial Analysis", "Field Research", "Geographic Information Systems", "Cartography"]
        }
        
        self._create_subject_topics(Subject.GEOGRAPHY, geography_topics)
    
    def _initialize_ict(self):
        """Initialize ICT curriculum topics."""
        ict_topics = {
            1: ["Computer Parts", "Using Mouse", "Keyboard Basics", "Simple Games", "Drawing Programs",
                "Safety Rules", "Digital Citizenship", "Basic Operations", "File Saving", "Technology Around Us"],
            2: ["Word Processing", "Internet Basics", "Email Communication", "Presentation Software", "Spreadsheet Basics",
                "Digital Research", "Online Safety", "Multimedia Creation", "Coding Introduction", "Problem Solving"],
            3: ["Programming Concepts", "Database Management", "Web Development", "Network Fundamentals", "Cybersecurity",
                "Artificial Intelligence", "Data Analysis", "Digital Innovation", "Ethics Technology", "Career Pathways"]
        }
        
        self._create_subject_topics(Subject.ICT, ict_topics)
    
    def _create_subject_topics(self, subject: Subject, topics_by_grade: Dict[int, List[str]]):
        """Create topic objects for a subject across grade levels."""
        if subject not in self.subject_trees:
            self.subject_trees[subject] = {}
        
        for country in [Country.UGANDA, Country.KENYA]:
            if country not in self.subject_trees[subject]:
                self.subject_trees[subject][country] = {}
            
            for grade, topic_names in topics_by_grade.items():
                topic_ids = []
                for i, topic_name in enumerate(topic_names):
                    topic_id = f"{subject.value}_{country.value}_g{grade}_{i+1:02d}"
                    
                    # Create learning objectives for each topic
                    objectives = self._generate_learning_objectives(topic_name, subject, grade)
                    
                    # Determine prerequisites (topics from previous grade)
                    prerequisites = set()
                    if grade > 1 and grade-1 in topics_by_grade:
                        prev_topics = topics_by_grade[grade-1]
                        # Add some previous topics as prerequisites
                        for j, prev_topic in enumerate(prev_topics[:min(3, len(prev_topics))]):
                            prereq_id = f"{subject.value}_{country.value}_g{grade-1}_{j+1:02d}"
                            prerequisites.add(prereq_id)
                    
                    topic = Topic(
                        id=topic_id,
                        name=topic_name,
                        description=f"{topic_name} curriculum for {subject.value.title()} Grade {grade}",
                        subject=subject,
                        grade_level=grade,
                        country=country,
                        learning_objectives=objectives,
                        prerequisites=prerequisites,
                        difficulty_progression=[DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE] if grade <= 4 else 
                                              [DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED],
                        estimated_weeks=2 if grade <= 7 else 3
                    )
                    
                    self.topics[topic_id] = topic
                    topic_ids.append(topic_id)
                
                self.subject_trees[subject][country][grade] = topic_ids
    
    def _generate_learning_objectives(self, topic_name: str, subject: Subject, grade: int) -> List[LearningObjective]:
        """Generate learning objectives for a topic."""
        objectives = []
        base_difficulty = DifficultyLevel.BEGINNER if grade <= 3 else DifficultyLevel.INTERMEDIATE
        
        # Generate 3-5 objectives per topic
        for i in range(3, 6):
            obj_id = f"{topic_name.lower().replace(' ', '_')}_obj_{i}"
            objectives.append(LearningObjective(
                id=obj_id,
                description=f"Understand and apply {topic_name.lower()} concepts",
                difficulty=base_difficulty,
                assessment_criteria=[
                    "Demonstrates understanding of key concepts",
                    "Can apply knowledge to new situations", 
                    "Shows mastery through assessment"
                ],
                estimated_hours=1.5 + (0.5 * (grade - 1) / 7)  # Scale with grade level
            ))
        
        return objectives
    
    def get_topics_for_grade(self, subject: Subject, grade: int, country: Country) -> List[Topic]:
        """Get all topics for a specific subject, grade, and country."""
        if (subject in self.subject_trees and 
            country in self.subject_trees[subject] and
            grade in self.subject_trees[subject][country]):
            
            topic_ids = self.subject_trees[subject][country][grade]
            return [self.topics[topic_id] for topic_id in topic_ids if topic_id in self.topics]
        
        return []
    
    def get_prerequisites(self, topic_id: str) -> List[Topic]:
        """Get prerequisite topics for a given topic."""
        if topic_id not in self.topics:
            return []
        
        topic = self.topics[topic_id]
        return [self.topics[prereq_id] for prereq_id in topic.prerequisites if prereq_id in self.topics]
    
    def get_learning_pathway(self, subject: Subject, start_grade: int, end_grade: int, country: Country) -> List[Topic]:
        """Get a complete learning pathway across grade levels."""
        pathway = []
        for grade in range(start_grade, end_grade + 1):
            grade_topics = self.get_topics_for_grade(subject, grade, country)
            pathway.extend(grade_topics)
        
        return pathway
    
    def validate_prerequisites(self, topic_id: str, completed_topics: Set[str]) -> Tuple[bool, List[str]]:
        """Check if prerequisites are met for a topic."""
        if topic_id not in self.topics:
            return False, [f"Topic {topic_id} not found"]
        
        topic = self.topics[topic_id]
        missing_prereqs = topic.prerequisites - completed_topics
        
        return len(missing_prereqs) == 0, list(missing_prereqs)
    
    def get_next_topics(self, completed_topics: Set[str], subject: Optional[Subject] = None, 
                       country: Optional[Country] = None) -> List[Topic]:
        """Get topics that can be started based on completed prerequisites."""
        available_topics = []
        
        for topic_id, topic in self.topics.items():
            # Filter by subject and country if specified
            if subject and topic.subject != subject:
                continue
            if country and topic.country != country:
                continue
            
            # Skip if already completed
            if topic_id in completed_topics:
                continue
            
            # Check prerequisites
            can_start, _ = self.validate_prerequisites(topic_id, completed_topics)
            if can_start:
                available_topics.append(topic)
        
        return available_topics
    
    def get_curriculum_summary(self, country: Country) -> Dict[str, Dict[int, int]]:
        """Get a summary of curriculum coverage by subject and grade."""
        summary = {}
        
        for subject in Subject:
            if subject in self.subject_trees and country in self.subject_trees[subject]:
                summary[subject.value] = {
                    grade: len(topic_ids) 
                    for grade, topic_ids in self.subject_trees[subject][country].items()
                }
        
        return summary