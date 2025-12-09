# Instructor Question Management Feature

## Overview
This feature allows instructors (users with role weight 5 or higher) to create, edit, and manage SAT practice questions for both English and Math sections through a user-friendly web interface.

## Access Requirements
- **Minimum Role**: Instructor (weight 5+)
- **URL**: `/instructor/questions/`

## Features

### 1. Question List View
- **URL**: `/instructor/questions/`
- View all questions in a paginated table
- Filter questions by:
  - Domain (e.g., Information and Ideas, Algebra)
  - Skill (e.g., Cross-Text Connections, Linear Equations)
  - Question Type (MCQ or SPR)
  - Status (Active/Inactive)
  - Search by ID, domain, skill, or question text
- Quick actions:
  - Edit question
  - Delete question
  - Toggle active/inactive status

### 2. Create Question
- **URL**: `/instructor/questions/create/`
- Comprehensive form with all required fields
- Organized sections:
  - **Identification**: Unique question identifier
  - **Classification**: Domain, skill, provider information
  - **Question Properties**: Type (MCQ/SPR) and difficulty level
  - **Question Content**: Stimulus, stem, explanation (supports HTML)
  - **MCQ Options**: Correct answer and JSON options for multiple choice
  - **SPR Answer**: JSON array of acceptable answers for grid-in questions
  - **Additional Settings**: Tutorial link and active status

### 3. Edit Question
- **URL**: `/instructor/questions/<question_id>/edit/`
- Pre-populated form with existing question data
- All fields editable
- Validation ensures data integrity

### 4. Delete Question
- **URL**: `/instructor/questions/<question_id>/delete/`
- Confirmation required
- Permanent deletion from database

### 5. Toggle Status
- **URL**: `/instructor/questions/<question_id>/toggle/`
- Quick toggle between active and inactive
- Inactive questions won't appear in student practice sessions

## Question Types

### Multiple Choice Question (MCQ)
- **Required Fields**:
  - Question identifier, domain, skill, stem
  - Correct answer (A, B, C, or D)
  - MCQ options in JSON format:
    ```json
    {
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    }
    ```

### Student Produced Response (SPR/Grid-in)
- **Required Fields**:
  - Question identifier, domain, skill, stem
  - SPR answer(s) in JSON array format:
    ```json
    ["2.5", "5/2"]
    ```
  - Multiple acceptable answers can be provided

## Domain and Skill Codes

### English Domains
- **II**: Information and Ideas
- **CAS**: Craft and Structure
- **EOI**: Expression of Ideas
- **SEC**: Standard English Conventions

### Math Domains
- **ALG**: Algebra
- **AAF**: Advanced Algebra and Functions
- **PST**: Problem-Solving and Data Analysis
- **GEO**: Geometry and Trigonometry

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| identifier_id | Text | Yes | Unique human-readable ID (e.g., JKZRJ) |
| domain_name | Text | Yes | Full domain name |
| domain_code | Text | Yes | Short domain code |
| skill_name | Text | Yes | Specific skill being tested |
| skill_code | Text | Yes | Short skill code |
| provider_name | Text | No | Provider name (default: College Board) |
| provider_code | Text | No | Provider code (default: cb) |
| question_type | Select | Yes | mcq or spr |
| stimulus | HTML | No | Question passage/context |
| stem | HTML | Yes | The actual question text |
| explanation | HTML | No | Answer explanation |
| mcq_answer | Select | For MCQ | Correct answer (A/B/C/D) |
| mcq_option_list | JSON | For MCQ | Answer options |
| spr_answer | JSON | For SPR | Acceptable answers |
| tutorial_link | URL | No | Link to tutorial resource |
| difficulty | Select | No | E (Easy), M (Medium), H (Hard) |
| is_active | Boolean | No | Whether question is active (default: true) |

## Form Validation

The form includes comprehensive validation:
- **Unique Identifier**: Ensures no duplicate question IDs
- **Question Type Validation**: 
  - MCQ questions must have correct answer and options
  - SPR questions must have at least one acceptable answer
- **JSON Validation**: 
  - MCQ options must be valid JSON with A, B, C, D keys
  - SPR answers must be valid JSON array
- **Required Fields**: Enforces all mandatory fields

## Usage Examples

### Creating an English MCQ Question
1. Navigate to `/instructor/questions/create/`
2. Fill in:
   - Identifier ID: `ENG001`
   - Domain: `Information and Ideas` (Code: `II`)
   - Skill: `Central Ideas and Details` (Code: `CID`)
   - Question Type: `Multiple Choice Question (MCQ)`
   - Stem: `What is the main idea of the passage?`
   - MCQ Answer: `B`
   - MCQ Options:
     ```json
     {
       "A": "The author's childhood memories",
       "B": "The importance of education",
       "C": "Modern technology trends",
       "D": "Historical events"
     }
     ```
3. Click "Create Question"

### Creating a Math SPR Question
1. Navigate to `/instructor/questions/create/`
2. Fill in:
   - Identifier ID: `MATH001`
   - Domain: `Algebra` (Code: `ALG`)
   - Skill: `Linear Equations` (Code: `LE`)
   - Question Type: `Student Produced Response (Grid-in)`
   - Stem: `If 2x + 5 = 15, what is the value of x?`
   - SPR Answer: `["5", "5.0"]`
3. Click "Create Question"

## Navigation
- Main dashboard: `/instructor/`
- Question management is accessible from the instructor dashboard
- Breadcrumb navigation and back buttons for easy navigation

## Security
- All views protected with `@instructor_required` decorator
- CSRF protection on all forms
- Input validation and sanitization
- Role-based access control (minimum weight 5)

## UI/UX Features
- Clean, professional interface following DSAT SCHOOL brand guidelines
- Compact spacing (text-sm, py-1.5, px-3)
- Responsive design (mobile-friendly)
- Clear visual feedback for actions
- Inline form validation errors
- Dynamic form sections based on question type
- Hover states and transitions for better UX

## Future Enhancements
- Bulk question import (CSV/JSON)
- Question preview before publishing
- Question versioning and history
- Question analytics (usage, difficulty metrics)
- Rich text editor for stimulus and stem
- Image upload for questions
- Question tagging and categorization
- Duplicate question detection
