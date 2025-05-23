import re
import sys
import os

def hyperlink(name):
    """Format a name with hyperlink appearance."""
    # Remove angle brackets around links
    name = re.sub(r'<(https?://[^>]+)>', r'\1', name)
    
    # Don't process Wikipedia URLs as hyperlinks with special formatting
    if name.startswith('http'):
        return name
        
    parts = [n.strip() for n in name.split(" and ")]
    return " and ".join(f"\\href{{#}}{{\\textcolor{{accent}}{{\\textbf{{\\underline{{{part}}}}}}}}}" for part in parts)

def format_person_block(entry_number, name, bio, marriage, children, generation=None):
    """Format a single LaTeX person block."""
    # Add generation title if provided and it's a new generation
    block = ""
    if generation:
        block += f"\\generationtitle{{{generation}}}\n"
    
    block += f"\\entry{{{entry_number}}}{{{name}}}{{{bio}}}\n"
    
    if marriage:
        block += f"\\marriage{{{marriage}}}\n"
    
    if children:
        if len(children) == 1:
            block += "\\childrenheading\n"
        else:
            block += "\\childrenheading\n".replace("child", "children").replace("was:", "were:")
        
        roman_numerals = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 'xi', 'xii', 'xiii', 'xiv', 'xv']
        
        for idx, (child_number, child_name, has_roman, is_linked) in enumerate(children):
            roman = roman_numerals[min(idx, len(roman_numerals)-1)]
            
            if is_linked:
                # This is a hyperlinked child with badge
                block += f"\\childentrylinked{{{child_number}}}{{{roman}}}{{{child_name}}}\n"
            else:
                # Extract name part for bolding (before any descriptive text)
                name_parts = child_name.split(',', 1)
                if len(name_parts) > 1:
                    name_part, desc_part = name_parts
                    block += f"\\childentryplain{{{name_part.strip()}}}{{{roman}}}{{{', ' + desc_part.strip()}}}\n"
                else:
                    block += f"\\childentry{{{''}}}{{{child_name}}}\n"
    
    # Add divider line after the entry
    if not generation:
        block += "\\dividerline\n"
    
    return block

def parse_genealogy_data(text):
    """Parse raw genealogy text into LaTeX blocks."""
    # Use a more robust pattern to identify entry start points
    entry_pattern = r"(?:^|\n)(\d{1,4})\.[\s]+([^,\n]+)(?:,\s*|\s*\n)(.+?)(?=(?:\n\d{1,4}\.\s)|$)"
    entries = re.findall(entry_pattern, text, re.DOTALL)
    
    person_blocks = []
    skipped_entries = []
    current_generation = None
    
    print(f"Found {len(entries)} potential entries to process")
    
    for i, (entry_number, name, content) in enumerate(entries):
        try:
            # Clean up the content
            lines = [line.strip() for line in content.splitlines() if line.strip()]
            
            # Extract bio lines
            bio_lines = []
            marriage = ""
            children = []
            in_children = False
            new_generation = None
            
            # Check for generation markers
            if any(gen in " ".join(lines[:3]).lower() for gen in 
                   ["first generation", "second generation", "third generation", 
                    "fourth generation", "fifth generation", "sixth generation",
                    "seventh generation", "eighth generation", "ninth generation",
                    "tenth generation"]):
                for line in lines[:3]:
                    if any(gen in line.lower() for gen in 
                          ["first generation", "second generation", "third generation", 
                           "fourth generation", "fifth generation", "sixth generation",
                           "seventh generation", "eighth generation", "ninth generation",
                           "tenth generation"]):
                        generation_match = re.search(r'([A-Za-z]+\s+Generation)', line, re.IGNORECASE)
                        if generation_match:
                            new_generation = generation_match.group(1)
                            # Remove the generation line from further processing
                            lines = [l for l in lines if generation_match.group(1).lower() not in l.lower()]
                            break
            
            # Skip processing if no content
            if not lines:
                skipped_entries.append((entry_number, name, "No content"))
                continue

            # Process each line
            for line in lines:
                # Check for children section marker
                if re.search(r'^(?:(?:The )?[Cc]hild(?:ren)?|The following child(?:ren)?) (?:from|of) this marriage', line):
                    in_children = True
                    continue
                # Check for special sections to skip or include in bio
                elif line.lower().startswith(("general notes:", "obituary:")):
                    bio_lines.append(line)
                    continue
                # Check for marriage line (only before children section)
                elif " married " in line.lower() and not in_children:
                    marriage = line
                # Process children lines
                elif in_children:
                    # Check if this line has a Roman numeral prefix (indicating a child entry)
                    roman_match = re.match(r'^([ivxlcdm]+)\.\s*(.*)', line, flags=re.IGNORECASE)
                    
                    if roman_match:
                        # This is a child entry with a Roman numeral
                        roman, child_text = roman_match.groups()
                        
                        # Check if there's a number before the name (numeric ID)
                        number_match = re.match(r'(?:(\d+)\s+)(.*)', child_text)
                        
                        if number_match:
                            # Child with a number ID
                            cid, cname = number_match.groups()
                            children.append((cid.strip(), hyperlink(cname.strip()), True, True))
                        else:
                            # Child without a number ID - still hyperlink the name
                            name_match = re.match(r'([^\.]+)(?:\.(.*)|$)', child_text.strip())
                            if name_match:
                                name_part, desc_part = name_match.groups()
                                if desc_part:
                                    children.append(("--", f"{hyperlink(name_part.strip())} {desc_part.strip()}", True, True))
                                else:
                                    children.append(("--", hyperlink(name_part.strip()), True, True))
                            else:
                                children.append(("--", hyperlink(child_text.strip()), True, True))
                    else:
                        # This is a continuation of a child description or a malformed entry
                        # Try to detect if it has a number format like "1020 i. and died on..."
                        number_in_circle = re.match(r'^\(?(\d+)\)?\s+i\.\s+(.*)', line)
                        
                        if number_in_circle:
                            # This is a special case with a number in parentheses or circle
                            cid, cname = number_in_circle.groups()
                            children.append((cid.strip(), hyperlink(cname.strip()), True, True))
                        else:
                            # Just add this as regular text (not hyperlinked)
                            children.append(("--", line.strip(), False, False))
                # Everything else goes to bio
                else:
                    bio_lines.append(line)
            
            # If no marriage line was found but there are children, the first bio line might be the marriage line
            if not marriage and children and bio_lines:
                # Check if any bio line contains "married"
                for idx, line in enumerate(bio_lines):
                    if " married " in line.lower():
                        marriage = line
                        bio_lines.pop(idx)
                        break
            
            # Join bio lines and format with hyperlinks
            bio = " ".join(bio_lines)
            
            # Process URLs in bio and marriage text
            bio = re.sub(r'<(https?://[^>]+)>', r'\1', bio)
            
            # Format parent references
            bio = re.sub(
                r'\b(son|daughter) of ([^.,]+)',
                lambda m: f"{m.group(1)} of {hyperlink(m.group(2))}",
                bio
            )
            
            # Format marriage with hyperlinks
            if marriage:
                marriage = re.sub(r'<(https?://[^>]+)>', r'\1', marriage)
                
                marriage = re.sub(
                    r'married ([^,]+)', 
                    lambda m: f"married {hyperlink(m.group(1))}", 
                    marriage
                )
                marriage = re.sub(
                    r'(son|daughter) of ([^.,]+)', 
                    lambda m: f"{m.group(1)} of {hyperlink(m.group(2))}", 
                    marriage
                )
            
            # Handle generation title - only include if it's a new generation
            if new_generation and new_generation != current_generation:
                current_generation = new_generation
                gen_to_use = current_generation
            else:
                gen_to_use = None
            
            # Create formatted block
            person_blocks.append(format_person_block(
                entry_number, 
                name.strip(), 
                bio, 
                marriage, 
                children, 
                gen_to_use
            ))
            
            # Progress report
            if (i+1) % 500 == 0:
                print(f"Processed {i+1} entries...")
        
        except Exception as e:
            # Log errors but continue processing
            skipped_entries.append((entry_number, name, f"Error: {str(e)}"))
            print(f"Error processing entry {entry_number}. {name}: {str(e)}")
    
    print(f"Successfully processed {len(person_blocks)} entries")
    print(f"Skipped {len(skipped_entries)} entries")
    
    # Optionally log skipped entries
    if skipped_entries:
        with open("skipped_entries.log", "w", encoding="utf-8") as log_file:
            for num, name, reason in skipped_entries:
                log_file.write(f"Entry {num}. {name}: {reason}\n")
    
    return "\n".join(person_blocks)

if __name__ == "__main__":
    try:
        print("Starting parsing process...")
        
        # Check if input file is specified as a command line argument
        if len(sys.argv) > 1:
            input_file = sys.argv[1]
        else:
            # Look for available input files
            input_files = [f for f in os.listdir('.') if f.startswith('raw_input') and f.endswith('.txt')]
            
            if not input_files:
                print("No input files found. Please create a raw_input.txt file or specify a filename.")
                sys.exit(1)
            
            if len(input_files) == 1:
                input_file = input_files[0]
            else:
                print("Multiple input files found. Please choose one:")
                for i, file in enumerate(input_files):
                    print(f"{i+1}. {file}")
                
                choice = input("Enter the number of the file to process: ")
                try:
                    index = int(choice) - 1
                    input_file = input_files[index]
                except (ValueError, IndexError):
                    print("Invalid choice. Using raw_input.txt as default.")
                    input_file = "raw_input.txt"
        
        # Generate output file name based on input file name
        output_file = input_file.replace('raw_input', 'parsed_output').replace('.txt', '.tex')
        if output_file == input_file:
            output_file = "parsed_output_new.tex"
        
        print(f"Reading {input_file}...")
        with open(input_file, "r", encoding="windows-1252", errors="ignore") as file:
            raw_text = file.read()
        
        print(f"Read {len(raw_text)} characters from {input_file}")
        
        # Parse the data
        print("Parsing genealogy data...")
        latex_output = parse_genealogy_data(raw_text)
        
        # Write the output file
        print(f"Writing to {output_file}...")
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(latex_output)
        
        print(f"✅ LaTeX generation complete: saved to {output_file}")
        print(f"Generated {latex_output.count('\\entry{')} entries")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
