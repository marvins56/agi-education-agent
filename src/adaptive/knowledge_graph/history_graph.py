"""History knowledge graph with concept dependencies and relationships."""
import logging
from typing import Dict, List, Set, Optional, Tuple
import numpy as np
from datetime import datetime

from src.adaptive.schemas import ConceptEmbedding, HistoryThinkingSkill, HistoryKnowledgeGraph

logger = logging.getLogger(__name__)


class HistoryKnowledgeGraphBuilder:
    """Builder for comprehensive History knowledge graph."""
    
    def __init__(self):
        self.concepts = {}
        self.concept_counter = 0
        
    def build_comprehensive_graph(self) -> HistoryKnowledgeGraph:
        """Build a comprehensive History knowledge graph."""
        
        # Create core historical concepts
        self._create_foundational_concepts()
        self._create_ancient_world_concepts()
        self._create_medieval_concepts()
        self._create_renaissance_concepts()
        self._create_modern_world_concepts()
        self._create_world_war_concepts()
        self._create_cold_war_concepts()
        self._create_contemporary_concepts()
        
        # Build relationship matrices
        num_concepts = len(self.concepts)
        prerequisite_matrix = self._build_prerequisite_matrix(num_concepts)
        difficulty_matrix = self._build_difficulty_matrix(num_concepts)
        
        # Create chronological and thematic structures
        chronological_ordering = self._create_chronological_ordering()
        thematic_clusters = self._create_thematic_clusters()
        thinking_skill_mapping = self._create_thinking_skill_mapping()
        
        return HistoryKnowledgeGraph(
            concepts=self.concepts,
            prerequisite_matrix=prerequisite_matrix,
            difficulty_matrix=difficulty_matrix,
            chronological_ordering=chronological_ordering,
            thematic_clusters=thematic_clusters,
            thinking_skill_mapping=thinking_skill_mapping
        )
    
    def _add_concept(
        self,
        name: str,
        subject: str = "History",
        prerequisites: List[str] = None,
        difficulty: float = 0.5,
        importance: float = 0.5
    ) -> int:
        """Add a concept to the graph."""
        concept_id = self.concept_counter
        self.concept_counter += 1
        
        # Convert prerequisite names to IDs (will be resolved later)
        prerequisite_ids = []
        if prerequisites:
            for prereq_name in prerequisites:
                prereq_id = self._find_concept_id_by_name(prereq_name)
                if prereq_id is not None:
                    prerequisite_ids.append(prereq_id)
        
        concept = ConceptEmbedding(
            concept_id=concept_id,
            concept_name=name,
            subject=subject,
            prerequisites=prerequisite_ids,
            enables=[],  # Will be populated when building relationships
            difficulty=difficulty,
            importance=importance,
            embedding_vector=None  # Could be added later with semantic embeddings
        )
        
        self.concepts[concept_id] = concept
        return concept_id
    
    def _find_concept_id_by_name(self, name: str) -> Optional[int]:
        """Find concept ID by name."""
        for concept_id, concept in self.concepts.items():
            if concept.concept_name == name:
                return concept_id
        return None
    
    def _create_foundational_concepts(self):
        """Create foundational historical concepts."""
        
        # Basic temporal concepts
        self._add_concept("Chronological Thinking", difficulty=0.3, importance=1.0)
        self._add_concept("Historical Timeline", difficulty=0.4, importance=0.9)
        self._add_concept("BCE/CE Dating System", prerequisites=["Historical Timeline"], difficulty=0.5, importance=0.8)
        
        # Fundamental analysis concepts  
        self._add_concept("Cause and Effect", difficulty=0.6, importance=1.0)
        self._add_concept("Historical Evidence", difficulty=0.5, importance=1.0)
        self._add_concept("Primary Sources", prerequisites=["Historical Evidence"], difficulty=0.6, importance=0.9)
        self._add_concept("Secondary Sources", prerequisites=["Historical Evidence"], difficulty=0.5, importance=0.8)
        self._add_concept("Historical Bias", prerequisites=["Primary Sources"], difficulty=0.7, importance=0.9)
        
        # Context and perspective
        self._add_concept("Historical Context", difficulty=0.6, importance=1.0)
        self._add_concept("Multiple Perspectives", prerequisites=["Historical Context"], difficulty=0.7, importance=0.9)
        self._add_concept("Cultural Relativism", prerequisites=["Multiple Perspectives"], difficulty=0.8, importance=0.8)
        
        # Change over time
        self._add_concept("Historical Change", difficulty=0.5, importance=1.0)
        self._add_concept("Continuity vs Change", prerequisites=["Historical Change"], difficulty=0.7, importance=0.9)
        self._add_concept("Patterns in History", prerequisites=["Historical Change"], difficulty=0.8, importance=0.8)
    
    def _create_ancient_world_concepts(self):
        """Create ancient world historical concepts."""
        
        # Prehistory
        self._add_concept("Neolithic Revolution", prerequisites=["Historical Timeline"], difficulty=0.6, importance=0.8)
        self._add_concept("Agricultural Development", prerequisites=["Neolithic Revolution"], difficulty=0.5, importance=0.7)
        
        # Ancient Civilizations
        self._add_concept("Mesopotamian Civilization", prerequisites=["Agricultural Development"], difficulty=0.6, importance=0.8)
        self._add_concept("Ancient Egypt", prerequisites=["Agricultural Development"], difficulty=0.5, importance=0.8)
        self._add_concept("Indus Valley Civilization", prerequisites=["Agricultural Development"], difficulty=0.6, importance=0.7)
        self._add_concept("Ancient China", prerequisites=["Agricultural Development"], difficulty=0.6, importance=0.8)
        
        # Classical Antiquity
        self._add_concept("Ancient Greece", prerequisites=["Mesopotamian Civilization"], difficulty=0.6, importance=0.9)
        self._add_concept("Athenian Democracy", prerequisites=["Ancient Greece"], difficulty=0.7, importance=0.9)
        self._add_concept("Sparta", prerequisites=["Ancient Greece"], difficulty=0.6, importance=0.7)
        self._add_concept("Persian Wars", prerequisites=["Ancient Greece"], difficulty=0.7, importance=0.8)
        self._add_concept("Alexander the Great", prerequisites=["Ancient Greece"], difficulty=0.6, importance=0.8)
        self._add_concept("Hellenistic Period", prerequisites=["Alexander the Great"], difficulty=0.7, importance=0.7)
        
        # Roman Empire
        self._add_concept("Roman Republic", prerequisites=["Ancient Greece"], difficulty=0.7, importance=0.9)
        self._add_concept("Julius Caesar", prerequisites=["Roman Republic"], difficulty=0.6, importance=0.8)
        self._add_concept("Roman Empire", prerequisites=["Julius Caesar"], difficulty=0.7, importance=0.9)
        self._add_concept("Pax Romana", prerequisites=["Roman Empire"], difficulty=0.6, importance=0.8)
        self._add_concept("Fall of Rome", prerequisites=["Roman Empire"], difficulty=0.8, importance=0.9)
        
        # Ancient religions
        self._add_concept("Ancient Polytheism", prerequisites=["Ancient Egypt"], difficulty=0.5, importance=0.6)
        self._add_concept("Judaism", prerequisites=["Mesopotamian Civilization"], difficulty=0.6, importance=0.7)
        self._add_concept("Buddhism", prerequisites=["Ancient China"], difficulty=0.6, importance=0.7)
        self._add_concept("Christianity", prerequisites=["Judaism", "Roman Empire"], difficulty=0.6, importance=0.8)
    
    def _create_medieval_concepts(self):
        """Create medieval period concepts."""
        
        # Byzantine Empire
        self._add_concept("Byzantine Empire", prerequisites=["Fall of Rome"], difficulty=0.7, importance=0.8)
        self._add_concept("Justinian Code", prerequisites=["Byzantine Empire"], difficulty=0.7, importance=0.7)
        
        # Islamic Expansion
        self._add_concept("Rise of Islam", prerequisites=["Christianity"], difficulty=0.6, importance=0.8)
        self._add_concept("Islamic Conquests", prerequisites=["Rise of Islam"], difficulty=0.7, importance=0.8)
        self._add_concept("Islamic Golden Age", prerequisites=["Islamic Conquests"], difficulty=0.7, importance=0.8)
        
        # Medieval Europe
        self._add_concept("Dark Ages", prerequisites=["Fall of Rome"], difficulty=0.6, importance=0.7)
        self._add_concept("Charlemagne", prerequisites=["Dark Ages"], difficulty=0.6, importance=0.7)
        self._add_concept("Holy Roman Empire", prerequisites=["Charlemagne"], difficulty=0.7, importance=0.8)
        self._add_concept("Feudalism", prerequisites=["Dark Ages"], difficulty=0.7, importance=0.9)
        self._add_concept("Manorialism", prerequisites=["Feudalism"], difficulty=0.6, importance=0.7)
        self._add_concept("Medieval Church", prerequisites=["Christianity", "Feudalism"], difficulty=0.6, importance=0.8)
        self._add_concept("Crusades", prerequisites=["Medieval Church", "Rise of Islam"], difficulty=0.8, importance=0.8)
        
        # High Middle Ages
        self._add_concept("Medieval Universities", prerequisites=["Medieval Church"], difficulty=0.6, importance=0.7)
        self._add_concept("Gothic Architecture", prerequisites=["Medieval Church"], difficulty=0.5, importance=0.6)
        self._add_concept("Black Death", prerequisites=["Medieval Europe"], difficulty=0.7, importance=0.8)
        self._add_concept("Hundred Years War", prerequisites=["Feudalism"], difficulty=0.8, importance=0.7)
        
        # Other regions
        self._add_concept("Medieval Africa", prerequisites=["Islamic Conquests"], difficulty=0.7, importance=0.7)
        self._add_concept("Mali Empire", prerequisites=["Medieval Africa"], difficulty=0.6, importance=0.7)
        self._add_concept("Medieval Asia", prerequisites=["Ancient China"], difficulty=0.7, importance=0.7)
        self._add_concept("Mongol Empire", prerequisites=["Medieval Asia"], difficulty=0.8, importance=0.8)
    
    def _create_renaissance_concepts(self):
        """Create Renaissance and Early Modern concepts."""
        
        # Renaissance
        self._add_concept("Italian Renaissance", prerequisites=["Black Death"], difficulty=0.7, importance=0.9)
        self._add_concept("Renaissance Humanism", prerequisites=["Italian Renaissance"], difficulty=0.8, importance=0.8)
        self._add_concept("Renaissance Art", prerequisites=["Italian Renaissance"], difficulty=0.6, importance=0.7)
        self._add_concept("Leonardo da Vinci", prerequisites=["Renaissance Art"], difficulty=0.5, importance=0.7)
        self._add_concept("Printing Press", prerequisites=["Italian Renaissance"], difficulty=0.6, importance=0.9)
        
        # Reformation
        self._add_concept("Protestant Reformation", prerequisites=["Medieval Church", "Printing Press"], difficulty=0.8, importance=0.9)
        self._add_concept("Martin Luther", prerequisites=["Protestant Reformation"], difficulty=0.6, importance=0.8)
        self._add_concept("Counter-Reformation", prerequisites=["Protestant Reformation"], difficulty=0.7, importance=0.7)
        
        # Age of Exploration
        self._add_concept("Age of Exploration", prerequisites=["Italian Renaissance"], difficulty=0.7, importance=0.9)
        self._add_concept("Christopher Columbus", prerequisites=["Age of Exploration"], difficulty=0.5, importance=0.8)
        self._add_concept("Conquistadors", prerequisites=["Age of Exploration"], difficulty=0.6, importance=0.7)
        self._add_concept("Columbian Exchange", prerequisites=["Christopher Columbus"], difficulty=0.8, importance=0.9)
        self._add_concept("Atlantic Slave Trade", prerequisites=["Columbian Exchange"], difficulty=0.8, importance=0.9)
        
        # Early Modern States
        self._add_concept("Absolute Monarchy", prerequisites=["Protestant Reformation"], difficulty=0.7, importance=0.8)
        self._add_concept("Louis XIV", prerequisites=["Absolute Monarchy"], difficulty=0.6, importance=0.7)
        self._add_concept("English Civil War", prerequisites=["Protestant Reformation"], difficulty=0.8, importance=0.8)
        self._add_concept("Scientific Revolution", prerequisites=["Renaissance Humanism"], difficulty=0.8, importance=0.9)
        self._add_concept("Enlightenment", prerequisites=["Scientific Revolution"], difficulty=0.8, importance=1.0)
    
    def _create_modern_world_concepts(self):
        """Create modern world concepts (1750-1914)."""
        
        # Revolutions
        self._add_concept("American Revolution", prerequisites=["Enlightenment"], difficulty=0.7, importance=0.9)
        self._add_concept("French Revolution", prerequisites=["Enlightenment"], difficulty=0.8, importance=1.0)
        self._add_concept("Napoleon", prerequisites=["French Revolution"], difficulty=0.7, importance=0.8)
        self._add_concept("Congress of Vienna", prerequisites=["Napoleon"], difficulty=0.8, importance=0.7)
        
        # Industrial Revolution
        self._add_concept("Industrial Revolution", prerequisites=["Scientific Revolution"], difficulty=0.8, importance=1.0)
        self._add_concept("Steam Engine", prerequisites=["Industrial Revolution"], difficulty=0.6, importance=0.8)
        self._add_concept("Factory System", prerequisites=["Industrial Revolution"], difficulty=0.7, importance=0.8)
        self._add_concept("Urbanization", prerequisites=["Factory System"], difficulty=0.7, importance=0.8)
        self._add_concept("Labor Movements", prerequisites=["Factory System"], difficulty=0.8, importance=0.8)
        
        # Nationalism and Liberalism
        self._add_concept("Nationalism", prerequisites=["French Revolution"], difficulty=0.8, importance=0.9)
        self._add_concept("Liberalism", prerequisites=["Enlightenment"], difficulty=0.8, importance=0.8)
        self._add_concept("Unification of Germany", prerequisites=["Nationalism"], difficulty=0.8, importance=0.8)
        self._add_concept("Unification of Italy", prerequisites=["Nationalism"], difficulty=0.8, importance=0.7)
        
        # Imperialism
        self._add_concept("New Imperialism", prerequisites=["Industrial Revolution"], difficulty=0.8, importance=0.9)
        self._add_concept("Scramble for Africa", prerequisites=["New Imperialism"], difficulty=0.8, importance=0.8)
        self._add_concept("British Empire", prerequisites=["Industrial Revolution"], difficulty=0.7, importance=0.8)
        self._add_concept("Opium Wars", prerequisites=["British Empire"], difficulty=0.7, importance=0.7)
        
        # Social Changes
        self._add_concept("Abolition of Slavery", prerequisites=["Enlightenment"], difficulty=0.7, importance=0.9)
        self._add_concept("Women's Rights Movement", prerequisites=["Liberalism"], difficulty=0.8, importance=0.8)
        self._add_concept("Education Reform", prerequisites=["Industrial Revolution"], difficulty=0.6, importance=0.7)
    
    def _create_world_war_concepts(self):
        """Create World War era concepts (1914-1945)."""
        
        # WWI
        self._add_concept("Causes of WWI", prerequisites=["Nationalism", "New Imperialism"], difficulty=0.9, importance=1.0)
        self._add_concept("Alliance System", prerequisites=["Causes of WWI"], difficulty=0.8, importance=0.9)
        self._add_concept("Trench Warfare", prerequisites=["WWI"], difficulty=0.6, importance=0.8)
        self._add_concept("WWI", prerequisites=["Causes of WWI"], difficulty=0.8, importance=1.0)
        self._add_concept("Russian Revolution", prerequisites=["WWI"], difficulty=0.9, importance=0.9)
        self._add_concept("Treaty of Versailles", prerequisites=["WWI"], difficulty=0.8, importance=0.9)
        
        # Interwar Period
        self._add_concept("Great Depression", prerequisites=["WWI"], difficulty=0.8, importance=0.9)
        self._add_concept("Rise of Fascism", prerequisites=["Treaty of Versailles", "Great Depression"], difficulty=0.9, importance=0.9)
        self._add_concept("Hitler's Rise", prerequisites=["Rise of Fascism"], difficulty=0.8, importance=0.9)
        self._add_concept("Soviet Union", prerequisites=["Russian Revolution"], difficulty=0.8, importance=0.9)
        self._add_concept("Stalin", prerequisites=["Soviet Union"], difficulty=0.7, importance=0.8)
        
        # WWII
        self._add_concept("Causes of WWII", prerequisites=["Rise of Fascism"], difficulty=0.9, importance=1.0)
        self._add_concept("WWII", prerequisites=["Causes of WWII"], difficulty=0.8, importance=1.0)
        self._add_concept("Holocaust", prerequisites=["WWII"], difficulty=0.9, importance=1.0)
        self._add_concept("Pearl Harbor", prerequisites=["WWII"], difficulty=0.6, importance=0.8)
        self._add_concept("D-Day", prerequisites=["WWII"], difficulty=0.6, importance=0.8)
        self._add_concept("Atomic Bomb", prerequisites=["WWII"], difficulty=0.7, importance=0.9)
        self._add_concept("End of WWII", prerequisites=["Atomic Bomb"], difficulty=0.7, importance=0.9)
    
    def _create_cold_war_concepts(self):
        """Create Cold War era concepts (1945-1991)."""
        
        # Cold War Beginning
        self._add_concept("Cold War Origins", prerequisites=["End of WWII"], difficulty=0.8, importance=0.9)
        self._add_concept("Iron Curtain", prerequisites=["Cold War Origins"], difficulty=0.7, importance=0.8)
        self._add_concept("Marshall Plan", prerequisites=["Cold War Origins"], difficulty=0.7, importance=0.8)
        self._add_concept("NATO", prerequisites=["Marshall Plan"], difficulty=0.6, importance=0.7)
        self._add_concept("Warsaw Pact", prerequisites=["NATO"], difficulty=0.6, importance=0.7)
        
        # Cold War Events
        self._add_concept("Korean War", prerequisites=["Cold War Origins"], difficulty=0.7, importance=0.7)
        self._add_concept("Cuban Missile Crisis", prerequisites=["Cold War Origins"], difficulty=0.8, importance=0.8)
        self._add_concept("Vietnam War", prerequisites=["Korean War"], difficulty=0.8, importance=0.8)
        self._add_concept("Space Race", prerequisites=["Cold War Origins"], difficulty=0.6, importance=0.7)
        self._add_concept("Berlin Wall", prerequisites=["Iron Curtain"], difficulty=0.6, importance=0.8)
        
        # Decolonization
        self._add_concept("Decolonization", prerequisites=["End of WWII"], difficulty=0.8, importance=0.9)
        self._add_concept("Indian Independence", prerequisites=["Decolonization"], difficulty=0.7, importance=0.8)
        self._add_concept("African Decolonization", prerequisites=["Decolonization"], difficulty=0.8, importance=0.8)
        
        # Civil Rights
        self._add_concept("Civil Rights Movement", prerequisites=["End of WWII"], difficulty=0.8, importance=0.9)
        self._add_concept("Martin Luther King Jr.", prerequisites=["Civil Rights Movement"], difficulty=0.6, importance=0.8)
        
        # Cold War End
        self._add_concept("Détente", prerequisites=["Cuban Missile Crisis"], difficulty=0.7, importance=0.7)
        self._add_concept("Gorbachev", prerequisites=["Soviet Union"], difficulty=0.6, importance=0.7)
        self._add_concept("Fall of Berlin Wall", prerequisites=["Berlin Wall"], difficulty=0.6, importance=0.8)
        self._add_concept("End of Cold War", prerequisites=["Fall of Berlin Wall"], difficulty=0.7, importance=0.9)
    
    def _create_contemporary_concepts(self):
        """Create contemporary world concepts (1991-present)."""
        
        self._add_concept("Post-Cold War World", prerequisites=["End of Cold War"], difficulty=0.7, importance=0.8)
        self._add_concept("Globalization", prerequisites=["Post-Cold War World"], difficulty=0.8, importance=0.9)
        self._add_concept("Internet Revolution", prerequisites=["Globalization"], difficulty=0.6, importance=0.8)
        self._add_concept("9/11 Attacks", prerequisites=["Post-Cold War World"], difficulty=0.6, importance=0.8)
        self._add_concept("War on Terror", prerequisites=["9/11 Attacks"], difficulty=0.7, importance=0.8)
        self._add_concept("Climate Change", prerequisites=["Globalization"], difficulty=0.8, importance=0.9)
    
    def _build_prerequisite_matrix(self, num_concepts: int) -> np.ndarray:
        """Build prerequisite relationship matrix."""
        matrix = np.zeros((num_concepts, num_concepts), dtype=int)
        
        for concept_id, concept in self.concepts.items():
            for prereq_id in concept.prerequisites:
                if prereq_id < num_concepts:
                    matrix[concept_id][prereq_id] = 1
        
        return matrix
    
    def _build_difficulty_matrix(self, num_concepts: int) -> np.ndarray:
        """Build difficulty relationship matrix."""
        matrix = np.zeros((num_concepts, num_concepts))
        
        for concept_id, concept in self.concepts.items():
            matrix[concept_id][concept_id] = concept.difficulty
        
        return matrix
    
    def _create_chronological_ordering(self) -> Dict[str, List[int]]:
        """Create chronological ordering of concepts."""
        
        ordering = {
            "Prehistory": [],
            "Ancient World (3000 BCE - 500 CE)": [],
            "Medieval Period (500 - 1450)": [],
            "Early Modern (1450 - 1750)": [],
            "Modern Era (1750 - 1914)": [],
            "World Wars (1914 - 1945)": [],
            "Cold War Era (1945 - 1991)": [],
            "Contemporary (1991 - Present)": []
        }
        
        # Map concepts to time periods based on keywords
        for concept_id, concept in self.concepts.items():
            name_lower = concept.concept_name.lower()
            
            if any(word in name_lower for word in ["neolithic", "agricultural"]):
                ordering["Prehistory"].append(concept_id)
            elif any(word in name_lower for word in ["ancient", "rome", "greece", "egypt", "mesopotamian"]):
                ordering["Ancient World (3000 BCE - 500 CE)"].append(concept_id)
            elif any(word in name_lower for word in ["medieval", "feudal", "crusade", "byzantine", "islam"]):
                ordering["Medieval Period (500 - 1450)"].append(concept_id)
            elif any(word in name_lower for word in ["renaissance", "reformation", "exploration", "columbus"]):
                ordering["Early Modern (1450 - 1750)"].append(concept_id)
            elif any(word in name_lower for word in ["revolution", "napoleon", "industrial", "nationalism"]):
                ordering["Modern Era (1750 - 1914)"].append(concept_id)
            elif any(word in name_lower for word in ["wwi", "wwii", "world war", "holocaust", "treaty"]):
                ordering["World Wars (1914 - 1945)"].append(concept_id)
            elif any(word in name_lower for word in ["cold war", "soviet", "korean", "vietnam", "cuba"]):
                ordering["Cold War Era (1945 - 1991)"].append(concept_id)
            elif any(word in name_lower for word in ["globalization", "internet", "9/11", "climate"]):
                ordering["Contemporary (1991 - Present)"].append(concept_id)
        
        return ordering
    
    def _create_thematic_clusters(self) -> Dict[str, List[int]]:
        """Create thematic clusters of concepts."""
        
        clusters = {
            "Political Systems": [],
            "Economic Systems": [],
            "Social Movements": [],
            "Military History": [],
            "Cultural Development": [],
            "Religious History": [],
            "Technological Progress": [],
            "Geographic Regions": []
        }
        
        for concept_id, concept in self.concepts.items():
            name_lower = concept.concept_name.lower()
            
            if any(word in name_lower for word in ["government", "democracy", "empire", "political", "monarchy"]):
                clusters["Political Systems"].append(concept_id)
            elif any(word in name_lower for word in ["economic", "trade", "industrial", "economy", "depression"]):
                clusters["Economic Systems"].append(concept_id)
            elif any(word in name_lower for word in ["rights", "movement", "civil", "women", "labor"]):
                clusters["Social Movements"].append(concept_id)
            elif any(word in name_lower for word in ["war", "military", "battle", "conquest", "army"]):
                clusters["Military History"].append(concept_id)
            elif any(word in name_lower for word in ["culture", "art", "renaissance", "architecture", "education"]):
                clusters["Cultural Development"].append(concept_id)
            elif any(word in name_lower for word in ["religion", "church", "islam", "christianity", "buddhism"]):
                clusters["Religious History"].append(concept_id)
            elif any(word in name_lower for word in ["technology", "invention", "steam", "printing", "internet"]):
                clusters["Technological Progress"].append(concept_id)
            elif any(word in name_lower for word in ["africa", "asia", "europe", "america", "region"]):
                clusters["Geographic Regions"].append(concept_id)
        
        return clusters
    
    def _create_thinking_skill_mapping(self) -> Dict[HistoryThinkingSkill, List[int]]:
        """Map concepts to historical thinking skills."""
        
        mapping = {
            HistoryThinkingSkill.CHRONOLOGICAL_REASONING: [],
            HistoryThinkingSkill.CRAFTING_ARGUMENTS: [],
            HistoryThinkingSkill.ANALYZING_SOURCES: [],
            HistoryThinkingSkill.CONTEXTUALIZATION: [],
            HistoryThinkingSkill.SYNTHESIS: []
        }
        
        for concept_id, concept in self.concepts.items():
            name_lower = concept.concept_name.lower()
            
            # Chronological reasoning - timeline and sequence concepts
            if any(word in name_lower for word in ["timeline", "chronological", "sequence", "dating", "period"]):
                mapping[HistoryThinkingSkill.CHRONOLOGICAL_REASONING].append(concept_id)
            
            # Source analysis - evidence and source concepts  
            if any(word in name_lower for word in ["source", "evidence", "bias", "perspective", "document"]):
                mapping[HistoryThinkingSkill.ANALYZING_SOURCES].append(concept_id)
            
            # Contextualization - understanding historical context
            if any(word in name_lower for word in ["context", "background", "setting", "environment"]):
                mapping[HistoryThinkingSkill.CONTEXTUALIZATION].append(concept_id)
            
            # Argument crafting - causation and complex concepts
            if any(word in name_lower for word in ["cause", "effect", "argument", "thesis", "claim"]):
                mapping[HistoryThinkingSkill.CRAFTING_ARGUMENTS].append(concept_id)
            
            # Synthesis - complex concepts that require integration
            if concept.difficulty > 0.7:  # High difficulty concepts typically require synthesis
                mapping[HistoryThinkingSkill.SYNTHESIS].append(concept_id)
        
        return mapping


# Convenience function to build the graph
def build_history_knowledge_graph() -> HistoryKnowledgeGraph:
    """Build and return a comprehensive History knowledge graph."""
    builder = HistoryKnowledgeGraphBuilder()
    return builder.build_comprehensive_graph()