import pydevd_pycharm
import streamlit as st
import requests
import logging

# ==============================
# Configuration
# ==============================
VERIFY_URL = "http://localhost:8000/verify_user_details"
ASK_URL = "http://localhost:8000/ask"


# ==============================
# Setup helpers
# ==============================
def setup_debugging():
    pydevd_pycharm.settrace(
        "localhost",
        port=5679,
        stdout_to_server=True,
        stderr_to_server=True,
        suspend=False
    )


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )
    return logging.getLogger(__name__)


def init_session_state():
    st.session_state.setdefault("user_info", {})
    st.session_state.setdefault("conversation_history", [])
    st.session_state.setdefault("language", "english")
    st.session_state.setdefault("user_input_attempt", {
        "text": "",
        "cumulative_corrected_info": {}
    })


# ==============================
# API helpers
# ==============================
def verify_user_details(raw_text: str, language: str, logger):
    response = requests.post(
        VERIFY_URL,
        json={
            "user_info": {"raw_text": raw_text},
            "language": language
        },
        timeout=20
    )
    response.raise_for_status()
    return response.json()


def ask_question(payload: dict):
    response = requests.post(ASK_URL, json=payload, timeout=20)
    response.raise_for_status()
    return response.json()


# ==============================
# UI Components
# ==============================
def render_language_selector():
    language = st.radio(
        "Choose output language / בחר שפה:",
        ("English", "Hebrew")
    )
    st.session_state.language = language.lower()


def render_user_info_collection(logger):
    st.markdown(
        "### Personal Information\n"
        "Please enter **all details in one box**, separated by **new lines**:\n\n"
        "- First name (letters only)\n"
        "- Last name (letters only)\n"
        "- ID number (9 digits)\n"
        "- Gender\n"
        "- Age (0–120)\n"
        "- HMO name (מכבי | מאוחדת | כללית)\n"
        "- HMO card number (9 digits)\n"
        "- Insurance membership tier (זהב | כסף | ארד)\n\n"
        "**Example:**\n"
        "```\n"
        "John\nDoe\n123456789\nMale\n30\nמכבי\n987654321\nזהב\n"
        "```"
    )

    user_text = st.text_area(
        "Enter your details / הזן את הפרטים שלך",
        value=st.session_state.user_input_attempt["text"]
    )

    if st.button("Submit / אשר"):
        st.session_state.user_input_attempt["text"] = user_text

        try:
            verify_data = verify_user_details(
                raw_text=user_text,
                language=st.session_state.language,
                logger=logger
            )

            all_correct = verify_data.get("all_correct", False)
            corrected_info = verify_data.get("corrected_info", {})
            missing_fields = verify_data.get("missing_fields", [])

            # Merge cumulative corrected info
            st.session_state.user_input_attempt["cumulative_corrected_info"].update(corrected_info)

            if all_correct:
                st.session_state.user_info = st.session_state.user_input_attempt["cumulative_corrected_info"]
                st.success("All details are valid! You can now ask questions.")
                logger.info("User info verified: %s", st.session_state.user_info)
                st.rerun()
            else:
                st.warning(
                    f"**Please correct the following fields:** {', '.join(missing_fields)}\n\n"
                    "Edit your input above, include **all personal details**, "
                    "each on a **new line**, and submit again."
                )
                logger.info(
                    "Partial user info collected: %s",
                    st.session_state.user_input_attempt["cumulative_corrected_info"]
                )

        except requests.RequestException as e:
            st.error("Failed to verify user details (server error)")
            logger.exception("Verification request failed", exc_info=e)

        except Exception as e:
            st.error("Invalid response from server")
            logger.exception("Verification parsing failed", exc_info=e)


def render_chat_ui(logger):
    question = st.text_input("Ask a question / שאל שאלה")

    if st.button("Send / שלח"):
        if not question.strip():
            st.error("Please enter a question / אנא הזן שאלה")
            return

        payload = {
            "user_info": st.session_state.user_info,
            "question": question,
            "conversation_history": st.session_state.conversation_history,
            "language": st.session_state.language
        }

        try:
            data = ask_question(payload)
            answer = data.get("answer", "")

            st.session_state.conversation_history.append({
                "user": question,
                "bot": answer
            })

            for turn in st.session_state.conversation_history:
                st.markdown(f"**User:** {turn['user']}")
                if st.session_state.language == "hebrew":
                    st.markdown(
                        f"<div dir='rtl'><b>Bot:</b> {turn['bot']}</div>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(f"**Bot:** {turn['bot']}")

            logger.info("Question answered successfully")

        except Exception as e:
            st.error("Failed to get answer from server")
            logger.exception("Ask API failed", exc_info=e)


# ==============================
# App Entry Point
# ==============================
def main():
    setup_debugging()
    logger = setup_logging()
    init_session_state()

    st.title("Medical Services Chatbot")

    render_language_selector()

    if not st.session_state.user_info:
        render_user_info_collection(logger)
    else:
        render_chat_ui(logger)


if __name__ == "__main__":
    main()
