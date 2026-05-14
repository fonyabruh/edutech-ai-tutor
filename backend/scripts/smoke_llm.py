from app.llm.prompts import load_prompt

msgs = load_prompt(
    "diagnose",
    grade=11,
    exam="ЕГЭ",
    subject_name="математика",
    goal="высокий балл",
    answers_summary="тригонометрия: 60%, производная: 40%, геометрия: 80%",
    mastery_summary="тригонометрия: 0.5, производная: 0.3, геометрия: 0.7",
)
print("\nMessages:", msgs)
