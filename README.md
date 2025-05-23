# LaTeX Genealogy Formatter

A tool for converting raw genealogical data into beautifully formatted LaTeX documents for use with Overleaf.

## Overview

This project processes raw genealogical data extracted from PDF documents and converts it into structured LaTeX code that renders professional-looking genealogical reports. The formatter handles person entries, their relationships, children, and generational groupings.

## Features

- Converts raw genealogical text into structured LaTeX code
- Properly formats person entries with biographical information
- Handles marriages and children relationships
- Creates generation titles and section dividers
- Formats names with hyperlink appearance
- Preserves formatting of Wikipedia URLs
- Properly handles Roman numerals for child entries
- Provides error logging for skipped or problematic entries

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

2. For large files, you may need to split the PDF first:
   ```
   # Process each batch separately
   python generate_latex.py
   ```

3. The script will generate `parsed_output_new.tex` with the formatted LaTeX code.

4. Import the output into your LaTeX document:
   ```latex
   \input{parsed_output_new.tex}
   ```

5. Compile your LaTeX document to generate the final PDF.

## Customization

### Styling

The LaTeX template defines colors, fonts, and styling for various elements:

- Color scheme: `accent` (#a85733), `olivegreen` (#656137), and `divider` (#2f3d22)
- Fonts: Public Sans for body text, EB Garamond for headers
- Badge style: Circular badges with accent color
- Hyperlink appearance: Bold, underlined, accent-colored text

You can modify these in the `main.tex` file.

### Pagination and Headers

The template includes a footer with "Sapling Platinum Report" and page numbers. Modify the footer in the `main.tex` file under the `% ======== FOOTER ========` section.

## Troubleshooting

### Large File Handling

For very large files, Overleaf may show "Document Too Long" errors. Solutions:

1. Split the input into multiple smaller files
2. Process each file separately with the script
3. Create a main LaTeX file that includes all parts with `\input{}`

### Skipped Entries

If entries are skipped, check:
1. The format of the raw input
2. The `skipped_entries.log` file for specific errors
3. Ensure the encoding is correct (the script uses windows-1252)

## License

This project is open-sourced under the MIT License.

## Acknowledgments

- Special thanks to the LaTeX community
- Inspired by genealogical reporting needs 
