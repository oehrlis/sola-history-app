# Changelog: Head-to-Head Runner Comparison Feature

## Version 1.1.0 - 2025-12-09

### 🎉 New Feature: Head-to-Head Runner Comparison

Added comprehensive runner comparison feature in the Runner tab, allowing side-by-side analysis of any two runners.

### ✨ Features Implemented

#### 1. **Side-by-Side Runner Selection**
- Two independent dropdown selectors for choosing runners
- Respects global active/inactive runner filter
- Validation to prevent comparing a runner against themselves
- Persistent selection using Streamlit session state

#### 2. **Career Statistics Comparison**
- Visual side-by-side metrics display with VS separator
- **Statistics tracked:**
  - Stage starts (total legs completed)
  - Years active (number of race years participated)
  - Total distance covered (km)
  - Average pace (min/km)
  - Best individual stage rank
  - Best final team rank (from team final standings)

#### 3. **Direct Matchups Analysis**
- Identifies all stages both runners have completed (across any years)
- Calculates win/loss/tie record based on individual times
- Shows detailed matchup table including:
  - Year for each runner (handles different participation years)
  - Stage number and name
  - Distance
  - Individual times and paces for both runners
  - Individual ranks for both runners
  - Winner indication
- Displays summary metrics: Wins, Losses, Ties

#### 4. **Performance Visualization Charts**

**Pace Trends Over Years:**
- Line chart showing average pace evolution by year
- Dual-line comparison with color-coded runners
- Tooltips with detailed year and pace information

**Stage Distribution:**
- Grouped bar chart showing which stages each runner has completed
- Visual comparison of stage preferences and experience
- Shows frequency of runs per stage number

### 🌍 Internationalization Support

Full multi-language support with 24 new translation keys across 4 languages:

#### Translation Keys Added:
- `h2h_title` - Section title
- `h2h_select_runner1` / `h2h_select_runner2` - Runner selection
- `h2h_career_stats` - Career statistics section
- `h2h_performance_comparison` - Performance charts section
- `h2h_direct_matchups` - Matchups table section
- `h2h_pace_trends` - Pace chart caption
- `h2h_stage_distribution` - Stage chart caption
- `h2h_metric_*` - Individual metrics (starts, years, distance, pace, ranks)
- `h2h_wins` / `h2h_losses` / `h2h_ties` - Win/loss/tie labels
- `h2h_no_matchups` - Info message when no common stages
- `h2h_select_two_runners` - Warning when same runner selected

#### Languages Supported:
- ✅ **English** - Standard professional terminology
- ✅ **German (Deutsch)** - Professional German translations
- ✅ **Swiss German (Bärndütsch)** - Regional dialect variant
- ✅ **Pirate Mode (🏴‍☠️)** - Fun themed translations ("Duel on the High Seas", "swashbucklers", etc.)

### 📊 Technical Implementation

#### Data Processing:
- Merges runner data on `leg_id` to find common stages
- Handles different participation years gracefully
- Uses pandas aggregations for efficient statistics calculation
- Caches runner info lookups for performance

#### UI/UX Design:
- Horizontal divider separates from single-runner view
- Three-column layout for balanced runner comparison
- Central "VS" icon for visual clarity
- Responsive charts using Altair
- Consistent styling with existing app design

#### Integration:
- Seamlessly integrated into existing Runner tab
- Reuses existing data structures (`merged`, `runners_df`, `teams_df`)
- Leverages existing formatting functions (`format_pace`, `format_seconds_to_hms`)
- Respects global runner filter settings
- Uses same runner selection list as single-runner view

### 🔧 Code Quality

- Type hints maintained throughout
- Follows existing code style and patterns
- Proper error handling (empty data checks)
- Clear variable naming conventions
- Efficient data operations (minimizes redundant calculations)
- Session state keys prevent widget conflicts

### 📈 Use Cases

This feature enables:
1. **Performance benchmarking** - Compare personal bests and averages
2. **Team planning** - Evaluate runner pairings for stage assignments
3. **Historical analysis** - Track performance evolution over years
4. **Friendly competition** - See who's "winning" the rivalry
5. **Stage expertise** - Identify which runner excels on specific stages

### 🎯 Testing Notes

**Test Scenarios:**
- ✅ Compare two runners with many common stages
- ✅ Compare runners with no overlapping stages
- ✅ Compare same runner (shows warning)
- ✅ Compare runners from different eras (different years)
- ✅ Test with all 4 languages
- ✅ Test with active/inactive filter
- ✅ Verify chart rendering with various data sizes

### 📦 Files Modified

- `app.py` - Added head-to-head comparison section (~150 lines)
- `locales/en.json` - Added 24 English translation keys
- `locales/de.json` - Added 24 German translation keys
- `locales/ch.json` - Added 24 Swiss German translation keys
- `locales/pirate.json` - Added 24 Pirate mode translation keys

### 🚀 Impact

- **Lines of Code:** ~150 lines added to app.py (now 2165 lines total)
- **Translation Keys:** 24 new keys per language (96 new translations total)
- **New Dependencies:** None (uses existing libraries)
- **Breaking Changes:** None (purely additive feature)

### 📝 Future Enhancements (Optional)

Potential improvements for future iterations:
- Export head-to-head comparison as PDF/Excel
- Add more chart types (box plots, heatmaps)
- Include team-based comparisons
- Add filters for year range or specific stages
- Show delta calculations (time differences, pace gaps)
- Historical head-to-head trends over multiple years

---

**Feature Status:** ✅ Complete and Production-Ready

**Developed:** December 9, 2025  
**Version:** 1.1.0
