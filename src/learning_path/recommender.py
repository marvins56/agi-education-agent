"""Priority-based learning path recommendation engine."""

from src.learning_path.graph import PrerequisiteGraph


class PathRecommender:
    """Recommends a prioritised study path based on goals and prerequisites."""

    def __init__(self, graph: PrerequisiteGraph):
        self.graph = graph

    def recommend(
        self,
        student_mastery: dict[str, float],
        goals: list[dict],
        max_items: int = 10,
    ) -> list[dict]:
        """Generate a prioritised list of topics to study.

        Each goal dict should have: 'topic_id', 'target_mastery' (float),
        and optionally 'deadline_days' (int, days until deadline).

        Priority scoring:
        1. prerequisite_depth — foundations first (higher depth = higher priority)
        2. impact_score — how many goals this topic unlocks
        3. estimated_time — shorter topics slightly preferred
        4. deadline proximity — urgent goals weighted higher
        """
        # Collect all goal topic_ids
        goal_topic_ids = [g["topic_id"] for g in goals]

        # Find prerequisite gaps across all goals
        all_gaps = self.graph.find_gaps(
            student_mastery=student_mastery,
            target_topics=goal_topic_ids,
            threshold=50.0,
        )

        # Also include goal topics themselves if mastery is below target
        for goal in goals:
            tid = goal["topic_id"]
            current = student_mastery.get(tid, 0.0)
            target = goal.get("target_mastery", 80.0)
            if current < target and not any(g["topic_id"] == tid for g in all_gaps):
                node = self.graph.nodes.get(tid, {})
                all_gaps.append({
                    "topic_id": tid,
                    "topic_name": node.get("topic_name", tid),
                    "subject": node.get("subject", ""),
                    "current_mastery": current,
                    "prerequisite_depth": 0,
                })

        # Build deadline map
        deadline_map: dict[str, int] = {}
        for goal in goals:
            if "deadline_days" in goal:
                deadline_map[goal["topic_id"]] = goal["deadline_days"]

        # Calculate impact: how many goals each gap topic is a prerequisite for
        impact_map: dict[str, int] = {}
        for gap in all_gaps:
            tid = gap["topic_id"]
            impact = 0
            for goal_tid in goal_topic_ids:
                all_prereqs = self.graph.get_all_prerequisites(goal_tid)
                if tid in all_prereqs or tid == goal_tid:
                    impact += 1
            impact_map[tid] = impact

        # Score and rank
        scored: list[dict] = []
        for gap in all_gaps:
            tid = gap["topic_id"]
            node = self.graph.nodes.get(tid, {})
            est_minutes = node.get("estimated_minutes", 30)

            depth_score = gap["prerequisite_depth"] * 10
            impact_score = impact_map.get(tid, 0) * 15
            time_score = max(0, 5 - (est_minutes / 30))  # shorter = slightly higher

            # Deadline urgency
            deadline_score = 0.0
            for goal_tid, deadline_days in deadline_map.items():
                all_prereqs = self.graph.get_all_prerequisites(goal_tid)
                if tid in all_prereqs or tid == goal_tid:
                    deadline_score = max(deadline_score, 100 / max(deadline_days, 1))

            priority = depth_score + impact_score + time_score + deadline_score

            reason_parts = []
            if gap["prerequisite_depth"] > 0:
                reason_parts.append("foundational prerequisite")
            if impact_map.get(tid, 0) > 1:
                reason_parts.append(f"unlocks {impact_map[tid]} goals")
            if deadline_score > 0:
                reason_parts.append("deadline approaching")
            if not reason_parts:
                reason_parts.append("goal topic")

            scored.append({
                "topic_id": tid,
                "topic_name": gap["topic_name"],
                "subject": gap["subject"],
                "current_mastery": gap["current_mastery"],
                "target_mastery": 80.0,
                "priority_score": round(priority, 2),
                "estimated_minutes": est_minutes,
                "reason": "; ".join(reason_parts),
            })

        scored.sort(key=lambda x: -x["priority_score"])
        return scored[:max_items]
