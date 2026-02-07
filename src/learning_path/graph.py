"""Prerequisite graph for topic dependencies."""

from collections import deque

# Supported relationship types between topics
REQUIRES = "requires"        # Hard prerequisite — must master before advancing
RECOMMENDS = "recommends"    # Soft prerequisite — helpful but not required
COMPLEMENTS = "complements"  # Related topic — useful for broader understanding


class PrerequisiteGraph:
    """Directed acyclic graph of topic prerequisites."""

    def __init__(self):
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []
        # Adjacency: topic_id -> list of (topic_id, relationship) it requires
        self._prereqs: dict[str, list[str]] = {}
        # Reverse adjacency: topic_id -> list of topic_ids that depend on it
        self._dependents: dict[str, list[str]] = {}
        # Edge metadata: (from, to) -> {relationship, weight}
        self._edge_meta: dict[tuple[str, str], dict] = {}

    def add_topic(
        self,
        topic_id: str,
        subject: str,
        topic_name: str,
        difficulty: str = "medium",
        estimated_minutes: int = 30,
    ) -> None:
        """Add a topic node to the graph."""
        self.nodes[topic_id] = {
            "topic_id": topic_id,
            "subject": subject,
            "topic_name": topic_name,
            "difficulty": difficulty,
            "estimated_minutes": estimated_minutes,
        }
        self._prereqs.setdefault(topic_id, [])
        self._dependents.setdefault(topic_id, [])

    def add_prerequisite(
        self,
        from_topic_id: str,
        to_topic_id: str,
        relationship: str = REQUIRES,
        weight: float = 1.0,
    ) -> None:
        """Add a prerequisite edge: to_topic_id requires from_topic_id.

        Supported relationship types:
        - "requires": hard prerequisite (must master first)
        - "recommends": soft prerequisite (helpful but optional)
        - "complements": related topic (broadens understanding)
        """
        self.edges.append({
            "from_topic_id": from_topic_id,
            "to_topic_id": to_topic_id,
            "relationship": relationship,
            "weight": weight,
        })
        self._prereqs.setdefault(to_topic_id, []).append(from_topic_id)
        self._dependents.setdefault(from_topic_id, []).append(to_topic_id)
        self._edge_meta[(from_topic_id, to_topic_id)] = {
            "relationship": relationship,
            "weight": weight,
        }

    def get_edge_relationship(self, from_id: str, to_id: str) -> str:
        """Return the relationship type for an edge, defaulting to 'requires'."""
        meta = self._edge_meta.get((from_id, to_id))
        return meta["relationship"] if meta else REQUIRES

    def get_prerequisites(self, topic_id: str) -> list[str]:
        """Return direct prerequisites for a topic."""
        return list(self._prereqs.get(topic_id, []))

    def get_all_prerequisites(self, topic_id: str) -> list[str]:
        """Return all transitive prerequisites using DFS."""
        visited: set[str] = set()
        result: list[str] = []

        def dfs(tid: str) -> None:
            for prereq in self._prereqs.get(tid, []):
                if prereq not in visited:
                    visited.add(prereq)
                    dfs(prereq)
                    result.append(prereq)

        dfs(topic_id)
        return result

    def topological_sort(self) -> list[str]:
        """Return a valid learning order (Kahn's algorithm)."""
        in_degree: dict[str, int] = {tid: 0 for tid in self.nodes}
        for tid, prereqs in self._prereqs.items():
            if tid in in_degree:
                in_degree[tid] = len(prereqs)

        queue = deque(tid for tid, deg in in_degree.items() if deg == 0)
        order: list[str] = []

        while queue:
            current = queue.popleft()
            order.append(current)

            for dependent in self._dependents.get(current, []):
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)

        return order

    def find_gaps(
        self,
        student_mastery: dict[str, float],
        target_topics: list[str],
        threshold: float = 50.0,
        include_soft: bool = False,
    ) -> list[dict]:
        """Find topics where mastery < threshold that are prerequisites of targets.

        By default only follows "requires" edges. Set include_soft=True to also
        include "recommends" and "complements" edges.

        Returns list sorted by prerequisite depth (deepest foundations first).
        """
        gaps: dict[str, int] = {}  # topic_id -> depth

        def find_depth(topic_id: str, depth: int) -> None:
            for prereq in self._prereqs.get(topic_id, []):
                rel = self.get_edge_relationship(prereq, topic_id)
                if not include_soft and rel != REQUIRES:
                    continue
                mastery = student_mastery.get(prereq, 0.0)
                if mastery < threshold:
                    if prereq not in gaps or depth + 1 > gaps[prereq]:
                        gaps[prereq] = depth + 1
                    find_depth(prereq, depth + 1)

        for target in target_topics:
            find_depth(target, 0)

        result = []
        for topic_id, depth in sorted(gaps.items(), key=lambda x: -x[1]):
            node = self.nodes.get(topic_id, {})
            result.append({
                "topic_id": topic_id,
                "topic_name": node.get("topic_name", topic_id),
                "subject": node.get("subject", ""),
                "current_mastery": student_mastery.get(topic_id, 0.0),
                "prerequisite_depth": depth,
            })

        return result

    async def load_from_db(self, db_session) -> None:
        """Load graph from database topic_nodes and topic_edges tables."""
        from sqlalchemy import select
        from src.models.learning_path import TopicEdge, TopicNode

        result = await db_session.execute(select(TopicNode))
        for node in result.scalars().all():
            self.add_topic(
                topic_id=str(node.id),
                subject=node.subject,
                topic_name=node.display_name or node.topic,
                difficulty=node.difficulty,
                estimated_minutes=node.estimated_minutes,
            )

        result = await db_session.execute(select(TopicEdge))
        for edge in result.scalars().all():
            self.add_prerequisite(
                from_topic_id=str(edge.from_topic_id),
                to_topic_id=str(edge.to_topic_id),
                relationship=edge.relationship_type,
                weight=edge.weight,
            )

    async def save_to_db(self, db_session) -> None:
        """Save graph to database topic_nodes and topic_edges tables."""
        import uuid
        from src.models.learning_path import TopicEdge, TopicNode

        for topic_id, data in self.nodes.items():
            node = TopicNode(
                id=uuid.UUID(topic_id) if len(topic_id) == 36 else None,
                subject=data["subject"],
                topic=data["topic_name"],
                display_name=data["topic_name"],
                difficulty=data["difficulty"],
                estimated_minutes=data["estimated_minutes"],
            )
            db_session.add(node)

        await db_session.flush()

        for edge_data in self.edges:
            edge = TopicEdge(
                from_topic_id=edge_data["from_topic_id"],
                to_topic_id=edge_data["to_topic_id"],
                relationship_type=edge_data["relationship"],
                weight=edge_data["weight"],
            )
            db_session.add(edge)
