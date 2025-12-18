import os
import shutil
import time
import streamlit as st
import requests
from logging_config import setup_logging
import logging

# ==============================
# Configuration
# ==============================
VERIFY_URL = "http://localhost:8000/verify_user_details"
ASK_URL = "http://localhost:8000/ask"
LOGS_DIR = "logs_part2"  # same as in logging_config


# ==============================
# Helper: Clear old logs
# ==============================
def clear_front_logs(logs_dir: str = "logs_part2", retries: int = 3, delay: float = 0.5):
    """
    Remove only log files containing 'front' in their name.
    Ensures logging handlers are removed before deletion.
    """
    if not os.path.exists(logs_dir):
        return

    for filename in os.listdir(logs_dir):
        if "front" in filename.lower():
            file_path = os.path.join(logs_dir, filename)

            # Remove handlers that use this file
            for handler in logging.root.handlers[:]:
                if hasattr(handler, "baseFilename") and handler.baseFilename == os.path.abspath(file_path):
                    logging.root.removeHandler(handler)
                    handler.close()

            # Retry deletion
            for i in range(retries):
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Removed log file: {file_path}")
                    break
                except Exception as e:
                    if i < retries - 1:
                        time.sleep(delay)
                    else:
                        print(f"Failed to remove {file_path}: {e}")


# ==============================
# Helpers
# ==============================
def setup_debugging(enable=False, host="localhost", port=5679, suspend=False):
    """Enable PyCharm remote debugging if enable=True."""
    if enable:
        try:
            import pydevd_pycharm
            pydevd_pycharm.settrace(
                host,
                port=port,
                stdout_to_server=True,
                stderr_to_server=True,
                suspend=suspend
            )
            print(f"PyCharm debugger attached to {host}:{port}")
        except ImportError:
            print("pydevd_pycharm module not found. Install PyCharm debug egg first.")
        except Exception as e:
            print(f"Failed to attach PyCharm debugger: {e}")


def init_session_state():
    st.session_state.setdefault("user_info", {})
    st.session_state.setdefault("conversation_history", [])
    st.session_state.setdefault("language", "english")
    st.session_state.setdefault("user_input_attempt", {"text": "", "cumulative_corrected_info": {}})


# ==============================
# API helpers
# ==============================
def verify_user_details(raw_text: str, language: str, logger):
    response = requests.post(
        VERIFY_URL,
        json={"user_info": {"raw_text": raw_text}, "language": language},
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
    language = st.radio("Choose output language / בחר שפה:", ("English", "Hebrew"))
    st.session_state.language = language.lower()


def render_user_info_collection(logger):
    st.markdown(
        "### Personal Information\n"
        "Enter **all details in one box**, separated by **new lines**:\n"
        "- First name\n- Last name\n- ID number\n- Gender\n- Age\n- HMO name\n- HMO card number\n- Insurance tier\n"
        "**Example:**\n```\nJohn\nDoe\n123456789\nMale\n30\nמכבי\n987654321\nזהב\n```"
    )

    # Always read from session state and start empty if not set
    user_text = st.text_area(
        "Enter your details / הזן את הפרטים שלך",
        value=st.session_state.get("user_input_box", ""),
        key="user_input_box"
    )

    if st.button("Submit / אשר"):
        user_text = st.session_state.user_input_box  # current input

        try:
            verify_data = verify_user_details(
                raw_text=user_text,
                language=st.session_state.language,
                logger=logger
            )
            all_correct = verify_data.get("all_correct", False)
            corrected_info = verify_data.get("corrected_info", {})
            missing_fields = verify_data.get("missing_fields", [])

            if all_correct:
                st.session_state.user_info = corrected_info
                st.success("All details are valid! You can now ask questions.")
                logger.info("User info verified: %s", corrected_info)

                # Clear the stored input for the next run
                del st.session_state["user_input_box"]
                st.rerun()

            else:
                st.warning(
                    f"**Please correct the following fields:** {', '.join(missing_fields)}"
                )
                logger.info("User info validation failed. Missing fields: %s", missing_fields)

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
            st.session_state.conversation_history.append({"user": question, "bot": answer})

            for turn in st.session_state.conversation_history:
                st.markdown(f"**User:** {turn['user']}")
                if st.session_state.language == "hebrew":
                    st.markdown(f"<div dir='rtl'><b>Bot:</b> {turn['bot']}</div>", unsafe_allow_html=True)
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

    # Clear old logs first
    clear_front_logs(LOGS_DIR)

    # Use backend logging config but log to front-end log file
    logger = setup_logging(log_file="part2_app_front.log")

    init_session_state()

    st.title("Medical Services Chatbot")

    render_language_selector()

    if not st.session_state.user_info:
        render_user_info_collection(logger)
    else:
        render_chat_ui(logger)


if __name__ == "__main__":
    main()
