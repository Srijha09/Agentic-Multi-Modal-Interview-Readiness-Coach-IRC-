"""
Compiled LangGraph workflows for the Interview Readiness Coach.
"""
from langgraph.graph import END, START, StateGraph

from app.graph.state import CoachState
from app.graph.nodes import (
    adaptive_planner_node,
    daily_coach_node,
    evaluation_node,
    gap_analysis_node,
    mastery_update_node,
    planner_node,
    practice_generator_node,
    route_after_eval,
    route_after_gap,
    validate_intake_node,
)


def _build_onboarding_graph():
    """Resume + JD upload → gap analysis → optional plan generation."""
    graph = StateGraph(CoachState)
    graph.add_node("validate_intake", validate_intake_node)
    graph.add_node("analyze_gaps", gap_analysis_node)
    graph.add_node("generate_plan", planner_node)

    graph.add_edge(START, "validate_intake")
    graph.add_edge("validate_intake", "analyze_gaps")
    graph.add_conditional_edges(
        "analyze_gaps",
        route_after_gap,
        {"planner": "generate_plan", "end": END},
    )
    graph.add_edge("generate_plan", END)
    return graph.compile()


def _build_gap_analysis_graph():
    """Gap analysis only (with intake validation)."""
    graph = StateGraph(CoachState)
    graph.add_node("validate_intake", validate_intake_node)
    graph.add_node("analyze_gaps", gap_analysis_node)

    graph.add_edge(START, "validate_intake")
    graph.add_edge("validate_intake", "analyze_gaps")
    graph.add_edge("analyze_gaps", END)
    return graph.compile()


def _build_plan_graph():
    """Study plan generation from existing gaps."""
    graph = StateGraph(CoachState)
    graph.add_node("generate_plan", planner_node)

    graph.add_edge(START, "generate_plan")
    graph.add_edge("generate_plan", END)
    return graph.compile()


def _build_daily_coach_graph():
    """Daily briefing workflow."""
    graph = StateGraph(CoachState)
    graph.add_node("generate_briefing", daily_coach_node)

    graph.add_edge(START, "generate_briefing")
    graph.add_edge("generate_briefing", END)
    return graph.compile()


def _build_practice_graph():
    """Practice item generation workflow."""
    graph = StateGraph(CoachState)
    graph.add_node("generate_practice", practice_generator_node)

    graph.add_edge(START, "generate_practice")
    graph.add_edge("generate_practice", END)
    return graph.compile()


def _build_learning_loop_graph():
    """Evaluate attempt → update mastery → optional adaptive replanning."""
    graph = StateGraph(CoachState)
    graph.add_node("run_evaluation", evaluation_node)
    graph.add_node("update_mastery", mastery_update_node)
    graph.add_node("run_adaptation", adaptive_planner_node)

    graph.add_edge(START, "run_evaluation")
    graph.add_edge("run_evaluation", "update_mastery")
    graph.add_conditional_edges(
        "update_mastery",
        route_after_eval,
        {"adapt": "run_adaptation", "end": END},
    )
    graph.add_edge("run_adaptation", END)
    return graph.compile()


def _build_adaptive_graph():
    """Standalone adaptive planning workflow."""
    graph = StateGraph(CoachState)
    graph.add_node("run_adaptation", adaptive_planner_node)

    graph.add_edge(START, "run_adaptation")
    graph.add_edge("run_adaptation", END)
    return graph.compile()


# Compiled graph singletons
onboarding_graph = _build_onboarding_graph()
gap_analysis_graph = _build_gap_analysis_graph()
plan_graph = _build_plan_graph()
daily_coach_graph = _build_daily_coach_graph()
practice_graph = _build_practice_graph()
learning_loop_graph = _build_learning_loop_graph()
adaptive_graph = _build_adaptive_graph()
