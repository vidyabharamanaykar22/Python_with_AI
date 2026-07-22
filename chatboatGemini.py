from config import get_env_var


def main():
    api_key = get_env_var("GEMINI_API_KEY", "your_gemini_api_key_here")
    model = get_env_var("GEMINI_MODEL", "gemini-3.5-flash")

    if not api_key or api_key == "your_gemini_api_key_here":
        print("Please set GEMINI_API_KEY in the local .env file before running this app.")
        return

    print(f"Gemini configuration loaded. Model: {model}")


if __name__ == "__main__":
    main()
