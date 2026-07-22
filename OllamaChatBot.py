import json
import threading
import urllib.error
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox

from config import get_env_var

OLLAMA_URL = get_env_var("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")


class OllamaChatBot:
    def __init__(self, model=None):
        self.model = model or get_env_var("OLLAMA_MODEL", "llama3.2")
        self.messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Keep answers short and clear."
            }
        ]

    def list_models(self):
        try:
            request = urllib.request.Request("http://127.0.0.1:11434/api/tags")
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.load(response)
            return [m.get("name") for m in data.get("models", []) if m.get("name")]
        except Exception:
            return []

    def select_model(self):
        models = self.list_models()
        if self.model in models:
            return self.model
        if models:
            return models[0]
        return self.model

    def send_message(self, user_text):
        self.messages.append({"role": "user", "content": user_text})

        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": False
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                OLLAMA_URL,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                result = json.load(response)
        except urllib.error.URLError as exc:
            raise RuntimeError(
                "Could not connect to Ollama. Please start it with 'ollama serve'."
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to get response from Ollama: {exc}") from exc

        assistant_text = result.get("message", {}).get("content", "").strip()
        if not assistant_text:
            assistant_text = "No response received."

        self.messages.append({"role": "assistant", "content": assistant_text})
        return assistant_text


class OllamaChatGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Ollama Chatbot")
        self.geometry("700x500")
        self.minsize(500, 400)

        self.bot = OllamaChatBot()
        self.sending = False
        self.models_loaded = False

        self.create_widgets()
        self.load_models()

    def create_widgets(self):
        top_frame = ttk.Frame(self, padding=10)
        top_frame.pack(fill="x")

        ttk.Label(top_frame, text="Model:").pack(side="left")

        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            top_frame,
            textvariable=self.model_var,
            state="readonly",
            width=25
        )
        self.model_combo.pack(side="left", padx=(5, 0))
        self.model_combo.bind("<<ComboboxSelected>>", self.on_model_selected)

        self.status_var = tk.StringVar(value="Loading models...")
        ttk.Label(top_frame, textvariable=self.status_var).pack(side="left", padx=(10, 0))

        self.chat_text = tk.Text(self, wrap="word", state="disabled", padx=10, pady=10)
        self.chat_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        bottom_frame = ttk.Frame(self, padding=(10, 0, 10, 10))
        bottom_frame.pack(fill="x")

        self.input_entry = ttk.Entry(bottom_frame)
        self.input_entry.pack(side="left", fill="x", expand=True)
        self.input_entry.bind("<Return>", self.send_message)

        self.send_button = ttk.Button(bottom_frame, text="Send", command=self.send_message)
        self.send_button.pack(side="left", padx=(8, 0))

        self.input_entry.focus_set()

    def load_models(self):
        threading.Thread(target=self._load_models_thread, daemon=True).start()

    def _load_models_thread(self):
        models = self.bot.list_models()
        self.after(0, lambda: self._update_models(models))

    def _update_models(self, models):
        if models:
            self.model_combo["values"] = models
            selected_model = self.bot.select_model()
            if selected_model in models:
                self.bot.model = selected_model
            else:
                self.bot.model = models[0]

            self.model_var.set(self.bot.model)
            self.status_var.set(f"Using model: {self.bot.model}")
            self.models_loaded = True
            self._set_ready()
        else:
            self.model_combo["values"] = []
            self.model_var.set("")
            self.status_var.set("No models found. Install one with: ollama pull llama3.2")
            self.models_loaded = False
            self._set_ready()
            self.append_message("System", "No Ollama models found. Please install one first.")

    def on_model_selected(self, event=None):
        selected = self.model_var.get()
        if selected:
            self.bot.model = selected
            self.status_var.set(f"Using model: {selected}")

    def send_message(self, event=None):
        if self.sending:
            return

        user_text = self.input_entry.get().strip()
        if not user_text:
            return

        self.input_entry.delete(0, tk.END)
        self.append_message("You", user_text)

        self.sending = True
        self._set_ready(disable=True)

        threading.Thread(target=self._send_message_thread, args=(user_text,), daemon=True).start()

    def _send_message_thread(self, user_text):
        try:
            response = self.bot.send_message(user_text)
        except RuntimeError as exc:
            self.after(0, lambda: self.handle_error(str(exc)))
        else:
            self.after(0, lambda: self.handle_response(response))

    def handle_response(self, response):
        self.append_message("Bot", response)
        self.sending = False
        self._set_ready()

    def handle_error(self, error):
        self.append_message("System", error)
        self.sending = False
        self._set_ready()
        messagebox.showerror("Ollama Error", error)

    def append_message(self, role, text):
        self.chat_text.configure(state="normal")
        self.chat_text.insert(tk.END, f"{role}: {text}\n\n")
        self.chat_text.configure(state="disabled")
        self.chat_text.see(tk.END)

    def _set_ready(self, disable=False):
        if disable:
            self.send_button.state(["disabled"])
            self.input_entry.state(["disabled"])
            return

        if self.models_loaded:
            self.send_button.state(["!disabled"])
            self.input_entry.state(["!disabled"])
        else:
            self.send_button.state(["disabled"])
            self.input_entry.state(["disabled"])

        self.input_entry.focus_set()


def main():
    app = OllamaChatGUI()
    app.mainloop()


if __name__ == "__main__":
    main()