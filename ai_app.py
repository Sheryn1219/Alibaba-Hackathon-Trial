import streamlit as st
import os
import dashscope
from dashscope import Generation
from datetime import datetime, timedelta

# === Configuration ===
DASHSCOPE_API_KEY = 'sk-ef829ff8d56042eda1969e860f2328c8'
dashscope.base_http_api_url = 'https://dashscope-intl.aliyuncs.com/api/v1'

# Initialize DashScope
dashscope.api_key = DASHSCOPE_API_KEY

# === Session State Initialization ===
if "study_plan" not in st.session_state:
    st.session_state.study_plan = {}
if "progress" not in st.session_state:
    st.session_state.progress = {"topics_completed": 0, "total_topics": 0, "questions_asked": 0}
if "homework_history" not in st.session_state:
    st.session_state.homework_history = []

# === Helper Functions ===
import json

def generate_study_plan(subject, days, difficulty):
    """Generate a structured study plan using Qwen-Plus"""
    prompt = f"""
    Create a {days}-day study plan for {subject} at {difficulty} level.
    Return ONLY a JSON object with these keys:
    - day_X_topics (array of strings)
    - day_X_resources (array of strings)
    - day_X_practice (array of strings)
    
    Example format:
    {{
      "day_1_topics": ["Intro to Algebra"],
      "day_1_resources": ["https://example.com/video1"],
      "day_1_practice": ["Solve 5 equations"]
    }}
    
    IMPORTANT: Return ONLY the JSON object, no markdown or extra text!
    """
    try:
        response = Generation.call(
            model="qwen-plus",
            prompt=prompt
        )
        
        # Try to parse response as JSON
        plan_text = response.output.text.strip()
        
        # Remove markdown code blocks if present
        if plan_text.startswith("```json"):
            plan_text = plan_text[7:-3].strip()
        
        return json.loads(plan_text)
        
    except json.JSONDecodeError as e:
        st.error(f"Failed to parse AI response as JSON: {str(e)}")
        st.debug("Raw AI Response:", plan_text)
        return {}
    except Exception as e:
        st.error(f"Error generating plan: {str(e)}")
        return {}
def get_homework_help(question):
    """Get detailed homework help with step-by-step solutions"""
    prompt = f"""
    Solve this homework problem step-by-step:
    "{question}"
    
    Provide:
    1. Clear explanation of concepts
    2. Step-by-step solution
    3. Common mistakes to avoid
    4. Related practice problems
    """
    try:
        response = Generation.call(
            model="qwen-plus",
            prompt=prompt
        )
        return response.output.text
    except Exception as e:
        return f"Error getting help: {str(e)}"

# === UI ===
st.set_page_config(page_title="Student AI Assistant", layout="wide")
st.title("🎓 Student Success Assistant")
st.markdown("Your AI-powered study companion for planning, homework help, and progress tracking!")

# Sidebar Navigation
tab1, tab2, tab3, tab4 = st.tabs([
    "🗓️ Study Planner", 
    "📚 Homework Help", 
    "🔍 Q&A Assistant", 
    "📊 Progress Dashboard"
])

# === 1. Study Planner Tab ===
with tab1:
    st.header("Create Your Study Plan")
    
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("Subject", placeholder="e.g., Algebra, Biology")
        difficulty = st.select_slider("Difficulty Level", ["Beginner", "Intermediate", "Advanced"])
    with col2:
        days = st.slider("Study Duration (Days)", 3, 30, 7)
        focus_areas = st.multiselect("Key Focus Areas", ["Concepts", "Problem Solving", "Exam Prep", "Projects"])
    
    if st.button("📅 Generate Plan"):
        if subject:
            with st.spinner("Creating your personalized study plan..."):
                st.session_state.study_plan = generate_study_plan(subject, days, difficulty)
                st.session_state.progress["total_topics"] = len(st.session_state.study_plan)
                st.session_state.progress["topics_completed"] = 0
                
            # Display generated plan
            st.success("✅ Study plan created!")
            for day in range(1, days+1):
                day_key = f"day_{day}"
                if day_key in st.session_state.study_plan:
                    with st.expander(f"Day {day} Plan"):
                        st.write("**Topics:**", st.session_state.study_plan[day_key].get("topics", []))
                        st.write("**Resources:**", st.session_state.study_plan[day_key].get("resources", []))
                        st.write("**Practice:**", st.session_state.study_plan[day_key].get("practice", []))
        else:
            st.warning("Please enter a subject!")

# === 2. Homework Help Tab ===
with tab2:
    st.header("Get Homework Help")
    
    hw_question = st.text_area("Describe your homework problem:", height=150)
    
    if st.button("💡 Get Solution"):
        if hw_question.strip():
            with st.spinner("Getting AI-powered help..."):
                solution = get_homework_help(hw_question)
                st.session_state.homework_history.append({
                    "question": hw_question,
                    "solution": solution,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.markdown(solution)
        else:
            st.warning("Please enter a homework question!")

# === 3. Q&A Assistant Tab ===
with tab3:
    st.header("Ask Your Study Questions")
    
    user_input = st.text_input("Your Question:")
    
    if st.button("🧠 Get Answer"):
        if user_input.strip():
            with st.spinner("Thinking..."):
                try:
                    messages = [
                        {'role': 'system', 'content': 'You are a helpful study assistant'},
                        {'role': 'user', 'content': user_input}
                    ]
                    response = Generation.call(
                        model="qwen-plus",
                        prompt=messages
                    )
                    answer = response.output.text
                    st.markdown(f"### Answer:\n{answer}")
                    st.session_state.progress["questions_asked"] += 1
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        else:
            st.warning("Please enter a question!")

# === 4. Progress Dashboard Tab ===
with tab4:
    st.header("Your Learning Progress")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.progress["total_topics"] > 0:
            completion_rate = (st.session_state.progress["topics_completed"] / st.session_state.progress["total_topics"]) * 100
            st.progress(int(completion_rate))
            st.write(f"📚 Topics Completed: {st.session_state.progress['topics_completed']}/{st.session_state.progress['total_topics']}")
        else:
            st.write("No study plan created yet.")
    
    with col2:
        st.write(f"🧠 Questions Asked: {st.session_state.progress['questions_asked']}")
        st.write(f"📖 Homework Sessions: {len(st.session_state.homework_history)}")
        
    if st.button("🔄 Reset Progress"):
        st.session_state.progress = {"topics_completed": 0, "total_topics": 0, "questions_asked": 0}

# === Footer ===
st.markdown("---")
st.markdown("💡 Tip: Use the Homework Help section for detailed step-by-step solutions to math problems!")
st.markdown("© 2024 Student Success Assistant | Powered by Alibaba Cloud Qwen-Plus")


