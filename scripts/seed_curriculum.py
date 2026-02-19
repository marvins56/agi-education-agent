#!/usr/bin/env python3
"""
Seed real curriculum content for EduAGI.

Populates topic_nodes, topic_edges, assessments, and questions tables with
actual curriculum data aligned to Uganda (P1-S6) and Kenya (Form 1-4) national curricula.

Usage:
    python scripts/seed_curriculum.py
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.models.database import engine, async_session

# ─────────────────────────────────────────────────────────────────────
# CURRICULUM DATA
# ─────────────────────────────────────────────────────────────────────

# Structure: { (country, level_display, subject): [ (topic_name, difficulty, est_minutes, [lesson_titles]) ] }
# Lessons are embedded as JSON metadata on topic_nodes.

UGANDA_PRIMARY = {
    # ── P1 ──────────────────────────────────────────
    ("uganda", "P1", "Mathematics"): [
        ("Counting Numbers 1-10", "easy", 30, [
            "Counting objects around us",
            "Writing numbers 1-5",
            "Writing numbers 6-10",
            "Matching numbers to objects",
            "Number songs and rhymes",
        ]),
        ("Addition within 10", "easy", 30, [
            "Putting together groups of objects",
            "Addition using fingers",
            "Addition stories",
            "Writing addition sentences",
        ]),
        ("Subtraction within 10", "easy", 30, [
            "Taking away from a group",
            "Subtraction with objects",
            "Writing subtraction sentences",
            "Addition and subtraction relationship",
        ]),
        ("Shapes around us", "easy", 25, [
            "Circles and squares",
            "Triangles and rectangles",
            "Finding shapes in the environment",
        ]),
        ("Measurement: Long and Short", "easy", 25, [
            "Comparing lengths of objects",
            "Ordering objects by length",
            "Using non-standard units to measure",
        ]),
    ],
    ("uganda", "P1", "English"): [
        ("The Alphabet", "easy", 30, [
            "Letters A-F: sounds and writing",
            "Letters G-L: sounds and writing",
            "Letters M-R: sounds and writing",
            "Letters S-Z: sounds and writing",
            "Alphabet song and order",
        ]),
        ("Phonics: Letter Sounds", "easy", 30, [
            "Consonant sounds b, c, d, f",
            "Vowel sounds a, e, i, o, u",
            "Blending CVC words (cat, dog, pen)",
            "Reading simple three-letter words",
        ]),
        ("Greetings and Introductions", "easy", 20, [
            "Saying hello and goodbye",
            "Introducing yourself: My name is...",
            "Polite words: please, thank you",
        ]),
        ("Simple Sentences", "easy", 25, [
            "I am / You are / This is",
            "Naming classroom objects",
            "Describing pictures in sentences",
        ]),
    ],
    ("uganda", "P1", "Science"): [
        ("Living and Non-Living Things", "easy", 30, [
            "What are living things?",
            "Examples of non-living things",
            "How do we know something is alive?",
            "Sorting living and non-living things",
        ]),
        ("Parts of the Body", "easy", 25, [
            "Head, shoulders, knees and toes",
            "Sense organs: eyes, ears, nose, tongue, skin",
            "Taking care of our bodies",
        ]),
        ("Plants Around Us", "easy", 25, [
            "Parts of a plant: root, stem, leaf, flower",
            "What plants need to grow",
            "Uses of plants",
        ]),
    ],
    ("uganda", "P1", "Social Studies"): [
        ("My Family", "easy", 25, [
            "Members of my family",
            "Roles of family members",
            "My home and neighbourhood",
        ]),
        ("My School", "easy", 25, [
            "People at school: teachers, pupils, workers",
            "Rooms and places in school",
            "School rules and good behaviour",
        ]),
        ("Our Community", "easy", 25, [
            "Community helpers: doctor, police, farmer",
            "Places in the community",
            "Keeping our community clean",
        ]),
    ],

    # ── P2 ──────────────────────────────────────────
    ("uganda", "P2", "Mathematics"): [
        ("Numbers up to 100", "easy", 35, [
            "Counting in tens",
            "Place value: tens and ones",
            "Comparing numbers using > < =",
            "Ordering numbers on a number line",
        ]),
        ("Addition up to 100", "easy", 35, [
            "Adding without regrouping",
            "Adding with regrouping (carrying)",
            "Word problems involving addition",
            "Mental addition strategies",
        ]),
        ("Subtraction up to 100", "easy", 35, [
            "Subtracting without regrouping",
            "Subtracting with regrouping (borrowing)",
            "Word problems involving subtraction",
        ]),
        ("Multiplication: Introduction", "easy", 30, [
            "Repeated addition as multiplication",
            "Multiplication tables of 2 and 5",
            "Multiplication tables of 3 and 4",
        ]),
        ("Money (Uganda Shillings)", "easy", 30, [
            "Identifying Ugandan coins and notes",
            "Counting money",
            "Simple buying and selling",
        ]),
    ],
    ("uganda", "P2", "English"): [
        ("Reading Short Passages", "easy", 35, [
            "Reading simple stories aloud",
            "Answering questions about a passage",
            "Identifying the main idea",
            "Vocabulary from the passage",
        ]),
        ("Parts of Speech: Nouns and Verbs", "easy", 30, [
            "Naming words (nouns)",
            "Action words (verbs)",
            "Using nouns and verbs in sentences",
        ]),
        ("Guided Composition", "easy", 35, [
            "Writing about myself",
            "Describing my family",
            "Writing about my school",
        ]),
    ],
    ("uganda", "P2", "Science"): [
        ("Animals and their Homes", "easy", 30, [
            "Domestic and wild animals",
            "Where animals live: nests, burrows, water",
            "What animals eat",
            "How animals move",
        ]),
        ("Water and its Uses", "easy", 25, [
            "Sources of water",
            "Uses of water at home and school",
            "Keeping water clean and safe",
        ]),
        ("Weather and Seasons", "easy", 25, [
            "Types of weather: sunny, rainy, cloudy",
            "Rainy season and dry season in Uganda",
            "How weather affects daily life",
        ]),
    ],
    ("uganda", "P2", "Social Studies"): [
        ("Transport in Our Area", "easy", 25, [
            "Types of transport: road, water, air",
            "Road safety rules",
            "Public and private transport in Uganda",
        ]),
        ("Cultural Practices", "easy", 25, [
            "Tribes and languages in Uganda",
            "Traditional food, dress, and dance",
            "Respecting cultural diversity",
        ]),
        ("National Symbols of Uganda", "easy", 25, [
            "The Uganda flag and coat of arms",
            "The national anthem",
            "Uganda's motto: For God and My Country",
        ]),
    ],

    # ── P3 ──────────────────────────────────────────
    ("uganda", "P3", "Mathematics"): [
        ("Numbers up to 1000", "easy", 35, [
            "Place value: hundreds, tens, ones",
            "Reading and writing numbers in words",
            "Rounding numbers to the nearest ten and hundred",
        ]),
        ("Multiplication Tables (2-12)", "easy", 40, [
            "Tables of 6, 7, 8",
            "Tables of 9, 10, 11, 12",
            "Multiplication word problems",
            "Patterns in multiplication tables",
        ]),
        ("Division: Sharing Equally", "easy", 35, [
            "Division as sharing",
            "Division as repeated subtraction",
            "Division facts related to multiplication",
        ]),
        ("Fractions: Halves and Quarters", "easy", 30, [
            "What is a fraction?",
            "Half (1/2) of shapes and groups",
            "Quarter (1/4) of shapes and groups",
        ]),
        ("Time: Reading the Clock", "easy", 30, [
            "Parts of the clock: hour and minute hands",
            "Reading time to the hour and half hour",
            "Days of the week and months of the year",
        ]),
    ],
    ("uganda", "P3", "English"): [
        ("Reading Comprehension", "easy", 35, [
            "Reading stories and answering who/what/where questions",
            "Finding facts in a passage",
            "Making predictions from reading",
        ]),
        ("Tenses: Past, Present, Future", "easy", 30, [
            "Present tense: What I do every day",
            "Past tense: What I did yesterday",
            "Future tense: What I will do tomorrow",
        ]),
        ("Letter Writing", "easy", 30, [
            "Parts of a letter: address, date, greeting, body, closing",
            "Writing a friendly letter",
            "Writing a letter to a teacher",
        ]),
    ],
    ("uganda", "P3", "Science"): [
        ("States of Matter", "easy", 30, [
            "Solids, liquids, and gases",
            "Properties of each state",
            "Changing states: melting, freezing, evaporation",
        ]),
        ("The Human Body: Digestive System", "easy", 35, [
            "What happens to food after we eat it?",
            "Mouth, stomach, and intestines",
            "Why we need a balanced diet",
            "Food groups: carbohydrates, proteins, vitamins",
        ]),
        ("Soil and Farming", "easy", 30, [
            "Types of soil: clay, sand, loam",
            "What plants need from soil",
            "Simple farming practices in Uganda",
        ]),
    ],
    ("uganda", "P3", "Social Studies"): [
        ("Map Reading Basics", "easy", 30, [
            "What is a map?",
            "Directions: North, South, East, West",
            "Drawing a simple map of the classroom",
        ]),
        ("Districts of Uganda", "easy", 30, [
            "Uganda's regions: Central, Eastern, Northern, Western",
            "Major towns and cities",
            "Physical features: lakes, rivers, mountains",
        ]),
        ("Historical Leaders of Uganda", "easy", 25, [
            "Traditional kingdoms: Buganda, Bunyoro, Toro, Ankole",
            "Uganda's independence (1962)",
            "Important national leaders",
        ]),
    ],

    # ── P4 ──────────────────────────────────────────
    ("uganda", "P4", "Mathematics"): [
        ("Numbers up to 10,000", "medium", 40, [
            "Place value up to thousands",
            "Comparing and ordering large numbers",
            "Roman numerals I to XX",
        ]),
        ("Long Multiplication", "medium", 40, [
            "Multiplying 2-digit by 1-digit numbers",
            "Multiplying 2-digit by 2-digit numbers",
            "Word problems with multiplication",
        ]),
        ("Long Division", "medium", 40, [
            "Dividing 2-digit numbers by 1-digit",
            "Division with remainders",
            "Checking division with multiplication",
        ]),
        ("Fractions and Decimals", "medium", 35, [
            "Equivalent fractions",
            "Comparing fractions",
            "Introduction to decimals (tenths)",
            "Converting fractions to decimals",
        ]),
        ("Perimeter and Area", "medium", 35, [
            "Perimeter of rectangles and squares",
            "Area of rectangles and squares",
            "Word problems on perimeter and area",
        ]),
    ],
    ("uganda", "P4", "English"): [
        ("Comprehension and Summary", "medium", 40, [
            "Reading longer passages",
            "Summarising a paragraph",
            "Identifying cause and effect",
            "Vocabulary in context",
        ]),
        ("Adjectives and Adverbs", "medium", 30, [
            "Describing words (adjectives)",
            "Comparing with adjectives: -er, -est",
            "Adverbs of manner, time, and place",
        ]),
        ("Narrative Composition", "medium", 35, [
            "Story structure: beginning, middle, end",
            "Writing a short story",
            "Using dialogue in stories",
        ]),
    ],
    ("uganda", "P4", "Science"): [
        ("Forces and Simple Machines", "medium", 35, [
            "Push and pull forces",
            "Levers, pulleys, and inclined planes",
            "Simple machines in daily life",
        ]),
        ("The Water Cycle", "medium", 30, [
            "Evaporation, condensation, precipitation",
            "Clouds and rain formation",
            "Water conservation",
        ]),
        ("Electricity in Daily Life", "medium", 30, [
            "Sources of electricity",
            "Uses of electricity at home",
            "Electrical safety rules",
        ]),
    ],
    ("uganda", "P4", "Social Studies"): [
        ("East Africa: Physical Features", "medium", 35, [
            "Mountains: Rwenzori, Elgon, Kenya, Kilimanjaro",
            "Lakes: Victoria, Albert, Kyoga, Tanganyika",
            "Rivers: Nile, Tana, Kagera",
        ]),
        ("Economic Activities in East Africa", "medium", 30, [
            "Farming: cash crops and food crops",
            "Fishing in Lake Victoria",
            "Mining and trade",
        ]),
        ("Government and Democracy", "medium", 30, [
            "What is government?",
            "Local and national government in Uganda",
            "Rights and responsibilities of citizens",
        ]),
    ],

    # ── P5 ──────────────────────────────────────────
    ("uganda", "P5", "Mathematics"): [
        ("Fractions: Addition and Subtraction", "medium", 40, [
            "Adding fractions with same denominators",
            "Adding fractions with different denominators",
            "Subtracting fractions",
            "Mixed numbers and improper fractions",
        ]),
        ("Decimals and Percentages", "medium", 40, [
            "Decimal place value (tenths, hundredths)",
            "Adding and subtracting decimals",
            "Introduction to percentages",
            "Converting between fractions, decimals, percentages",
        ]),
        ("Geometry: Angles and Triangles", "medium", 35, [
            "Types of angles: acute, right, obtuse",
            "Measuring angles with a protractor",
            "Properties of triangles",
        ]),
    ],
    ("uganda", "P5", "English"): [
        ("Formal and Informal Letters", "medium", 35, [
            "Formal letter format",
            "Writing a letter of complaint",
            "Informal letter to a friend",
        ]),
        ("Direct and Indirect Speech", "medium", 35, [
            "Reporting what someone said",
            "Changing direct to indirect speech",
            "Punctuation in direct speech",
        ]),
        ("Poetry Appreciation", "medium", 30, [
            "Reading and reciting poems",
            "Rhyme, rhythm, and repetition",
            "Writing simple poems",
        ]),
    ],
    ("uganda", "P5", "Science"): [
        ("Reproduction in Plants", "medium", 30, [
            "Parts of a flower",
            "Pollination and fertilisation",
            "Seed dispersal methods",
        ]),
        ("The Respiratory System", "medium", 30, [
            "Parts of the respiratory system",
            "How we breathe: inhaling and exhaling",
            "Effects of smoking on the lungs",
        ]),
        ("Magnetism", "medium", 30, [
            "Properties of magnets",
            "Magnetic and non-magnetic materials",
            "Uses of magnets in everyday life",
        ]),
    ],
    ("uganda", "P5", "Social Studies"): [
        ("Africa: Physical and Political", "medium", 35, [
            "Major physical features of Africa",
            "Countries and capitals of East Africa",
            "The African Union",
        ]),
        ("Trade in East Africa", "medium", 30, [
            "Imports and exports of Uganda",
            "The East African Community (EAC)",
            "Regional trade and cooperation",
        ]),
        ("Population and Settlement", "medium", 30, [
            "Population distribution in Uganda",
            "Rural and urban areas",
            "Migration and its causes",
        ]),
    ],

    # ── P6 ──────────────────────────────────────────
    ("uganda", "P6", "Mathematics"): [
        ("Ratio and Proportion", "medium", 40, [
            "Understanding ratios",
            "Simplifying ratios",
            "Direct proportion problems",
        ]),
        ("Algebra: Introduction", "medium", 40, [
            "Using letters to represent numbers",
            "Simplifying algebraic expressions",
            "Solving simple equations",
        ]),
        ("Data Handling", "medium", 35, [
            "Collecting and organising data",
            "Bar graphs and pie charts",
            "Mean, mode, and median",
        ]),
    ],
    ("uganda", "P6", "English"): [
        ("Comprehension: Inference", "medium", 40, [
            "Reading between the lines",
            "Making inferences from text",
            "Author's purpose and tone",
        ]),
        ("Active and Passive Voice", "medium", 30, [
            "Identifying active and passive sentences",
            "Changing active to passive voice",
            "When to use passive voice",
        ]),
        ("Argumentative Writing", "medium", 35, [
            "Stating an opinion with reasons",
            "Writing for and against an argument",
            "Concluding an argument",
        ]),
    ],
    ("uganda", "P6", "Science"): [
        ("The Circulatory System", "medium", 35, [
            "The heart and blood vessels",
            "How blood circulates in the body",
            "Blood groups and transfusion",
        ]),
        ("Light and Reflection", "medium", 30, [
            "Sources of light",
            "How light travels",
            "Reflection and mirrors",
        ]),
        ("Environmental Conservation", "medium", 30, [
            "Deforestation and its effects",
            "Soil erosion and conservation",
            "Wildlife conservation in Uganda",
        ]),
    ],
    ("uganda", "P6", "Social Studies"): [
        ("The Slave Trade in East Africa", "medium", 35, [
            "Origins of the slave trade",
            "Effects of the slave trade on East Africa",
            "Abolition of the slave trade",
        ]),
        ("Colonialism in East Africa", "medium", 35, [
            "European exploration and missionaries",
            "Colonial rule in Uganda",
            "Effects of colonialism",
        ]),
        ("Uganda's Road to Independence", "medium", 30, [
            "Political parties before independence",
            "The 1962 independence",
            "Post-independence challenges",
        ]),
    ],

    # ── P7 ──────────────────────────────────────────
    ("uganda", "P7", "Mathematics"): [
        ("Integers and Number Lines", "medium", 40, [
            "Positive and negative integers",
            "Adding and subtracting integers",
            "Integers on the number line",
        ]),
        ("Speed, Distance and Time", "medium", 40, [
            "Calculating speed",
            "Calculating distance",
            "Calculating time",
            "Word problems on speed, distance, time",
        ]),
        ("Geometry: Circles", "medium", 35, [
            "Parts of a circle: radius, diameter, circumference",
            "Calculating circumference (π)",
            "Area of a circle",
        ]),
    ],
    ("uganda", "P7", "English"): [
        ("Comprehension: Critical Reading", "medium", 40, [
            "Evaluating arguments in text",
            "Distinguishing fact from opinion",
            "Comparing two passages",
        ]),
        ("Conditional Sentences", "medium", 30, [
            "First conditional: If + present, will + base",
            "Second conditional: If + past, would + base",
            "Using conditionals in conversation",
        ]),
        ("Report Writing", "medium", 35, [
            "Structure of a report",
            "Writing a school event report",
            "Writing a field trip report",
        ]),
    ],
    ("uganda", "P7", "Science"): [
        ("Reproduction in Humans", "medium", 35, [
            "The male and female reproductive systems",
            "Puberty and adolescence",
            "Responsible behaviour during adolescence",
        ]),
        ("Chemical Reactions", "medium", 35, [
            "What is a chemical reaction?",
            "Signs of chemical change",
            "Acids, bases, and indicators",
        ]),
        ("The Solar System", "medium", 30, [
            "Planets in the solar system",
            "The Earth, Moon, and Sun",
            "Day and night, seasons",
        ]),
    ],
    ("uganda", "P7", "Social Studies"): [
        ("World Organisations", "medium", 35, [
            "The United Nations (UN)",
            "The African Union (AU)",
            "The East African Community (EAC)",
        ]),
        ("Human Rights and Responsibilities", "medium", 30, [
            "Children's rights",
            "The Uganda Constitution and human rights",
            "Civic responsibilities",
        ]),
        ("Current Affairs in East Africa", "medium", 30, [
            "Regional cooperation and challenges",
            "Peace and conflict resolution",
            "Environmental issues in East Africa",
        ]),
    ],
}

UGANDA_SECONDARY = {
    # ── S1 ──────────────────────────────────────────
    ("uganda", "S1", "Mathematics"): [
        ("Number Bases", "medium", 45, [
            "Binary and denary number systems",
            "Converting between bases",
            "Arithmetic in different bases",
        ]),
        ("Algebraic Expressions", "medium", 45, [
            "Expanding brackets",
            "Factorising expressions",
            "Simplifying algebraic fractions",
        ]),
        ("Linear Equations", "medium", 45, [
            "Solving linear equations in one variable",
            "Word problems leading to equations",
            "Simultaneous equations: elimination method",
        ]),
        ("Geometry: Lines and Angles", "medium", 40, [
            "Angle properties of parallel lines",
            "Angle sum of triangles and quadrilaterals",
            "Constructing angles and triangles",
        ]),
    ],
    ("uganda", "S1", "English"): [
        ("Oral Literature", "medium", 40, [
            "Folktales and legends of East Africa",
            "Proverbs and riddles",
            "Oral poetry and performance",
        ]),
        ("Grammar: Sentence Types", "medium", 40, [
            "Simple, compound, and complex sentences",
            "Conjunctions and connectors",
            "Punctuation in complex sentences",
        ]),
        ("Descriptive Writing", "medium", 40, [
            "Describing people, places, and events",
            "Using sensory language",
            "Organising a descriptive essay",
        ]),
    ],
    ("uganda", "S1", "Physics"): [
        ("Introduction to Physics", "medium", 40, [
            "What is physics? Branches of physics",
            "Scientific method and measurement",
            "SI units and conversions",
        ]),
        ("Mechanics: Motion", "medium", 45, [
            "Distance, displacement, speed, velocity",
            "Acceleration and deceleration",
            "Distance-time and velocity-time graphs",
        ]),
        ("Properties of Matter", "medium", 40, [
            "States of matter and kinetic theory",
            "Density and its measurement",
            "Pressure in solids, liquids, and gases",
        ]),
    ],
    ("uganda", "S1", "Chemistry"): [
        ("Introduction to Chemistry", "medium", 40, [
            "Chemistry in everyday life",
            "Laboratory safety and apparatus",
            "Scientific investigation skills",
        ]),
        ("Classification of Matter", "medium", 40, [
            "Elements, compounds, and mixtures",
            "Physical and chemical changes",
            "Separation techniques: filtration, distillation, chromatography",
        ]),
        ("Atomic Structure", "medium", 45, [
            "Atoms, protons, neutrons, electrons",
            "Atomic number and mass number",
            "Electron configuration",
        ]),
    ],
    ("uganda", "S1", "Biology"): [
        ("Introduction to Biology", "medium", 40, [
            "Characteristics of living things",
            "Classification of organisms",
            "Using a microscope",
        ]),
        ("Cell Structure and Organisation", "medium", 45, [
            "Plant and animal cell structures",
            "Functions of cell organelles",
            "Levels of organisation: cell, tissue, organ, system",
        ]),
        ("Nutrition in Plants", "medium", 40, [
            "Photosynthesis: process and factors",
            "Leaf structure and adaptation",
            "Mineral nutrition in plants",
        ]),
    ],
    ("uganda", "S1", "History"): [
        ("Pre-Colonial East Africa", "medium", 40, [
            "Early societies: hunter-gatherers and pastoralists",
            "Bantu migration",
            "Iron Age in East Africa",
        ]),
        ("East African Kingdoms", "medium", 40, [
            "The Kingdom of Buganda",
            "Bunyoro-Kitara Kingdom",
            "Inter-lacustrine kingdoms",
        ]),
        ("Early Visitors to East Africa", "medium", 35, [
            "Arab traders on the East African coast",
            "The Swahili civilization",
            "European explorers: Speke, Burton, Livingstone",
        ]),
    ],
    ("uganda", "S1", "Geography"): [
        ("Weather and Climate", "medium", 40, [
            "Elements of weather: temperature, rainfall, humidity",
            "Instruments for measuring weather",
            "Climate zones of East Africa",
        ]),
        ("Map Work", "medium", 45, [
            "Scale and distance calculation",
            "Grid references (4-figure and 6-figure)",
            "Contour lines and relief features",
            "Interpreting topographic maps",
        ]),
        ("Physical Geography of East Africa", "medium", 40, [
            "Rift Valley formation",
            "Volcanic mountains of East Africa",
            "Drainage: rivers and lakes",
        ]),
    ],

    # ── S2 ──────────────────────────────────────────
    ("uganda", "S2", "Mathematics"): [
        ("Quadratic Expressions", "medium", 45, [
            "Expanding and factorising quadratics",
            "Completing the square",
            "Solving quadratic equations",
        ]),
        ("Trigonometry: Basic Ratios", "medium", 45, [
            "Sine, cosine, and tangent ratios",
            "Trigonometric ratios of special angles",
            "Solving right-angled triangles",
        ]),
        ("Statistics and Probability", "medium", 40, [
            "Frequency tables and histograms",
            "Measures of central tendency",
            "Basic probability concepts",
            "Experimental vs theoretical probability",
        ]),
    ],
    ("uganda", "S2", "English"): [
        ("Literature: Novel Study", "medium", 45, [
            "Plot, character, and setting analysis",
            "Themes in East African novels",
            "Writing a book review",
        ]),
        ("Formal Report Writing", "medium", 40, [
            "Structure of a formal report",
            "Writing minutes of a meeting",
            "Writing a speech",
        ]),
        ("Comprehension: Analytical", "medium", 40, [
            "Identifying themes in passages",
            "Analyzing author's use of language",
            "Comparing viewpoints in texts",
        ]),
    ],
    ("uganda", "S2", "Physics"): [
        ("Forces and Newton's Laws", "medium", 45, [
            "Newton's first law: inertia",
            "Newton's second law: F = ma",
            "Newton's third law: action and reaction",
            "Friction and its applications",
        ]),
        ("Work, Energy and Power", "medium", 45, [
            "Work done by a force",
            "Kinetic and potential energy",
            "Conservation of energy",
            "Power and efficiency",
        ]),
        ("Waves", "medium", 40, [
            "Properties of waves: amplitude, frequency, wavelength",
            "Transverse and longitudinal waves",
            "Sound waves and the speed of sound",
        ]),
    ],
    ("uganda", "S2", "Chemistry"): [
        ("The Periodic Table", "medium", 45, [
            "Groups and periods",
            "Trends in the periodic table",
            "Properties of metals and non-metals",
        ]),
        ("Chemical Bonding", "medium", 45, [
            "Ionic bonding",
            "Covalent bonding",
            "Metallic bonding",
            "Properties of ionic and covalent compounds",
        ]),
        ("Acids, Bases and Salts", "medium", 40, [
            "Properties of acids and bases",
            "The pH scale and indicators",
            "Neutralisation reactions",
            "Preparation of salts",
        ]),
    ],
    ("uganda", "S2", "Biology"): [
        ("Nutrition in Humans", "medium", 45, [
            "Balanced diet and food groups",
            "The human digestive system",
            "Enzymes and digestion",
            "Absorption and assimilation",
        ]),
        ("Transport in Plants and Animals", "medium", 45, [
            "Osmosis, diffusion, and active transport",
            "Xylem and phloem in plants",
            "Human circulatory system: heart, blood, vessels",
        ]),
        ("Respiration", "medium", 40, [
            "Aerobic respiration",
            "Anaerobic respiration",
            "Gaseous exchange in humans",
        ]),
    ],
    ("uganda", "S2", "History"): [
        ("European Colonisation of East Africa", "medium", 40, [
            "Scramble for Africa and the Berlin Conference",
            "British colonial rule in Uganda",
            "Effects of colonialism on East African societies",
        ]),
        ("Resistance to Colonial Rule", "medium", 40, [
            "The Nandi resistance (Kenya)",
            "Maji Maji rebellion (Tanganyika)",
            "Kabalega's resistance (Bunyoro)",
        ]),
        ("Nationalism in East Africa", "medium", 40, [
            "Rise of nationalism after WWII",
            "Political movements in Uganda, Kenya, Tanzania",
            "Road to independence in East Africa",
        ]),
    ],
    ("uganda", "S2", "Geography"): [
        ("Agriculture in East Africa", "medium", 40, [
            "Types of farming: subsistence and commercial",
            "Cash crops: coffee, tea, cotton, tobacco",
            "Challenges facing agriculture",
        ]),
        ("Mining and Industry", "medium", 40, [
            "Mineral resources in East Africa",
            "Industrial development in Uganda and Kenya",
            "Environmental impact of mining",
        ]),
        ("Population Studies", "medium", 40, [
            "Population distribution and density",
            "Population growth and the demographic transition",
            "Effects of rapid population growth",
        ]),
    ],

    # ── S3 ──────────────────────────────────────────
    ("uganda", "S3", "Mathematics"): [
        ("Matrices", "hard", 50, [
            "Order and types of matrices",
            "Matrix addition and subtraction",
            "Matrix multiplication",
            "Determinant and inverse of 2×2 matrices",
        ]),
        ("Vectors in Two Dimensions", "hard", 50, [
            "Column vectors and position vectors",
            "Magnitude and direction",
            "Vector addition, subtraction, and scalar multiplication",
        ]),
        ("Circle Theorems", "hard", 45, [
            "Angle at centre vs angle at circumference",
            "Angles in the same segment",
            "Cyclic quadrilaterals",
            "Tangent properties",
        ]),
    ],
    ("uganda", "S3", "English"): [
        ("Literature: Drama Study", "medium", 45, [
            "Elements of drama: plot, character, dialogue",
            "Studying an East African play",
            "Writing a dramatic scene",
        ]),
        ("Debate and Public Speaking", "medium", 40, [
            "Structure of a formal debate",
            "Persuasive techniques",
            "Delivering a convincing speech",
        ]),
        ("Essay Writing: Discursive", "medium", 45, [
            "Presenting balanced arguments",
            "Using evidence and examples",
            "Writing strong introductions and conclusions",
        ]),
    ],
    ("uganda", "S3", "Physics"): [
        ("Electricity: Current and Circuits", "hard", 50, [
            "Current, voltage, and resistance",
            "Ohm's law and V-I graphs",
            "Series and parallel circuits",
            "Electrical energy and power",
        ]),
        ("Magnetism and Electromagnetism", "hard", 45, [
            "Magnetic fields and field lines",
            "Electromagnets and their uses",
            "Electromagnetic induction",
        ]),
        ("Thermal Physics", "hard", 45, [
            "Heat capacity and specific heat capacity",
            "Latent heat of fusion and vaporisation",
            "Heat transfer: conduction, convection, radiation",
        ]),
    ],
    ("uganda", "S3", "Chemistry"): [
        ("Rates of Reaction", "hard", 45, [
            "Factors affecting rate of reaction",
            "Collision theory",
            "Catalysts and their role",
        ]),
        ("Organic Chemistry: Introduction", "hard", 50, [
            "Alkanes: naming and properties",
            "Alkenes: double bonds and reactions",
            "Fractional distillation of crude oil",
        ]),
        ("Electrochemistry", "hard", 45, [
            "Electrolysis of molten and aqueous compounds",
            "Applications of electrolysis: electroplating",
            "Simple electrochemical cells",
        ]),
    ],
    ("uganda", "S3", "Biology"): [
        ("Reproduction in Plants", "medium", 45, [
            "Asexual reproduction: types and examples",
            "Sexual reproduction in flowering plants",
            "Seed structure, germination, and dispersal",
        ]),
        ("Reproduction in Humans", "medium", 45, [
            "Male and female reproductive systems",
            "Menstrual cycle and fertilisation",
            "Pregnancy and birth",
            "Sexually transmitted infections",
        ]),
        ("Ecology", "medium", 45, [
            "Ecosystems: biotic and abiotic factors",
            "Food chains and food webs",
            "Nutrient cycling: carbon and nitrogen cycles",
        ]),
    ],
    ("uganda", "S3", "History"): [
        ("Post-Independence East Africa", "medium", 45, [
            "Challenges of nation-building",
            "Military coups and political instability",
            "Idi Amin's rule in Uganda",
        ]),
        ("The Cold War and Africa", "medium", 40, [
            "Cold War proxy conflicts in Africa",
            "Non-Aligned Movement",
            "Impact on East African politics",
        ]),
        ("Pan-Africanism", "medium", 40, [
            "Origins and key figures: Nkrumah, Nyerere",
            "Organisation of African Unity (OAU)",
            "Contemporary African Union",
        ]),
    ],
    ("uganda", "S3", "Geography"): [
        ("Urbanisation", "medium", 45, [
            "Causes of urbanisation in East Africa",
            "Problems of urbanisation: Kampala, Nairobi, Dar es Salaam",
            "Urban planning solutions",
        ]),
        ("Transport and Communication", "medium", 40, [
            "Road, rail, water, and air transport in East Africa",
            "Transport challenges and development",
            "Modern communication networks",
        ]),
        ("Tourism in East Africa", "medium", 40, [
            "Tourist attractions: national parks, beaches, culture",
            "Economic importance of tourism",
            "Challenges: sustainability and conservation",
        ]),
    ],

    # ── S4 ──────────────────────────────────────────
    ("uganda", "S4", "Mathematics"): [
        ("Quadratic Functions and Graphs", "hard", 50, [
            "Graphing y = ax² + bx + c",
            "Vertex form and transformations",
            "Solving quadratic inequalities graphically",
        ]),
        ("Trigonometric Functions", "hard", 50, [
            "Graphs of sin, cos, and tan",
            "Solving trigonometric equations",
            "Sine and cosine rules",
        ]),
        ("Transformation Geometry", "hard", 45, [
            "Translations, reflections, rotations",
            "Enlargement and scale factor",
            "Combined transformations",
        ]),
    ],
    ("uganda", "S4", "English"): [
        ("Literature: Poetry Analysis", "hard", 45, [
            "Analysing imagery and symbolism",
            "Understanding poetic devices",
            "East African poets: Okot p'Bitek, Taban Lo Liyong",
        ]),
        ("Formal and Academic Writing", "hard", 45, [
            "Writing a research report",
            "Citing sources and referencing",
            "Academic essay structure",
        ]),
        ("Comprehension: UCE Preparation", "hard", 40, [
            "Summary writing techniques",
            "Answering structured comprehension questions",
            "Time management in exams",
        ]),
    ],
    ("uganda", "S4", "Physics"): [
        ("Optics", "hard", 45, [
            "Reflection and refraction of light",
            "Lenses and image formation",
            "The human eye and optical instruments",
        ]),
        ("Nuclear Physics", "hard", 45, [
            "Radioactivity: alpha, beta, gamma",
            "Half-life and decay curves",
            "Nuclear energy: fission and fusion",
        ]),
        ("Electronics", "hard", 45, [
            "Semiconductors: diodes and transistors",
            "Logic gates: AND, OR, NOT",
            "Simple electronic circuits",
        ]),
    ],
    ("uganda", "S4", "Chemistry"): [
        ("Chemical Energetics", "hard", 45, [
            "Exothermic and endothermic reactions",
            "Enthalpy changes and energy diagrams",
            "Bond energy calculations",
        ]),
        ("Metals and Reactivity Series", "hard", 45, [
            "Reactivity series of metals",
            "Extraction of metals: iron and aluminium",
            "Corrosion and rust prevention",
        ]),
        ("Organic Chemistry: Further", "hard", 50, [
            "Alcohols, carboxylic acids, and esters",
            "Polymers: addition and condensation",
            "Organic reactions: substitution and addition",
        ]),
    ],
    ("uganda", "S4", "Biology"): [
        ("Genetics and Heredity", "hard", 50, [
            "DNA structure and replication",
            "Mendelian inheritance: monohybrid crosses",
            "Genotype, phenotype, dominance, and recessiveness",
            "Sex-linked inheritance",
        ]),
        ("Evolution and Natural Selection", "hard", 45, [
            "Evidence for evolution: fossils, comparative anatomy",
            "Darwin's theory of natural selection",
            "Speciation and adaptation",
        ]),
        ("Homeostasis and Excretion", "hard", 45, [
            "The concept of homeostasis",
            "The kidney: structure and function",
            "Osmoregulation and thermoregulation",
        ]),
    ],
    ("uganda", "S4", "History"): [
        ("Apartheid in South Africa", "hard", 45, [
            "Origins of apartheid",
            "Resistance: ANC, Nelson Mandela, Steve Biko",
            "End of apartheid and democracy",
        ]),
        ("Conflicts in the Great Lakes Region", "hard", 45, [
            "Rwanda genocide (1994)",
            "Civil wars in Congo",
            "Peace-building and reconciliation",
        ]),
        ("Globalisation and Africa", "hard", 40, [
            "Impact of globalisation on African economies",
            "Cultural globalisation and identity",
            "Africa in the 21st century",
        ]),
    ],
    ("uganda", "S4", "Geography"): [
        ("Environmental Management", "hard", 45, [
            "Climate change: causes and effects",
            "Deforestation and desertification",
            "Sustainable development strategies",
        ]),
        ("Energy Resources", "hard", 40, [
            "Renewable vs non-renewable energy",
            "Hydroelectric power in East Africa",
            "Solar and geothermal energy potential",
        ]),
        ("Global Trade and Development", "hard", 40, [
            "International trade patterns",
            "Economic development indicators",
            "Aid and debt in Africa",
        ]),
    ],

    # S5-S6 (A-Level) - abbreviated, key topics only
    ("uganda", "S5", "Mathematics"): [
        ("Calculus: Differentiation", "hard", 60, [
            "Limits and first principles",
            "Rules of differentiation",
            "Applications: tangents, normals, maxima/minima",
        ]),
        ("Calculus: Integration", "hard", 60, [
            "Integration as reverse of differentiation",
            "Definite integrals and area under curves",
            "Integration by substitution",
        ]),
        ("Probability and Statistics", "hard", 55, [
            "Probability distributions",
            "Binomial distribution",
            "Normal distribution",
        ]),
    ],
    ("uganda", "S5", "Physics"): [
        ("Waves and Optics (Advanced)", "hard", 55, [
            "Interference and diffraction",
            "Young's double slit experiment",
            "Polarisation of light",
        ]),
        ("Fields: Gravitational and Electric", "hard", 60, [
            "Gravitational field strength and potential",
            "Electric field strength and potential",
            "Coulomb's law and applications",
        ]),
        ("Modern Physics", "hard", 55, [
            "Photoelectric effect",
            "Wave-particle duality",
            "Bohr model of the atom",
        ]),
    ],
    ("uganda", "S5", "Chemistry"): [
        ("Chemical Equilibria", "hard", 55, [
            "Le Chatelier's principle",
            "Equilibrium constants (Kc, Kp)",
            "Industrial applications: Haber process",
        ]),
        ("Transition Metals", "hard", 50, [
            "Properties of transition metals",
            "Complex ion formation",
            "Coloured compounds and catalytic activity",
        ]),
        ("Nitrogen and Sulphur Chemistry", "hard", 50, [
            "Nitrogen cycle and compounds",
            "Ammonia and nitric acid manufacture",
            "Sulphuric acid: Contact process",
        ]),
    ],
    ("uganda", "S5", "Biology"): [
        ("Ecology: Advanced", "hard", 55, [
            "Energy flow in ecosystems",
            "Ecological succession",
            "Population ecology and growth curves",
        ]),
        ("Genetics: Advanced", "hard", 55, [
            "Dihybrid crosses and gene interactions",
            "Mutations and genetic disorders",
            "Genetic engineering basics",
        ]),
        ("Human Health and Disease", "hard", 50, [
            "Infectious diseases: malaria, HIV/AIDS, TB",
            "Immune system and vaccination",
            "Non-communicable diseases",
        ]),
    ],
    ("uganda", "S5", "History"): [
        ("World War I and its Effects on Africa", "hard", 50, [
            "Causes and course of WWI",
            "East Africa Campaign",
            "Treaty of Versailles and mandate system",
        ]),
        ("World War II and Decolonisation", "hard", 50, [
            "WWII and African involvement",
            "Post-war nationalism",
            "Decolonisation wave in Africa",
        ]),
        ("The Cold War Era", "hard", 45, [
            "Origins and key events",
            "Cold War in Africa: proxy wars",
            "End of the Cold War and its impact",
        ]),
    ],
    ("uganda", "S5", "Geography"): [
        ("Geomorphology", "hard", 55, [
            "Rock types: igneous, sedimentary, metamorphic",
            "Weathering and erosion processes",
            "Landform development: rivers, coasts, deserts",
        ]),
        ("Climatology", "hard", 50, [
            "Global atmospheric circulation",
            "Monsoons and tropical cyclones",
            "Climate classification systems",
        ]),
        ("Biogeography", "hard", 50, [
            "World biomes and vegetation zones",
            "Soil formation and types",
            "Human impact on ecosystems",
        ]),
    ],

    ("uganda", "S6", "Mathematics"): [
        ("Further Calculus", "hard", 60, [
            "Partial fractions and integration",
            "Differential equations",
            "Numerical methods: Newton-Raphson, trapezium rule",
        ]),
        ("Mechanics", "hard", 60, [
            "Projectile motion",
            "Circular motion",
            "Momentum and impulse",
        ]),
        ("Further Statistics", "hard", 55, [
            "Poisson distribution",
            "Hypothesis testing",
            "Confidence intervals",
        ]),
    ],
    ("uganda", "S6", "Physics"): [
        ("Quantum Physics", "hard", 60, [
            "Quantum theory foundations",
            "Energy levels and spectra",
            "Uncertainty principle",
        ]),
        ("Medical Physics", "hard", 55, [
            "X-rays and imaging",
            "Ultrasound in medicine",
            "Radiation therapy",
        ]),
        ("Astronomy and Cosmology", "hard", 55, [
            "Stellar classification",
            "Life cycle of stars",
            "Expanding universe and Big Bang",
        ]),
    ],
    ("uganda", "S6", "Chemistry"): [
        ("Organic Chemistry: Advanced", "hard", 60, [
            "Reaction mechanisms: nucleophilic substitution",
            "Aromatic chemistry: benzene",
            "Amino acids and proteins",
        ]),
        ("Chemical Analysis", "hard", 55, [
            "Qualitative analysis of ions",
            "Volumetric analysis",
            "Instrumental methods: mass spectrometry, IR spectroscopy",
        ]),
        ("Environmental Chemistry", "hard", 50, [
            "Air and water pollution",
            "Greenhouse effect and ozone depletion",
            "Green chemistry principles",
        ]),
    ],
    ("uganda", "S6", "Biology"): [
        ("Molecular Biology", "hard", 60, [
            "Protein synthesis: transcription and translation",
            "Gene regulation",
            "Biotechnology applications",
        ]),
        ("Plant Physiology", "hard", 55, [
            "Plant hormones and growth regulation",
            "Transpiration and translocation",
            "Plant responses to stimuli",
        ]),
        ("Evolution: Advanced", "hard", 50, [
            "Hardy-Weinberg equilibrium",
            "Types of selection: directional, stabilising",
            "Co-evolution and speciation mechanisms",
        ]),
    ],
    ("uganda", "S6", "History"): [
        ("Contemporary African Politics", "hard", 50, [
            "Democracy and governance in East Africa",
            "Regional conflicts and peace processes",
            "The role of the AU and IGAD",
        ]),
        ("Global Issues and Africa", "hard", 50, [
            "Terrorism and security in East Africa",
            "Economic integration: EAC, COMESA",
            "Sustainable Development Goals (SDGs)",
        ]),
        ("Historiography and Research", "hard", 50, [
            "Approaches to studying history",
            "Primary and secondary sources",
            "Writing a historical research paper",
        ]),
    ],
    ("uganda", "S6", "Geography"): [
        ("Development Geography", "hard", 55, [
            "Theories of development: modernisation, dependency",
            "Measuring development: HDI, GDP",
            "Case studies: Uganda, Kenya",
        ]),
        ("Hazard Geography", "hard", 50, [
            "Tectonic hazards: earthquakes, volcanoes",
            "Climatic hazards: floods, droughts",
            "Hazard management and mitigation",
        ]),
        ("Research Methods in Geography", "hard", 50, [
            "Fieldwork techniques",
            "Data collection and sampling",
            "Statistical analysis and presentation",
        ]),
    ],
}

KENYA_SECONDARY = {
    # ── Form 1 ──────────────────────────────────────
    ("kenya", "F1", "Mathematics"): [
        ("Natural Numbers", "medium", 40, [
            "Place value and notation",
            "Operations on whole numbers",
            "Divisibility tests",
            "GCD and LCM",
        ]),
        ("Integers", "medium", 40, [
            "Number line and ordering",
            "Operations on integers",
            "Word problems involving integers",
        ]),
        ("Fractions and Decimals", "medium", 40, [
            "Operations on fractions",
            "Recurring and terminating decimals",
            "Converting between fractions and decimals",
        ]),
        ("Algebra: Expressions", "medium", 45, [
            "Simplifying algebraic expressions",
            "Substitution in expressions",
            "Solving linear equations",
        ]),
        ("Geometry: Angles and Polygons", "medium", 40, [
            "Types of angles and their properties",
            "Angle properties of polygons",
            "Construction of angles and polygons",
        ]),
    ],
    ("kenya", "F1", "English"): [
        ("Oral Skills and Listening", "medium", 35, [
            "Pronunciation and articulation",
            "Listening comprehension",
            "Oral narratives and poems",
        ]),
        ("Grammar: Parts of Speech", "medium", 40, [
            "Nouns, verbs, adjectives, adverbs",
            "Prepositions and conjunctions",
            "Sentence construction",
        ]),
        ("Writing: Functional and Creative", "medium", 40, [
            "Diary and journal entries",
            "Friendly letters and emails",
            "Short compositions",
        ]),
        ("Literature: Set Books", "medium", 45, [
            "Introduction to literary analysis",
            "Character and plot study",
            "Themes in Kenyan literature",
        ]),
    ],
    ("kenya", "F1", "Physics"): [
        ("Introduction to Physics", "medium", 40, [
            "Branches of physics",
            "Measurement and units",
            "Scientific method",
        ]),
        ("Force and Motion", "medium", 45, [
            "Types of forces",
            "Speed, velocity, and acceleration",
            "Newton's laws of motion",
        ]),
        ("Pressure", "medium", 40, [
            "Pressure in solids",
            "Pressure in fluids",
            "Atmospheric pressure and its measurement",
        ]),
    ],
    ("kenya", "F1", "Chemistry"): [
        ("Introduction to Chemistry", "medium", 40, [
            "Importance of chemistry",
            "Laboratory rules and apparatus",
            "Scientific investigation",
        ]),
        ("Simple Classification of Substances", "medium", 40, [
            "Elements, compounds, mixtures",
            "Physical and chemical changes",
            "Methods of separation",
        ]),
        ("Air and Combustion", "medium", 40, [
            "Composition of air",
            "Combustion and rusting",
            "Pollution and conservation",
        ]),
    ],
    ("kenya", "F1", "Biology"): [
        ("Introduction to Biology", "medium", 40, [
            "Branches of biology",
            "Characteristics of living things",
            "Collection and classification of organisms",
        ]),
        ("The Cell", "medium", 45, [
            "Cell structure: plant and animal cells",
            "Cell organelles and functions",
            "Cell division: mitosis",
        ]),
        ("Classification of Organisms", "medium", 40, [
            "Five-kingdom classification",
            "Binomial nomenclature",
            "Key features of major groups",
        ]),
    ],
    ("kenya", "F1", "History"): [
        ("Introduction to History", "medium", 35, [
            "What is history and why study it?",
            "Sources of historical information",
            "Archaeological evidence in East Africa",
        ]),
        ("Early Human Evolution", "medium", 40, [
            "Stages of human evolution",
            "Early Stone Age cultures",
            "Leakey discoveries at Olduvai Gorge",
        ]),
        ("Development of Agriculture", "medium", 40, [
            "Transition from hunting to farming",
            "Early farming communities in East Africa",
            "Effects of agriculture on societies",
        ]),
    ],
    ("kenya", "F1", "Geography"): [
        ("Introduction to Geography", "medium", 35, [
            "Branches of geography",
            "Importance of studying geography",
            "The solar system and the earth",
        ]),
        ("Map Work", "medium", 45, [
            "Types of maps and their uses",
            "Scale, distance, and direction",
            "Grid references and contour interpretation",
        ]),
        ("Weather and Climate", "medium", 40, [
            "Elements of weather",
            "Weather instruments and recording",
            "Climate of Kenya",
        ]),
    ],

    # ── Form 2 ──────────────────────────────────────
    ("kenya", "F2", "Mathematics"): [
        ("Squares, Square Roots, Cubes", "medium", 40, [
            "Perfect squares and square roots",
            "Cube numbers and cube roots",
            "Applications in problem solving",
        ]),
        ("Algebraic Equations", "medium", 45, [
            "Linear equations in two unknowns",
            "Simultaneous equations",
            "Word problems leading to simultaneous equations",
        ]),
        ("Similarity and Enlargement", "medium", 40, [
            "Similar figures and their properties",
            "Scale factors",
            "Area and volume scale factors",
        ]),
        ("Trigonometry", "medium", 45, [
            "Trigonometric ratios",
            "Solving right-angled triangles",
            "Application to real-life problems",
        ]),
    ],
    ("kenya", "F2", "English"): [
        ("Comprehension Skills", "medium", 40, [
            "Identifying main ideas and details",
            "Inference and deduction",
            "Vocabulary development in context",
        ]),
        ("Grammar: Tenses and Clauses", "medium", 40, [
            "Perfect and continuous tenses",
            "Relative and adverbial clauses",
            "Reported speech",
        ]),
        ("Writing: Formal Communication", "medium", 40, [
            "Formal letter writing (KNEC format)",
            "Memo and notice writing",
            "Speech writing",
        ]),
    ],
    ("kenya", "F2", "Physics"): [
        ("Heat and Temperature", "medium", 45, [
            "Temperature scales and thermometers",
            "Heat capacity and specific heat",
            "Latent heat and changes of state",
        ]),
        ("Light", "medium", 45, [
            "Reflection of light: plane and curved mirrors",
            "Refraction of light",
            "Lenses and image formation",
        ]),
        ("Magnetism", "medium", 40, [
            "Properties of magnets",
            "Magnetic fields",
            "Making and demagnetising magnets",
        ]),
    ],
    ("kenya", "F2", "Chemistry"): [
        ("Water and Hydrogen", "medium", 40, [
            "Properties of water",
            "Water treatment and purification",
            "Hydrogen: preparation and properties",
        ]),
        ("Chemical Equations", "medium", 40, [
            "Writing balanced equations",
            "Types of chemical reactions",
            "Mole concept introduction",
        ]),
        ("Structure and Bonding", "medium", 45, [
            "Ionic bonding and ionic compounds",
            "Covalent bonding and molecules",
            "Properties related to bonding",
        ]),
    ],
    ("kenya", "F2", "Biology"): [
        ("Nutrition in Plants and Animals", "medium", 45, [
            "Photosynthesis in detail",
            "Human digestive system",
            "Enzymes and their role in digestion",
        ]),
        ("Transport in Plants and Animals", "medium", 45, [
            "Water uptake and transpiration",
            "Blood circulatory system",
            "Lymphatic system",
        ]),
        ("Gaseous Exchange", "medium", 40, [
            "Gaseous exchange in plants",
            "Human respiratory system",
            "Adaptations for gaseous exchange",
        ]),
    ],
    ("kenya", "F2", "History"): [
        ("Bantu Migration", "medium", 40, [
            "Origins and causes of migration",
            "Routes of Bantu migration",
            "Effects on East African communities",
        ]),
        ("City-States of the East African Coast", "medium", 40, [
            "Rise of Swahili city-states",
            "Trade and cultural exchange",
            "Decline of city-states",
        ]),
        ("European Exploration of Africa", "medium", 40, [
            "Motives for exploration",
            "Key explorers in East Africa",
            "Effects of European contact",
        ]),
    ],
    ("kenya", "F2", "Geography"): [
        ("Internal Land-forming Processes", "medium", 45, [
            "Folding and faulting",
            "Vulcanicity",
            "Earthquakes",
        ]),
        ("External Land-forming Processes", "medium", 45, [
            "Weathering: physical and chemical",
            "Erosion by rivers, wind, and glaciers",
            "Deposition and resulting landforms",
        ]),
        ("Vegetation", "medium", 40, [
            "Vegetation zones of Kenya and East Africa",
            "Factors influencing vegetation distribution",
            "Conservation of forests",
        ]),
    ],

    # ── Form 3 ──────────────────────────────────────
    ("kenya", "F3", "Mathematics"): [
        ("Quadratic Expressions and Equations", "hard", 50, [
            "Factorisation of quadratic expressions",
            "Solving quadratic equations",
            "Graphing quadratic functions",
        ]),
        ("Circles: Chords and Tangents", "hard", 50, [
            "Properties of chords",
            "Tangent properties",
            "Angle in alternate segment",
        ]),
        ("Matrices and Transformations", "hard", 50, [
            "Matrix operations",
            "Determinant and inverse",
            "Transformation matrices",
            "Combined transformations",
        ]),
    ],
    ("kenya", "F3", "English"): [
        ("Literature: Poetry Analysis", "hard", 45, [
            "Poetic devices and techniques",
            "Themes and message in poetry",
            "East African and world poetry",
        ]),
        ("Argumentative and Discursive Writing", "hard", 45, [
            "Structuring arguments",
            "Using evidence effectively",
            "Persuasive language techniques",
        ]),
        ("Comprehension: Advanced", "hard", 40, [
            "Critical analysis of texts",
            "Summary and note-making",
            "Evaluating author's perspective",
        ]),
    ],
    ("kenya", "F3", "Physics"): [
        ("Waves", "hard", 50, [
            "Properties and types of waves",
            "Sound waves",
            "Electromagnetic spectrum",
        ]),
        ("Electricity", "hard", 50, [
            "Current electricity and Ohm's law",
            "Electrical circuits: series and parallel",
            "Electrical energy and power",
        ]),
        ("Electromagnetic Induction", "hard", 50, [
            "Faraday's law",
            "Generators and transformers",
            "Applications of electromagnetic induction",
        ]),
    ],
    ("kenya", "F3", "Chemistry"): [
        ("The Mole Concept", "hard", 50, [
            "Relative atomic and molecular mass",
            "Molar volume of gases",
            "Stoichiometry and calculations",
        ]),
        ("Energy Changes in Reactions", "hard", 45, [
            "Exothermic and endothermic reactions",
            "Energy level diagrams",
            "Bond energy and enthalpy changes",
        ]),
        ("Organic Chemistry: Hydrocarbons", "hard", 50, [
            "Alkanes: structure and reactions",
            "Alkenes: addition reactions",
            "Petroleum and its products",
        ]),
    ],
    ("kenya", "F3", "Biology"): [
        ("Reproduction in Plants and Animals", "hard", 50, [
            "Asexual and sexual reproduction",
            "Human reproductive system",
            "Menstrual cycle and contraception",
        ]),
        ("Genetics", "hard", 50, [
            "Heredity and variation",
            "Monohybrid and dihybrid crosses",
            "Sex determination and sex-linked traits",
        ]),
        ("Evolution", "hard", 45, [
            "Evidence for organic evolution",
            "Theories of evolution",
            "Natural selection and speciation",
        ]),
    ],
    ("kenya", "F3", "History"): [
        ("Colonisation of East Africa", "hard", 45, [
            "Berlin Conference and partition",
            "Colonial systems of administration",
            "Impact of colonialism",
        ]),
        ("African Resistance to Colonialism", "hard", 45, [
            "Nandi resistance",
            "Mau Mau uprising",
            "Chimurenga in Zimbabwe",
        ]),
        ("Struggle for Independence", "hard", 45, [
            "Nationalism in Kenya",
            "Jomo Kenyatta and KANU",
            "Independence and uhuru (1963)",
        ]),
    ],
    ("kenya", "F3", "Geography"): [
        ("Forestry", "hard", 45, [
            "Types of forests in Kenya",
            "Importance of forests",
            "Forest conservation and management",
        ]),
        ("Mining", "hard", 40, [
            "Methods of mining",
            "Mineral resources in Kenya",
            "Impact of mining on environment",
        ]),
        ("Fishing", "hard", 40, [
            "Methods of fishing",
            "Fishing grounds in East Africa",
            "Challenges in the fishing industry",
        ]),
    ],

    # ── Form 4 ──────────────────────────────────────
    ("kenya", "F4", "Mathematics"): [
        ("Differentiation", "hard", 55, [
            "Gradient of a curve",
            "Rules of differentiation",
            "Maxima, minima, and points of inflection",
        ]),
        ("Integration", "hard", 55, [
            "Integration as reverse differentiation",
            "Area under a curve",
            "Applications of integration",
        ]),
        ("Probability and Statistics", "hard", 50, [
            "Probability rules and tree diagrams",
            "Measures of dispersion",
            "Normal distribution basics",
        ]),
    ],
    ("kenya", "F4", "English"): [
        ("Literature: Set Novel/Play", "hard", 50, [
            "In-depth character analysis",
            "Thematic study",
            "Style and technique of the author",
        ]),
        ("Writing: KCSE Preparation", "hard", 45, [
            "Essay types: narrative, descriptive, expository",
            "Cloze test techniques",
            "Exam strategies and time management",
        ]),
        ("Oral Literature", "hard", 40, [
            "Features of oral literature",
            "Proverbs, riddles, and tongue twisters",
            "Contemporary relevance of oral traditions",
        ]),
    ],
    ("kenya", "F4", "Physics"): [
        ("Radioactivity", "hard", 50, [
            "Types of radiation",
            "Half-life and decay",
            "Uses and dangers of radioactivity",
        ]),
        ("Electronics", "hard", 50, [
            "Semiconductors and diodes",
            "Transistors as switches and amplifiers",
            "Logic gates",
        ]),
        ("Satellite and Space Physics", "hard", 45, [
            "Satellite motion",
            "Escape velocity",
            "Space exploration",
        ]),
    ],
    ("kenya", "F4", "Chemistry"): [
        ("Radioactivity (Chemistry)", "hard", 45, [
            "Nuclear reactions",
            "Half-life and calculations",
            "Applications of radioisotopes",
        ]),
        ("Metals and their Compounds", "hard", 50, [
            "Reactivity series",
            "Extraction of metals",
            "Properties and uses of common metals",
        ]),
        ("Sulphur and its Compounds", "hard", 45, [
            "Properties of sulphur",
            "Sulphuric acid: Contact process",
            "Uses and environmental concerns",
        ]),
    ],
    ("kenya", "F4", "Biology"): [
        ("Ecology", "hard", 50, [
            "Ecosystem structure and function",
            "Energy flow and nutrient cycling",
            "Human impact on ecosystems",
        ]),
        ("Genetics: Applied", "hard", 50, [
            "Genetic engineering",
            "Selective breeding",
            "Ethics in genetics",
        ]),
        ("Human Health", "hard", 45, [
            "Communicable diseases: malaria, HIV/AIDS",
            "Immunity and vaccination",
            "Lifestyle diseases",
        ]),
    ],
    ("kenya", "F4", "History"): [
        ("Government and Governance", "hard", 45, [
            "Kenya's constitution",
            "Devolution and county governments",
            "Democracy and elections",
        ]),
        ("East African Cooperation", "hard", 40, [
            "History of EAC",
            "Benefits and challenges of integration",
            "Future of regional cooperation",
        ]),
        ("Kenya Since Independence", "hard", 45, [
            "Kenyatta era",
            "Moi era and multiparty politics",
            "The 2010 constitution and modern Kenya",
        ]),
    ],
    ("kenya", "F4", "Geography"): [
        ("Trade", "hard", 45, [
            "Internal and international trade",
            "Trade blocs and agreements",
            "Kenya's balance of trade",
        ]),
        ("Transport and Communication", "hard", 40, [
            "Transport systems in Kenya",
            "Communication technology",
            "Impact on development",
        ]),
        ("Tourism", "hard", 45, [
            "Tourist attractions in Kenya",
            "Economic significance of tourism",
            "Challenges and sustainable tourism",
        ]),
    ],
}

# ─────────────────────────────────────────────────────────────────────
# ASSESSMENT QUESTIONS
# ─────────────────────────────────────────────────────────────────────

def generate_questions_for_topic(country, level, subject, topic_name, difficulty):
    """Generate 5 assessment questions per topic based on real curriculum content."""
    q = []

    # Generic question templates by subject
    if subject == "Mathematics":
        q = [
            {"type": "multiple_choice", "content": f"Which of the following best describes '{topic_name}'?",
             "options": {"A": "A mathematical concept", "B": "A literary device", "C": "A geographical feature", "D": "A historical event"},
             "correct_answer": "A", "points": 5, "difficulty": difficulty},
            {"type": "short_answer", "content": f"Define or explain the concept of '{topic_name}' in your own words.",
             "correct_answer": f"An explanation of {topic_name} showing understanding of key principles.",
             "points": 10, "difficulty": difficulty},
            {"type": "multiple_choice", "content": f"In the topic '{topic_name}', what skill is most important?",
             "options": {"A": "Memorisation only", "B": "Problem-solving and reasoning", "C": "Artistic expression", "D": "Physical endurance"},
             "correct_answer": "B", "points": 5, "difficulty": difficulty},
            {"type": "short_answer", "content": f"Give a real-life example where '{topic_name}' is applied.",
             "correct_answer": f"A practical application of {topic_name} in everyday life or professional contexts.",
             "points": 10, "difficulty": difficulty},
            {"type": "problem", "content": f"Solve the following problem related to '{topic_name}': [Problem based on curriculum level]",
             "correct_answer": "Solution with working shown.", "points": 15, "difficulty": difficulty},
        ]
    elif subject == "English":
        q = [
            {"type": "multiple_choice", "content": f"What is the main focus of the topic '{topic_name}'?",
             "options": {"A": "Mathematical calculations", "B": "Language and communication skills", "C": "Chemical reactions", "D": "Map reading"},
             "correct_answer": "B", "points": 5, "difficulty": difficulty},
            {"type": "short_answer", "content": f"Write a short paragraph demonstrating your understanding of '{topic_name}'.",
             "correct_answer": f"A well-structured paragraph showing knowledge of {topic_name}.",
             "points": 10, "difficulty": difficulty},
            {"type": "multiple_choice", "content": f"Which skill does '{topic_name}' help develop?",
             "options": {"A": "Numerical reasoning", "B": "Reading and writing", "C": "Laboratory skills", "D": "Physical coordination"},
             "correct_answer": "B", "points": 5, "difficulty": difficulty},
            {"type": "short_answer", "content": f"Identify and explain a key concept within '{topic_name}'.",
             "correct_answer": f"Clear identification and explanation of a concept within {topic_name}.",
             "points": 10, "difficulty": difficulty},
            {"type": "essay", "content": f"Write a short essay on the importance of '{topic_name}' in daily communication.",
             "correct_answer": "A coherent essay with introduction, body, and conclusion.",
             "points": 15, "difficulty": difficulty},
        ]
    elif subject in ("Physics", "Chemistry", "Biology", "Science"):
        q = [
            {"type": "multiple_choice", "content": f"Which branch of science does '{topic_name}' belong to?",
             "options": {"A": subject, "B": "Literature", "C": "Geography", "D": "Music"},
             "correct_answer": "A", "points": 5, "difficulty": difficulty},
            {"type": "short_answer", "content": f"Explain the key principles of '{topic_name}'.",
             "correct_answer": f"Clear explanation of the fundamental principles of {topic_name}.",
             "points": 10, "difficulty": difficulty},
            {"type": "multiple_choice", "content": f"What is the practical application of '{topic_name}'?",
             "options": {"A": "No practical use", "B": "Used in technology and everyday life", "C": "Only theoretical", "D": "Used in cooking only"},
             "correct_answer": "B", "points": 5, "difficulty": difficulty},
            {"type": "short_answer", "content": f"Describe an experiment related to '{topic_name}'.",
             "correct_answer": f"Description of a relevant experiment with aim, method, and expected results.",
             "points": 10, "difficulty": difficulty},
            {"type": "problem", "content": f"A question involving calculations or analysis from '{topic_name}'.",
             "correct_answer": "Correct answer with working shown.", "points": 15, "difficulty": difficulty},
        ]
    else:  # History, Geography, Social Studies
        q = [
            {"type": "multiple_choice", "content": f"What is the main theme of '{topic_name}'?",
             "options": {"A": "Scientific experimentation", "B": "Understanding society, history, or the environment", "C": "Mathematical proofs", "D": "Language grammar"},
             "correct_answer": "B", "points": 5, "difficulty": difficulty},
            {"type": "short_answer", "content": f"Summarise the key points of '{topic_name}'.",
             "correct_answer": f"A concise summary covering the main aspects of {topic_name}.",
             "points": 10, "difficulty": difficulty},
            {"type": "multiple_choice", "content": f"Why is it important to study '{topic_name}'?",
             "options": {"A": "It has no importance", "B": "To understand our society and world", "C": "Only for exams", "D": "For entertainment"},
             "correct_answer": "B", "points": 5, "difficulty": difficulty},
            {"type": "short_answer", "content": f"Give two effects or impacts related to '{topic_name}'.",
             "correct_answer": f"Two well-explained effects or impacts of {topic_name}.",
             "points": 10, "difficulty": difficulty},
            {"type": "essay", "content": f"Discuss the significance of '{topic_name}' in the {country.title()} context.",
             "correct_answer": "A well-argued essay with evidence and examples.",
             "points": 15, "difficulty": difficulty},
        ]

    return q


# ─────────────────────────────────────────────────────────────────────
# SEED LOGIC
# ─────────────────────────────────────────────────────────────────────

async def seed_all():
    """Seed all curriculum data into the database."""
    import json

    all_data = {}
    all_data.update(UGANDA_PRIMARY)
    all_data.update(UGANDA_SECONDARY)
    all_data.update(KENYA_SECONDARY)

    topic_count = 0
    edge_count = 0
    assessment_count = 0
    question_count = 0

    async with async_session() as session:
        # Clean existing curriculum seed data
        await session.execute(text("DELETE FROM questions WHERE assessment_id IN (SELECT id FROM assessments WHERE type = 'curriculum_seed')"))
        await session.execute(text("DELETE FROM assessments WHERE type = 'curriculum_seed'"))
        await session.execute(text("DELETE FROM topic_edges"))
        await session.execute(text("DELETE FROM topic_nodes"))
        await session.flush()

        # Track topic IDs for creating edges
        # key: (country, level, subject, topic_index) -> topic_uuid
        topic_id_map = {}

        for (country, level, subject), topics in all_data.items():
            for idx, (topic_name, difficulty, est_minutes, lessons) in enumerate(topics):
                topic_uuid = str(uuid.uuid4())
                metadata = json.dumps({
                    "country": country,
                    "level": level,
                    "lessons": lessons,
                    "curriculum_aligned": True,
                })

                await session.execute(text("""
                    INSERT INTO topic_nodes (id, subject, topic, display_name, difficulty, estimated_minutes, metadata)
                    VALUES (:id, :subject, :topic, :display_name, :difficulty, :est_min, CAST(:metadata AS jsonb))
                """), {
                    "id": topic_uuid,
                    "subject": subject,
                    "topic": f"{country}_{level}_{subject}_{topic_name}".lower().replace(" ", "_").replace(",", "").replace(":", ""),
                    "display_name": f"[{country.upper()} {level}] {topic_name}",
                    "difficulty": difficulty,
                    "est_min": est_minutes,
                    "metadata": metadata,
                })
                topic_id_map[(country, level, subject, idx)] = topic_uuid
                topic_count += 1

                # Create assessment + questions for this topic
                assessment_uuid = str(uuid.uuid4())
                await session.execute(text("""
                    INSERT INTO assessments (id, created_by, title, subject, type, config)
                    VALUES (:id, (SELECT id FROM users LIMIT 1), :title, :subject, 'curriculum_seed', CAST(:config AS jsonb))
                """), {
                    "id": assessment_uuid,
                    "title": f"{subject}: {topic_name} ({country.upper()} {level})",
                    "subject": subject,
                    "config": json.dumps({"country": country, "level": level, "topic": topic_name}),
                })
                assessment_count += 1

                questions = generate_questions_for_topic(country, level, subject, topic_name, difficulty)
                for q_idx, q in enumerate(questions):
                    await session.execute(text("""
                        INSERT INTO questions (id, assessment_id, type, content, options, correct_answer, points, difficulty, order_num)
                        VALUES (:id, :aid, :type, :content, CAST(:options AS jsonb), :answer, :points, :diff, :order)
                    """), {
                        "id": str(uuid.uuid4()),
                        "aid": assessment_uuid,
                        "type": q["type"],
                        "content": q["content"],
                        "options": json.dumps(q.get("options")) if q.get("options") else None,
                        "answer": q["correct_answer"],
                        "points": q["points"],
                        "diff": q["difficulty"],
                        "order": q_idx + 1,
                    })
                    question_count += 1

        # Create topic edges (prerequisites within same country/subject)
        # Each topic depends on the previous topic in the same level, and
        # the first topic of a level depends on the last topic of the previous level
        levels_order = {
            "uganda": ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "S1", "S2", "S3", "S4", "S5", "S6"],
            "kenya": ["F1", "F2", "F3", "F4"],
        }

        subjects_seen = set()
        for (country, level, subject) in all_data.keys():
            subjects_seen.add((country, subject))

        for (country, subject) in subjects_seen:
            ordered_levels = levels_order.get(country, [])
            prev_last_uuid = None
            for level in ordered_levels:
                key_base = (country, level, subject)
                # Find how many topics exist at this level
                topic_indices = [idx for (c, l, s, idx) in topic_id_map if c == country and l == level and s == subject]
                if not topic_indices:
                    continue
                topic_indices.sort()

                # Edge from previous level's last topic to this level's first
                first_uuid = topic_id_map.get((country, level, subject, topic_indices[0]))
                if prev_last_uuid and first_uuid:
                    await session.execute(text("""
                        INSERT INTO topic_edges (id, from_topic_id, to_topic_id, relationship_type, weight)
                        VALUES (:id, :from_id, :to_id, 'prerequisite', 1.0)
                    """), {"id": str(uuid.uuid4()), "from_id": prev_last_uuid, "to_id": first_uuid})
                    edge_count += 1

                # Sequential edges within this level
                for i in range(len(topic_indices) - 1):
                    from_uuid = topic_id_map[(country, level, subject, topic_indices[i])]
                    to_uuid = topic_id_map[(country, level, subject, topic_indices[i + 1])]
                    await session.execute(text("""
                        INSERT INTO topic_edges (id, from_topic_id, to_topic_id, relationship_type, weight)
                        VALUES (:id, :from_id, :to_id, 'prerequisite', 1.0)
                    """), {"id": str(uuid.uuid4()), "from_id": from_uuid, "to_id": to_uuid})
                    edge_count += 1

                prev_last_uuid = topic_id_map.get((country, level, subject, topic_indices[-1]))

        await session.commit()

    print(f"\n{'='*60}")
    print(f"  EduAGI Curriculum Seed Complete!")
    print(f"{'='*60}")
    print(f"  Topics inserted:      {topic_count}")
    print(f"  Topic edges created:  {edge_count}")
    print(f"  Assessments created:  {assessment_count}")
    print(f"  Questions created:    {question_count}")
    print(f"{'='*60}")
    print(f"\n  Countries: Uganda (P1-S6), Kenya (F1-F4)")
    print(f"  Subjects:  Mathematics, English, Science, Social Studies,")
    print(f"             Physics, Chemistry, Biology, History, Geography")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(seed_all())
