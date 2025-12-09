# 🚀 Quick Start Guide - Instructor Question Management

## TL;DR
Instructors can now create, edit, and manage SAT questions through a web interface at `/instructor/questions/`

---

## ⚡ Quick Access

### URLs
- **Dashboard**: https://your-domain.com/instructor/
- **Questions**: https://your-domain.com/instructor/questions/
- **Create**: https://your-domain.com/instructor/questions/create/

### Requirements
- ✅ User must have **Instructor role** (weight ≥ 5)
- ✅ User must be logged in

---

## 📝 Create Your First Question (30 seconds)

### MCQ Question Example
```
1. Go to: /instructor/questions/create/

2. Fill minimum required fields:
   Identifier: TEST001
   Domain Name: Information and Ideas
   Domain Code: II
   Skill Name: Central Ideas
   Skill Code: CI
   Question Type: Multiple Choice Question (MCQ)
   Stem: What is 2+2?
   MCQ Answer: C
   MCQ Options:
   {
     "A": "3",
     "B": "4", 
     "C": "5",
     "D": "6"
   }

3. Click "Create Question" ✓
```

### SPR Question Example
```
1. Go to: /instructor/questions/create/

2. Fill minimum required fields:
   Identifier: MATH001
   Domain Name: Algebra
   Domain Code: ALG
   Skill Name: Linear Equations
   Skill Code: LE
   Question Type: Student Produced Response (Grid-in)
   Stem: If x + 5 = 12, what is x?
   SPR Answer: ["7", "7.0"]

3. Click "Create Question" ✓
```

---

## 🔍 Filter Questions

### Available Filters
- **Search**: Type ID, domain, skill, or text
- **Domain**: Select from dropdown
- **Skill**: Select from dropdown  
- **Type**: MCQ or SPR
- **Status**: Active or Inactive

Click "Apply Filters" to filter, "Clear Filters" to reset.

---

## ✏️ Edit Questions

```
1. Find question in list
2. Click "Edit" button
3. Modify fields
4. Click "Edit Question"
```

---

## 🗑️ Delete Questions

```
1. Find question in list
2. Click "Delete" button
3. Confirm deletion
```

---

## 🔄 Toggle Active/Inactive

```
1. Find question in list
2. Click status badge (Active/Inactive)
3. Status toggles immediately
```

---

## 📋 Field Reference

### Required Fields (*)
- Identifier ID
- Domain Name & Code
- Skill Name & Code
- Question Type
- Question Stem

### MCQ-Specific (if type = MCQ)
- MCQ Answer (A/B/C/D)
- MCQ Options (JSON)

### SPR-Specific (if type = SPR)
- SPR Answer(s) (JSON array)

### Optional Fields
- Stimulus/Passage
- Explanation
- Tutorial Link
- Difficulty Level
- Provider Info

---

## 💡 Pro Tips

### JSON Formatting

✅ **Correct MCQ Options**:
```json
{
  "A": "First option",
  "B": "Second option",
  "C": "Third option",
  "D": "Fourth option"
}
```

❌ **Wrong MCQ Options**:
```json
["A", "B", "C", "D"]  // Must be object, not array
```

✅ **Correct SPR Answers**:
```json
["5", "5.0", "5.00"]
```

❌ **Wrong SPR Answers**:
```json
"5"  // Must be array, not string
```

### HTML Support
You can use HTML in:
- Stimulus (passage)
- Stem (question text)
- Explanation

Example:
```html
<p>This is a <strong>bold</strong> word.</p>
<p>This is an <em>italic</em> word.</p>
```

---

## 🎓 Common Domains & Skills

### English (Reading & Writing)
```
Domain: Information and Ideas (II)
Skills: Central Ideas (CI), Details (DET), Inferences (INF)

Domain: Craft and Structure (CAS)
Skills: Word Choice (WC), Text Structure (TS)

Domain: Expression of Ideas (EOI)
Skills: Rhetorical Synthesis (RS)

Domain: Standard English Conventions (SEC)
Skills: Boundaries (BND), Form/Structure (FS)
```

### Math
```
Domain: Algebra (ALG)
Skills: Linear Equations (LE), Systems (SYS)

Domain: Advanced Algebra and Functions (AAF)
Skills: Quadratics (QUAD), Functions (FUN)

Domain: Problem-Solving and Data Analysis (PST)
Skills: Ratios (RAT), Percentages (PCT), Statistics (STAT)

Domain: Geometry and Trigonometry (GEO)
Skills: Lines/Angles (LA), Circles (CIR), Trigonometry (TRIG)
```

---

## 🐛 Troubleshooting

### Error: "A question with this identifier already exists"
- Solution: Use a unique identifier (e.g., ENG_001, MATH_002)

### Error: "MCQ questions must have answer options"
- Solution: Ensure MCQ Options field has valid JSON with A, B, C, D keys

### Error: "Invalid JSON format"
- Solution: Check JSON syntax (quotes, commas, brackets)

### Cannot access /instructor/ page
- Solution: Verify you have Instructor role (contact admin)

---

## 📞 Need Help?

1. **Documentation**: See `docs/INSTRUCTOR_QUESTION_MANAGEMENT.md`
2. **Summary**: See `INSTRUCTOR_FEATURE_SUMMARY.md`
3. **Overview**: See `INSTRUCTOR_FEATURE_OVERVIEW.md`

---

## 🎉 That's It!

You're ready to start creating questions. Happy teaching! 🎓

**Remember**: 
- Always preview your questions before marking them active
- Use descriptive identifiers for easy searching
- Add explanations to help students learn

---

*Last Updated: December 9, 2025*
*DSAT SCHOOL - Practice Portal*
