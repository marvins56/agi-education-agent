"""Tests for learning path graph, recommender, and spaced repetition."""

from datetime import date, timedelta

from src.learning_path.graph import COMPLEMENTS, RECOMMENDS, REQUIRES, PrerequisiteGraph
from src.learning_path.recommender import PathRecommender
from src.learning_path.spaced_repetition import SpacedRepetitionScheduler


def _build_math_graph() -> PrerequisiteGraph:
    """Build a sample math prerequisite graph for testing.

    Structure:
        arithmetic -> algebra -> calculus
        arithmetic -> geometry
        algebra -> statistics
    """
    graph = PrerequisiteGraph()
    graph.add_topic("arithmetic", "math", "Arithmetic", "easy", 20)
    graph.add_topic("algebra", "math", "Algebra", "medium", 30)
    graph.add_topic("geometry", "math", "Geometry", "medium", 25)
    graph.add_topic("calculus", "math", "Calculus", "hard", 45)
    graph.add_topic("statistics", "math", "Statistics", "medium", 35)

    # algebra requires arithmetic
    graph.add_prerequisite("arithmetic", "algebra")
    # calculus requires algebra
    graph.add_prerequisite("algebra", "calculus")
    # geometry requires arithmetic
    graph.add_prerequisite("arithmetic", "geometry")
    # statistics requires algebra
    graph.add_prerequisite("algebra", "statistics")

    return graph


class TestPrerequisiteGraph:
    def test_prerequisite_graph_add_topics(self):
        graph = PrerequisiteGraph()
        graph.add_topic("t1", "math", "Topic 1")
        graph.add_topic("t2", "math", "Topic 2")
        assert len(graph.nodes) == 2
        assert "t1" in graph.nodes
        assert "t2" in graph.nodes
        assert graph.nodes["t1"]["topic_name"] == "Topic 1"

    def test_get_prerequisites(self):
        graph = _build_math_graph()
        prereqs = graph.get_prerequisites("algebra")
        assert prereqs == ["arithmetic"]

    def test_get_prerequisites_none(self):
        graph = _build_math_graph()
        prereqs = graph.get_prerequisites("arithmetic")
        assert prereqs == []

    def test_get_all_prerequisites(self):
        graph = _build_math_graph()
        all_prereqs = graph.get_all_prerequisites("calculus")
        assert set(all_prereqs) == {"algebra", "arithmetic"}

    def test_topological_sort(self):
        graph = _build_math_graph()
        order = graph.topological_sort()
        assert len(order) == 5

        # arithmetic must come before algebra
        assert order.index("arithmetic") < order.index("algebra")
        # algebra must come before calculus
        assert order.index("algebra") < order.index("calculus")
        # algebra must come before statistics
        assert order.index("algebra") < order.index("statistics")
        # arithmetic must come before geometry
        assert order.index("arithmetic") < order.index("geometry")

    def test_find_gaps_below_threshold(self):
        graph = _build_math_graph()
        student_mastery = {
            "arithmetic": 80.0,
            "algebra": 30.0,  # below 50 threshold
            "geometry": 60.0,
            "calculus": 0.0,
            "statistics": 0.0,
        }
        gaps = graph.find_gaps(
            student_mastery=student_mastery,
            target_topics=["calculus"],
            threshold=50.0,
        )
        # algebra is below threshold and is a prerequisite of calculus
        gap_ids = [g["topic_id"] for g in gaps]
        assert "algebra" in gap_ids
        # arithmetic is above threshold, should not appear
        assert "arithmetic" not in gap_ids

    def test_relationship_types(self):
        """Test that different edge types are stored correctly."""
        graph = PrerequisiteGraph()
        graph.add_topic("a", "math", "Topic A")
        graph.add_topic("b", "math", "Topic B")
        graph.add_topic("c", "math", "Topic C")
        graph.add_prerequisite("a", "b", relationship=REQUIRES)
        graph.add_prerequisite("c", "b", relationship=RECOMMENDS)

        assert graph.get_edge_relationship("a", "b") == REQUIRES
        assert graph.get_edge_relationship("c", "b") == RECOMMENDS

    def test_find_gaps_ignores_soft_edges_by_default(self):
        """find_gaps should only follow 'requires' edges by default."""
        graph = PrerequisiteGraph()
        graph.add_topic("basics", "cs", "Basics", "easy", 20)
        graph.add_topic("advanced", "cs", "Advanced", "hard", 40)
        graph.add_topic("optional", "cs", "Optional", "medium", 25)

        graph.add_prerequisite("basics", "advanced", relationship=REQUIRES)
        graph.add_prerequisite("optional", "advanced", relationship=RECOMMENDS)

        student_mastery = {"basics": 10.0, "optional": 10.0, "advanced": 0.0}
        gaps = graph.find_gaps(student_mastery, ["advanced"], threshold=50.0)
        gap_ids = [g["topic_id"] for g in gaps]
        assert "basics" in gap_ids
        assert "optional" not in gap_ids  # soft edge excluded

    def test_find_gaps_includes_soft_edges_when_requested(self):
        """find_gaps with include_soft=True should include recommends edges."""
        graph = PrerequisiteGraph()
        graph.add_topic("basics", "cs", "Basics", "easy", 20)
        graph.add_topic("advanced", "cs", "Advanced", "hard", 40)
        graph.add_topic("optional", "cs", "Optional", "medium", 25)

        graph.add_prerequisite("basics", "advanced", relationship=REQUIRES)
        graph.add_prerequisite("optional", "advanced", relationship=RECOMMENDS)

        student_mastery = {"basics": 10.0, "optional": 10.0, "advanced": 0.0}
        gaps = graph.find_gaps(student_mastery, ["advanced"], threshold=50.0, include_soft=True)
        gap_ids = [g["topic_id"] for g in gaps]
        assert "basics" in gap_ids
        assert "optional" in gap_ids

    def test_complements_relationship(self):
        """Complements edges should be stored and retrievable."""
        graph = PrerequisiteGraph()
        graph.add_topic("a", "math", "A")
        graph.add_topic("b", "math", "B")
        graph.add_prerequisite("a", "b", relationship=COMPLEMENTS)
        assert graph.get_edge_relationship("a", "b") == COMPLEMENTS


class TestPathRecommender:
    def test_path_recommendation_foundations_first(self):
        graph = _build_math_graph()
        student_mastery = {
            "arithmetic": 20.0,
            "algebra": 10.0,
            "calculus": 0.0,
        }
        recommender = PathRecommender(graph)
        recs = recommender.recommend(
            student_mastery=student_mastery,
            goals=[{"topic_id": "calculus", "target_mastery": 80.0}],
        )
        assert len(recs) > 0
        # Arithmetic (deeper prerequisite) should be ranked higher than algebra
        topic_ids = [r["topic_id"] for r in recs]
        assert "arithmetic" in topic_ids
        assert "algebra" in topic_ids
        if "arithmetic" in topic_ids and "algebra" in topic_ids:
            assert topic_ids.index("arithmetic") < topic_ids.index("algebra")

    def test_path_recommendation_includes_goal_topic(self):
        graph = _build_math_graph()
        student_mastery = {
            "arithmetic": 90.0,
            "algebra": 90.0,
            "calculus": 20.0,
        }
        recommender = PathRecommender(graph)
        recs = recommender.recommend(
            student_mastery=student_mastery,
            goals=[{"topic_id": "calculus", "target_mastery": 80.0}],
        )
        topic_ids = [r["topic_id"] for r in recs]
        assert "calculus" in topic_ids

    def test_path_recommendation_empty_goals(self):
        graph = _build_math_graph()
        recommender = PathRecommender(graph)
        recs = recommender.recommend(
            student_mastery={},
            goals=[],
        )
        assert recs == []


class TestSpacedRepetition:
    def test_spaced_repetition_quality_high(self):
        """High quality (5) should increase interval."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=5,
            repetition_count=2,
            easiness_factor=2.5,
            current_interval=6,
        )
        # With EF=2.5 and quality=5, EF adjusts up: EF' = 2.5 + 0.1 = 2.6
        assert result["next_interval_days"] > 6
        assert result["easiness_factor"] >= 2.5
        assert result["next_review_date"] > date.today()

    def test_spaced_repetition_quality_low(self):
        """Low quality (1) should reset interval to 1."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=1,
            repetition_count=5,
            easiness_factor=2.5,
            current_interval=30,
        )
        assert result["next_interval_days"] == 1
        assert result["next_review_date"] == date.today() + timedelta(days=1)

    def test_spaced_repetition_first_review(self):
        """First successful review should set interval to 1."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=4,
            repetition_count=0,
            easiness_factor=2.5,
            current_interval=0,
        )
        assert result["next_interval_days"] == 1

    def test_spaced_repetition_second_review(self):
        """Second successful review should set interval to 6."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=4,
            repetition_count=1,
            easiness_factor=2.5,
            current_interval=1,
        )
        assert result["next_interval_days"] == 6

    def test_spaced_repetition_ef_minimum(self):
        """Easiness factor should never go below 1.3."""
        result = SpacedRepetitionScheduler.calculate_next_review(
            quality=0,
            repetition_count=0,
            easiness_factor=1.3,
            current_interval=1,
        )
        assert result["easiness_factor"] >= 1.3

    def test_reviews_due_filtering(self):
        """Only schedules with next_review_date <= as_of should be returned."""
        today = date.today()
        schedules = [
            {"topic_id": "t1", "next_review_date": today - timedelta(days=1)},
            {"topic_id": "t2", "next_review_date": today},
            {"topic_id": "t3", "next_review_date": today + timedelta(days=1)},
            {"topic_id": "t4", "next_review_date": today + timedelta(days=5)},
        ]
        due = SpacedRepetitionScheduler.get_reviews_due(schedules, as_of=today)
        due_ids = [s["topic_id"] for s in due]
        assert "t1" in due_ids
        assert "t2" in due_ids
        assert "t3" not in due_ids
        assert "t4" not in due_ids

    def test_reviews_due_empty(self):
        due = SpacedRepetitionScheduler.get_reviews_due([], as_of=date.today())
        assert due == []
