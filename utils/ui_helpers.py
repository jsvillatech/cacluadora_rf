import streamlit as st


def display_errors(errors, placeholders):
    """Updates error placeholders dynamically based on the errors dictionary."""
    for key, placeholder in placeholders.items():
        placeholder.error(errors[key]) if key in errors else placeholder.empty()
