# Automated Website Query Tool

## What This Script Does
This script automates the process of navigating websites to extract answers to specific questions. It efficiently navigates pages, avoids traps like infinite loops, and focuses on relevant links and content. It also leverages **Langfuse** for observability, providing detailed insights into the automation process.

### Key Features:
1. **Dynamic Navigation:**
   - Automatically decides which links to follow based on page content and context.
   - Handles multi-level navigation (up to 2-3 pages deep).

2. **Targeted Content Extraction:**
   - Extracts specific answers to predefined questions from the content of web pages.
   - Analyzes text, links, and metadata to identify relevant information.

3. **Trap Avoidance:**
   - Recognizes and avoids loops or dead-end links designed to waste resources.

4. **Answer Generation:**
   - Produces structured responses in JSON format:
     ```json
     {
         "01": "short answer to question 1",
         "02": "short answer to question 2",
         "03": "short answer to question 3"
     }
     ```

5. **Observability with Langfuse:**
   - Tracks navigation steps, decisions, and data extraction processes.
   - Provides insights for debugging and optimization.

## How It Works
- **Data Retrieval:**
  - Fetches a list of questions and the target website URL.
- **Navigation and Analysis:**
  - Iteratively explores pages, evaluates their content, and follows relevant links.
  - Combines extracted data to generate concise answers.
- **Result Reporting:**
  - Outputs answers in JSON format for submission.
- **Observability:**
  - Monitors the entire process using Langfuse for enhanced transparency and performance insights.
