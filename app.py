#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
# Name........: app.py
# Author......: Stefan Oehrli (oes) stefan.oehrli@oradba.ch
# Editor......: Stefan Oehrli
# Date........: 2024-12-09
# Version.....: v1.0.0
# Purpose.....: SOLA History - Streamlit web application for relay race analytics.
#               Provides interactive visualizations, runner profiles, team planning,
#               and historical race data analysis.
# Requires....: Python >=3.11, streamlit, pandas, altair, fpdf (optional)
# License.....: Apache License Version 2.0
# ------------------------------------------------------------------------------

"""
SOLA History - Internal Analytics Web Application

A comprehensive Streamlit application for analyzing historical SOLA relay race data.
Provides multi-tab interface for year overviews, runner details, team planning,
and data visualization.

Features:
  - Password-protected access
  - Multi-language support (English/German)
  - Interactive data filters and visualizations
  - Runner profile management with overrides
  - Team planning and PDF export
  - Historical statistics and highlights
  - Admin interface for data management

Environment Variables:
  SOLA_APP_PASSWORD - Application password (default: 'sola')

Data Structure:
  Requires JSON files in data/processed/:
    - races.json    : Race events by year
    - legs.json     : Race stages/legs
    - teams.json    : Participating teams
    - runners.json  : Runner profiles
    - results.json  : Individual race results
    - runners_overrides.json : Optional runtime overrides

Usage:
  streamlit run app.py
  # With custom password:
  SOLA_APP_PASSWORD=secret123 streamlit run app.py
"""

import json
import locale
import os
from datetime import date, datetime, time, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Optional

import logging

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

import altair as alt
import pandas as pd
import streamlit as st

# ==============================================================================
# LOGGING CONFIGURATION
# ==============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# ==============================================================================
# CONFIGURATION CONSTANTS
# ==============================================================================

# Base directory (application root)
BASE_DIR: Path = Path(__file__).resolve().parent

# Directory containing processed JSON data files
DATA_DIR: Path = BASE_DIR / "data" / "processed"

# Application password from environment variable
APP_PASSWORD: str = os.environ.get("SOLA_APP_PASSWORD", "sola")

# Runner overrides file for runtime modifications
RUNNER_OVERRIDES_FILE: Path = DATA_DIR / "runners_overrides.json"

# Locales directory for translation files
LOCALES_DIR: Path = BASE_DIR / "locales"

# Supported languages for UI
SUPPORTED_LANGS: list[str] = ["en", "de", "ch", "pirate"]

# ==============================================================================
# AUTHENTICATION
# ==============================================================================

def check_password() -> None:
    """
    Simple password protection using Streamlit session state.

    Displays password input field and validates against APP_PASSWORD.
    Stops application execution if password is incorrect or not entered.
    Uses session state to persist authentication across page interactions.

    Session State:
        password_ok (bool): True if correct password entered
        password (str): User-entered password

    Exits:
        st.stop() if password not correct

    Example:
        >>> check_password()  # Shows password prompt if not authenticated
    """

    def password_entered():
        """Callback to validate entered password."""
        if st.session_state["password"] == APP_PASSWORD:
            st.session_state["password_ok"] = True
            logger.info("User authenticated successfully")
        else:
            st.session_state["password_ok"] = False
            logger.warning("Failed authentication attempt")

    if "password_ok" not in st.session_state:
        st.text_input(
            t("password_label"),
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.stop()
    elif not st.session_state["password_ok"]:
        st.text_input(
            t("password_label"),
            type="password",
            on_change=password_entered,
            key="password",
        )
        st.error(t("password_incorrect"))
        st.stop()


# ==============================================================================
# DATA LOADING & MANIPULATION
# ==============================================================================

def build_overrides_export_df(runners_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge override data with runner base data for export.

    Creates a DataFrame suitable for export that combines base runner data
    with any override values, preferring override values when available.

    Args:
        runners_df: Base DataFrame containing runner data

    Returns:
        DataFrame with merged base and override data, or empty DataFrame
        if no overrides exist

    Example:
        >>> runners = pd.DataFrame({'runner_id': ['R1'], 'active': [True]})
        >>> export_df = build_overrides_export_df(runners)
        >>> 'runner_id' in export_df.columns
        True
    """
    overrides = load_runner_overrides()
    if not overrides:
        return pd.DataFrame()

    ov_df = pd.DataFrame.from_dict(overrides, orient="index")
    ov_df.index.name = "runner_id"
    ov_df.reset_index(inplace=True)

    base_cols = [
        "runner_id",
        "first_name",
        "last_name",
        "company",
        "email",
        "mobile",
        "street",
        "zip_code",
        "city",
        "country",
        "gender",
        "birth_year",
        "default_pace_sec",
        "preferred_distance",
        "favorite_stage",
        "tshirt_size",
        "food_preference",
        "active",
        "notes",
    ]
    base = runners_df.reindex(columns=base_cols)

    merged = base.merge(ov_df, on="runner_id", how="right", suffixes=("", "_ov"))

    # For export: prefer override values, fallback to base values
    out_rows = []
    for _, row in merged.iterrows():
        def val(col):
            ov_col = f"{col}_ov"
            if ov_col in row and not pd.isna(row[ov_col]):
                return row[ov_col]
            return row.get(col, None)

        out_rows.append(
            {
                "runner_id": row["runner_id"],
                "first_name": val("first_name"),
                "last_name": val("last_name"),
                "company": val("company"),
                "email": val("email"),
                "mobile": val("mobile"),
                "street": val("street"),
                "zip_code": val("zip_code"),
                "city": val("city"),
                "country": val("country"),
                "gender": val("gender"),
                "birth_year": val("birth_year"),
                "default_pace_sec": val("default_pace_sec"),
                "preferred_distance": val("preferred_distance"),
                "favorite_stage": val("favorite_stage"),
                "tshirt_size": val("tshirt_size"),
                "food_preference": val("food_preference"),
                "active": val("active"),
                "notes": val("notes"),
            }
        )

    return pd.DataFrame(out_rows)

def load_json(name: str) -> pd.DataFrame:
    """
    Load JSON file and convert to pandas DataFrame.

    Args:
        name: Base filename without .json extension (e.g., 'races', 'runners')

    Returns:
        DataFrame with loaded data, or empty DataFrame on error

    Example:
        >>> races_df = load_json('races')
        >>> 'year' in races_df.columns  # doctest: +SKIP
        True
    """
    path = DATA_DIR / f"{name}.json"
    if not path.exists():
        logger.error(f"Missing data file: {path}")
        st.error(f"Missing data file: {path}")
        return pd.DataFrame()

    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"Loaded {len(data)} records from {name}.json")
        return pd.DataFrame(data)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {path}: {e}")
        st.error(f"Invalid JSON in {path}: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading {path}: {e}")
        st.error(f"Error loading {path}: {e}")
        return pd.DataFrame()


# ==============================================================================
# FORMATTING UTILITIES
# ==============================================================================

def format_seconds_to_hms(seconds: Any) -> str:
    """
    Convert seconds to H:MM:SS or HH:MM:SS format.

    Args:
        seconds: Number of seconds (numeric or None)

    Returns:
        Formatted time string, or empty string if invalid/zero

    Example:
        >>> format_seconds_to_hms(3665)
        '1:01:05'
        >>> format_seconds_to_hms(None)
        ''
        >>> format_seconds_to_hms(0)
        ''
    """
    if seconds is None or pd.isna(seconds):
        return ""
    try:
        seconds = int(round(float(seconds)))
    except (ValueError, TypeError):
        return ""
    if seconds <= 0:
        return ""
    return str(timedelta(seconds=seconds))


def format_pace(sec_per_km: Any) -> str:
    """
    Format pace as MM:SS min/km.

    Args:
        sec_per_km: Seconds per kilometer (numeric or None)

    Returns:
        Formatted pace string (e.g., '05:30 min/km'), or empty string if invalid

    Example:
        >>> format_pace(330)
        '05:30 min/km'
        >>> format_pace(None)
        ''
        >>> format_pace(-5)
        ''
    """
    if sec_per_km is None or pd.isna(sec_per_km):
        return ""
    try:
        sec = float(sec_per_km)
    except (ValueError, TypeError):
        return ""
    if sec <= 0:
        return ""
    minutes = int(sec // 60)
    seconds = int(round(sec % 60))
    return f"{minutes:02d}:{seconds:02d} min/km"


def apply_runner_filter(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    """
    Filter runners DataFrame by active status.

    Args:
        df: DataFrame containing runner data
        mode: Filter mode - 'All', 'Active only', or 'Inactive only'

    Returns:
        Filtered DataFrame. Returns unfiltered if 'active' column missing.

    Example:
        >>> df = pd.DataFrame({'runner_id': ['R1', 'R2'], 'active': [True, False]})
        >>> filtered = apply_runner_filter(df, 'Active only')
        >>> len(filtered)
        1
    """
    if "active" not in df.columns:
        return df

    if mode == t("filter_runners_active"):
        return df[df["active"] == True]
    if mode == t("filter_runners_inactive"):
        return df[df["active"] == False]
    return df


# ==============================================================================
# RUNNER OVERRIDES MANAGEMENT
# ==============================================================================

def load_runner_overrides() -> Dict[str, Dict[str, Any]]:
    """
    Load runner override data from JSON file.

    Overrides allow runtime modifications to runner data (active status,
    pace, preferences, etc.) without changing the base data files.

    Returns:
        Dictionary mapping runner_id to override fields, or empty dict
        if file doesn't exist or is invalid

    Example:
        >>> overrides = load_runner_overrides()
        >>> isinstance(overrides, dict)
        True
    """
    if not RUNNER_OVERRIDES_FILE.exists():
        logger.debug("No runner overrides file found")
        return {}
    try:
        with RUNNER_OVERRIDES_FILE.open(encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            logger.info(f"Loaded {len(data)} runner overrides")
            return data
        logger.warning(f"Invalid format in {RUNNER_OVERRIDES_FILE}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in overrides file: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading overrides: {e}")
        return {}


# ==============================================================================
# PDF EXPORT
# ==============================================================================

def plan_df_to_pdf_bytes(plan_df: pd.DataFrame, title: str = "SOLA Plan") -> bytes:
    """
    Generate PDF from planning DataFrame.

    Creates a simple PDF table from the provided DataFrame. Requires fpdf
    package to be installed.

    Args:
        plan_df: DataFrame containing planning data
        title: PDF document title (default: 'SOLA Plan')

    Returns:
        PDF as bytes, or empty bytes if fpdf not available

    Example:
        >>> df = pd.DataFrame({'Name': ['Alice'], 'Leg': [1]})
        >>> pdf_bytes = plan_df_to_pdf_bytes(df)
        >>> isinstance(pdf_bytes, bytes)
        True
    """
    if not HAS_FPDF:
        logger.warning("fpdf not installed, cannot generate PDF")
        return b""

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, title, ln=True)

    pdf.set_font("Arial", size=9)

    # Simple table with fixed column widths
    col_widths = []
    for col in plan_df.columns:
        col_widths.append(25)  # Fixed width, adjust if needed

    pdf.ln(5)
    for i, col in enumerate(plan_df.columns):
        pdf.cell(col_widths[i], 6, txt=str(col)[:20], border=1)
    pdf.ln(6)

    # Rows
    for _, row in plan_df.iterrows():
        for i, col in enumerate(plan_df.columns):
            txt = str(row[col])[:20]
            pdf.cell(col_widths[i], 6, txt=txt, border=1)
        pdf.ln(6)

    # fpdf output(dest="S") returns a latin-1 encoded string
    return pdf.output(dest="S").encode("latin-1")


def save_runner_overrides(overrides: Dict[str, Dict[str, Any]]) -> None:
    """
    Save runner overrides to JSON file.

    Args:
        overrides: Dictionary mapping runner_id to override fields

    Example:
        >>> overrides = {'R1': {'active': False}}
        >>> save_runner_overrides(overrides)  # doctest: +SKIP
    """
    try:
        RUNNER_OVERRIDES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with RUNNER_OVERRIDES_FILE.open("w", encoding="utf-8") as f:
            json.dump(overrides, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(overrides)} runner overrides")
    except Exception as e:
        logger.error(f"Failed to save overrides: {e}")
        st.error(f"Failed to save overrides: {e}")


def apply_runner_overrides_df(runners_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply override data to runners DataFrame.

    Merges override values into the base runner data, replacing base values
    where overrides exist.

    Args:
        runners_df: Base runners DataFrame

    Returns:
        DataFrame with overrides applied

    Example:
        >>> df = pd.DataFrame({'id': ['R1'], 'active': [True]})
        >>> result_df = apply_runner_overrides_df(df)
        >>> 'runner_id' in result_df.columns or 'id' in result_df.columns
        True
    """
    overrides = load_runner_overrides()
    if not overrides:
        return runners_df

    df = runners_df.copy()
    if "runner_id" not in df.columns and "id" in df.columns:
        df = df.rename(columns={"id": "runner_id"})

    for runner_id, fields in overrides.items():
        mask = df["runner_id"] == runner_id
        if not mask.any():
            continue
        for col, val in fields.items():
            if col in df.columns:
                df.loc[mask, col] = val

    return df


@st.cache_data
def load_data() -> Optional[Dict[str, pd.DataFrame]]:
    """
    Load all JSON data files and create merged fact table.

    Loads races, legs, teams, runners, and results from JSON files,
    applies runner overrides, and creates a comprehensive merged DataFrame
    for analysis.

    Returns:
        Dictionary containing:
            - races: DataFrame of race events
            - legs: DataFrame of race stages
            - teams: DataFrame of teams
            - runners: DataFrame of runners (with overrides applied)
            - results: DataFrame of race results
            - merged: Comprehensive fact table joining all data
        Returns None if any required file is missing

    Caching:
        Uses Streamlit @st.cache_data for performance

    Example:
        >>> data = load_data()  # doctest: +SKIP
        >>> 'merged' in data
        True
    """
    races_df = load_json("races")
    legs_df = load_json("legs")
    teams_df = load_json("teams")
    runners_df = load_json("runners")
    results_df = load_json("results")

    if races_df.empty or legs_df.empty or teams_df.empty or runners_df.empty or results_df.empty:
        logger.error("One or more required data files are empty")
        return None

    logger.info("All data files loaded successfully")

    # Normalize ID columns for consistent naming
    races_df = races_df.rename(columns={"id": "race_id"})
    legs_df = legs_df.rename(columns={"id": "leg_id"})
    teams_df = teams_df.rename(columns={"id": "team_id"})
    runners_df = runners_df.rename(columns={"id": "runner_id"})

    # Apply runtime overrides to runner data
    runners_df = apply_runner_overrides_df(runners_df)

    # Merge everything into one big fact table
    merged = (
        results_df.merge(
            runners_df,
            on="runner_id",
            how="left",
            suffixes=("", "_runner"),
        )
        .merge(legs_df, on="leg_id", how="left", suffixes=("", "_leg"))
        .merge(teams_df, on="team_id", how="left", suffixes=("", "_team"))
        .merge(
            races_df[["race_id", "year", "event_name", "num_teams"]],
            on="race_id",
            how="left",
        )
    )

    # Avoid confusing column names
    merged = merged.rename(
        columns={
            "name_team": "team_name",
            "name": "leg_name",  # from legs
        }
    )

    return {
        "races": races_df,
        "legs": legs_df,
        "teams": teams_df,
        "runners": runners_df,
        "results": results_df,
        "merged": merged,
    }

# ==============================================================================
# INTERNATIONALIZATION (i18n)
# ==============================================================================

@st.cache_data
def load_translations() -> Dict[str, Dict[str, str]]:
    """
    Load translation files from locales directory.

    Loads JSON translation files for all supported languages.
    Uses Streamlit caching for performance.

    Returns:
        Dictionary mapping language codes to translation dictionaries
        Falls back to empty dict for each language if file not found

    Example:
        >>> translations = load_translations()
        >>> 'en' in translations
        True
        >>> 'app_title' in translations['en']
        True
    """
    translations: Dict[str, Dict[str, str]] = {}
    
    for lang in SUPPORTED_LANGS:
        locale_file = LOCALES_DIR / f"{lang}.json"
        if not locale_file.exists():
            logger.warning(f"Translation file not found: {locale_file}")
            translations[lang] = {}
            continue
        
        try:
            with locale_file.open(encoding="utf-8") as f:
                translations[lang] = json.load(f)
            logger.info(f"Loaded {len(translations[lang])} translations for '{lang}'")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {locale_file}: {e}")
            translations[lang] = {}
        except Exception as e:
            logger.error(f"Error loading {locale_file}: {e}")
            translations[lang] = {}
    
    return translations


# Fallback translations for critical keys (if JSON files missing)
_FALLBACK_STRINGS: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "🏃‍♂️ Sola History - Internal Analytics",
        "page_title": "Sola History",
        "language_selector": "Language / Sprache",
        "password_label": "Password",
        "password_incorrect": "Incorrect password.",
        "error_load_data": "Could not load data. Please check data/processed/*.json.",
    },
    "de": {
        "app_title": "🏃‍♂️ Sola History - Interne Auswertungen",
        "page_title": "Sola History",
        "language_selector": "Language / Sprache",
        "password_label": "Passwort",
        "password_incorrect": "Falsches Passwort.",
        "error_load_data": "Daten konnten nicht geladen werden. Bitte data/processed/*.json prüfen.",
    },
}


def detect_default_lang() -> str:
    """
    Detect default language from system environment.

    Checks LANG environment variable and system locale to determine
    appropriate default language.

    Returns:
        Language code: 'de' for German, 'en' for English (default)

    Example:
        >>> lang = detect_default_lang()
        >>> lang in ['en', 'de']
        True
    """
    # Simple heuristic based on system environment
    env_lang = os.environ.get("LANG", "") or locale.getdefaultlocale()[0] or ""
    env_lang = env_lang.lower()
    if env_lang.startswith("de"):
        return "de"
    return "en"


def get_lang() -> str:
    """
    Get current UI language from session state.

    Returns:
        Current language code ('en' or 'de')

    Example:
        >>> lang = get_lang()  # doctest: +SKIP
        >>> lang in SUPPORTED_LANGS
        True
    """
    if "lang" in st.session_state:
        return st.session_state["lang"]
    # Set default on first access
    st.session_state["lang"] = detect_default_lang()
    return st.session_state["lang"]


def t(key: str) -> str:
    """
    Translate UI string key to current language.

    Loads translations from JSON files in locales/ directory.
    Falls back to English if key not found, then to fallback strings,
    then returns the key itself.

    Args:
        key: Translation key from translation files

    Returns:
        Translated string, or key itself if translation not found

    Example:
        >>> t('app_title')  # doctest: +SKIP
        '🏃\u200d♂️ Sola History - Internal Analytics'
    """
    lang = get_lang()
    translations = load_translations()
    
    # Try current language
    if lang in translations and key in translations[lang]:
        return translations[lang][key]
    
    # Fallback to English
    if "en" in translations and key in translations["en"]:
        return translations["en"][key]
    
    # Fallback to hardcoded strings (critical keys only)
    if lang in _FALLBACK_STRINGS and key in _FALLBACK_STRINGS[lang]:
        return _FALLBACK_STRINGS[lang][key]
    
    if key in _FALLBACK_STRINGS.get("en", {}):
        return _FALLBACK_STRINGS["en"][key]
    
    # Last resort: return the key itself
    return key

# ==============================================================================
# MAIN STREAMLIT APPLICATION
# ==============================================================================

def main() -> None:
    """
    Main entry point for Streamlit application.

    Orchestrates the entire application flow:
      1. Configure page settings
      2. Authenticate user
      3. Load data
      4. Render UI with tabs and filters
      5. Handle user interactions

    Example:
        Run via command line:
        $ streamlit run app.py
    """
    # MUST be first Streamlit command - before any session_state access
    st.set_page_config(page_title="Sola History", layout="wide")
    
    check_password()

    # Language selection in sidebar (small select)
    with st.sidebar:
        lang_default = get_lang()
        
        def format_language(lang_code: str) -> str:
            """Format language code for display."""
            lang_names = {
                "en": "English",
                "de": "Deutsch",
                "ch": "Bärndütsch",
                "pirate": "🏴‍☠️ Pirate"
            }
            return lang_names.get(lang_code, lang_code)
        
        lang = st.selectbox(
            t("language_selector"),
            options=SUPPORTED_LANGS,
            format_func=format_language,
            index=SUPPORTED_LANGS.index(lang_default),
        )
        st.session_state["lang"] = lang

    st.title(t("app_title"))
            
    data = load_data()
    if data is None:
        st.error(t("error_load_data"))
        return

    races_df = data["races"]
    legs_df = data["legs"]
    teams_df = data["teams"]
    runners_df = data["runners"]
    merged = data["merged"]

    # -------------------------------------------------------------------
    # Sidebar filters
    # -------------------------------------------------------------------
    st.sidebar.header("Filters")

    # Global runner filter
    runner_filter_mode = st.sidebar.radio(
        t("filter_runners"),
        options=[t("filter_runners_all"), t("filter_runners_active"), t("filter_runners_inactive")],
        index=0,
        help=t("filter_runners_help"),
    )

    # Year filter (for Year view) - default = newest year
    years = sorted(races_df["year"].unique())
    if years:
        default_year_index = len(years) - 1  # newest year
    else:
        default_year_index = 0

    selected_year = st.sidebar.selectbox(
        t("filter_year"), years, index=default_year_index if years else 0
    )

    # Pre-filtered DF for the selected year (for sidebar)
    year_df_for_sidebar = merged[merged["year"] == selected_year].copy()

    # Team selector (Year view only)
    teams_in_year = (
        year_df_for_sidebar[["team_id", "team_name"]]
        .drop_duplicates()
        .sort_values("team_name")
    )
    team_options = [t("option_all_teams")] + [
        f"{row['team_name']} (#{row['team_id'].split('-')[-1]})"
        for _, row in teams_in_year.iterrows()
    ]
    selected_team_label = st.sidebar.selectbox(t("filter_team"), team_options)

    # Runner selector (Year view only, independent from global active filter)
    runners_in_year = (
        year_df_for_sidebar[["runner_id", "first_name", "last_name"]]
        .drop_duplicates()
        .sort_values(["last_name", "first_name"])
    )
    runner_options_year = [t("option_all_runners")] + [
        f"{row['first_name']} {row['last_name']} ({row['runner_id']})"
        for _, row in runners_in_year.iterrows()
    ]
    selected_runner_label_year = st.sidebar.selectbox(
        t("filter_runner_year"),
        runner_options_year,
    )

    # -------------------------------------------------------------------
    # Tabs
    # -------------------------------------------------------------------
    (
        tab_year,
        tab_runner,
        tab_overview,
        tab_highlights,
        tab_planning,
        tab_admin,
    ) = st.tabs(
        [
            t("tab_year"),
            t("tab_runner"),
            t("tab_overview"),
            t("tab_highlights"),
            t("tab_planning"),
            t("tab_admin"),
        ]
    )


    # -------------------------------------------------------------------
    # TAB: Year overview
    # -------------------------------------------------------------------
    with tab_year:
        st.subheader(f"{t('year_overview_title')} - {selected_year}")

        year_df = merged[merged["year"] == selected_year].copy()

        # Apply team filter (Year tab only)
        if selected_team_label != t("option_all_teams"):
            team_suffix = selected_team_label.split("#")[-1].rstrip(")")
            year_df = year_df[year_df["team_id"].str.endswith(team_suffix)]

        # Apply runner filter (Year tab only)
        if selected_runner_label_year != t("option_all_runners"):
            rid = selected_runner_label_year.split("(")[-1].rstrip(")")
            year_df = year_df[year_df["runner_id"] == rid]

        num_teams = year_df["team_id"].nunique()
        num_runners = year_df["runner_id"].nunique()
        num_legs = year_df["leg_id"].nunique()
        total_km = year_df["distance_km"].fillna(0).sum()

        valid_paces = year_df["ind_pace_sec_per_km"].dropna()
        avg_pace = valid_paces.mean() if not valid_paces.empty else None

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric(t("metric_teams"), num_teams)
        c2.metric(t("metric_runners"), num_runners)
        c3.metric(t("metric_stages"), num_legs)
        c4.metric(t("metric_distance"), f"{total_km:.1f} km")
        c5.metric(
            t("metric_avg_pace"),
            format_pace(avg_pace) if avg_pace else "-",
        )

        num_teams_total = year_df["num_teams"].dropna().unique()
        if len(num_teams_total) == 1:
            st.caption(
                f"Total of {int(num_teams_total[0])} teams were registered in {selected_year}."
            )

        st.markdown(t("charts_title"))

        col_chart1, col_chart2 = st.columns(2)

        # Distance per leg
        with col_chart1:
            st.caption(t("chart_stage_distances"))
            dist_per_leg = (
                year_df[["leg_number", "leg_name", "distance_km"]]
                .drop_duplicates()
                .sort_values("leg_number")
            )
            if not dist_per_leg.empty:
                chart = (
                    alt.Chart(dist_per_leg)
                    .mark_bar()
                    .encode(
                        x=alt.X("leg_number:O", title="Stage"),
                        y=alt.Y("distance_km:Q", title="Distance (km)"),
                        tooltip=["leg_number", "leg_name", "distance_km"],
                    )
                )
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info(t("info_no_stage_data"))

        # Team rank over legs (if exactly one team selected)
        with col_chart2:
            st.caption(t("chart_team_ranks"))
            teams_in_filtered = year_df["team_id"].nunique()
            if teams_in_filtered == 1:
                rank_df = (
                    year_df[["leg_number", "team_rank_after_leg"]]
                    .dropna()
                    .sort_values("leg_number")
                )
                if not rank_df.empty:
                    chart = (
                        alt.Chart(rank_df)
                        .mark_line(point=True)
                        .encode(
                            x=alt.X("leg_number:O", title="Stage"),
                            y=alt.Y(
                                "team_rank_after_leg:Q",
                                title="Team rank",
                                sort="descending",
                            ),
                            tooltip=["leg_number", "team_rank_after_leg"],
                        )
                    )
                    st.altair_chart(chart, use_container_width=True)
                else:
                    st.info(t("info_no_team_rank_data"))
            else:
                st.info(t("info_select_team"))

        st.markdown(t("results_title"))

        table_df = pd.DataFrame()
        table_df["Year"] = year_df["year"].astype("int").astype("string")
        table_df["Team"] = year_df["team_name"]
        table_df["Bib #"] = year_df["bib_number"]
        table_df["Stage"] = year_df["leg_number"]
        table_df["Stage name"] = year_df["leg_name"]
        table_df["Distance (km)"] = year_df["distance_km"]
        table_df["First name"] = year_df["first_name"]
        table_df["Last name"] = year_df["last_name"]
        table_df["Runner company"] = year_df["company"]
        table_df["External"] = year_df["is_external"].map(
            {True: "Yes", False: "No"}
        )

        table_df["Individual rank"] = year_df["ind_rank_leg"]
        table_df["Individual time"] = year_df["ind_time_seconds"].apply(
            format_seconds_to_hms
        )
        table_df["Individual pace"] = year_df["ind_pace_sec_per_km"].apply(
            format_pace
        )

        table_df["Team rank after stage"] = year_df["team_rank_after_leg"]
        table_df["Team time after stage"] = year_df[
            "team_time_after_leg_seconds"
        ].apply(format_seconds_to_hms)
        table_df["Team pace after stage"] = year_df[
            "team_pace_after_leg_sec_per_km"
        ].apply(format_pace)

        table_df = table_df.sort_values(["Team", "Stage"])
        st.dataframe(table_df, use_container_width=True)

    # -------------------------------------------------------------------
    # TAB: Runner details
    # -------------------------------------------------------------------
    with tab_runner:
        st.subheader(t("runner_details_title"))

        # Apply global active filter to runner list
        runners_filtered = apply_runner_filter(runners_df, runner_filter_mode)
        runners_sorted = (
            runners_filtered.sort_values(["last_name", "first_name"])
            .reset_index(drop=True)
        )

        runner_options_global = [
            f"{row['first_name']} {row['last_name']} ({row['runner_id']})"
            for _, row in runners_sorted.iterrows()
        ]

        selected_runner_label = st.selectbox(
            t("select_runner"),
            ["(please select)"] + runner_options_global,
        )

        if selected_runner_label != "(please select)":
            selected_runner_id = selected_runner_label.split("(")[-1].rstrip(")")
            runner_info = runners_df[
                runners_df["runner_id"] == selected_runner_id
            ].iloc[0]

            st.markdown(t("runner_profile_title"))

            col_a, col_b = st.columns(2)

            # Left: base info
            with col_a:
                st.markdown(
                    f"""
                    **{runner_info['first_name']} {runner_info['last_name']}**  
                    ID: `{runner_info['runner_id']}`  
                    Company: {runner_info.get('company') or '-'}  
                    External: {'Yes' if runner_info.get('is_external') else 'No'}  
                    Active: {'Yes' if runner_info.get('active') else 'No'}  
                    Gender: {runner_info.get('gender') or '-'}  
                    Birth year: {runner_info.get('birth_year') or '-'}
                    """
                )

            # Right: address, contact, preferences
            with col_b:
                addr_parts = []
                street = runner_info.get("street")
                zip_code = runner_info.get("zip_code")
                city = runner_info.get("city")
                country = runner_info.get("country")

                if street:
                    addr_parts.append(street)
                if zip_code or city:
                    addr_parts.append(f"{zip_code or ''} {city or ''}".strip())
                if country:
                    addr_parts.append(country)

                address_str = "<br>".join(addr_parts) if addr_parts else "-"

                email = runner_info.get("email")
                mobile = runner_info.get("mobile")
                external_ids = runner_info.get("external_ids") or {}
                strava = external_ids.get("strava")

                food_pref = runner_info.get("food_preference") or "-"
                tshirt = runner_info.get("tshirt_size") or "-"

                default_pace = runner_info.get("default_pace_sec")
                default_pace_str = (
                    format_pace(default_pace) if default_pace else "-"
                )
                pref_dist = runner_info.get("preferred_distance") or "-"
                fav_stage = runner_info.get("favorite_stage") or "-"

                st.markdown(
                    f"""
                    **Address**  
                    {address_str}  

                    **Contact**  
                    Email: {email or '-'}  
                    Mobile: {mobile or '-'}  
                    Strava: {strava or '-'}  

                    **Preferences**  
                    Default pace: {default_pace_str}  
                    Preferred distance: {pref_dist}  
                    Favourite stage: {fav_stage}  
                    T-shirt size: {tshirt}  
                    Food preference: {food_pref}
                    """,
                    unsafe_allow_html=True,
                )

            # All runs of this runner
            runner_runs = merged[merged["runner_id"] == selected_runner_id].copy()
            if runner_runs.empty:
                st.info(t("info_no_runs"))
            else:
                # Stats
                total_runs = runner_runs["leg_id"].nunique()
                total_years = runner_runs["year"].nunique()
                total_km_runner = runner_runs["distance_km"].sum()
                best_rank_stage = runner_runs["ind_rank_leg"].min()
                best_team_rank_stage = runner_runs["team_rank_after_leg"].min()

                # Best final team rank (from teams table)
                teams_for_runner = (
                    runner_runs[["team_id", "year"]]
                    .drop_duplicates()
                    .merge(
                        teams_df[["team_id", "name", "rank_final"]],
                        on="team_id",
                        how="left",
                    )
                )
                teams_with_final_rank = teams_for_runner[
                    teams_for_runner["rank_final"].notna()
                ]
                best_final_rank = None
                best_final_team_name = None
                best_final_year = None
                if not teams_with_final_rank.empty:
                    idx = teams_with_final_rank["rank_final"].idxmin()
                    row_best = teams_with_final_rank.loc[idx]
                    best_final_rank = int(row_best["rank_final"])
                    best_final_team_name = row_best["name"]
                    best_final_year = int(row_best["year"])

                c1, c2, c3, c4, c5 = st.columns(5)
                c1.metric("Stage starts", total_runs)
                c2.metric("Years", total_years)
                c3.metric("Total distance", f"{total_km_runner:.1f} km")
                c4.metric(
                    "Best individual rank",
                    int(best_rank_stage) if pd.notna(best_rank_stage) else "-",
                )
                c5.metric(
                    "Best team rank after stage",
                    int(best_team_rank_stage)
                    if pd.notna(best_team_rank_stage)
                    else "-",
                )

                if best_final_rank is not None:
                    st.caption(
                        f"Best **final team rank**: {best_final_rank} "
                        f"with team *{best_final_team_name}* in {best_final_year}."
                    )

                # All runs table (newest year first)
                st.markdown(t("runner_all_runs_title"))

                runner_runs_sorted = runner_runs.sort_values(
                    ["year", "leg_number"], ascending=[False, True]
                )

                runner_table = pd.DataFrame()
                runner_table["Year"] = (
                    runner_runs_sorted["year"].astype("int").astype("string")
                )
                runner_table["Team"] = runner_runs_sorted["team_name"]
                runner_table["Bib #"] = runner_runs_sorted["bib_number"]
                runner_table["Stage"] = runner_runs_sorted["leg_number"]
                runner_table["Stage name"] = runner_runs_sorted["leg_name"]
                runner_table["Distance (km)"] = runner_runs_sorted["distance_km"]
                runner_table["Individual rank"] = runner_runs_sorted["ind_rank_leg"]
                runner_table["Individual time"] = runner_runs_sorted[
                    "ind_time_seconds"
                ].apply(format_seconds_to_hms)
                runner_table["Individual pace"] = runner_runs_sorted[
                    "ind_pace_sec_per_km"
                ].apply(format_pace)
                runner_table["Team rank after stage"] = runner_runs_sorted[
                    "team_rank_after_leg"
                ]
                runner_table["Team time after stage"] = runner_runs_sorted[
                    "team_time_after_leg_seconds"
                ].apply(format_seconds_to_hms)

                st.dataframe(runner_table, use_container_width=True)

        # -------------------------------------------------------------------
        # Head-to-Head Comparison
        # -------------------------------------------------------------------
        st.markdown("---")
        st.subheader(t("h2h_title"))

        col_h2h1, col_h2h2, col_h2h3 = st.columns([2, 2, 1])

        with col_h2h1:
            runner1_label = st.selectbox(
                t("h2h_select_runner1"),
                ["(select)"] + runner_options_global,
                key="h2h_runner1",
            )

        with col_h2h2:
            runner2_label = st.selectbox(
                t("h2h_select_runner2"),
                ["(select)"] + runner_options_global,
                key="h2h_runner2",
            )

        if runner1_label != "(select)" and runner2_label != "(select)":
            runner1_id = runner1_label.split("(")[-1].rstrip(")")
            runner2_id = runner2_label.split("(")[-1].rstrip(")")

            if runner1_id == runner2_id:
                st.warning(t("h2h_select_two_runners"))
            else:
                # Get runner info
                r1_info = runners_df[runners_df["runner_id"] == runner1_id].iloc[0]
                r2_info = runners_df[runners_df["runner_id"] == runner2_id].iloc[0]

                r1_name = f"{r1_info['first_name']} {r1_info['last_name']}"
                r2_name = f"{r2_info['first_name']} {r2_info['last_name']}"

                # Get all runs for both runners
                r1_runs = merged[merged["runner_id"] == runner1_id].copy()
                r2_runs = merged[merged["runner_id"] == runner2_id].copy()

                # Career statistics comparison
                st.markdown(f"### {t('h2h_career_stats')}")

                # Calculate stats for runner 1
                r1_total_runs = r1_runs["leg_id"].nunique()
                r1_total_years = r1_runs["year"].nunique()
                r1_total_km = r1_runs["distance_km"].sum()
                r1_avg_pace = r1_runs["ind_pace_sec_per_km"].mean()
                r1_best_rank = r1_runs["ind_rank_leg"].min()

                # Best final team rank for runner 1
                r1_teams = r1_runs[["team_id", "year"]].drop_duplicates().merge(
                    teams_df[["team_id", "rank_final"]], on="team_id", how="left"
                )
                r1_best_team_rank = r1_teams["rank_final"].min() if not r1_teams["rank_final"].isna().all() else None

                # Calculate stats for runner 2
                r2_total_runs = r2_runs["leg_id"].nunique()
                r2_total_years = r2_runs["year"].nunique()
                r2_total_km = r2_runs["distance_km"].sum()
                r2_avg_pace = r2_runs["ind_pace_sec_per_km"].mean()
                r2_best_rank = r2_runs["ind_rank_leg"].min()

                # Best final team rank for runner 2
                r2_teams = r2_runs[["team_id", "year"]].drop_duplicates().merge(
                    teams_df[["team_id", "rank_final"]], on="team_id", how="left"
                )
                r2_best_team_rank = r2_teams["rank_final"].min() if not r2_teams["rank_final"].isna().all() else None

                # Display side-by-side metrics
                col_r1, col_vs, col_r2 = st.columns([2, 1, 2])

                with col_r1:
                    st.markdown(f"**{r1_name}**")
                    st.metric(t("h2h_metric_starts"), r1_total_runs)
                    st.metric(t("h2h_metric_years"), r1_total_years)
                    st.metric(t("h2h_metric_total_km"), f"{r1_total_km:.1f} km")
                    st.metric(
                        t("h2h_metric_avg_pace"),
                        format_pace(r1_avg_pace) if pd.notna(r1_avg_pace) else "-",
                    )
                    st.metric(
                        t("h2h_metric_best_rank"),
                        int(r1_best_rank) if pd.notna(r1_best_rank) else "-",
                    )
                    st.metric(
                        t("h2h_metric_best_team_rank"),
                        int(r1_best_team_rank) if pd.notna(r1_best_team_rank) else "-",
                    )

                with col_vs:
                    st.markdown("<br>" * 10, unsafe_allow_html=True)
                    st.markdown("### 🆚")

                with col_r2:
                    st.markdown(f"**{r2_name}**")
                    st.metric(t("h2h_metric_starts"), r2_total_runs)
                    st.metric(t("h2h_metric_years"), r2_total_years)
                    st.metric(t("h2h_metric_total_km"), f"{r2_total_km:.1f} km")
                    st.metric(
                        t("h2h_metric_avg_pace"),
                        format_pace(r2_avg_pace) if pd.notna(r2_avg_pace) else "-",
                    )
                    st.metric(
                        t("h2h_metric_best_rank"),
                        int(r2_best_rank) if pd.notna(r2_best_rank) else "-",
                    )
                    st.metric(
                        t("h2h_metric_best_team_rank"),
                        int(r2_best_team_rank) if pd.notna(r2_best_team_rank) else "-",
                    )

                # Direct matchups (same stages in same years)
                st.markdown(f"### {t('h2h_direct_matchups')}")

                # Find common stages (same leg_id)
                r1_stages = r1_runs[["leg_id", "year", "leg_number", "leg_name", "distance_km",
                                      "ind_time_seconds", "ind_pace_sec_per_km", "ind_rank_leg"]].copy()
                r2_stages = r2_runs[["leg_id", "year", "leg_number", "leg_name", "distance_km",
                                      "ind_time_seconds", "ind_pace_sec_per_km", "ind_rank_leg"]].copy()

                # Merge on leg_id to find same stages (regardless of year)
                matchups = r1_stages.merge(
                    r2_stages,
                    on=["leg_id"],
                    suffixes=("_r1", "_r2"),
                    how="inner",
                )

                if matchups.empty:
                    st.info(t("h2h_no_matchups"))
                else:
                    # Calculate wins/losses based on individual time
                    matchups["winner"] = matchups.apply(
                        lambda row: r1_name if row["ind_time_seconds_r1"] < row["ind_time_seconds_r2"]
                        else (r2_name if row["ind_time_seconds_r1"] > row["ind_time_seconds_r2"] else "Tie"),
                        axis=1,
                    )

                    r1_wins = (matchups["winner"] == r1_name).sum()
                    r2_wins = (matchups["winner"] == r2_name).sum()
                    ties = (matchups["winner"] == "Tie").sum()

                    # Display win/loss record
                    col_w1, col_w2, col_w3 = st.columns(3)
                    col_w1.metric(f"{r1_name} {t('h2h_wins')}", r1_wins)
                    col_w2.metric(t("h2h_ties"), ties)
                    col_w3.metric(f"{r2_name} {t('h2h_wins')}", r2_wins)

                    # Detailed matchups table
                    matchup_table = pd.DataFrame()
                    matchup_table["Year (R1)"] = matchups["year_r1"].astype("int").astype("string")
                    matchup_table["Year (R2)"] = matchups["year_r2"].astype("int").astype("string")
                    matchup_table["Stage"] = matchups["leg_number_r1"]
                    matchup_table["Stage name"] = matchups["leg_name_r1"]
                    matchup_table["Distance (km)"] = matchups["distance_km_r1"]
                    matchup_table[f"{r1_name} Time"] = matchups["ind_time_seconds_r1"].apply(
                        format_seconds_to_hms
                    )
                    matchup_table[f"{r1_name} Pace"] = matchups["ind_pace_sec_per_km_r1"].apply(
                        format_pace
                    )
                    matchup_table[f"{r1_name} Rank"] = matchups["ind_rank_leg_r1"]
                    matchup_table[f"{r2_name} Time"] = matchups["ind_time_seconds_r2"].apply(
                        format_seconds_to_hms
                    )
                    matchup_table[f"{r2_name} Pace"] = matchups["ind_pace_sec_per_km_r2"].apply(
                        format_pace
                    )
                    matchup_table[f"{r2_name} Rank"] = matchups["ind_rank_leg_r2"]
                    matchup_table["Winner"] = matchups["winner"]

                    st.dataframe(matchup_table, use_container_width=True)

                # Performance charts
                st.markdown(f"### {t('h2h_performance_comparison')}")

                col_chart1, col_chart2 = st.columns(2)

                # Pace trends over years
                with col_chart1:
                    st.caption(t("h2h_pace_trends"))

                    r1_yearly = (
                        r1_runs.groupby("year")["ind_pace_sec_per_km"]
                        .mean()
                        .reset_index()
                    )
                    r1_yearly["Runner"] = r1_name

                    r2_yearly = (
                        r2_runs.groupby("year")["ind_pace_sec_per_km"]
                        .mean()
                        .reset_index()
                    )
                    r2_yearly["Runner"] = r2_name

                    combined_yearly = pd.concat([r1_yearly, r2_yearly])

                    if not combined_yearly.empty:
                        chart_pace = (
                            alt.Chart(combined_yearly)
                            .mark_line(point=True)
                            .encode(
                                x=alt.X("year:O", title="Year"),
                                y=alt.Y("ind_pace_sec_per_km:Q", title="Avg. Pace (sec/km)"),
                                color=alt.Color("Runner:N", legend=alt.Legend(title="Runner")),
                                tooltip=["year", "Runner", "ind_pace_sec_per_km"],
                            )
                        )
                        st.altair_chart(chart_pace, use_container_width=True)

                # Stage distribution
                with col_chart2:
                    st.caption(t("h2h_stage_distribution"))

                    r1_stage_dist = (
                        r1_runs.groupby("leg_number")
                        .size()
                        .reset_index(name="count")
                    )
                    r1_stage_dist["Runner"] = r1_name

                    r2_stage_dist = (
                        r2_runs.groupby("leg_number")
                        .size()
                        .reset_index(name="count")
                    )
                    r2_stage_dist["Runner"] = r2_name

                    combined_stages = pd.concat([r1_stage_dist, r2_stage_dist])

                    if not combined_stages.empty:
                        chart_stages = (
                            alt.Chart(combined_stages)
                            .mark_bar()
                            .encode(
                                x=alt.X("leg_number:O", title="Stage Number"),
                                y=alt.Y("count:Q", title="Times Run"),
                                color=alt.Color("Runner:N", legend=alt.Legend(title="Runner")),
                                xOffset="Runner:N",
                                tooltip=["leg_number", "Runner", "count"],
                            )
                        )
                        st.altair_chart(chart_stages, use_container_width=True)

    # -------------------------------------------------------------------
    # TAB: Runner overview
    # -------------------------------------------------------------------
    with tab_overview:
        st.subheader(t("overview_title"))

        results_all = merged.copy()
        results_all = apply_runner_filter(results_all, runner_filter_mode)

        runner_stats = (
            results_all.groupby("runner_id")
            .agg(
                first_name=("first_name", "first"),
                last_name=("last_name", "first"),
                company=("company", "first"),
                is_external=("is_external", "first"),
                active=("active", "first"),
                num_runs=("leg_id", "count"),
                num_years=("year", "nunique"),
                total_km=("distance_km", "sum"),
                avg_pace_sec=("ind_pace_sec_per_km", "mean"),
                best_rank=("ind_rank_leg", "min"),
            )
            .reset_index()
        )

        runner_stats["Name"] = (
            runner_stats["first_name"] + " " + runner_stats["last_name"]
        )
        runner_stats["Avg. pace"] = runner_stats["avg_pace_sec"].apply(format_pace)
        runner_stats["External"] = runner_stats["is_external"].map(
            {True: "Yes", False: "No"}
        )
        runner_stats["Active"] = runner_stats["active"].map(
            {True: "Yes", False: "No"}
        )
        runner_stats["total_km"] = runner_stats["total_km"].round(1)

        runner_stats_display = runner_stats[
            [
                "runner_id",
                "Name",
                "company",
                "External",
                "Active",
                "num_runs",
                "num_years",
                "total_km",
                "Avg. pace",
                "best_rank",
            ]
        ].rename(
            columns={
                "company": "Company",
                "num_runs": "Starts",
                "num_years": "Years",
                "total_km": "Total km",
                "best_rank": "Best individual rank",
            }
        )

        # Sort: most starts first, then most years
        runner_stats_display = runner_stats_display.sort_values(
            ["Starts", "Years"], ascending=[False, False]
        )

        st.dataframe(runner_stats_display, use_container_width=True)

    # -------------------------------------------------------------------
    # TAB: Highlights & charts
    # -------------------------------------------------------------------
    with tab_highlights:
        st.subheader(t("highlights_title"))

        results_all = merged.copy()
        results_all = apply_runner_filter(results_all, runner_filter_mode)

        runner_stats = (
            results_all.groupby("runner_id")
            .agg(
                first_name=("first_name", "first"),
                last_name=("last_name", "first"),
                company=("company", "first"),
                is_external=("is_external", "first"),
                active=("active", "first"),
                num_runs=("leg_id", "count"),
                num_years=("year", "nunique"),
                total_km=("distance_km", "sum"),
                avg_pace_sec=("ind_pace_sec_per_km", "mean"),
                best_rank=("ind_rank_leg", "min"),
            )
            .reset_index()
        )

        runner_stats["Name"] = (
            runner_stats["first_name"] + " " + runner_stats["last_name"]
        )

        # Top 10 total km
        st.markdown("### Top 10 - total distance")

        top_km = runner_stats.sort_values("total_km", ascending=False).head(10)
        top_km["total_km"] = top_km["total_km"].round(1)

        chart_km = (
            alt.Chart(top_km)
            .mark_bar()
            .encode(
                x=alt.X("total_km:Q", title="Total km"),
                y=alt.Y("Name:N", sort="-x", title="Runner"),
                color=alt.Color(
                    "company:N", legend=alt.Legend(title="Company")
                ),
                tooltip=["Name", "company", "total_km", "num_runs", "num_years"],
            )
        )
        st.altair_chart(chart_km, use_container_width=True)

        # Top 10 starts
        st.markdown("### Top 10 - number of starts")

        top_starts = runner_stats.sort_values(
            ["num_runs", "num_years"], ascending=[False, False]
        ).head(10)
        chart_starts = (
            alt.Chart(top_starts)
            .mark_bar()
            .encode(
                x=alt.X("num_runs:Q", title="Starts"),
                y=alt.Y("Name:N", sort="-x", title="Runner"),
                color=alt.Color(
                    "company:N", legend=alt.Legend(title="Company")
                ),
                tooltip=[
                    "Name",
                    "company",
                    "num_runs",
                    "num_years",
                    "total_km",
                ],
            )
        )
        st.altair_chart(chart_starts, use_container_width=True)

        # Best team rankings
        st.markdown("### Top 5 - best final team rankings")

        teams_ranked = teams_df[teams_df["rank_final"].notna()].copy()
        teams_ranked = teams_ranked.sort_values("rank_final", ascending=True).head(5)

        teams_display = pd.DataFrame()
        teams_display["Year"] = teams_ranked["race_id"].str.extract(
            r"sola-(\d+)", expand=False
        )
        teams_display["Team"] = teams_ranked["name"]
        teams_display["Company"] = teams_ranked["company"]
        teams_display["Bib #"] = teams_ranked["bib_number"]
        teams_display["Final rank"] = teams_ranked["rank_final"].astype(int)
        teams_display["Final time"] = teams_ranked["time_final_seconds"].apply(
            format_seconds_to_hms
        )
        teams_display["Avg. team pace"] = teams_ranked["pace_final_sec_per_km"].apply(
            format_pace
        )

        st.dataframe(teams_display, use_container_width=True)

        # Runners with top-10 individual ranks
        st.markdown("### Runners with top-10 individual stage ranks")

        top10_results = results_all[
            results_all["ind_rank_leg"].notna()
            & (results_all["ind_rank_leg"] <= 10)
        ].copy()

        if top10_results.empty:
            st.info(t("info_no_top10_results"))
        else:
            top10_summary = (
                top10_results.groupby("runner_id")
                .agg(
                    first_name=("first_name", "first"),
                    last_name=("last_name", "first"),
                    company=("company", "first"),
                    count_top10=("ind_rank_leg", "count"),
                    best_rank=("ind_rank_leg", "min"),
                )
                .reset_index()
                .sort_values(
                    ["count_top10", "best_rank"],
                    ascending=[False, True],
                )
            )
            top10_summary["Name"] = (
                top10_summary["first_name"] + " " + top10_summary["last_name"]
            )
            top10_display = top10_summary[
                ["Name", "company", "count_top10", "best_rank"]
            ].rename(
                columns={
                    "company": "Company",
                    "count_top10": "Top-10 finishes",
                    "best_rank": "Best rank",
                }
            )
            st.dataframe(top10_display, use_container_width=True)

        # Fastest stages by pace
        st.markdown("### Fastest stages (by pace)")

        fastest = results_all[results_all["ind_pace_sec_per_km"].notna()].copy()

        if fastest.empty:
            st.info(t("info_no_pace_data"))
        else:
            fastest = fastest.nsmallest(10, "ind_pace_sec_per_km")
            fast_table = pd.DataFrame()
            fast_table["Year"] = (
                fastest["year"].astype("int").astype("string")
            )
            fast_table["Team"] = fastest["team_name"]
            fast_table["Runner"] = (
                fastest["first_name"] + " " + fastest["last_name"]
            )
            fast_table["Stage"] = fastest["leg_number"]
            fast_table["Stage name"] = fastest["leg_name"]
            fast_table["Distance (km)"] = fastest["distance_km"]
            fast_table["Pace"] = fastest["ind_pace_sec_per_km"].apply(format_pace)
            fast_table["Time"] = fastest["ind_time_seconds"].apply(
                format_seconds_to_hms
            )
            fast_table["Individual rank"] = fastest["ind_rank_leg"]

            st.dataframe(fast_table, use_container_width=True)

        # -------------------------------------------------------------------
    # TAB: Planning (draft)
    # -------------------------------------------------------------------
    with tab_planning:
        st.subheader(t("planning_title"))

        years_existing = sorted(races_df["year"].unique())
        last_year = years_existing[-1] if years_existing else date.today().year

        # Planned race year is usually next year
        default_planned_year = last_year + 1

        col_y1, col_y2 = st.columns(2)
        with col_y1:
            planned_year = st.number_input(
                "Planned race year",
                min_value=last_year,
                max_value=last_year + 10,
                value=default_planned_year,
                step=1,
            )
        with col_y2:
            template_year = st.selectbox(
                t("planning_template_year"),
                years_existing,
                index=len(years_existing) - 1 if years_existing else 0,
            )

        race_id_template = f"sola-{template_year}"

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            race_date = st.date_input(
                t("planning_race_date"),
                value=date(int(planned_year), 5, 1),
            )
        with col_p2:
            race_start_time = st.time_input(
                t("planning_start_time"),
                value=time(7, 30),
            )

        st.markdown(
            f"Using distances & stages from **{template_year}**, "
            f"planning for race year **{int(planned_year)}**."
        )

        # Free team definition (no dependency on existing teams)
        st.markdown(f"### {t('planning_team_info')}")

        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            team_name_plan = st.text_input(t("planning_team_name"), value="Optimizers")
        with col_t2:
            company_plan = st.text_input(t("planning_company"), value="Accenture")
        with col_t3:
            bib_plan = st.text_input(
                t("planning_bib_number"),
                value="",
                help=t("planning_bib_help"),
            )

        legs_plan = (
            legs_df[legs_df["race_id"] == race_id_template]
            .sort_values("leg_number")
            .reset_index(drop=True)
        )

        if legs_plan.empty:
            st.info(t("info_no_stages_template"))
        else:
            # Runner list for planning (respecting active filter)
            runners_for_plan = apply_runner_filter(runners_df, runner_filter_mode)
            runners_for_plan = (
                runners_for_plan.sort_values(["last_name", "first_name"])
                .reset_index(drop=True)
            )
            runner_choices = [
                f"{row['first_name']} {row['last_name']} ({row['runner_id']})"
                for _, row in runners_for_plan.iterrows()
            ]

            st.markdown(f"### {t('planning_stage_assignments')}")

            base_start_dt = datetime.combine(race_date, race_start_time)
            cumulative_sec = 0.0
            plan_rows: list[dict[str, Any]] = []

            # A simple key base to keep widgets stable
            team_key_base = f"{int(planned_year)}_{team_name_plan.replace(' ', '_')}"

            for _, leg in legs_plan.iterrows():
                leg_num = int(leg["leg_number"])
                dist_km = float(leg.get("distance_km") or 0.0)
                leg_name = leg.get("name", f"Stage {leg_num}")

                col_l1, col_l2, col_l3 = st.columns([3, 2, 2])

                with col_l1:
                    runner_sel = st.selectbox(
                        f"Stage {leg_num}: {leg_name} ({dist_km:.1f} km)",
                        ["(unassigned)"] + runner_choices,
                        key=f"plan_runner_{team_key_base}_{leg_num}",
                    )
                with col_l2:
                    default_pace_sec = 360
                    pace_input = st.number_input(
                        t("planning_pace"),
                        min_value=150,
                        max_value=720,
                        value=default_pace_sec,
                        step=5,
                        key=f"plan_pace_{team_key_base}_{leg_num}",
                    )
                with col_l3:
                    restart_here = st.checkbox(
                        t("planning_restart_here"),
                        key=f"plan_restart_{team_key_base}_{leg_num}",
                        help=t("planning_restart_help"),
                    )
                    restart_time = None
                    if restart_here:
                        restart_time = st.time_input(
                            t("planning_restart_time"),
                            value=race_start_time,
                            key=f"plan_restart_time_{team_key_base}_{leg_num}",
                        )

                # Apply restart logic for scheduling
                if restart_here and restart_time is not None:
                    base_start_dt = datetime.combine(race_date, restart_time)
                    cumulative_sec = 0.0

                # Compute times
                leg_time_sec = pace_input * dist_km if dist_km else 0.0
                start_dt = base_start_dt + timedelta(seconds=cumulative_sec)
                end_dt = start_dt + timedelta(seconds=leg_time_sec)
                cumulative_sec += leg_time_sec

                plan_rows.append(
                    {
                        "Stage": leg_num,
                        "Stage name": leg_name,
                        "Distance (km)": round(dist_km, 1),
                        "Runner": (
                            runner_sel if runner_sel != "(unassigned)" else ""
                        ),
                        "Pace (s/km)": pace_input,
                        "Pace": format_pace(pace_input),
                        "Planned time (hh:mm:ss)": format_seconds_to_hms(
                            leg_time_sec
                        ),
                        "Planned start time": start_dt.strftime("%H:%M"),
                        "Planned finish time": end_dt.strftime("%H:%M"),
                        "Restart here": "Yes" if restart_here else "No",
                    }
                )

            # ---------- ab hier NACH der Schleife ----------
            st.markdown(f"### {t('planning_schedule_title')}")

            plan_df = pd.DataFrame(plan_rows)
            st.dataframe(plan_df, use_container_width=True)

            st.markdown(f"### {t('planning_checklist_title')}")

            checklist_items = [
                t("checklist_runners_assigned"),
                t("checklist_paces_realistic"),
                t("checklist_restart_verified"),
                t("checklist_runners_informed"),
                t("checklist_logistics_clarified"),
                t("checklist_contact_ready"),
            ]

            # einfache Session-State-Checkliste
            if "planning_checklist" not in st.session_state:
                st.session_state["planning_checklist"] = {
                    item: False for item in checklist_items
                }

            for item in checklist_items:
                checked = st.checkbox(
                    item,
                    value=st.session_state["planning_checklist"].get(item, False),
                )
                st.session_state["planning_checklist"][item] = checked

            st.markdown(f"### {t('planning_export_title')}")

            col_exp1, col_exp2, col_exp3 = st.columns(3)

            # CSV
            csv_bytes = plan_df.to_csv(index=False).encode("utf-8")
            with col_exp1:
                st.download_button(
                    t("download_csv"),
                    data=csv_bytes,
                    file_name=f"sola_plan_{int(planned_year)}_{team_name_plan.replace(' ', '_')}.csv",
                    mime="text/csv",
                )

            # Excel
            excel_buffer = BytesIO()
            plan_df.to_excel(excel_buffer, index=False, sheet_name="Plan")
            excel_buffer.seek(0)
            with col_exp2:
                st.download_button(
                    t("download_excel"),
                    data=excel_buffer,
                    file_name=f"sola_plan_{int(planned_year)}_{team_name_plan.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

            # PDF (optional)
            with col_exp3:
                if HAS_FPDF:
                    pdf_bytes = plan_df_to_pdf_bytes(
                        plan_df,
                        title=f"SOLA Plan {int(planned_year)} - {team_name_plan}",
                    )
                    st.download_button(
                        t("download_pdf"),
                        data=pdf_bytes,
                        file_name=f"sola_plan_{int(planned_year)}_{team_name_plan.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                    )
                else:
                    st.caption(t("info_pdf_install"))

    # -------------------------------------------------------------------
    # TAB: Admin
    # -------------------------------------------------------------------
    with tab_admin:
        st.subheader(t("admin_title"))

        st.info(t("admin_info_overrides"))

        runners_filtered = apply_runner_filter(runners_df, runner_filter_mode)
        runners_sorted = (
            runners_filtered.sort_values(["last_name", "first_name"])
            .reset_index(drop=True)
        )

        runner_options_admin = [
            f"{row['first_name']} {row['last_name']} ({row['runner_id']})"
            for _, row in runners_sorted.iterrows()
        ]

        selected_runner_admin = st.selectbox(
            t("admin_select_runner"),
            [t("please_select")] + runner_options_admin,
        )

        if selected_runner_admin != t("please_select"):
            rid = selected_runner_admin.split("(")[-1].rstrip(")")
            runner_row = runners_df[runners_df["runner_id"] == rid]
            if runner_row.empty:
                st.error(t("error_runner_not_found"))
            else:
                r = runner_row.iloc[0]

                st.markdown(
                    f"### Edit runner: **{r['first_name']} {r['last_name']}** "
                    f"(`{r['runner_id']}`)"
                )

                overrides = load_runner_overrides()
                current_override = overrides.get(rid, {})

                # Helper: override value if present, otherwise base value
                def ov(col: str, base: Any):
                    return current_override.get(col, base)

                with st.form(f"runner_admin_form_{rid}"):
                    col1, col2 = st.columns(2)

                    # -------------------------------
                    # Left: status, running-related
                    # -------------------------------
                    with col1:
                        active = st.checkbox(
                            t("admin_active"),
                            value=bool(ov("active", r.get("active", True))),
                        )

                        default_pace_sec = st.number_input(
                            t("admin_default_pace"),
                            min_value=150,
                            max_value=900,
                            value=int(
                                ov(
                                    "default_pace_sec",
                                    r.get("default_pace_sec") or 360,
                                )
                            ),
                            step=5,
                        )

                        # Preferred distance dropdown
                        pref_dist_options = ["", "Short", "Middle", "Long", "Any"]
                        pref_dist_current = str(
                            ov(
                                "preferred_distance",
                                r.get("preferred_distance") or "",
                            )
                        ).strip()
                        if pref_dist_current not in pref_dist_options:
                            pref_dist_current = ""
                        preferred_distance = st.selectbox(
                            t("admin_preferred_distance"),
                            options=pref_dist_options,
                            index=pref_dist_options.index(pref_dist_current),
                        )

                        # Favourite stage dropdown (1-14)
                        fav_stage_options = [""] + [str(i) for i in range(1, 15)]
                        fav_stage_current = str(
                            ov(
                                "favorite_stage",
                                r.get("favorite_stage") or "",
                            )
                        ).strip()
                        if fav_stage_current not in fav_stage_options:
                            fav_stage_current = ""
                        favorite_stage = st.selectbox(
                            t("admin_favorite_stage"),
                            options=fav_stage_options,
                            index=fav_stage_options.index(fav_stage_current),
                        )

                        # Gender dropdown
                        gender_options = ["", "Male", "Female", "No answer"]
                        gender_current_raw = str(
                            ov("gender", r.get("gender") or "")
                        ).strip()
                        # normalize a bit
                        gender_current_norm = gender_current_raw.capitalize()
                        if gender_current_norm not in gender_options:
                            gender_current_norm = ""
                        gender = st.selectbox(
                            t("admin_gender"),
                            options=gender_options,
                            index=gender_options.index(gender_current_norm),
                        )

                        # Birth year
                        birth_year_val = ov("birth_year", r.get("birth_year"))
                        if birth_year_val in (None, "", float("nan")):
                            birth_year_val = 0
                        try:
                            birth_year_val = int(birth_year_val)
                        except Exception:
                            birth_year_val = 0

                        birth_year = st.number_input(
                            t("admin_birth_year"),
                            min_value=0,
                            max_value=2100,
                            value=birth_year_val,
                            step=1,
                        )

                    # -----------------------------------------
                    # Right: contact, address, t-shirt, food
                    # -----------------------------------------
                    with col2:
                        company = st.text_input(
                            t("admin_company"),
                            value=str(ov("company", r.get("company") or "")),
                        )
                        email = st.text_input(
                            t("admin_email"),
                            value=str(ov("email", r.get("email") or "")),
                        )
                        mobile = st.text_input(
                            t("admin_mobile"),
                            value=str(ov("mobile", r.get("mobile") or "")),
                        )

                        street = st.text_input(
                            t("admin_street"),
                            value=str(ov("street", r.get("street") or "")),
                        )
                        zip_code = st.text_input(
                            t("admin_zip_code"),
                            value=str(ov("zip_code", r.get("zip_code") or "")),
                        )
                        city = st.text_input(
                            t("admin_city"),
                            value=str(ov("city", r.get("city") or "")),
                        )
                        country = st.text_input(
                            t("admin_country"),
                            value=str(ov("country", r.get("country") or "")),
                        )

                        # T-shirt size dropdown
                        tshirt_options = ["", "XS", "S", "M", "L", "XL", "XXL"]
                        tshirt_current = str(
                            ov("tshirt_size", r.get("tshirt_size") or "")
                        ).upper().strip()
                        if tshirt_current not in tshirt_options:
                            tshirt_current = ""
                        tshirt_size = st.selectbox(
                            t("admin_tshirt_size"),
                            options=tshirt_options,
                            index=tshirt_options.index(tshirt_current),
                        )

                        # Food preference dropdown
                        food_options = ["", "Meat", "Vegetarian", "Fish"]
                        food_current_raw = str(
                            ov("food_preference", r.get("food_preference") or "")
                        ).strip().capitalize()
                        if food_current_raw not in food_options:
                            food_current_raw = ""
                        food_preference = st.selectbox(
                            t("admin_food_preference"),
                            options=food_options,
                            index=food_options.index(food_current_raw),
                        )

                        notes = st.text_area(
                            t("admin_notes"),
                            value=str(ov("notes", r.get("notes") or "")),
                        )

                    submitted = st.form_submit_button(t("admin_save_button"))

                if submitted:
                    # 0 as birth year => treat as None
                    birth_year_out = int(birth_year) if birth_year > 0 else None

                    overrides[rid] = {
                        "active": active,
                        "default_pace_sec": float(default_pace_sec),
                        "preferred_distance": preferred_distance or None,
                        "favorite_stage": favorite_stage or None,
                        "gender": gender or None,
                        "birth_year": birth_year_out,
                        "company": company or None,
                        "email": email or None,
                        "mobile": mobile or None,
                        "street": street or None,
                        "zip_code": zip_code or None,
                        "city": city or None,
                        "country": country or None,
                        "tshirt_size": tshirt_size or None,
                        "food_preference": food_preference or None,
                        "notes": notes or None,
                    }
                    save_runner_overrides(overrides)
                    st.success(t("admin_save_success"))
                    st.info(t("admin_rerun_info"))

        # ---- Export-Section IMMER sichtbar (unabhängig vom selected_runner_admin) ----
        st.markdown(f"### {t('admin_export_title')}")

        export_df = build_overrides_export_df(runners_df)
        if export_df.empty:
            st.caption(t("info_no_overrides"))
        else:
            csv_ov = export_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                t("admin_download_overrides"),
                data=csv_ov,
                file_name="runner_overrides.csv",
                mime="text/csv",
            )

if __name__ == "__main__":
    main()
