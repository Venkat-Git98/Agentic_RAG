# Deep Testing Suite Documentation

## Overview

The Deep Testing Suite is a comprehensive testing framework for the AI Agent system that tests all components with 79+ diverse queries and provides detailed analysis.

## Files

### Core Testing Scripts

- **`deep_test_suite.py`** - Main comprehensive testing script
  - Tests 79+ queries across 13 categories
  - Covers all agent components (Triage, Planning, Research, Synthesis, Memory)
  - Saves detailed results to JSON files
  - Runs automatically with incremental saves every 10 tests

### Monitoring & Analysis Scripts

- **`monitor_deep_test.py`** - Real-time progress monitoring
  - Shows current test progress
  - Displays success rates and performance metrics
  - Can run continuously with `--continuous` flag

- **`analyze_results.py`** - Comprehensive results analysis
  - Category performance breakdown
  - Workflow path analysis
  - Agent-specific insights
  - Performance analytics

- **`investigate_fallback.py`** - Fallback mechanism analysis
  - Identifies fallback trigger patterns
  - Analyzes retrieval method usage
  - Provides recommendations for optimization

## Usage

### Running the Deep Test Suite

```bash
# Run the complete test suite (79+ tests)
python deep_test_suite.py
```

### Monitoring Progress

```bash
# Check current progress
python monitor_deep_test.py

# Continuous monitoring (updates every 30 seconds)
python monitor_deep_test.py --continuous
```

### Analyzing Results

```bash
# Analyze current results
python analyze_results.py

# Investigate fallback patterns
python investigate_fallback.py
```

## Test Categories

The deep test suite covers these categories:

1. **triage_clarify** - Help requests requiring clarification
2. **triage_reject** - Off-topic queries that should be rejected
3. **direct_retrieval** - Direct section references (e.g., "Section 1607.12.1")
4. **basic_engagement** - Standard building code queries
5. **calculation** - Math/calculation queries (Planning Agent calculation strategy)
6. **comparison** - Comparative analysis queries (Planning Agent comparison strategy)
7. **requirements** - Requirements-focused queries (Planning Agent requirements strategy)
8. **complex** - Multi-part complex queries
9. **edge_case** - Edge cases and ambiguous queries
10. **technical** - Technical terminology testing
11. **code_sections** - Specific code chapters
12. **research_stress** - Research orchestrator stress tests
13. **synthesis** - Synthesis agent testing
14. **memory** - Memory agent conversation flow
15. **fallback** - Fallback mechanism testing
16. **performance** - Performance testing with long queries

## Output Files

Results are saved in the `deep_test_results/` directory:

- **`incremental_results_X.json`** - Incremental saves every 10 tests
- **`deep_test_results_YYYYMMDD_HHMMSS.json`** - Complete detailed results
- **`simple_results_YYYYMMDD_HHMMSS.json`** - Simplified results for quick analysis
- **`test_summary_report_YYYYMMDD_HHMMSS.json`** - Comprehensive analysis report

## Key Metrics Tracked

- **Success Rate** - Percentage of successful tests
- **Execution Time** - Performance metrics for each test
- **Workflow Paths** - Which agents were executed
- **Triage Classifications** - How queries were classified
- **Research Quality** - Quality of research results
- **Fallback Usage** - When and why fallback mechanisms trigger
- **Agent Performance** - Individual agent execution metrics

## Recent Findings

From the latest test run (40 tests):
- **Success Rate**: 100%
- **Average Time**: 19.43s
- **Fallback Issue**: 73.3% of research queries falling back to web search
- **Recommendation**: Optimize vector database and similarity thresholds

## Troubleshooting

### Encoding Issues
If you see encoding errors, the scripts use UTF-8 encoding. Make sure your terminal supports UTF-8.

### Long Execution Times
The full test suite takes significant time due to comprehensive testing. Use the monitor script to track progress.

### Memory Usage
Large test runs generate substantial JSON files. Monitor disk space in the `deep_test_results/` directory.

## Next Steps

1. **Optimize Vector Search** - Address the high fallback usage
2. **Improve Query Processing** - Better match between queries and indexed content
3. **Enhance Similarity Thresholds** - Reduce unnecessary fallbacks
4. **Expand Test Coverage** - Add more edge cases as needed 