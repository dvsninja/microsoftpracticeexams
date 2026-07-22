"""Streamlit host for the Microsoft Practice Exams question banks."""

from __future__ import annotations

import json
import random
import time
from pathlib import Path

import streamlit as st


st.set_page_config(page_title="Microsoft Practice Exams", page_icon="🎓", layout="wide")

APP_BACKGROUND = "#333333"
BANK_FOLDER = Path(__file__).parent / "PracticeExamQuestionBanks"
PASSING_SCORE = 700

EXAMS = {
    "PL-900": {
        "title": "Microsoft Certified: Power Platform Fundamentals",
        "bank": "pl900_questions.json",
        "minutes": 45,
        "pillars": ["Power Platform concepts", "Data foundations", "Power Apps", "Power Automate", "Power BI"],
    },
    "AZ-500": {
        "title": "Microsoft Certified: Azure Security Engineer Associate",
        "bank": "az500_questions.json",
        "minutes": 100,
        "pillars": ["Secure identity and access", "Secure networking", "Secure compute, storage, and databases", "Secure Azure using Defender for Cloud and Sentinel"],
    },
    "AB-730": {"title": "Microsoft Certified: AI Business Solutions Architect", "bank": "ab730_questions.json", "minutes": 45, "pillars": ["Generative AI fundamentals", "Prompts and conversations", "Business content", "Meetings and collaboration", "Responsible use"]},
    "AB-900": {"title": "Microsoft 365 Certified: Copilot and Agent Administration Fundamentals", "bank": "ab900_questions.json", "minutes": 45, "pillars": ["Copilot administration", "Security and compliance", "Agents", "Governance", "Adoption"]},
    "AI-901": {"title": "Microsoft Certified: Azure AI Fundamentals", "bank": "ai901_questions.json", "minutes": 45, "pillars": ["AI concepts", "Machine learning", "Computer vision", "Natural language processing", "Generative AI and Foundry"]},
    "PL-300": {"title": "Microsoft Certified: Power BI Data Analyst Associate", "bank": "pl300_questions.json", "minutes": 45, "pillars": ["Prepare data", "Model data", "Visualize and analyze", "Usability and storytelling", "Manage and secure Power BI"]},
    "PL-200": {"title": "Microsoft Certified: Power Platform Functional Consultant Associate", "bank": "pl200_questions.json", "minutes": 45, "pillars": ["Dataverse", "Power Apps", "Process automation", "Power Pages", "Environments and ALM"]},
    "AB-731": {"title": "Microsoft Certified: AI Transformation Leader", "bank": "ab731_questions.json", "minutes": 45, "pillars": ["AI strategy", "Use-case prioritization", "Responsible AI and governance", "Adoption and change", "Innovation and optimization"]},
}


def init_state() -> None:
    defaults = {
        "screen": "selector", "exam_id": None, "questions": [], "answers": {}, "reviewed": set(),
        "question_index": 0, "start_time": None, "duration": 0, "drag_orders": {}, "drag_touched": set(),
        "finish_requested": False,
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def load_bank(filename: str) -> list[dict]:
    path = BANK_FOLDER / filename
    with path.open(encoding="utf-8") as file:
        questions = json.load(file)
    if not isinstance(questions, list):
        raise ValueError(f"{filename} must contain a JSON question list.")
    for number, question in enumerate(questions, start=1):
        if not {"question", "answer", "explanation", "pillar", "weight"}.issubset(question):
            raise ValueError(f"Question {number} in {filename} is missing required data.")
        if question.get("question_type") == "true_false" and len(question.get("options", [])) != 2:
            raise ValueError(f"True/False question {number} in {filename} must have exactly two options.")
    return questions


def make_exam(pool: list[dict], pillars: list[str]) -> list[dict]:
    """Create a fresh, pillar-balanced 40–65 question practice exam."""
    total = min(random.randint(40, 65), len(pool))
    groups = {pillar: [q for q in pool if q["pillar"] == pillar] for pillar in pillars}
    base, remainder = divmod(total, len(pillars))
    selected: list[dict] = []
    for position, pillar in enumerate(random.sample(pillars, len(pillars))):
        count = min(base + (position < remainder), len(groups[pillar]))
        selected.extend(random.sample(groups[pillar], count))
    # Fill any small gap if a future bank has fewer questions in one pillar.
    if len(selected) < total:
        unused = [q for q in pool if q not in selected]
        selected.extend(random.sample(unused, total - len(selected)))
    random.shuffle(selected)
    return selected


def start_exam(exam_id: str) -> None:
    config = EXAMS[exam_id]
    st.session_state.exam_id = exam_id
    st.session_state.questions = make_exam(load_bank(config["bank"]), config["pillars"])
    st.session_state.answers = {}
    st.session_state.reviewed = set()
    st.session_state.question_index = 0
    st.session_state.start_time = time.time()
    st.session_state.duration = config["minutes"] * 60
    st.session_state.drag_orders = {}
    st.session_state.drag_touched = set()
    st.session_state.finish_requested = False
    st.session_state.screen = "exam"


def answer_letters(question: dict) -> set[str]:
    value = question["answer"]
    return set(value) if isinstance(value, list) else {value}


def is_correct(index: int) -> bool:
    question = st.session_state.questions[index]
    answer = st.session_state.answers.get(index)
    kind = question.get("question_type", "single")
    if kind == "matching":
        return answer == question["answer"]
    if kind == "drag_drop":
        return answer == question["answer"]
    selected = set(answer) if isinstance(answer, list) else ({answer} if answer else set())
    return selected == answer_letters(question)


def answer_text(question: dict, answer) -> str:
    kind = question.get("question_type", "single")
    if answer is None:
        return "Unanswered"
    if kind == "matching":
        return "\n".join(f"- {left} → {right}" for left, right in answer.items())
    if kind == "drag_drop":
        return "\n".join(f"{number}. {item}" for number, item in enumerate(answer, start=1))
    letters = sorted(answer) if isinstance(answer, list) else [answer]
    return ", ".join(question["options"][ord(letter) - 65] for letter in letters)


def finish_exam() -> None:
    st.session_state.screen = "results"
    st.session_state.finish_requested = False


def move_drag_item(index: int, source: int, direction: int) -> None:
    order = st.session_state.drag_orders[index]
    destination = source + direction
    if 0 <= destination < len(order):
        order[source], order[destination] = order[destination], order[source]
        st.session_state.answers[index] = list(order)
        st.session_state.drag_touched.add(index)


def render_progress(results: bool = False) -> None:
    questions = st.session_state.questions
    columns = st.columns(len(questions), gap="small")
    for index, column in enumerate(columns):
        if results:
            marker = "🟨" if index not in st.session_state.answers else ("🟩" if is_correct(index) else "🟥")
        else:
            marker = "🔵" if index == st.session_state.question_index else ("🟩" if index in st.session_state.answers else "⬜")
        if column.button(f"{marker}{index + 1}", key=f"jump_{results}_{index}", use_container_width=True):
            st.session_state.question_index = index
            st.session_state.screen = "results_review" if results else "exam"
            st.rerun()


def render_feedback(question: dict, index: int, results: bool) -> None:
    answer = st.session_state.answers.get(index)
    correct = is_correct(index) if answer is not None else False
    correct_answer = answer_text(question, question["answer"])
    if answer is None:
        st.warning(f"Unanswered.\n\nCorrect answer:\n{correct_answer}\n\nWhy: {question['explanation']}")
    elif correct:
        st.success(f"Correct.\n\nWhy: {question['explanation']}")
    else:
        st.error(f"Incorrect — you selected:\n{answer_text(question, answer)}\n\nCorrect answer:\n{correct_answer}\n\nWhy: {question['explanation']}")


def render_question(results: bool = False) -> None:
    index = st.session_state.question_index
    question = st.session_state.questions[index]
    kind = question.get("question_type", "single")
    locked = results or index in st.session_state.reviewed
    st.subheader(f"{'Results review — ' if results else ''}Question {index + 1}")
    st.write(question["question"])
    st.caption(f"Practice value: {question['weight']} point{'s' if question['weight'] != 1 else ''}")

    if results:
        render_feedback(question, index, results=True)
    elif kind in ("single", "true_false"):
        choice = st.session_state.answers.get(index)
        selected = st.radio(
            "Select one answer" if kind == "single" else "Select True or False",
            question["options"], index=(ord(choice) - 65 if choice else None), key=f"choice_{index}", disabled=locked,
        )
        if not locked and selected:
            st.session_state.answers[index] = chr(65 + question["options"].index(selected))
    elif kind == "multi_select":
        selected_letters = st.session_state.answers.get(index, [])
        selected = st.multiselect(
            "Select all that apply", question["options"],
            default=[question["options"][ord(letter) - 65] for letter in selected_letters], key=f"multi_{index}", disabled=locked,
        )
        if not locked:
            st.session_state.answers[index] = sorted(chr(65 + question["options"].index(item)) for item in selected)
            if not selected:
                st.session_state.answers.pop(index, None)
    elif kind == "matching":
        if results:
            st.markdown("**Correct matches**")
            st.markdown(answer_text(question, question["answer"]))
        else:
            st.caption("Choose one matching description for each term. Each description can be used once.")
            assignments = {}
            for left in question["left_items"]:
                current = st.session_state.answers.get(index, {}).get(left, "— Select —")
                selection = st.selectbox(left, ["— Select —"] + question["right_items"],
                                         index=(["— Select —"] + question["right_items"]).index(current),
                                         key=f"match_{index}_{left}", disabled=locked)
                if selection != "— Select —":
                    assignments[left] = selection
            if not locked:
                st.session_state.answers[index] = assignments
                if len(assignments) != len(question["left_items"]) or len(set(assignments.values())) != len(assignments):
                    st.info("Complete every match with a different description before reviewing.")
    elif kind == "drag_drop":
        order = st.session_state.drag_orders.setdefault(index, random.sample(question["items"], len(question["items"])))
        if results:
            st.markdown("**Correct order**")
            st.markdown(answer_text(question, question["answer"]))
        else:
            st.caption("Use the arrow buttons to arrange the items, then review your order.")
            for position, item in enumerate(order):
                left, middle, right = st.columns([1, 10, 1])
                if left.button("↑", key=f"up_{index}_{position}", disabled=locked or position == 0):
                    move_drag_item(index, position, -1)
                    st.rerun()
                middle.markdown(f"**{position + 1}.** {item}")
                if right.button("↓", key=f"down_{index}_{position}", disabled=locked or position == len(order) - 1):
                    move_drag_item(index, position, 1)
                    st.rerun()

    if not results:
        eligible = index in st.session_state.answers
        if kind == "matching":
            current = st.session_state.answers.get(index, {})
            eligible = len(current) == len(question["left_items"]) and len(set(current.values())) == len(current)
        elif kind == "drag_drop":
            eligible = index in st.session_state.drag_touched
        if locked:
            render_feedback(question, index, results=False)
        elif st.button("Review Answer", disabled=not eligible, type="primary"):
            st.session_state.reviewed.add(index)
            st.rerun()

    previous, spacer, next_button = st.columns([1, 8, 1])
    if previous.button("Previous", disabled=index == 0):
        st.session_state.question_index -= 1
        st.rerun()
    if next_button.button("Next", disabled=index == len(st.session_state.questions) - 1):
        st.session_state.question_index += 1
        st.rerun()


def selector_page() -> None:
    st.title("Microsoft Certified Practice Exams")
    st.write("Choose an exam to generate a new randomized practice session.")
    for row_start in range(0, len(EXAMS), 4):
        columns = st.columns(4)
        for column, (exam_id, config) in zip(columns, list(EXAMS.items())[row_start:row_start + 4]):
            with column:
                st.markdown(f"<div class='exam-card'><u>MICROSOFT CERTIFIED:</u><br><br><b>{config['title']}</b><h1>{exam_id}</h1></div>", unsafe_allow_html=True)
                if st.button("START", key=f"start_{exam_id}", use_container_width=True, type="primary"):
                    start_exam(exam_id)
                    st.rerun()


def exam_page() -> None:
    config = EXAMS[st.session_state.exam_id]
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = max(0, st.session_state.duration - elapsed)
    if remaining == 0:
        finish_exam()
        st.rerun()
    minutes, seconds = divmod(remaining, 60)
    left, middle, right = st.columns([2, 7, 2])
    if left.button("FINISH EXAM", type="primary"):
        st.session_state.finish_requested = True
    middle.markdown(f"### {config['title']} | {st.session_state.exam_id}")
    right.markdown(f"### ⏱ {minutes:02d}:{seconds:02d}")
    if st.session_state.finish_requested:
        st.warning("Finish this practice exam now? Unanswered questions will be scored as unanswered.")
        confirm, cancel = st.columns(2)
        if confirm.button("Yes, finish exam", type="primary"):
            finish_exam()
            st.rerun()
        if cancel.button("Keep working"):
            st.session_state.finish_requested = False
            st.rerun()
    render_question()
    st.divider()
    render_progress()


def results_page() -> None:
    questions = st.session_state.questions
    earned = sum(question["weight"] for index, question in enumerate(questions) if is_correct(index))
    available = sum(question["weight"] for question in questions)
    score = round(1000 * earned / available) if available else 0
    correct_count = sum(is_correct(index) for index in range(len(questions)))
    unanswered = len(questions) - len(st.session_state.answers)
    st.title("Exam Complete")
    st.metric("Estimated practice score", f"{score} / 1000")
    (st.success if score >= PASSING_SCORE else st.error)("PASS" if score >= PASSING_SCORE else "FAIL")
    st.write(f"Correct answers: {correct_count} / {len(questions)}  |  Weighted points: {earned} / {available}  |  Unanswered: {unanswered}")
    st.caption("Practice pass line: 700/1000. This is an estimate and not Microsoft's proprietary scaled-score formula.")
    review, retry, home = st.columns(3)
    if review.button("Review Answers", type="primary"):
        st.session_state.question_index = 0
        st.session_state.screen = "results_review"
        st.rerun()
    if retry.button("Try Again"):
        start_exam(st.session_state.exam_id)
        st.rerun()
    if home.button("Choose another exam"):
        st.session_state.screen = "selector"
        st.rerun()


def results_review_page() -> None:
    st.title("Results Review")
    if st.button("Back to results"):
        st.session_state.screen = "results"
        st.rerun()
    render_question(results=True)
    st.divider()
    render_progress(results=True)


st.markdown(f"""
<style>
    .stApp {{ background: {APP_BACKGROUND}; color: #f6f6f6; }}
    .exam-card {{ background: #FAF9F6; color: #111; border: 5px solid #111; height: 250px;
                  box-sizing: border-box; padding: 18px; text-align: center; font-size: 1rem;
                  display: flex; flex-direction: column; justify-content: space-between; }}
    .exam-card h1 {{ color: #0067ce; margin: 18px 0 0; }}
</style>
""", unsafe_allow_html=True)

init_state()
if st.session_state.screen == "selector":
    selector_page()
elif st.session_state.screen == "exam":
    exam_page()
elif st.session_state.screen == "results":
    results_page()
else:
    results_review_page()
