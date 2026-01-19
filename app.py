import streamlit as st
import random
import time
import pandas as pd
from question_reader import read_questions_from_docx

st.set_page_config(page_title="Online Quiz System", layout="centered")

# ==================================================
# SESSION STATE INIT
# ==================================================
defaults = {
    "faculty_logged": False,
    "exam_code": None,
    "questions": [],
    "timer_enabled": False,
    "exam_duration": 0,
    "exam_started": False,
    "exam_finished": False,
    "student_questions": [],
    "current_q": 0,
    "answers": {},
    "exam_start_time": None,
    "student_info": {},
    "results": []
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==================================================
# HELPERS
# ==================================================
def load_faculty():
    return pd.read_csv("faculty.csv")

def assign_questions(qs, count=30):
    return random.sample(qs, min(count, len(qs)))

def submit_exam():
    st.session_state.exam_started = False
    st.session_state.exam_finished = True

# ==================================================
# HEADER
# ==================================================
st.image("vignan_logo.png", width=600)
st.title("📝 Online Quiz Examination")
st.markdown("---")
role = st.selectbox("Login as", ["Select", "Faculty", "Student"])

# ==================================================
# 👨‍🏫 FACULTY
# ==================================================
if role == "Faculty":

    st.subheader("👨‍🏫 Faculty Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        df = load_faculty()
        user = df[(df.email == email) & (df.password == password)]
        if not user.empty:
            st.session_state.faculty_logged = True
            st.success("Login successful")
        else:
            st.error("Invalid credentials")

    if st.session_state.faculty_logged:

        uploaded = st.file_uploader("Upload Question Paper (.docx)", type=["docx"])
        if uploaded:
            st.session_state.questions = read_questions_from_docx(uploaded)
            st.success(f"{len(st.session_state.questions)} questions loaded")

        st.markdown("### ⏱️ Timer Settings")
        st.session_state.timer_enabled = st.checkbox("Enable Timer")
        if st.session_state.timer_enabled:
            st.session_state.exam_duration = st.number_input(
                "Exam duration (minutes)", min_value=1, max_value=180, value=30
            )

        if st.button("Generate Exam Code"):
            st.session_state.exam_code = "CA" + str(random.randint(100000, 999999))
            st.info(f"Exam Code: {st.session_state.exam_code}")

        if st.session_state.results:
            df = pd.DataFrame(st.session_state.results)

            # ranking based on submission time (early = top)
            df = df.sort_values(by="SubmitTime").reset_index(drop=True)
            df["Rank"] = df.index + 1
            df.loc[df["Rank"] > 3, "Rank"] = ""

            final_df = df[["Roll No", "Name", "Marks", "Rank"]]

            st.download_button(
                "⬇️ Download Results (Excel)",
                data=final_df.to_excel(index=False),
                file_name="results.xlsx"
            )


# ==================================================
# 👨‍🎓 STUDENT
# ==================================================
elif role == "Student":

    # ---------------- LOGIN ----------------
    if not st.session_state.exam_started and not st.session_state.exam_finished:
        st.subheader("👨‍🎓 Student Login")
        roll = st.text_input("Roll Number")
        name = st.text_input("Name")
        code = st.text_input("Exam Code")

        if st.button("Start Exam"):
            if code != st.session_state.exam_code:
                st.error("Invalid exam code")
            else:
                st.session_state.student_info = {"roll": roll, "name": name}
                st.session_state.student_questions = assign_questions(
                    st.session_state.questions
                )
                st.session_state.exam_started = True
                st.session_state.exam_start_time = time.time()
                st.session_state.current_q = 0
                st.session_state.answers = {}
                st.success("Exam Started")
                st.rerun()

    # ---------------- EXAM SCREEN (SMOOTH) ----------------
    if st.session_state.exam_started and not st.session_state.exam_finished:

        # TIMER
        if st.session_state.timer_enabled:
            elapsed = int((time.time() - st.session_state.exam_start_time) / 60)
            remaining = st.session_state.exam_duration - elapsed
            st.warning(f"⏳ Time Remaining: {remaining} minutes")
            if remaining <= 0:
                submit_exam()
                st.rerun()

        qno = st.session_state.current_q
        questions = st.session_state.student_questions
        q = questions[qno]

        st.markdown(f"### Question {qno + 1} of {len(questions)}")
        st.write(q["question"])

        selected = st.session_state.answers.get(qno)
        if selected:
            st.info(f"Selected Answer: {selected}")

        # OPTIONS (FAST RESPONSE)
        for idx, opt in enumerate(["A", "B", "C", "D"]):
            if st.button(f"{opt}) {q['options'][idx]}", key=f"{qno}_{opt}"):
                st.session_state.answers[qno] = opt
                st.rerun()

        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("⬅️ Previous", disabled=(qno == 0)):
                st.session_state.current_q -= 1
                st.rerun()

        with col2:
            if st.button("Next ➡️", disabled=(qno == len(questions) - 1)):
                st.session_state.current_q += 1
                st.rerun()

        with col3:
            if st.button("Submit Exam"):
                submit_exam()
                st.rerun()

    # ---------------- RESULT ----------------
    if st.session_state.exam_finished:

        score = 0
        for i, q in enumerate(st.session_state.student_questions):
            if st.session_state.answers.get(i) == q["answer"]:
                score += 1

        total = len(st.session_state.student_questions)
        percent = round((score / total) * 100, 2)

        st.success("🎉 Exam Completed")
        st.write(f"Score: {score} / {total}")
        st.write(f"Percentage: {percent}%")

        st.session_state.results.append({
            "Roll No": st.session_state.student_info["roll"],
            "Name": st.session_state.student_info["name"],
            "Marks": score,
            "SubmitTime": time.time()   # ranking kosam
        })


# ==================================================
# FIXED FOOTER
# ==================================================
st.markdown(
    """
    <style>
    .custom-footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0e2a3a;
        color: red;
        text-align: center;
        padding: 10px;
        font-size: 14px;
        z-index: 100;
    }
    </style>

    <div class="custom-footer">
        Developed by <b>Mr. A.N. Harshith Vardhan</b> | Department of Computer Applications
    </div>
    """,
    unsafe_allow_html=True
)
