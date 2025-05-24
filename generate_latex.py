import re
import sys
import os

class PersonRegistry:
    """Track person names and their IDs for hyperlinking."""
    def __init__(self):
        self.name_to_id = {}
        self.normalized_to_id = {}  # Normalized versions for fuzzy matching
        
    def register_person(self, person_id, name):
        """Register a person with their ID and name."""
        self.name_to_id[name.strip()] = person_id
        
        # Create normalized versions for better matching
        normalized = self._normalize_name(name)
        self.normalized_to_id[normalized] = person_id
        
        # Handle names with middle initials by creating versions without them
        if '.' in name:
            simplified = re.sub(r'\s+[A-Z]\.\s+', ' ', name)
            if simplified != name:
                self.normalized_to_id[self._normalize_name(simplified)] = person_id
    
    def get_person_id(self, name):
        """Get the ID for a person if registered."""
        # First try exact match
        if name.strip() in self.name_to_id:
            return self.name_to_id[name.strip()]
            
        # Then try normalized match
        normalized = self._normalize_name(name)
        if normalized in self.normalized_to_id:
            return self.normalized_to_id[normalized]
            
        # Try without middle initials
        if '.' in name:
            simplified = re.sub(r'\s+[A-Z]\.\s+', ' ', name)
            if self._normalize_name(simplified) in self.normalized_to_id:
                return self.normalized_to_id[self._normalize_name(simplified)]
                
        return None
    
    def _normalize_name(self, name):
        """Normalize a name for fuzzy matching."""
        return name.lower().strip()

# Create a global person registry
person_registry = PersonRegistry()

def hyperlink(name):
    """Format a name with hyperlink appearance."""
    # Remove angle brackets around links
    name = re.sub(r'<(https?://[^>]+)>', r'\1', name)
    
    # Don't process Wikipedia URLs as hyperlinks with special formatting
    if name.startswith('http'):
        return name
        
    parts = [n.strip() for n in name.split(" and ")]
    hyperlinked_parts = []
    
    for part in parts:
        # Check if we know this person's ID
        person_id = person_registry.get_person_id(part)
        
        if person_id:
            # Create a proper hyperlink to the person's entry
            hyperlinked_parts.append(f"\\hyperlink{{person{person_id}}}{{\\textcolor{{accent}}{{\\textbf{{\\underline{{{part}}}}}}}}}")
        else:
            # Use the original styling with no functional link
            hyperlinked_parts.append(f"\\href{{#}}{{\\textcolor{{accent}}{{\\textbf{{\\underline{{{part}}}}}}}}}")
    
    return " and ".join(hyperlinked_parts)

def format_person_block(entry_number, name, bio, marriage, children, generation=None):
    """Format a single LaTeX person block."""
    # Register this person in the registry
    person_registry.register_person(entry_number, name)
    
    # Add generation title if provided and it's a new generation
    block = ""
    if generation:
        block += f"\\generationtitle{{{generation}}}\n"
    
    block += f"\\entry{{{entry_number}}}{{{name}}}{{{bio}}}\n"
    
    if marriage:
        block += f"\\marriage{{{marriage}}}\n"
    
    if children:
        # Use proper commands for singular/plural children heading
        if len(children) == 1:
            block += "\\childrenheadingsingular\n"
        else:
            block += "\\childrenheadingplural\n"
        
        roman_numerals = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 'xi', 'xii', 'xiii', 'xiv', 'xv']
        
        for idx, (child_number, child_name, has_roman, is_linked) in enumerate(children):
            roman = roman_numerals[min(idx, len(roman_numerals)-1)]
            
            # Only use childentrylinked for children with actual reference numbers
            if is_linked and child_number != "--":
                # This is a hyperlinked child with badge
                block += f"\\childentrylinked{{{child_number}}}{{{roman}}}{{{child_name}}}\n"
            else:
                # For children without reference numbers but with descriptions
                if "was born" in child_name or "died" in child_name:
                    # Use childentry for regular entries without splitting
                    block += f"\\childentry{{{''}}}{{{roman}. {child_name}}}\n"
                else:
                    # Extract name part for bolding (before any descriptive text)
                    name_parts = child_name.split(',', 1)
                    if len(name_parts) > 1:
                        name_part, desc_part = name_parts
                        block += f"\\childentryplain{{{name_part.strip()}}}{{{roman}}}{{{', ' + desc_part.strip()}}}\n"
                    else:
                        # Use childentry for regular entries without splitting
                        block += f"\\childentry{{{''}}}{{{roman}. {child_name}}}\n"
    
    # Add divider line after the entry
    if not generation:
        block += "\\dividerline\n"
    
    return block

def parse_genealogy_data(text):
    """Parse raw genealogy text into LaTeX blocks."""
    # Reset the person registry for a new parsing session
    global person_registry
    person_registry = PersonRegistry()
    
    # Use a more robust pattern to identify entry start points
    entry_pattern = r"(?:^|\n)(\d{1,4})\.[\s]+([^,\n]+)(?:,\s*|\s*\n)(.+?)(?=(?:\n\d{1,4}\.\s)|$)"
    entries = re.findall(entry_pattern, text, re.DOTALL)
    
    # First pass - register all persons with their IDs
    print("First pass: registering all persons...")
    for entry_number, name, _ in entries:
        person_registry.register_person(entry_number.strip(), name.strip())
        
    # Second pass - process entries with proper hyperlinks
    print("Second pass: creating formatted entries...")
    
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

            if entry_number == "2":  # Special logging for entry #2
                print(f"\nProcessing entry {entry_number}. {name}")
                print(f"Found {len(lines)} lines to process")
                for l in lines:
                    print(f"  Line: {l}")

            # Process each line
            for line_index, line in enumerate(lines):
                # Check for children section marker - more inclusive pattern
                if re.search(r'^(?:(?:The )?[Cc]hild(?:ren)?|(?:The )?[Cc]hildren|The following child(?:ren)?) (?:from|of) this marriage', line):
                    in_children = True
                    if entry_number == "2":  # Special logging
                        print(f"  Found children marker: {line}")
                    continue
                # Check for special sections to skip or include in bio
                elif line.lower().startswith(("general notes:", "obituary:")):
                    bio_lines.append(line)
                    continue
                # Check for marriage line (only before children section)
                elif " married " in line.lower() and not in_children:
                    # Check if the next line might contain the continuation of the marriage info
                    if line_index + 1 < len(lines):
                        next_line = lines[line_index + 1].strip()
                        # If next line starts with a date or year pattern, it's likely part of the marriage
                        if re.match(r'^(?:on |in |about |circa |c\. )?\d{1,2}\s+[A-Za-z]+\s+\d{4}', next_line) or \
                           re.match(r'^(?:on |in |about |circa |c\. )?\d{4}', next_line):
                            marriage = f"{line} {next_line}"
                            # Skip the next line since we've included it
                            lines[line_index + 1] = ""
                            if entry_number == "2":  # Special logging
                                print(f"  Combined marriage line: {marriage}")
                        else:
                            marriage = line
                            if entry_number == "2":  # Special logging
                                print(f"  Found marriage line: {marriage}")
                    else:
                        marriage = line
                        if entry_number == "2":  # Special logging
                            print(f"  Found marriage line: {marriage}")
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
                            if entry_number == "2":  # Special logging
                                print(f"  Child with ID: [{cid.strip()}] {cname.strip()}")
                        else:
                            # Child without a number ID - don't hyperlink description parts
                            if "was born" in child_text or "died" in child_text:
                                # For entries with descriptions, only hyperlink the name part
                                name_match = re.match(r'([^\.]+?)(?:\s+was\s+|\s+died\s+)(.*)', child_text)
                                if name_match:
                                    name_part, desc_part = name_match.groups()
                                    children.append(("--", f"{hyperlink(name_part.strip())} was {desc_part.strip()}", True, False))
                                    if entry_number == "2":  # Special logging
                                        print(f"  Child with birth/death: {name_part.strip()} | was {desc_part.strip()}")
                                else:
                                    # Just add the whole text without hyperlink
                                    children.append(("--", child_text.strip(), True, False))
                                    if entry_number == "2":  # Special logging
                                        print(f"  Child without parsed desc: {child_text.strip()}")
                            else:
                                # For simple name entries
                                children.append(("--", hyperlink(child_text.strip()), True, False))
                                if entry_number == "2":  # Special logging
                                    print(f"  Simple child entry: {child_text.strip()}")
                    else:
                        # This is a continuation of a child description or a malformed entry
                        # Try to detect if it has a number format like "1020 i. and died on..."
                        number_in_circle = re.match(r'^\(?(\d+)\)?\s+i\.\s+(.*)', line)
                        
                        if number_in_circle:
                            # This is a special case with a number in parentheses or circle
                            cid, cname = number_in_circle.groups()
                            children.append((cid.strip(), hyperlink(cname.strip()), True, True))
                            if entry_number == "2":  # Special logging
                                print(f"  Special child with ID: [{cid.strip()}] {cname.strip()}")
                        else:
                            # Just add this as regular text (not hyperlinked)
                            children.append(("--", line.strip(), False, False))
                            if entry_number == "2":  # Special logging
                                print(f"  Non-matched child line: {line.strip()}")
                # Everything else goes to bio
                elif line.strip():  # Only add non-empty lines
                    bio_lines.append(line)
            
            # If no marriage line was found but there are children, the first bio line might be the marriage line
            if not marriage and children and bio_lines:
                # Check if any bio line contains "married"
                for idx, line in enumerate(bio_lines):
                    if " married " in line.lower():
                        marriage = line
                        bio_lines.pop(idx)
                        if entry_number == "2":  # Special logging
                            print(f"  Found marriage in bio: {marriage}")
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
            output_file = "parsed_output.tex"
        
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
