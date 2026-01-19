from docx import Document
import re

def read_questions_from_docx(file):
    doc = Document(file)

    # 1️⃣ Convert full document to single text
    full_text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    # 2️⃣ Split into question blocks
    blocks = re.split(r"\n(?=\d+\.)", full_text)

    questions = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Question
        q_match = re.search(r"^\d+\.\s*(.+)", block, re.M)
        if not q_match:
            continue
        question_text = q_match.group(1).strip()

        # Options
        options = ["", "", "", ""]
        for idx, letter in enumerate(["A", "B", "C", "D"]):
            opt_match = re.search(
                rf"{letter}\)\s*(.+?)(?=\n[A-D]\)|\nAnswer|\Z)",
                block,
                re.S
            )
            if opt_match:
                options[idx] = opt_match.group(1).strip()

        # Answer
        ans_match = re.search(r"Answer\s*:\s*([A-D])", block, re.I)
        answer = ans_match.group(1).upper() if ans_match else ""

        questions.append({
            "question": question_text,
            "options": options,
            "answer": answer
        })

    return questions
