import os
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont

from google import genai

from config import get_env_var

# Load the API key and model from the local .env file.
API_KEY = get_env_var("GEMINI_API_KEY", "your_gemini_api_key_here")
MODEL_NAME = get_env_var("GEMINI_MODEL", "gemini-3.5-flash")


class GeminiChatGUI:
    """Create a simple graphical chatbot window using Tkinter."""

    def __init__(self, root):
        # Keep a reference to the main window.
        self.root = root

        # Set the window title and size.
        self.root.title("Gemini Chatbot")
        self.root.geometry("700x500")
        self.root.configure(bg="#faf9fd")

        # Create empty variables for the client and chat session.
        self.client = None
        self.chat = None

        # Build the user interface.
        self.build_ui()

        # Connect to the Gemini API and create a chat session.
        self.initialize_client()

    def build_ui(self):
        """Create the chat window layout."""
        # Create a larger title font for the top label.
        title_font = tkfont.Font(size=12, weight="bold")

        # Add a title label at the top of the window.
        self.title_label = tk.Label(
            self.root,
            text="Gemini AI Chatbot",
            font=title_font,
            bg="#f2f2f2",
            fg="#f011c0",
        )
        self.title_label.pack(pady=(10, 5))

        # Create a text box where messages will be shown.
        self.chat_area = tk.Text(
            self.root,
            wrap="word",
            state="disabled",
            bg="white",
            fg="#C53A3A",
            padx=10,
            pady=10,
        )
        self.chat_area.pack(fill="both", expand=True, padx=10, pady=5)

        # Create a bottom frame to hold the input box and send button.
        self.bottom_frame = tk.Frame(self.root, bg="#f0e9e9")
        self.bottom_frame.pack(fill="x", padx=10, pady=10)

        # Create the input box where the user types messages.
        self.message_entry = tk.Entry(self.bottom_frame)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        # Make pressing Enter send the message.
        self.message_entry.bind("<Return>", self.send_message_event)

        # Create the send button.
        self.send_button = tk.Button(self.bottom_frame, text="Send", command=self.send_message)
        self.send_button.pack(side="right")

    def initialize_client(self):
        """Create the Gemini client and start a chat session."""
        # Stop the program if the API key is missing.
        if not API_KEY or API_KEY in {"your_gemini_api_key_here", "YOUR_API_KEY_HERE"}:
            messagebox.showerror(
                "Missing API Key",
                "Please set GEMINI_API_KEY in the local .env file before running this app.",
            )
            self.root.destroy()
            return

        # Try to create the Gemini client.
        try:
            self.client = genai.Client(api_key=API_KEY)
            self.chat = self.client.chats.create(model=MODEL_NAME)
            self.append_message("Bot", "Hello! I am ready to chat.")
        except Exception as error:
            messagebox.showerror("Connection Error", f"Unable to start the chatbot:\n{error}")
            self.root.destroy()

    def append_message(self, sender, message):
        """Show a message inside the chat area."""
        self.chat_area.configure(state="normal")
        self.chat_area.insert(tk.END, f"{sender}: {message}\n\n")
        self.chat_area.configure(state="disabled")
        self.chat_area.see(tk.END)

    def send_message_event(self, event=None):
        """Handle pressing Enter in the input box."""
        self.send_message()

    def send_message(self):
        """Send the typed message to Gemini and display the reply."""
        # Read the message from the input box.
        user_message = self.message_entry.get().strip()

        # Ignore empty messages.
        if not user_message:
            return

        # Display the user's message in the chat area.
        self.append_message("You", user_message)

        # Clear the input box after sending.
        self.message_entry.delete(0, tk.END)

        # Disable the button while waiting for the reply.
        self.send_button.configure(state="disabled")

        # Run the API call in a background thread so the window stays responsive.
        threading.Thread(target=self.get_reply, args=(user_message,), daemon=True).start()

    def get_reply(self, user_message):
        """Call the Gemini API and return the response."""
        try:
            # Send the message to the Gemini chat session.
            response = self.chat.send_message(user_message)

            # Get the text part of the reply.
            reply_text = response.text
        except Exception as error:
            # Show a friendly error message if the request fails.
            reply_text = f"Error: {error}"

        # Update the Tkinter window from the main thread.
        self.root.after(0, lambda: self.show_reply(reply_text))

    def show_reply(self, reply_text):
        """Display the bot reply in the chat area."""
        self.append_message("Bot", reply_text)
        self.send_button.configure(state="normal")


def main():
    """Start the Tkinter GUI application."""
    root = tk.Tk()
    GeminiChatGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()