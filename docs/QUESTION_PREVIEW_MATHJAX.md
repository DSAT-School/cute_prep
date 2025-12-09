# Question Form Preview & MathJax Enhancement

## 🎉 New Features Added

### 1. **MathJax Support**
- Full LaTeX math rendering support
- Use `$...$` for inline math: `$x^2 + y^2 = r^2$`
- Use `$$...$$` for display math: `$$\int_0^\infty e^{-x^2} dx$$`

### 2. **Live Preview Buttons**
Preview buttons added for:
- ✅ **Stimulus/Passage** - Preview with rendered math
- ✅ **Question Stem** - Preview with rendered math
- ✅ **Explanation** - Preview with rendered math
- ✅ **MCQ Options** - Preview all options with rendered math

### 3. **Smart Dropdown Fields**
Changed from text input to dropdown select:
- ✅ **Domain Name** - Select from predefined SAT domains
- ✅ **Skill Name** - Select from predefined SAT skills

### 4. **Auto-fill Feature**
Domain and skill codes are automatically filled when you select:
- Select "Algebra" → Auto-fills code "ALG"
- Select "Central Ideas and Details" → Auto-fills code "CID"

---

## 📝 How to Use

### Writing Math Equations

#### Inline Math
```
The solution to $ax + b = 0$ is $x = -\frac{b}{a}$
```

#### Display Math
```
$$\frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$$
```

#### Complex Fractions
```
$$\frac{x^2 + 2x + 1}{x^2 - 1} = \frac{(x+1)^2}{(x+1)(x-1)}$$
```

### Using Preview

1. **Type your content** in the text field (stimulus, stem, explanation, or MCQ options)
2. **Click the Preview button** (eye icon) next to the field label
3. **View rendered output** in the blue preview box below
4. **Make adjustments** and click Preview again

### MCQ Options with Math

```json
{
  "A": "$x = 5$",
  "B": "$x = -5$",
  "C": "$x = \\pm 5$",
  "D": "$x = 25$"
}
```

Click "Preview Options" to see all options rendered with math.

---

## 🎓 Available Domains

### English/Reading & Writing
- **Information and Ideas** (Code: II)
- **Craft and Structure** (Code: CAS)
- **Expression of Ideas** (Code: EOI)
- **Standard English Conventions** (Code: SEC)

### Math
- **Algebra** (Code: ALG)
- **Advanced Math** (Code: AAF)
- **Problem-Solving and Data Analysis** (Code: PST)
- **Geometry and Trigonometry** (Code: GEO)

---

## 🎯 Available Skills

### English Skills (10)
- Central Ideas and Details
- Command of Evidence
- Inferences
- Words in Context
- Text Structure and Purpose
- Cross-Text Connections
- Rhetorical Synthesis
- Transitions
- Boundaries
- Form, Structure, and Sense

### Math Skills (21)
- Linear equations in one variable
- Linear equations in two variables
- Linear functions
- Systems of two linear equations in two variables
- Linear inequalities in one or two variables
- Equivalent expressions
- Nonlinear equations in one variable
- Systems of equations in two variables
- Nonlinear functions
- Ratios, rates, proportional relationships, and units
- Percentages
- One-variable data: distributions and measures of center and spread
- Two-variable data: models and scatterplots
- Probability and conditional probability
- Inference from sample statistics and margin of error
- Evaluating statistical claims: observational studies and experiments
- Area and volume
- Lines, angles, and triangles
- Right triangles and trigonometry
- Circles

---

## 💡 Tips

### Math Formatting
- **Superscript**: `x^2` → $x^2$
- **Subscript**: `x_1` → $x_1$
- **Fractions**: `\frac{a}{b}` → $\frac{a}{b}$
- **Square root**: `\sqrt{x}` → $\sqrt{x}$
- **Greek letters**: `\alpha, \beta, \theta` → $\alpha, \beta, \theta$

### Common Math Symbols
- `\times` → ×
- `\div` → ÷
- `\pm` → ±
- `\leq` → ≤
- `\geq` → ≥
- `\neq` → ≠
- `\approx` → ≈

### Preview Best Practices
1. **Preview frequently** to catch formatting errors early
2. **Use preview before submitting** to ensure math renders correctly
3. **Check MCQ options** to ensure all options display properly

---

## 🐛 Troubleshooting

### Math Not Rendering
- Ensure you're using `$...$` or `$$...$$` delimiters
- Check for matching delimiters (open and close)
- Escape special characters: `\\` for backslash

### Preview Not Showing
- Make sure field has content
- Click preview button after typing
- Refresh page if MathJax doesn't load

### MCQ Preview Error
- Verify JSON format is correct
- Ensure it's an object `{}`, not array `[]`
- Check all quotes and commas

---

## 📚 Example Questions

### Math Question with LaTeX
```
Stem: If $2x + 3 = 11$, what is the value of $x$?

MCQ Options:
{
  "A": "$x = 2$",
  "B": "$x = 4$",
  "C": "$x = 5$",
  "D": "$x = 7$"
}

Explanation: Subtract 3 from both sides: $2x = 8$. Then divide by 2: $x = 4$. The answer is **B**.
```

### Geometry Question
```
Stem: What is the area of a circle with radius $r = 5$ cm? Use $\pi \approx 3.14$.

MCQ Options:
{
  "A": "$15.7$ cm²",
  "B": "$31.4$ cm²",
  "C": "$78.5$ cm²",
  "D": "$157$ cm²"
}

Explanation: The area formula is $A = \pi r^2 = \pi (5)^2 = 25\pi \approx 78.5$ cm². The answer is **C**.
```

---

**Updated**: December 9, 2025  
**Feature Status**: ✅ Production Ready
