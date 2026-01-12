# # app.py

# import streamlit as st
# import os
# from openai import OpenAI
# from dotenv import load_dotenv
# load_dotenv()


# from agents.coordinator import TravelPlannerCoordinator

# # ----------------------------
# # Page Configuration
# # ----------------------------
# st.set_page_config(
#     page_title="AI Travel Planner",
#     page_icon="🌍",
#     layout="centered"
# )

# st.title("🌍 AI Travel Planner")
# st.caption("A multi-agent AI system that plans personalized trips")

# # ----------------------------
# # API Key Input
# # ----------------------------
# openai_api_key = st.text_input(
#     "Enter your OpenAI API Key",
#     type="password"
# )

# if openai_api_key:
#     os.environ["OPENAI_API_KEY"] = openai_api_key

# # ----------------------------
# # User Input
# # ----------------------------
# user_query = st.text_area(
#     "Describe your trip",
#     placeholder="Example: I want a 5 day relaxing trip with my partner in December on a moderate budget"
# )

# # ----------------------------
# # Run Planner
# # ----------------------------
# if st.button("Generate Travel Plan"):
#     if not openai_api_key:
#         st.warning("Please enter your OpenAI API Key.")
#     elif not user_query:
#         st.warning("Please describe your travel plan.")
#     else:
#         with st.spinner("Planning your trip..."):
#             planner = TravelPlannerCoordinator()
#             output = planner.run(user_query)

#         if "error" in output:
#             st.error("Something went wrong while planning your trip.")
#             st.json(output)
#         else:
#             # ----------------------------
#             # Display Results
#             # ----------------------------

#             st.subheader("🧠 Travel Intent")
#             st.json(output["intent"])

#             st.subheader("📍 Recommended Destinations")
#             st.json(output["destinations"])

#             st.subheader("💰 Budget Analysis")
#             st.json(output["budget_analysis"])

#             st.subheader("🎒 Experiences")
#             st.json(output["experiences"])

#             st.subheader("🗓️ Itinerary")
#             st.json(output["itinerary"])



import streamlit as st
import json

from agents.coordinator import TravelPlannerCoordinator


# ---------------------------------------------
# PAGE CONFIG
# ---------------------------------------------
st.set_page_config(
    page_title="TripCraft AI",
    page_icon="🌍",
    layout="wide",
)


# ---------------------------------------------
# HEADER
# ---------------------------------------------
st.title("🌍 TripCraft AI")
st.caption("AI-powered travel planning — realistic, budget-aware, human-friendly")

st.divider()


# ---------------------------------------------
# USER INPUT
# ---------------------------------------------
st.subheader("✍️ Describe your trip")

user_input = st.text_area(
    label="Travel request",
    placeholder=(
        "Example:\n"
        "Plan a relaxing 5-day trip for a couple with a moderate budget. "
        "We love beaches, spa experiences, and good food."
    ),
    height=160,
)

run_button = st.button("✨ Generate Travel Plan", type="primary")


# ---------------------------------------------
# EXECUTION
# ---------------------------------------------
if run_button:
    if not user_input.strip():
        st.warning("Please describe your travel plan.")
        st.stop()

    coordinator = TravelPlannerCoordinator()

    with st.spinner("Planning your trip…"):
        result = coordinator.run(user_input)

    st.divider()

    # -----------------------------------------
    # FAILURE STATES
    # -----------------------------------------
    if result["status"] != "success":
        st.error("❌ Travel plan could not be generated")

        st.subheader("Failure Details")
        st.json(result)

        st.stop()

    travel_plan = result["travel_plan"]

    # -----------------------------------------
    # PIPELINE LOG
    # -----------------------------------------
    with st.expander("🧠 Pipeline Execution Log"):
        for step in result["pipeline_log"]:
            st.write("•", step)

    # -----------------------------------------
    # INTENT
    # -----------------------------------------
    st.subheader("🧠 Travel Intent")
    st.json(travel_plan["intent"])

    # -----------------------------------------
    # DESTINATIONS
    # -----------------------------------------
    st.subheader("📍 Recommended Destinations")

    for dest in travel_plan["destinations"]["recommended_destinations"]:
        with st.container():
            st.markdown(
                f"""
                ### {dest['name']}, {dest['country']}
                **Why:** {dest['why_suitable']}

                **Best for:** {', '.join(dest.get('best_for', []))}  
                **Budget:** {dest.get('budget_range')}  
                **Ideal Duration:** {dest.get('ideal_duration')}  
                **Best Season:** {dest.get('best_season')}
                """
            )
            st.markdown("**Pros:**")
            for p in dest.get("pros", []):
                st.write("•", p)

            st.markdown("**Cons:**")
            for c in dest.get("cons", []):
                st.write("•", c)

            st.divider()

    # -----------------------------------------
    # BUDGET
    # -----------------------------------------
    st.subheader("💰 Budget Feasibility")

    for b in travel_plan["budget_analysis"]["budget_analysis"]:
        icon = "✅" if b["feasibility"] == "feasible" else "❌"

        with st.container():
            st.markdown(
                f"""
                ### {icon} {b['destination']}
                **Estimated Cost:** {b['estimated_total_cost']}  
                **Assessment:** {b['reason']}
                """
            )

            if b["suggested_adjustments"]:
                st.markdown("**Suggested Adjustments:**")
                for adj in b["suggested_adjustments"]:
                    st.write(
                        f"- **{adj['category']}**: {adj['suggestion']} ({adj['impact']})"
                    )

            st.divider()

    # -----------------------------------------
    # EXPERIENCES
    # -----------------------------------------
    st.subheader("✨ Curated Experiences")

    for plan in travel_plan["experiences"]["experience_plan"]:
        st.markdown(f"## 📍 {plan['destination']}")

        st.markdown("### 🌟 Signature Experiences")
        for e in plan.get("signature_experiences", []):
            st.markdown(
                f"""
                **{e['title']}**  
                {e['description']}  
                _Why special:_ {e['why_special']}  
                ⏱ {e['duration']} | 💸 {e['approximate_cost']}
                """
            )
            if e.get("insider_tips"):
                st.markdown("**Insider Tips:**")
                for tip in e["insider_tips"]:
                    st.write("•", tip)

        st.markdown("### 🧭 Additional Experiences")
        for e in plan.get("additional_experiences", []):
            st.write(f"• **{e['title']}** — {e['description']}")

        st.markdown("### 🆓 Free Activities")
        for f in plan.get("free_activities", []):
            st.write(f"• **{f['title']}** ({f['best_time']})")

        st.divider()

    # -----------------------------------------
    # ITINERARY
    # -----------------------------------------
    st.subheader("🗓️ Final Itinerary")

    itinerary = travel_plan["itinerary"]

    if isinstance(itinerary, dict) and "itinerary" in itinerary:
        for day in itinerary["itinerary"]:
            with st.expander(day["day"], expanded=True):
                for item in day["plan"]:
                    st.markdown(
                        f"""
                        **{item['time_slot']}**  
                        {item['activity']}  
                        _{item['notes']}_
                        """
                    )
    else:
        st.warning("Itinerary format not available.")
        st.json(itinerary)

    # -----------------------------------------
    # RAW OUTPUT (DEBUG)
    # -----------------------------------------
    with st.expander("🧪 Raw JSON Output"):
        st.json(result)
