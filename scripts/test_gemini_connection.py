
import getpass
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from google import genai
from google.genai import types

from backend.app.gemini_adapter import DEFAULT_MODEL


def main():
    api_key = getpass.getpass("Gemini API key (hidden): ").strip()

    if not api_key:
        print("Connection test aborted: no API key provided.")
        return 1

    client = None

    try:
        try:
            client = genai.Client(api_key=api_key)
        except Exception as exc:
            print(
                "Client initialization failed: "
                f"{type(exc).__name__}."
            )
            return 1
    finally:
        del api_key

    try:
        try:
            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents='Return exactly this JSON: {"status":"ok"}',
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    max_output_tokens=32,
                ),
            )

            response_text = getattr(response, "text", None)

            if (
                not isinstance(response_text, str)
                or not response_text.strip()
            ):
                print("Connection test failed: no usable response.")
                return 1

            print("Model:", DEFAULT_MODEL)
            print("Response received:", True)
            print("Response length:", len(response_text))
            print("Raw response: not displayed")
            return 0

        except Exception as exc:
            print(
                "Gemini request failed: "
                f"{type(exc).__name__}. "
                "Check API access, quota, and connectivity."
            )
            return 1

    finally:
        try:
            client.close()
        except Exception as exc:
            print(
                "Client cleanup warning: "
                f"{type(exc).__name__}."
            )


if __name__ == "__main__":
    raise SystemExit(main())
