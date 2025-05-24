# LaTeX Genealogy Formatter

A tool for converting raw genealogical data into beautifully formatted LaTeX documents with working hyperlinks.

## Overview

This project processes raw genealogical data extracted from PDF documents and converts it into structured LaTeX code that renders professional-looking genealogical reports with functional cross-references.

## Features

- Converts raw genealogical text into structured LaTeX code
- Creates working hyperlinks between person references
- Each person entry becomes a clickable destination in the PDF
- References to people (in bios, marriages, children) become clickable links
- External URLs (Wikipedia, etc.) remain functional
- Intelligent name matching for better cross-referencing (handles middle initials)
- Preserves existing styling and formatting

## Requirements

- Python 3.6 or higher
- LaTeX distribution (for rendering the output)
- Overleaf account (optional, for online compilation)

## File Structure

- `generate_latex.py` - The main Python script that processes genealogical data
- `main.tex` - The LaTeX template with styling and formatting commands
- `.gitignore` - Git configuration for excluding unnecessary files

## Input Format

The script expects raw genealogical text with a format similar to:

```
1. Person Name, biographical information and details.

   Person married Spouse Name, optional spouse details.
   
   Children from this marriage were:
   i. Child Name was born on date.
   ii. 2 Another Child Name with reference number.
```

Entry numbers should be at the beginning of lines followed by a period, then the person's name.

## Output Format

The script generates LaTeX code using these custom commands:

- `\entry{number}{name}{bio}` - For person entries
- `\marriage{text}` - For marriage information
- `\childrenheading` - Header for children section
- `\childentrylinked{number}{roman}{name}` - For children with reference numbers
- `\childentryplain{name}{roman}{description}` - For non-linked children
- `\generationtitle{title}` - For generation headings
- `\dividerline` - For separation between entries

## Usage

1. Convert your genealogical PDF to text:
   ```
   pdftotext -layout "Your_Report.pdf" raw_input.txt
   ```

2. Run the Python script:
   ```
   python generate_latex.py raw_input.txt
   ```

3. The script will generate a `.tex` file with the formatted LaTeX code and working hyperlinks.

4. Import the output into your LaTeX document using the provided template:
   ```latex
   \input{parsed_output.tex}
   ```

5. Compile your LaTeX document to generate the final PDF with clickable links.

## How the Linking Works

- Each person entry gets a `\hypertarget{personID}{}` anchor
- References to other people use `\hyperlink{personID}{Name}` when the person exists in the registry
- Fallback to styled non-functional links for unknown people
- Smart matching with case-insensitive comparison and middle initial handling

## License

This project is open-sourced under the MIT License.

## Acknowledgments

- Special thanks to the LaTeX community
- Inspired by genealogical reporting needs 
