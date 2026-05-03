import json
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4
 
import requests
import streamlit as st
 
from config import settings
from agents.coordinator import TravelPlannerCoordinator
from llm.errors import LLMError
 
 
APP_NAME = "WayMapper"
APP_TAGLINE = "Map your route. Own your journey."
APP_SUBTITLE = (
    "Describe your trip in one line — WayMapper maps out the destinations, budget, and itinerary you need, fast."
)
BACKEND_URL = settings.backend_url


logging.basicConfig(level=getattr(logging, settings.log_level, logging.INFO))
logger = logging.getLogger(__name__)
 
PROMPT_PRESETS = [
    {
        "label": "Weekend outing",
        "prompt": "plan an outing in delhi for next weekend",
    },
    {
        "label": "Budget check",
        "prompt": "what budget do i need for a 4 day goa trip for 2 people",
    },
    {
        "label": "Pilgrimage itinerary",
        "prompt": "plan my trip to vaisnodevi",
    },
    {
        "label": "Destination ideas",
        "prompt": "suggest hill stations near delhi for a weekend trip",
    },
    {
        "label": "Family trip",
        "prompt": "plan a 5 day family trip to jaipur and udaipur",
    },
    {
        "label": "Food-focused break",
        "prompt": "plan a short food trip in amritsar",
    },
]
 
FOCUS_PREFERENCE_MAP = {
    "Auto detect": None,
    "Itinerary first": "itinerary",
    "Budget first": "budget",
    "Destinations first": "destination",
    "Experiences first": "experiences",
    "Full trip plan": "full_trip",
}
 
 
def init_session_state() -> None:
    defaults = {
        "history": [],
        "draft_prompt": "",
        "last_result": None,
        "last_request": "",
        "last_focus": "full_trip",
        "view_preference": "Auto detect",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
 
 
FOCUS_KEYWORDS = {
    "itinerary": [
        "itinerary",
        "day by day",
        "day-by-day",
        "schedule",
        "plan each day",
        "daily plan",
    ],
    "budget": [
        "budget",
        "cheap",
        "affordable",
        "cost",
        "price",
        "under ",
        "save money",
        "expensive",
    ],
    "destination": [
        "destination",
        "destinations",
        "where should",
        "where can",
        "recommend",
        "suggest",
        "best place",
        "best places",
        "compare",
        "vs ",
    ],
    "experiences": [
        "things to do",
        "activities",
        "experience",
        "experiences",
        "food",
        "sightseeing",
        "what to do",
    ],
    "summary": [
        "summary",
        "overview",
        "quick",
        "concise",
        "short",
        "best option",
        "top option",
    ],
}
 
FOCUS_HINTS = {
    "itinerary": "Showing the day-by-day plan first because your request reads like a scheduling question.",
    "budget": "Showing cost and feasibility first because your request reads like a budget question.",
    "destination": "Showing destination comparison first because your request reads like a destination-choice question.",
    "experiences": "Showing activities first because your request reads like an experiences question.",
    "summary": "Showing a concise trip summary first because your request reads like an overview question.",
    "full_trip": "Showing the full trip map with the most important decision points first.",
}
 
SECTION_TITLES = {
    "destinations": "Mapped Destinations",
    "budget": "Budget Breakdown",
    "experiences": "Curated Experiences",
    "itinerary": "Trip Itinerary",
    "intent": "Trip Details",
}
 
SECTION_ORDER = {
    "itinerary": ["itinerary", "budget", "destinations", "experiences", "intent"],
    "budget": ["budget", "destinations", "itinerary", "experiences", "intent"],
    "destination": ["destinations", "budget", "experiences", "itinerary", "intent"],
    "experiences": ["experiences", "itinerary", "budget", "destinations", "intent"],
    "summary": ["destinations", "budget", "itinerary", "experiences", "intent"],
    "full_trip": ["destinations", "budget", "experiences", "itinerary", "intent"],
}
 
 
def inject_styles() -> None:
    st.markdown(
        """
        <style>
        html, body, [class*="css"]  {
            font-family: "Aptos", "Segoe UI", sans-serif;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(205, 230, 255, 0.72), transparent 28%),
                radial-gradient(circle at top right, rgba(242, 227, 204, 0.82), transparent 32%),
                linear-gradient(180deg, #f5f3ee 0%, #eaf0f5 100%);
        }
        h1, h2, h3, .stTabs [data-baseweb="tab"] {
            font-family: "Aptos Display", "Trebuchet MS", sans-serif;
        }
        .hero {
            padding: 1.6rem 1.8rem;
            border: 1px solid rgba(29, 62, 92, 0.12);
            border-radius: 24px;
            background:
                radial-gradient(circle at top right, rgba(255, 231, 186, 0.18), transparent 24%),
                linear-gradient(135deg, rgba(19, 52, 80, 0.97), rgba(49, 92, 110, 0.92));
            color: #f8fbff;
            box-shadow: 0 20px 40px rgba(19, 52, 80, 0.14);
            margin-bottom: 1.15rem;
        }
        .hero-badge {
            display: inline-block;
            padding: 0.28rem 0.62rem;
            border-radius: 999px;
            border: 1px solid rgba(248, 251, 255, 0.18);
            background: rgba(255, 255, 255, 0.10);
            color: rgba(248, 251, 255, 0.9);
            font-size: 0.78rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.8rem;
        }
        .hero h1 {
            margin: 0 0 0.4rem 0;
            font-size: 2.45rem;
            line-height: 1.1;
        }
        .hero p {
            margin: 0;
            max-width: 48rem;
            color: rgba(248, 251, 255, 0.88);
        }
        .panel {
            padding: 1.08rem 1.14rem;
            border-radius: 20px;
            border: 1px solid rgba(29, 62, 92, 0.10);
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 14px 30px rgba(19, 52, 80, 0.07);
            margin-bottom: 1rem;
        }
        .panel h3 {
            margin-top: 0;
            margin-bottom: 0.45rem;
            color: #193450;
        }
        .panel p {
            color: #4b6177;
            margin-bottom: 0;
        }
        .workspace-panel {
            padding: 1.1rem 1.15rem 0.6rem 1.15rem;
        }
        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.6rem;
        }
        .pill {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: #e8f0f7;
            color: #193450;
            font-size: 0.86rem;
            border: 1px solid rgba(25, 52, 80, 0.10);
        }
        .assumption-chip {
            display: inline-block;
            padding: 0.4rem 0.7rem;
            border-radius: 12px;
            background: #f6efe1;
            color: #5f4a23;
            border: 1px solid rgba(95, 74, 35, 0.10);
            margin: 0.15rem 0.3rem 0.15rem 0;
            font-size: 0.9rem;
        }
        .kpi-card {
            padding: 0.9rem 1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(29, 62, 92, 0.10);
            min-height: 108px;
        }
        .kpi-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #67829b;
            margin-bottom: 0.4rem;
        }
        .kpi-value {
            font-size: 1.35rem;
            font-weight: 700;
            color: #193450;
            line-height: 1.2;
        }
        .kpi-note {
            color: #4b6177;
            font-size: 0.92rem;
            margin-top: 0.35rem;
        }
        .timeline-card {
            padding: 0.95rem 1rem;
            border-radius: 16px;
            background: linear-gradient(180deg, #ffffff 0%, #f7fafc 100%);
            border-left: 4px solid #315c6e;
            border-top: 1px solid rgba(29, 62, 92, 0.08);
            border-right: 1px solid rgba(29, 62, 92, 0.08);
            border-bottom: 1px solid rgba(29, 62, 92, 0.08);
            margin-bottom: 0.8rem;
        }
        .timeline-slot {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #67829b;
            margin-bottom: 0.3rem;
        }
        .timeline-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #193450;
            margin-bottom: 0.35rem;
        }
        .timeline-note {
            color: #4b6177;
            margin: 0;
        }
        .sidebar-card {
            padding: 0.95rem 1rem;
            border-radius: 16px;
            background: linear-gradient(180deg, rgba(19, 52, 80, 0.98), rgba(49, 92, 110, 0.92));
            color: #f8fbff;
            margin-bottom: 1rem;
        }
        .sidebar-card h3 {
            margin: 0 0 0.35rem 0;
            color: #f8fbff;
        }
        .sidebar-card p {
            margin: 0;
            color: rgba(248, 251, 255, 0.82);
            font-size: 0.92rem;
        }
        div.stButton > button {
            border-radius: 14px;
            border: 1px solid rgba(29, 62, 92, 0.12);
            min-height: 2.8rem;
            font-weight: 600;
        }
        div[data-testid="stForm"] {
            border: 1px solid rgba(29, 62, 92, 0.10);
            border-radius: 22px;
            padding: 0.8rem 0.95rem 0.2rem 0.95rem;
            background: rgba(255, 255, 255, 0.82);
        }
        div[data-testid="stTextArea"] textarea {
            border-radius: 16px;
            background: rgba(247, 250, 252, 0.9);
        }
        div[data-baseweb="select"] > div {
            border-radius: 14px;
        }
        .spotlight-panel {
            padding: 1rem 1.05rem;
            border-radius: 18px;
            border: 1px solid rgba(29, 62, 92, 0.10);
            background: rgba(255, 255, 255, 0.92);
            margin-bottom: 1rem;
        }
        .spotlight-eyebrow {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #67829b;
            margin-bottom: 0.45rem;
        }
        .spotlight-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #193450;
            margin-bottom: 0.35rem;
        }
        .spotlight-note {
            color: #4b6177;
            margin: 0;
        }
        .hint-list p {
            margin: 0.15rem 0;
        }
        .planner-divider {
            height: 1px;
            background: rgba(29, 62, 92, 0.08);
            margin: 0.8rem 0 1rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
 
 
def normalize_text(value: str) -> str:
    return " ".join(value.lower().split())
 
 
def detect_response_focus(query: str) -> str:
    normalized = normalize_text(query)
    scores = {
        focus: sum(keyword in normalized for keyword in keywords)
        for focus, keywords in FOCUS_KEYWORDS.items()
    }
 
    best_focus = max(scores, key=scores.get)
    if scores[best_focus] == 0:
        return "full_trip"
    return best_focus
 
 
def format_list(values: Optional[List[str]]) -> str:
    cleaned = [value for value in (values or []) if value]
    return ", ".join(cleaned) if cleaned else "Not specified"
 
 
def display_value(value: Any, default: str = "Not specified") -> str:
    if value in (None, "", [], {}):
        return default
    return str(value)
 
 
def format_location(name: Any, country: Any) -> str:
    clean_name = display_value(name, "")
    clean_country = display_value(country, "")
    if clean_name and clean_country:
        return f"{clean_name}, {clean_country}"
    return clean_name or clean_country or "Not available"


def get_trip_options(travel_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
    itinerary = travel_plan.get("itinerary", {})
    if not isinstance(itinerary, dict):
        return []
    return itinerary.get("trip_options", [])


def looks_like_edit_request(user_input: str) -> bool:
    normalized = normalize_text(user_input)
    edit_phrases = [
        "make it cheaper",
        "make this cheaper",
        "add nightlife",
        "remove museums",
        "remove museum",
        "change the plan",
        "update the plan",
        "edit the plan",
        "swap ",
        "replace ",
        "remove ",
        "add ",
        "skip ",
        "without ",
        "less expensive",
        "more affordable",
        "budget-friendly",
        "cheaper",
        "nightlife",
    ]
    new_trip_signals = [
        "plan a trip to",
        "plan my trip to",
        "suggest destinations",
        "where should i go",
        "weekend trip to",
    ]
    if any(signal in normalized for signal in new_trip_signals):
        return False
    return any(phrase in normalized for phrase in edit_phrases)
 
 
def build_enhanced_input(
    current_request: str,
    history: List[str],
    focus_override: Optional[str] = None,
) -> str:
    prior_context = history[-4:]
    history_block = "\n".join(f"- {item}" for item in prior_context) or "- None"
    focus_block = (
        f"\nPLANNER PRIORITY:\nIf possible, prioritize {focus_override} in the response.\n"
        if focus_override
        else ""
    )
 
    return f"""
Use the CURRENT REQUEST as the primary instruction.
Use PREVIOUS CONTEXT only when it supports the latest request.
Do not let older context override the new request.
{focus_block}
 
PREVIOUS CONTEXT:
{history_block}
 
CURRENT REQUEST:
{current_request}
""".strip()
 
 
def post_to_backend(
    enhanced_input: str,
    raw_user_input: str,
    previous_result: Optional[Dict[str, Any]],
    request_id: str,
) -> Dict[str, Any]:
    response = requests.post(
        BACKEND_URL,
        json={
            "request_id": request_id,
            "user_input": enhanced_input,
            "raw_user_input": raw_user_input,
            "previous_result": previous_result,
        },
        timeout=(10, settings.backend_timeout_seconds),
    )
    response.raise_for_status()
    return response.json()
 
 
def generate_travel_plan(
    enhanced_input: str,
    raw_user_input: str,
    previous_result: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    request_id = str(uuid4())
    try:
        logger.info(
            json.dumps(
                {
                    "event": "backend_request_started",
                    "request_id": request_id,
                    "backend_url": BACKEND_URL,
                }
            )
        )
        result = post_to_backend(
            enhanced_input,
            raw_user_input,
            previous_result,
            request_id,
        )
        result["_execution_mode"] = "api"
        result["request_id"] = request_id
        logger.info(
            json.dumps(
                {
                    "event": "backend_request_succeeded",
                    "request_id": request_id,
                    "backend_url": BACKEND_URL,
                }
            )
        )
        return result
    except requests.RequestException as exc:
        logger.error(
            json.dumps(
                {
                    "event": "backend_request_failed",
                    "request_id": request_id,
                    "backend_url": BACKEND_URL,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "fallback_enabled": settings.allow_local_coordinator_fallback,
                }
            )
        )
        if settings.allow_local_coordinator_fallback:
            logger.warning(
                json.dumps(
                    {
                        "event": "local_fallback_enabled",
                        "request_id": request_id,
                        "backend_url": BACKEND_URL,
                    }
                )
            )
            coordinator = TravelPlannerCoordinator()
            result = coordinator.run(
                user_input=enhanced_input,
                previous_result=previous_result,
                raw_user_input=raw_user_input,
            )
            result["_execution_mode"] = "local"
            result["request_id"] = request_id
            result["_fallback_reason"] = str(exc)
            return result
        raise RuntimeError(
            f"Trip planner backend is unavailable at {BACKEND_URL} for request_id={request_id}. "
            "Set ALLOW_LOCAL_COORDINATOR_FALLBACK=true only if you explicitly want local fallback."
        ) from exc
    except LLMError:
        raise
    except Exception as exc:
        logger.error(
            json.dumps(
                {
                    "event": "trip_generation_unexpected_failure",
                    "request_id": request_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
        )
        raise RuntimeError("Trip generation failed unexpectedly.") from exc
 
 
def find_budget_item(travel_plan: Dict[str, Any], destination_name: str) -> Optional[Dict[str, Any]]:
    for item in travel_plan.get("budget_analysis", {}).get("budget_analysis", []):
        if destination_name.lower() in item.get("destination", "").lower():
            return item
    return None
 
 
def get_top_destination(travel_plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    destinations = travel_plan.get("destinations", {}).get("recommended_destinations", [])
    if not destinations:
        return None
    return destinations[0]
 
 
def section_has_content(travel_plan: Dict[str, Any], section: str) -> bool:
    if section == "destinations":
        return bool(
            travel_plan.get("destinations", {}).get("recommended_destinations", [])
        )
    if section == "budget":
        return bool(travel_plan.get("budget_analysis", {}).get("budget_analysis", []))
    if section == "experiences":
        return bool(travel_plan.get("experiences", {}).get("experience_plan", []))
    if section == "itinerary":
        itinerary = travel_plan.get("itinerary", {})
        return bool(isinstance(itinerary, dict) and itinerary.get("itinerary", []))
    if section == "intent":
        return bool(travel_plan.get("intent"))
    return False
 
 
def render_kpi_card(label: str, value: str, note: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
 
def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-card">
                <h3>{APP_NAME}</h3>
                <p>{APP_TAGLINE}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
 
        st.caption("Map shortcuts")
 
        st.markdown("### Quick routes")
        for index, preset in enumerate(PROMPT_PRESETS):
            if st.button(
                preset["label"],
                key=f"sidebar_preset_{index}",
                use_container_width=True,
            ):
                st.session_state["draft_prompt"] = preset["prompt"]
                st.rerun()
 
        st.markdown("### Recent trips")
        history = list(reversed(st.session_state["history"][-6:]))
        if history:
            for index, item in enumerate(history):
                label = item[:55] + ("..." if len(item) > 55 else "")
                if st.button(label, key=f"history_{index}", use_container_width=True):
                    st.session_state["draft_prompt"] = item
                    st.rerun()
        else:
            st.caption("Your recent trip requests will appear here.")
 
        last_result = st.session_state.get("last_result")
        if last_result:
            st.markdown("### Last mapped trip")
            st.caption(
                f"Mode: {display_value(last_result.get('_execution_mode'), 'api').upper()}"
            )
            st.caption(
                f"Focus: {display_value(last_result.get('response_focus'), st.session_state.get('last_focus', 'full_trip')).replace('_', ' ').title()}"
            )
            last_request = st.session_state.get("last_request", "")
            if last_request:
                st.caption(
                    f"Request: {last_request[:70]}{'...' if len(last_request) > 70 else ''}"
                )
 
 
def render_hero() -> None:
    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-badge">Trip Mapping Workspace</div>
            <h1>{APP_NAME}</h1>
            <p>{APP_SUBTITLE}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
 
def render_prompt_presets() -> None:
    st.markdown("### Map a trip")
    columns = st.columns(3)
    for index, preset in enumerate(PROMPT_PRESETS):
        with columns[index % 3]:
            if st.button(
                preset["label"],
                key=f"main_preset_{index}",
                use_container_width=True,
            ):
                st.session_state["draft_prompt"] = preset["prompt"]
                st.rerun()
 
 
def render_primary_result(result: Dict[str, Any], focus: str) -> None:
    primary_result = result.get("primary_result") or {}
    if not primary_result:
        return
 
    title = display_value(primary_result.get("title"), "Mapped Result")
    data = primary_result.get("data")
    st.markdown(
        f"""
        <div class="spotlight-panel">
            <div class="spotlight-eyebrow">Primary output</div>
            <div class="spotlight-title">{title}</div>
            <p class="spotlight-note">This is WayMapper's primary answer for your current request.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
 
    if focus == "itinerary" and isinstance(data, dict) and data.get("itinerary"):
        render_itinerary({"itinerary": data})
        return
 
    if focus == "budget" and isinstance(data, dict):
        render_budget({"budget_analysis": data})
        return
 
    if focus == "destination" and isinstance(data, dict):
        render_destinations({"destinations": data})
        return
 
    if focus == "experiences" and isinstance(data, dict):
        render_experiences({"experiences": data})
        return
 
    if data is not None:
        st.json(data)


def render_quality_report(result: Dict[str, Any]) -> None:
    quality_report = result.get("quality_report") or {}
    if not quality_report:
        return

    st.markdown("### Quality Check")
    quality_items = [
        ("This saved me time", quality_report.get("saves_time")),
        ("This plan actually works", quality_report.get("works_in_real_world")),
        ("It feels personalized", quality_report.get("feels_personalized")),
    ]

    for label, passed in quality_items:
        prefix = "PASS" if passed else "REVIEW"
        st.markdown(f"- **{prefix}** {label}")

    strengths = quality_report.get("strengths") or []
    if strengths:
        st.markdown("**Why this plan is strong**")
        for item in strengths:
            st.markdown(f"- {item}")

    issues = quality_report.get("issues") or []
    if issues:
        st.markdown("**What was tightened**")
        for item in issues:
            st.markdown(f"- {item}")


def render_grounding_report(result: Dict[str, Any]) -> None:
    grounding_report = result.get("grounding_report") or {}
    if not grounding_report:
        return

    st.markdown("### Grounding Check")
    grounding_items = [
        ("Avoids invented specifics", grounding_report.get("avoids_invented_specifics")),
        ("Consistent across planner sections", grounding_report.get("consistent_across_sections")),
        ("Uses estimates, not fake precision", grounding_report.get("uses_estimates_not_fake_precision")),
    ]

    for label, passed in grounding_items:
        prefix = "PASS" if passed else "REVIEW"
        st.markdown(f"- **{prefix}** {label}")

    issues = grounding_report.get("issues") or []
    if issues:
        st.markdown("**Risk controls applied**")
        for item in issues:
            st.markdown(f"- {item}")
 
 
def render_summary(travel_plan: Dict[str, Any], focus: str) -> None:
    intent = travel_plan.get("intent", {})
    top_destination = get_top_destination(travel_plan)
    top_budget = find_budget_item(travel_plan, top_destination["name"]) if top_destination else None
    itinerary_payload = travel_plan.get("itinerary", {})
    itinerary_days = itinerary_payload.get("itinerary", []) if isinstance(itinerary_payload, dict) else []
    trip_options = get_trip_options(travel_plan)
    planner_brief = travel_plan.get("planner_brief")
    assumptions = travel_plan.get("assumptions", [])
 
    st.subheader("Trip Map Summary")
    st.caption(FOCUS_HINTS.get(focus, FOCUS_HINTS["full_trip"]))
    if planner_brief:
        st.info(planner_brief)
 
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card(
            "Best match",
            format_location(
                top_destination.get("name") if top_destination else None,
                top_destination.get("country") if top_destination else None,
            ),
            "Top destination",
        )
    with col2:
        render_kpi_card(
            "Duration",
            f"{display_value(intent.get('duration_days'), 'N/A')} days",
            "Trip length",
        )
    with col3:
        render_kpi_card(
            "Budget signal",
            display_value(intent.get("budget_level"), "Unspecified"),
            "User-stated budget level",
        )
    with col4:
        render_kpi_card(
            "Companions",
            display_value(intent.get("companions"), "Unspecified"),
            "Traveler setup",
        )
 
    summary_points = []
 
    if top_destination:
        summary_points.append(
            f"Top destination: {format_location(top_destination.get('name'), top_destination.get('country'))} — {top_destination.get('why_suitable', 'fits your request')}."
        )
    if top_budget:
        summary_points.append(
            f"Budget: {top_budget['feasibility'].replace('_', ' ')} with an estimated total of {top_budget['estimated_total_cost']}."
        )
    if itinerary_days:
        summary_points.append(
            f"Itinerary mapped for {len(itinerary_days)} day(s) with structured pacing."
        )
    if trip_options:
        summary_points.append(
            f"{trip_options[0].get('label', 'Primary option')}: {trip_options[0].get('summary', 'Balanced route with practical timing.')}"
        )
    if len(trip_options) > 1:
        summary_points.append(
            f"{trip_options[1].get('label', 'Alternative option')}: {trip_options[1].get('summary', 'Backup plan prepared for tradeoffs.')}"
        )
    if isinstance(itinerary_payload, dict) and itinerary_payload.get("internal_transport_tip"):
        summary_points.append(
            f"Local transport: {itinerary_payload.get('internal_transport_tip')}"
        )
    if intent.get("special_preferences"):
        summary_points.append(
            f"Preferences captured: {format_list(intent.get('special_preferences'))}"
        )
 
    for point in summary_points:
        st.markdown(f"- {point}")
 
    if assumptions:
        st.markdown("**Mapping assumptions**")
        chips = "".join(
            f"<span class='assumption-chip'>{display_value(item)}</span>"
            for item in assumptions
        )
        st.markdown(chips, unsafe_allow_html=True)
 
 
def render_destinations(travel_plan: Dict[str, Any]) -> None:
    destinations = travel_plan.get("destinations", {}).get("recommended_destinations", [])
    st.subheader("Mapped Destinations")
 
    if not destinations:
        st.info("No destinations could be mapped for this request.")
        return
 
    st.success(
        f"Best match: {format_location(destinations[0].get('name'), destinations[0].get('country'))}"
    )
 
    tabs = st.tabs([destination["name"] for destination in destinations])
    for tab, destination in zip(tabs, destinations):
        with tab:
            st.markdown(
                f"### {format_location(destination.get('name'), destination.get('country'))}"
            )
            st.write(display_value(destination.get("why_suitable")))
 
            info_col1, info_col2 = st.columns(2)
            info_col1.markdown(f"**Best for:** {format_list(destination.get('best_for'))}")
            info_col1.markdown(f"**Budget:** {destination.get('budget_range', 'Not specified')}")
            info_col2.markdown(f"**Ideal duration:** {destination.get('ideal_duration', 'Not specified')}")
            info_col2.markdown(f"**Best season:** {destination.get('best_season', 'Not specified')}")
 
            pros_col, cons_col = st.columns(2)
            with pros_col:
                st.markdown("**Pros**")
                for item in destination.get("pros", []):
                    st.markdown(f"- {item}")
            with cons_col:
                st.markdown("**Cons**")
                for item in destination.get("cons", []):
                    st.markdown(f"- {item}")
 
 
def render_budget(travel_plan: Dict[str, Any]) -> None:
    budget_items = travel_plan.get("budget_analysis", {}).get("budget_analysis", [])
    st.subheader("Budget Breakdown")
 
    if not budget_items:
        st.info("No budget breakdown is available for this trip.")
        return
 
    status_label = {
        "feasible": "Good fit",
        "tight_but_feasible": "Possible with tradeoffs",
        "not_feasible": "Over budget",
    }
 
    for item in budget_items:
        st.markdown(f"### {item['destination']}")
        metric_cols = st.columns(3)
        with metric_cols[0]:
            render_kpi_card(
                "Estimated cost",
                display_value(item.get("estimated_total_cost"), "N/A"),
                "Total trip estimate",
            )
        with metric_cols[1]:
            render_kpi_card(
                "Assessment",
                status_label.get(item["feasibility"], item["feasibility"]),
                "Budget fit",
            )
        with metric_cols[2]:
            render_kpi_card(
                "Transport",
                display_value(item.get("cost_breakdown", {}).get("transport"), "N/A"),
                "Travel component",
            )
        st.write(item["reason"])
 
        breakdown = item.get("cost_breakdown") or {}
        if breakdown:
            st.markdown(
                f"**Breakdown:** Transport {breakdown.get('transport', 'N/A')} | "
                f"Stay {breakdown.get('stay', 'N/A')} | "
                f"Food {breakdown.get('food', 'N/A')} | "
                f"Activities {breakdown.get('activities', 'N/A')}"
            )
 
        pricing_notes = item.get("pricing_notes") or []
        if pricing_notes:
            st.markdown("**Assumptions**")
            for note in pricing_notes:
                st.markdown(f"- {note}")
 
        adjustments = item.get("suggested_adjustments") or []
        if adjustments:
            st.markdown("**Suggested adjustments**")
            for adjustment in adjustments:
                st.markdown(
                    f"- **{adjustment['category']}**: {adjustment['suggestion']} ({adjustment['impact']})"
                )
 
        st.divider()
 
 
def render_experiences(travel_plan: Dict[str, Any]) -> None:
    experience_plans = travel_plan.get("experiences", {}).get("experience_plan", [])
    st.subheader("Curated Experiences")
 
    if not experience_plans:
        st.info("No experiences have been mapped for this trip.")
        return
 
    tabs = st.tabs([plan["destination"] for plan in experience_plans])
    for tab, plan in zip(tabs, experience_plans):
        with tab:
            st.markdown(f"### {plan['destination']}")
 
            st.markdown("**Signature experiences**")
            for experience in plan.get("signature_experiences", []):
                st.markdown(
                    "\n".join(
                        [
                            f"- **{experience['title']}**",
                            f"  {experience['description']}",
                            f"  Why it stands out: {experience['why_special']}",
                            f"  Timing: {experience['duration']} | Cost: {experience['approximate_cost']}",
                        ]
                    )
                )
                for tip in experience.get("insider_tips", []):
                    st.caption(f"Tip: {tip}")
 
            additional = plan.get("additional_experiences", [])
            if additional:
                st.markdown("**Additional options**")
                for experience in additional:
                    st.markdown(
                        f"- **{experience['title']}**: {experience['description']} ({experience['duration']}, {experience['cost']})"
                    )
 
            free_activities = plan.get("free_activities", [])
            if free_activities:
                st.markdown("**Free activities**")
                for activity in free_activities:
                    st.markdown(f"- **{activity['title']}** ({activity['best_time']})")
 
 
def render_itinerary(travel_plan: Dict[str, Any]) -> None:
    itinerary = travel_plan.get("itinerary", {})
    st.subheader("Trip Itinerary")

    if not isinstance(itinerary, dict) or "itinerary" not in itinerary:
        st.info("A structured itinerary could not be mapped for this trip.")
        if itinerary:
            st.json(itinerary)
        return
 
    if itinerary.get("trip_style"):
        st.markdown(f"**Trip style:** {display_value(itinerary.get('trip_style'))}")
    if itinerary.get("planning_logic"):
        st.caption(display_value(itinerary.get("planning_logic")))
    if itinerary.get("internal_transport_tip"):
        st.info(display_value(itinerary.get("internal_transport_tip")))

    trip_options = itinerary.get("trip_options", [])
    if trip_options:
        st.markdown("**Trip options**")
        option_cols = st.columns(len(trip_options))
        for col, option in zip(option_cols, trip_options):
            with col:
                st.markdown(
                    f"""
                    <div class="timeline-card">
                        <div class="timeline-slot">{display_value(option.get('label'))}</div>
                        <div class="timeline-title">{display_value(option.get('estimated_total_cost'), 'Cost TBD')}</div>
                        <p class="timeline-note">
                            {display_value(option.get('summary'))}<br/>
                            Best for: {display_value(option.get('best_for'))}<br/>
                            Tradeoff: {display_value(option.get('tradeoff'))}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    days = itinerary.get("itinerary", [])
    if not days:
        st.info("A structured itinerary could not be mapped for this trip.")
        return

    tabs = st.tabs([display_value(day.get("day"), "Day") for day in days])
    for tab, day in zip(tabs, days):
        with tab:
            day_meta = [
                f"Date: {display_value(day.get('date'))}",
                f"Area: {display_value(day.get('zone'))}",
                f"Theme: {display_value(day.get('theme'))}",
                f"Day timing: {display_value(day.get('start_time'))} - {display_value(day.get('end_time'))}",
                f"Day cost: {display_value(day.get('estimated_day_cost'))}",
            ]
            st.markdown(" | ".join(day_meta))
            st.caption(display_value(day.get("local_transport_strategy")))

            for item in day.get("plan", []):
                transit_mode = item.get("transit_mode_from_previous")
                transit_minutes = item.get("transit_time_from_previous_minutes")
                transit_text = "Start of day"
                if transit_mode and transit_minutes is not None:
                    transit_text = f"{transit_mode} {transit_minutes} min from previous stop"
                elif transit_mode:
                    transit_text = transit_mode

                timing = (
                    f"{display_value(item.get('start_time'))} - {display_value(item.get('end_time'))}"
                )
                st.markdown(
                    f"""
                    <div class="timeline-card">
                        <div class="timeline-slot">{timing} | {display_value(item.get('category'))}</div>
                        <div class="timeline-title">{display_value(item.get('activity'))} @ {display_value(item.get('place'))}</div>
                        <p class="timeline-note">
                            Transit: {transit_text} | Buffer: {display_value(item.get('buffer_minutes'), '0')} min | Cost: {display_value(item.get('estimated_cost'))}<br/>
                            Why this stop: {display_value(item.get('reason_to_visit'))}<br/>
                            Notes: {display_value(item.get('notes'))}<br/>
                            Backup: {display_value(item.get('backup_option'))}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
 
 
def render_intent(travel_plan: Dict[str, Any]) -> None:
    intent = travel_plan.get("intent", {})
    st.subheader("Trip Details")
 
    if not intent:
        st.info("No trip details were captured for this request.")
        return
 
    col1, col2 = st.columns(2)
    col1.markdown(f"**Travel purpose:** {display_value(intent.get('travel_purpose'))}")
    col1.markdown(f"**Travel type:** {display_value(intent.get('travel_type'))}")
    col1.markdown(f"**Trip scope:** {display_value(intent.get('trip_scope'), 'trip')}")
    col1.markdown(f"**Origin:** {display_value(intent.get('origin'))}")
    col2.markdown(f"**Destination preference:** {display_value(intent.get('destination_preference'), 'Flexible')}")
    col2.markdown(f"**Country preference:** {display_value(intent.get('country_preference'), 'Flexible')}")
    col2.markdown(f"**Special preferences:** {format_list(intent.get('special_preferences'))}")
 
 
def render_ordered_sections(travel_plan: Dict[str, Any], focus: str) -> None:
    renderers = {
        "destinations": render_destinations,
        "budget": render_budget,
        "experiences": render_experiences,
        "itinerary": render_itinerary,
        "intent": render_intent,
    }
 
    ordered_sections = SECTION_ORDER.get(focus, SECTION_ORDER["full_trip"])
    ordered_sections = [
        section for section in ordered_sections if section_has_content(travel_plan, section)
    ]
 
    if not ordered_sections:
        st.info("No trip sections are available to display.")
        return
 
    primary_sections = ordered_sections[:2]
    secondary_sections = ordered_sections[2:]
 
    for section in primary_sections:
        renderers[section](travel_plan)
 
    for section in secondary_sections:
        with st.expander(SECTION_TITLES[section]):
            renderers[section](travel_plan)
 
 
def render_no_feasible_plan(result: Dict[str, Any], focus: str) -> None:
    st.warning("No destination could be mapped within the current budget and constraints.")
 
    partial_plan = {
        "intent": result.get("intent", {}),
        "destinations": result.get("destinations", {}),
        "budget_analysis": result.get("budget_analysis", {}),
        "experiences": {},
        "itinerary": {},
    }
 
    render_summary(partial_plan, focus)
    render_budget(partial_plan)
 
    with st.expander("Alternative destinations"):
        render_destinations(partial_plan)
 
    with st.expander("Trip details"):
        render_intent(partial_plan)
 
 
def render_result_header(result: Dict[str, Any], focus: str) -> None:
    travel_plan = result.get("travel_plan", {})
    intent = travel_plan.get("intent", {})
    top_destination = get_top_destination(travel_plan)
    planner_brief = result.get("planner_brief") or travel_plan.get("planner_brief")
    generation_mode = display_value(result.get("generation_mode"), "fresh_plan").replace("_", " ").title()
    mode = display_value(result.get("_execution_mode"), "api").upper()
 
    st.markdown("## Your Trip Map")
    if planner_brief:
        st.markdown(
            f"""
            <div class="panel">
                <h3>{planner_brief}</h3>
                <div class="pill-row">
                    <span class="pill">Workflow: {generation_mode}</span>
                    <span class="pill">Focus: {focus.replace('_', ' ').title()}</span>
                    <span class="pill">Mode: {mode}</span>
                    <span class="pill">Duration: {display_value(intent.get('duration_days'), 'N/A')} days</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
 
    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_kpi_card(
            "Destination",
            format_location(
                top_destination.get("name") if top_destination else None,
                top_destination.get("country") if top_destination else None,
            ),
            "Best mapped match",
        )
    with metric_cols[1]:
        render_kpi_card(
            "Trip type",
            display_value(intent.get("travel_type"), "Trip"),
            "Detected from request",
        )
    with metric_cols[2]:
        render_kpi_card(
            "Trip scope",
            display_value(intent.get("trip_scope"), "trip"),
            "WayMapper interpretation",
        )
    with metric_cols[3]:
        render_kpi_card(
            "Response focus",
            focus.replace("_", " ").title(),
            FOCUS_HINTS.get(focus, FOCUS_HINTS["full_trip"]),
        )
 
 
def render_supported_examples() -> None:
    st.markdown("**Try mapping a trip like:**")
    for preset in PROMPT_PRESETS[:4]:
        st.markdown(f"- {preset['prompt']}")
 
 
def render_result(result: Dict[str, Any], requested_focus: str) -> None:
    status = result.get("status")
    if status == "unsupported_request":
        st.warning(result.get("message", "WayMapper only handles trip planning requests."))
        render_supported_examples()
        return
 
    if status == "no_feasible_plan":
        render_no_feasible_plan(result, requested_focus)
        return
 
    if status != "success":
        st.error("Trip map could not be generated.")
        st.json(result)
        return
 
    focus = result.get("response_focus", requested_focus)
    travel_plan = result.get("travel_plan", {})
    assumptions = result.get("assumptions") or travel_plan.get("assumptions", [])
    edit_summary = result.get("edit_summary")
 
    render_result_header(result, focus)
 
    spotlight_tab, board_tab, detail_tab = st.tabs(
        ["Spotlight", "Trip Map", "Raw Data"]
    )
 
    with spotlight_tab:
        if assumptions:
            st.markdown("### Mapping assumptions")
            chips = "".join(
                f"<span class='assumption-chip'>{display_value(item)}</span>"
                for item in assumptions
            )
            st.markdown(chips, unsafe_allow_html=True)

        render_grounding_report(result)
        render_quality_report(result)
        render_primary_result(result, focus)
 
    with board_tab:
        if edit_summary:
            st.success(f"Updated existing trip map: {display_value(edit_summary)}")
        render_summary(travel_plan, focus)
        render_ordered_sections(travel_plan, focus)
 
    with detail_tab:
        with st.expander("Pipeline execution log", expanded=True):
            for step in result.get("pipeline_log", []):
                st.write(f"- {step}")
 
        with st.expander("Recent trip requests"):
            for item in st.session_state["history"]:
                st.write(f"- {item}")
 
        with st.expander("Raw trip map JSON"):
            st.json(result)
 
 
def run_generation(user_input: str, focus_override: Optional[str]) -> None:
    requested_focus = focus_override or detect_response_focus(user_input)
    previous_result = st.session_state.get("last_result")
    is_edit_request = bool(previous_result and looks_like_edit_request(user_input))
    enhanced_input = build_enhanced_input(
        current_request=user_input,
        history=st.session_state["history"],
        focus_override=focus_override,
    )
 
    with st.status("Updating your trip..." if is_edit_request else "Mapping your trip...", expanded=True) as status:
        try:
            st.write("Understanding your request")
            if is_edit_request:
                st.write("Loading your current trip map")
                st.write("Applying targeted edits instead of restarting the plan")
                st.write("Refreshing budget, experiences, and itinerary consistency")
            else:
                st.write("Mapping destinations")
                st.write("Calculating budget feasibility")
                st.write("Curating experiences")
                st.write("Building the route itinerary")
            result = generate_travel_plan(
                enhanced_input=enhanced_input,
                raw_user_input=user_input,
                previous_result=previous_result,
            )
            mode = result.get("_execution_mode", "api")
            status.update(
                label=(
                    f"Trip update ready ({'backend API' if mode == 'api' else 'local fallback'})"
                    if result.get("generation_mode") == "iterative_edit"
                    else f"Trip map ready ({'backend API' if mode == 'api' else 'local fallback'})"
                ),
                state="complete",
            )
        except Exception as exc:
            status.update(label="Trip mapping failed", state="error")
            st.error(f"Unable to map your trip: {exc}")
            return
 
    st.session_state["history"].append(user_input)
    st.session_state["history"] = st.session_state["history"][-12:]
    st.session_state["last_result"] = result
    st.session_state["last_request"] = user_input
    st.session_state["last_focus"] = result.get("response_focus", requested_focus)
 
 
def render_workspace() -> None:
    left_col, right_col = st.columns([1.7, 1], gap="large")
 
    with left_col:
        render_prompt_presets()
        st.markdown(
            """
            <div class="panel workspace-panel">
                <h3>Where do you want to go?</h3>
                <p>Describe your trip in one line. WayMapper will map out destinations, budget, and itinerary — showing the most relevant view first.</p>
                <p>Follow-up edits also work: make it cheaper, add nightlife, remove museums.</p>
                <div class="planner-divider"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
 
        with st.form("planner_form", clear_on_submit=False):
            st.text_area(
                "Travel request",
                key="draft_prompt",
                height=160,
                placeholder=(
                    "Examples:\n"
                    "plan my trip to vaisnodevi\n"
                    "what budget do i need for a 4 day goa trip for 2 people\n"
                    "suggest hill stations near delhi for a weekend trip"
                ),
                label_visibility="collapsed",
            )
 
            form_cols = st.columns([1, 1.1, 0.9])
            with form_cols[0]:
                st.selectbox(
                    "Show first",
                    options=list(FOCUS_PREFERENCE_MAP.keys()),
                    key="view_preference",
                )
            with form_cols[1]:
                st.caption("Leave on auto and WayMapper will decide the best view.")
                st.caption("Pick a focus only when you want a specific section first.")
            with form_cols[2]:
                submit = st.form_submit_button(
                    "Map my trip",
                    type="primary",
                    use_container_width=True,
                )
 
        if submit:
            user_input = st.session_state["draft_prompt"].strip()
            if not user_input:
                st.warning("Tell WayMapper where you want to go.")
            else:
                focus_override = FOCUS_PREFERENCE_MAP.get(
                    st.session_state["view_preference"]
                )
                run_generation(user_input, focus_override)
 
    with right_col:
        st.markdown(
            """
            <div class="panel">
                <h3>What WayMapper maps</h3>
                <p>WayMapper is built for trip planning — not open-ended chat. Describe destinations, budgets, experiences, or itineraries and it maps them out for you.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="panel">
                <h3>Good starting points</h3>
                <div class="hint-list">
                    <p>plan my trip to vaishno devi</p>
                    <p>itinerary for a 2 day delhi outing</p>
                    <p>budget for a 3 day jaipur trip for 2 people</p>
                    <p>suggest beach places in india for august</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="panel">
                <h3>Get a sharper map</h3>
                <div class="hint-list">
                    <p>Include your destination if you already know it.</p>
                    <p>Add days or dates for a tighter itinerary.</p>
                    <p>Ask for budget, itinerary, or destinations when you only need one view.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
 
 
def render_last_result() -> None:
    result = st.session_state.get("last_result")
    if not result:
        return
 
    request = st.session_state.get("last_request", "")
    requested_focus = st.session_state.get("last_focus", "full_trip")
 
    header_cols = st.columns([2.2, 1])
    with header_cols[0]:
        st.markdown("### Last mapped trip")
        st.write(request)
    with header_cols[1]:
        st.download_button(
            label="Download trip map",
            data=json.dumps(result, indent=2),
            file_name="waymapper_trip.json",
            mime="application/json",
            use_container_width=True,
        )
 
    render_result(result, requested_focus)
 
 
st.set_page_config(
    page_title="WayMapper — Trip Planner",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
init_session_state()
inject_styles()
render_sidebar()
render_hero()
 
render_workspace()
render_last_result()
