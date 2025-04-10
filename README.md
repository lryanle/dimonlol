# DimonLOL

A smart URL alias manager that converts simple commands into customizable URLs with pattern matching.

## Getting Started

### Prerequisites

- Chrome browser
- Local development server

### Installation

1. Clone the repository
2. Install python packages (`pip install -r requirements.txt`)
3. Activate python environment
   1. Mac: `source ./.venv/bin/activate`
   2. Windows: `.venv/Scripts/activate`
4. Open [chrome://settings/searchEngines](chrome://settings/searchEngines)
5. Navigate to `Site search` > `Add`
6. Fill in the following fields and save:
   1. Name: `DimonLOL`
   2. Shortcut: `.`
   3. URL with %s in place of query: `http://127.0.0.1:5000/search?q=%s`
7. In the search bar type: `.` followed by a space (` `), then `admin`. Together, this should look like: `. admin`.
8. Thats it! You can add your own configurations in the admin page, or use the pre-configured ones!  

## How It Works

### Core Concepts

1. **Aliases** - Short keywords that map to URL patterns
2. **Patterns** - URL templates with token placeholders
3. **Tokens** - Variables like `<$1>`, `<$2>`, `<$&>` that get replaced with search terms

### Token Rules

- `<$1>`, `<$2>`, etc: Captures specific position tokens
- `<$&>`: Captures all remaining tokens
- An alias can only have one `<$&>` token

### Processing Flow

1. Input gets tokenized
2. First token is matched against aliases
3. If matched:
   - Multiple tokens: Apply pattern matching
   - Single token: Use fallback URL
4. If no match: Default to Google search

## Examples

### Basic Usage

```txt
Input: gh microsoft vscode
Result: https://github.com/microsoft/vscode
```

### Pattern Tokens

```txt
Input: gh facebook react
Pattern: https://github.com/<$1>/<$2>
Result: https://github.com/facebook/react
```

### All-Token Capture

```txt
Input: yt learn javascript 2025
Pattern: https://youtube.com/results?search_query=<$&>
Result: https://youtube.com/results?search_query=learn+javascript+2025
```

## System Architecture

DimonLOL consists of several key components:

### Components

1. **Web Interface**
   - Admin dashboard for managing aliases
   - Built with HTML and Tailwind CSS
   - JavaScript for dynamic interactions

2. **Backend Server**
   - Handles HTTP requests
   - Manages alias database operations
   - Processes search queries and pattern matching

3. **Database**
   - Stores alias definitions
   - Each record contains:
     - Unique identifier
     - Alias keyword
     - URL pattern

### Flow

1. User enters a search query
2. Backend tokenizes the input
3. System looks up the first token in alias database
4. Pattern matching engine processes remaining tokens
5. Returns either:
   - Formatted URL based on pattern
   - Default Google search

## Database Structure

| Field | Type | Description |
|-------|------|-------------|
| id | Integer | Unique identifier |
| alias | String | Command keyword |
| pattern | String | URL pattern with tokens |

## API Reference

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /search | List all aliases |
| POST | /alias | Create alias |
| PUT | /alias/{id} | Update alias |
| DELETE | /alias/{id} | Remove alias |

### Response Format

```json
{
  "aliases": [
    {
      "id": 1,
      "alias": "gh",
      "pattern": "https://github.com/<$1>/<$2>",
      "fallback": "https://github.com"
    }
  ]
}
```

## Acknowledgement

The original idea for DimonLOL comes from bunny1 by Charlie Cheever (Facebook) and yubnub.org
