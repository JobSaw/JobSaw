# LaTeX Writing Skills for CV Generation

As an AI CV writer, you must master the syntax and rules of LaTeX to ensure the document compiles successfully without human intervention. LaTeX is highly sensitive to special characters and command syntax.

## 1. Escaping Special Characters
The most common cause of compilation failure is unescaped special characters. You MUST escape these characters using a backslash `\`:
- Ampersand: `&` -> `\&` (e.g., "R\&D", "AT\&T")
- Percent sign: `%` -> `\%` 
- Dollar sign: `$` -> `\$` 
- Hash/Pound: `#` -> `\#` (e.g., "C\#", "F\#")
- Underscore: `_` -> `\_`
- Braces: `{` -> `\{` and `}` -> `\}`

## 2. Technical Terms
Pay particular attention to programming languages and technologies:
- **C++**: Write exactly as `C++`.
- **C#**: Write exactly as `C\#`.
- **Node.js**: Write exactly as `Node.js`.
- **.NET**: Write exactly as `.NET`.

## 3. Emphasizing Text
- Use `\textbf{text}` to make text **bold**. Use this to highlight key technologies, languages, or achievements in bullet points to make them stand out.
- Use `\textit{text}` to make text *italic*.

## 4. Bullet Points (Itemize)
When creating bulleted lists for experience or education, ALWAYS use the `itemize` environment. 
Correct syntax:
\begin{itemize}
    \item First bullet point.
    \item Second bullet point with \textbf{bold tech}.
\end{itemize}

## 5. Common Errors to Avoid
- **Unescaped '&' in text**: This will break table alignments or cause immediate failures. Always use `\&`.
- **Backslashes before normal text**: Do NOT put a backslash in front of normal words. `\The` is an invalid command.
- **Inventing commands**: Do NOT invent LaTeX commands or FontAwesome icons. Use ONLY the commands defined in the template.

## 6. Quotation Marks
- In LaTeX, standard double quotes (`"`) do not render correctly as opening quotes. Use two backticks for the opening quote and two single quotes for the closing quote: ``This is quoted text''.

## 7. CRITICAL: One Page Limit
Your output MUST perfectly fit on a single page. 
- NEVER generate a 2-page CV.
- Try to fill the single page with relevant information, but do not exceed it. Aim for 3-4 concise bullet points per recent role.
- **Condense information:** If you receive feedback that your output is too long, you MUST cut text. Rephrase bullet points into single, short sentences to prevent text wrapping.
- **Delete content:** If the CV is still too long after condensing, drop the least important bullet points first. If absolutely necessary, delete the oldest experiences completely to satisfy the 1-page requirement.
- Choose brevity over comprehensiveness. A 1-page CV is a hard requirement.
