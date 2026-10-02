import os

from groq import Groq

from app.processing.chunker import Chunk


LLM_MODEL = os.environ.get(
    "LLM_MODEL",
    "openai/gpt-oss-120b"
)


SYSTEM_PROMPT = (
    "You are Codent, a code-understanding assistant. Answer the question using ONLY "
    "the numbered code sources provided. Cite sources like [1] or [2] after each claim. "
    "If the sources do not contain enough information, say so plainly instead of guessing. "
    "Be concise and specific."
)


def build_prompt(question: str, chunks: list[Chunk]) -> str:
    """Format retrieved chunks as numbered sources followed by the question."""

    sources = []

    for i, c in enumerate(chunks, start=1):
        sources.append(
            f"[{i}] {c.file} "
            f"(lines {c.start_line}-{c.end_line}) "
            f"{c.kind}: {c.name}\n"
            f"```\n{c.code}\n```"
        )

    return (
        "Sources:\n\n"
        + "\n\n".join(sources)
        + f"\n\nQuestion: {question}"
    )


def answer_question(
    question: str,
    chunks: list[Chunk],
    client=None,
) -> str:
    """Ask the LLM to answer from the retrieved chunks only."""

    if not chunks:
        return "I couldn't find any relevant code to answer that."

    client = client or Groq()  # reads GROQ_API_KEY from env

    response = client.chat.completions.create(
        model=LLM_MODEL,
        max_tokens=1000,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": build_prompt(
                    question,
                    chunks,
                ),
            },
        ],
    )

    return response.choices[0].message.content or ""