from dotenv import load_dotenv
from openai import OpenAI
import json
import os
from pathlib import Path
import requests
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel


load_dotenv(override=True)


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        },
    )


def record_user_details(email, name="Name not provided", notes="not provided"):
    push(f"Recording {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question):
    push(f"Recording unknown question: {question}")
    return {"recorded": "ok"}


record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {
                "type": "string",
                "description": "The email address of this user",
            },
            "name": {
                "type": "string",
                "description": "The user's name, if they provided it",
            },
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered",
            },
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

tools = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]


class Me:
    def __init__(self):
        self.openai = OpenAI()
        self.gemini = OpenAI(
            api_key=os.getenv("GEMINI_API_KEY"),
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        self.name = "Gaston Quiroga"
        base_dir = Path(__file__).resolve().parent
        me_dir = base_dir / "me"
        reader = PdfReader(me_dir / "quiroga_gaston_linkedin.pdf")
        self.linkedin = ""
        self.resume = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        reader = PdfReader(me_dir / "quiroga_gaston_cv.pdf")
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.resume += text
        with open(me_dir / "summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        self._context_embedding = None

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id,
                }
            )
        return results

    def system_prompt(self):
        system_prompt = f"You are an AI assistant representing {self.name}. You are answering questions on {self.name}'s website, \
particularly questions related to {self.name}'s career, background, skills and experience. \
Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible, \
speaking in the first person about {self.name}'s background based only on the provided materials. \
You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
Always include a brief disclosure in your responses that you are an AI assistant representing {self.name}. \
If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
Only suggest futher contact if the user is engaging in discussion, that means 2 or 3 questions about my experience or explicitly asks for contact information. \
Do not propose or schedule calls or meetings. You may only offer contact via email, mobile/cellular, or LinkedIn, and for email you should ask for their email and record it using your record_user_details tool. "

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        system_prompt += f"## Resume:\n{self.resume}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt

    def _embed_text(self, text: str) -> list[float]:
        response = self.openai.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding

    def is_relevant_question(self, message: str) -> bool:
        if not self._context_embedding:
            context = f"{self.summary}\n\n{self.linkedin}\n\n{self.resume}"
            self._context_embedding = self._embed_text(context)

        question_embedding = self._embed_text(message)
        dot = sum(a * b for a, b in zip(self._context_embedding, question_embedding))
        norm_a = sum(a * a for a in self._context_embedding) ** 0.5
        norm_b = sum(b * b for b in question_embedding) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return False
        similarity = dot / (norm_a * norm_b)
        if similarity >= 0.10:
            return True

        msg = message.lower()
        summary = self.summary.lower()
        hobby_keywords = [
            "food",
            "eat",
            "favorite",
            "favourite",
            "cake",
            "cheesecake",
            "lemon pie",
            "key lime",
            "cinema",
            "movie",
            "dog",
            "chess",
            "videogame",
            "video game",
            "book",
            "read",
        ]
        return any(kw in msg and kw in summary for kw in hobby_keywords)

    def evaluator_prompt(self):
        evaluator_system_prompt = f"You are an evaluator that decides whether a response to a question is acceptable. \
        You are provided with a conversation between a User and an Agent. Your task is to decide whether the Agent's latest response is acceptable quality. \
        The Agent is an AI assistant representing {self.name} on their website. The Agent may speak in the first person about {self.name}'s background, \
        as long as it is grounded in the provided materials and does not invent personal experiences beyond them. \
        The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. \
        The Agent has been provided with context on {self.name} in the form of their summary and LinkedIn details. Here's the information:"

        evaluator_system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n"
        evaluator_system_prompt += f"## Resume:\n{self.resume}\n\n"
        evaluator_system_prompt += "With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."

    def evaluator_user_prompt(self, reply, message, history):
        user_prompt = (
            f"Here's the conversation between the User and the Agent: \n\n{history}\n\n"
        )
        user_prompt += f"Here's the latest message from the User: \n\n{message}\n\n"
        user_prompt += f"Here's the latest response from the Agent: \n\n{reply}\n\n"
        user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
        return user_prompt

    def evaluate(self, reply, message, history) -> Evaluation:
        messages = [{"role": "system", "content": self.evaluator_prompt()}] + [
            {
                "role": "user",
                "content": self.evaluator_user_prompt(reply, message, history),
            }
        ]
        response = self.gemini.beta.chat.completions.parse(
            model="gemini-3-flash-preview",
            messages=messages,
            response_format=Evaluation,
        )
        return response.choices[0].message.parsed

    def rerun(self, reply, message, history, feedback):
        updated_system_prompt = (
            self.system_prompt()
            + "\n\n## Previous answer rejected\nYou just tried to reply, but the quality control rejected your reply\n"
        )
        updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
        updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
        messages = (
            [{"role": "system", "content": updated_system_prompt}]
            + history
            + [{"role": "user", "content": message}]
        )
        response = self.openai.chat.completions.create(
            model="gpt-5-nano", messages=messages
        )
        return response.choices[0].message.content

    def chat(self, message, history):
        if not self.is_relevant_question(message):
            record_unknown_question(message)
            return (
                f"I'm an AI assistant representing {self.name}. "
                "I can only answer questions about my career, background, skills, experience, or projects."
            )
        messages = (
            [{"role": "system", "content": self.system_prompt()}]
            + history
            + [{"role": "user", "content": message}]
        )
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="gpt-5-nano", messages=messages, tools=tools
            )
            if response.choices[0].finish_reason == "tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        reply = response.choices[0].message.content

        evaluation = self.evaluate(reply, message, history)

        if not evaluation.is_acceptable:
            print("Response not acceptable, rerunning...", flush=True)
            print(f"Feedback: {evaluation.feedback}", flush=True)
            reply = self.rerun(reply, message, history, evaluation.feedback)
        return reply


if __name__ == "__main__":
    me = Me()
    theme = gr.themes.Base(
        primary_hue="cyan",
        secondary_hue="blue",
        neutral_hue="slate",
        font=[
            gr.themes.GoogleFont("Manrope"),
            "ui-sans-serif",
            "system-ui",
            "sans-serif",
        ],
        font_mono=[
            gr.themes.GoogleFont("JetBrains Mono"),
            "ui-monospace",
            "SFMono-Regular",
            "Menlo",
            "monospace",
        ],
    )

    css = """
    :root {
      --bg: #f7f8fc;
      --panel: #ffffff;
      --text: #0f172a;
      --border: rgba(15, 23, 42, 0.08);
      --accent: #06b6d4;
      --accent-2: #3b82f6;
      --shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
      --radius: 14px;
    }

    @media (prefers-color-scheme: dark) {
      :root {
        --bg: #0b1020;
        --panel: #111827;
        --text: #e5e7eb;
        --border: rgba(148, 163, 184, 0.18);
        --shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
      }
    }

    body, .gradio-container {
      background: linear-gradient(180deg, rgba(6, 182, 212, 0.08), transparent 45%),
                  var(--bg);
      color: var(--text);
    }

    .gradio-container {
      min-height: 100vh;
    }

    .app-header {
      background: var(--panel);
      border: 1px solid var(--border);
      box-shadow: var(--shadow);
      border-radius: var(--radius);
      padding: 16px 18px;
      margin-bottom: 14px;
    }

    .chat-wrap {
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }

    .message, .bubble, .chatbot .message {
      border-radius: 12px !important;
      border: 1px solid var(--border);
      background: rgba(6, 182, 212, 0.06) !important;
      color: var(--text) !important;
      box-shadow: none !important;
    }

    .message.user, .bubble.user, .chatbot .message.user {
      background: linear-gradient(135deg, rgba(6, 182, 212, 0.20), rgba(59, 130, 246, 0.20)) !important;
      border: 1px solid rgba(6, 182, 212, 0.35) !important;
    }

    textarea, input[type="text"] {
      background: var(--panel) !important;
      color: var(--text) !important;
      border: 1px solid var(--border) !important;
      border-radius: 10px !important;
    }

    button, .gr-button {
      background: linear-gradient(135deg, var(--accent), var(--accent-2)) !important;
      color: #0b1020 !important;
      border: none !important;
      border-radius: 10px !important;
      box-shadow: var(--shadow);
    }

    .footer, .gradio-container .footer {
      display: none !important;
    }
    """

    with gr.Blocks(theme=theme, css=css) as demo:
        gr.Markdown(
            f"# {me.name}\nAI assistant for career, projects, and background.",
            elem_classes=["app-header"],
        )
        with gr.Group(elem_classes=["chat-wrap"]):
            gr.ChatInterface(me.chat, type="messages")

    demo.launch()
