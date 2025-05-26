#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import argparse
from collections import defaultdict

class PersonRegistry:
    """A registry to keep track of person references and IDs."""
    
    def __init__(self):
        """Initialize an empty registry."""
        self.id_map = {}  # Maps normalized names to IDs
        self.name_map = {}  # Maps IDs to original names
    
    def register_person(self, person_id, name):
        """Register a person with their ID and name."""
        norm_name = self._normalize_name(name)
        self.id_map[norm_name] = person_id
        self.name_map[person_id] = name
    
    def get_person_id(self, name):
        """Look up a person's ID by name."""
        norm_name = self._normalize_name(name)
        
        # Try direct match
        if norm_name in self.id_map:
            return self.id_map[norm_name]
        
        # Try partial match (for names that might be incomplete)
        for reg_name, reg_id in self.id_map.items():
            if norm_name in reg_name or reg_name in norm_name:
                return reg_id
                
        # No match found
        return None
    
    def _normalize_name(self, name):
        """Normalize a name for consistent matching."""
        # Convert to lowercase and remove excess spaces
        name = name.lower().strip()
        # Remove titles and suffixes for better matching
        name = re.sub(r'\b(sir|lady|lord|count|countess|duke|duchess|baron|baroness|mr|mrs|miss|dr|rev|jr|sr|i|ii|iii|iv|v)\b\.?', '', name)
        return ' '.join(name.split())

# Initialize the global person registry
person_registry = PersonRegistry()


def hyperlink(name):
    """Convert a name to a LaTeX hyperlink if possible."""
    if not name:
        return ""
    
    # Clean up the name
    name = name.strip()
    
    # Remove period at the end if present
    if name.endswith('.'):
        name = name[:-1]
        add_period = True
    else:
        add_period = False
    
    # Check for special cases
    if name.lower() in ["unknown", "unnamed"]:
        return name + ('.' if add_period else '')
    
    # If the name already contains hyperlink commands, don't add another one
    if "\\hyperlink" in name or "\\href" in name:
        return name + ('.' if add_period else '')
    
    # Detect if the text looks like a date or place rather than a name
    if re.match(r'^(on|in|about|from|at) ', name) or re.search(r'\d{4}', name):
        return name + ('.' if add_period else '')
    
    # Look for a person ID
    person_id = person_registry.get_person_id(name)
    
    if person_id:
        # Create a hyperlink to the person's entry using hyperlink command with bold and underline
        result = "\\hyperlink{person" + str(person_id) + "}{\\textcolor{accent}{\\textbf{\\underline{" + name + "}}}}"
    else:
        # For unlinked names, use href with # to indicate it's a missing link
        result = "\\href{#}{\\textcolor{accent}{\\textbf{\\underline{" + name + "}}}}"
    
    # Add period back if needed
    if add_period:
        result += '.'
    
    return result



def format_person_block(entry_number, name, bio, marriage, children, generation=None):
    """Format a single LaTeX person block."""
    # Add generation title if provided
    block = ""
    if generation:
        block += f"\\generationtitle{{{generation}}}\n"
    
    # Split bio into parts if needed for better formatting
    bio_parts = []
    if len(bio) > 300:
        # Split at a reasonable point (after a sentence or at a comma)
        split_point = bio[:300].rfind(". ")
        if split_point == -1:
            split_point = bio[:300].rfind(", ")
        
        if split_point != -1:
            bio_parts.append(bio[:split_point+1])
            bio_parts.append(bio[split_point+1:])
        else:
            bio_parts.append(bio)
    else:
        bio_parts.append(bio)
    
    # Extract just the name part, separating it from any following bio information
    name_parts = name.split(',', 1)
    actual_name = name_parts[0].strip()
    rest_of_name = name_parts[1].strip() if len(name_parts) > 1 else ""
    
    # Clean up bio - ensure we don't have any marriage info mixed in
    for i in range(len(bio_parts)):
        # Remove any marriage lines that might have gotten into the bio
        if " next married " in bio_parts[i]:
            parts = bio_parts[i].split(" next married ", 1)
            bio_parts[i] = parts[0].strip()
    
    # Create the main entry with proper ID and only the name part bolded
    if len(bio_parts) == 1:
        if rest_of_name:
            block += f"\\entry{{{entry_number}}}{{\\textbf{{{actual_name}}}, {rest_of_name}}}{{{bio_parts[0]}}}\n"
        else:
            block += f"\\entry{{{entry_number}}}{{\\textbf{{{actual_name}}}}}{{{bio_parts[0]}}}\n"
    else:
        if rest_of_name:
            block += f"\\entry{{{entry_number}}}{{\\textbf{{{actual_name}}}, {rest_of_name}}}{{{bio_parts[0]}}}{{{bio_parts[1]}}}\n"
        else:
            block += f"\\entry{{{entry_number}}}{{\\textbf{{{actual_name}}}}}{{{bio_parts[0]}}}{{{bio_parts[1]}}}\n"
    
    # Add marriage information if available - ensure it's on a new line with proper formatting
    if marriage:
        # Make sure marriage text doesn't end with a period that belongs to a previous sentence
        if marriage.endswith('.'):
            last_period = marriage.rfind('.')
            if last_period > 0 and marriage[last_period-1].isalpha():
                # This appears to be a proper sentence end
                marriage = marriage[:last_period] + marriage[last_period:]
        
        # Ensure marriage text doesn't have trailing commas or periods that should be part of the next line
        marriage = marriage.rstrip(',.')
        block += f"\\marriage{{{marriage}}}\n"
    
    # Add children section if there are children - ensure it's on a separate line
    if children:
        # Use proper commands for singular/plural children heading
        if len(children) == 1:
            block += "\\childrenheadingsingular\n"
        else:
            block += "\\childrenheadingplural\n"
        
        # Generate Roman numerals for child entries
        roman_numerals = ['i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x', 
                         'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx']
        
        for idx, (child_number, child_name, has_roman, is_linked) in enumerate(children):
            roman = roman_numerals[min(idx, len(roman_numerals)-1)]
            
            # Only use childentrylinked for children with actual reference numbers
            if is_linked and child_number != "--":
                # This is a hyperlinked child with badge
                block += f"\\childentrylinked{{{child_number}}}{{{roman}}}{{{child_name}}}\n"
            else:
                # For children without reference numbers or with descriptions
                if has_roman:
                    # Regular child entry with roman numeral
                    block += f"\\childentry{{{''}}}{{{roman}}}{{{child_name}}}\n"
                else:
                    # This is a continuation of a child description, format with plain text
                    block += f"\\childentryplain{{{child_name}}}{{{roman}}}{{{''}}}\n"
    
    # Add divider line after the entry
    block += "\\dividerline\n"
    
    return block

def parse_genealogy_data(text):
    """Parse the genealogy data from the text."""
    # Use the global person registry instead of creating a new one
    global person_registry
    person_registry = PersonRegistry()
    
    # Clean up some common OCR issues and special characters
    text = text.replace('\u201c', '"')  # opening double quote
    text = text.replace('\u201d', '"')  # closing double quote
    text = text.replace('\u2019', "'")  # apostrophe
    text = text.replace('\u2013', "-")  # en dash
    text = text.replace('\u2014', "--") # em dash
    
    # Analyze the file to understand its structure
    lines = text.splitlines()
    
    # Various patterns for identifying entry points
    entry_start_pattern = re.compile(r'^(\d{5,10})\.(\s+)(.+)')  # Updated to match 5-10 digit numbers
    alt_entry_start_pattern = re.compile(r'^(\d{5,10})\.\s+(.+)')  # Alternative pattern for potential missed entries
    large_id_entry_pattern = re.compile(r'^(\d{11,})\.(\s+)(.+)')  # Pattern for large ID entries (18138...)
    generation_pattern = re.compile(r'^\s+(\d+)(?:st|nd|rd|th) Generation\s*$', re.IGNORECASE)
    roman_numeral_pattern = re.compile(r'^\s+(?:[ivxlcdm]+)\.\s+', re.IGNORECASE)
    child_entry_pattern = re.compile(r'^\s+(\d{5,10})\s+([ivxlcdm]+)\.\s+(.*)', re.IGNORECASE)
    
    # Skip any lines at the start that might be continuation from previous file
    start_idx = 0
    for i, line in enumerate(lines):
        if entry_start_pattern.match(line) or alt_entry_start_pattern.match(line) or large_id_entry_pattern.match(line):
            start_idx = i
            break
    
    print(f"Starting parsing process...")
    print(f"Reading {len(lines)} lines of text...")
    
    # Divide text into entry sections
    entry_sections = []
    current_entry = []
    in_children_section = False
    in_generation_header = False
    current_generation = None
    
    i = start_idx
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Check for generation markers
        gen_match = generation_pattern.match(line)
        if gen_match:
            current_generation = line.strip()
            in_generation_header = True
            i += 1
            continue
        
        # Check if line starts with a number followed by period - indicates main entry
        # Use all patterns to catch more variations including large IDs
        match = entry_start_pattern.match(line) or alt_entry_start_pattern.match(line) or large_id_entry_pattern.match(line)
        
        if match:
            # This is the start of a new entry
            if current_entry:
                entry_sections.append((current_entry, current_generation))
                current_entry = []
            
            in_generation_header = False
            in_children_section = False
            current_entry.append(line)
        elif line.strip().startswith("Children from this marriage") or line.strip().startswith("The child from this marriage"):
            # Mark that we're in a children section
            in_children_section = True
            if current_entry:
                current_entry.append(line)
        elif in_children_section and (roman_numeral_pattern.match(line) or child_entry_pattern.match(line)):
            # This is a child entry with roman numeral, not a new main entry
            if current_entry:
                current_entry.append(line)
        elif line.strip() and (re.match(r'^(\d{5,10})\.\s+(.+)', line) or re.match(r'^(\d{11,})\.\s+(.+)', line)):
            # This is a new main entry that was missed by our primary pattern
            # It starts with a digit sequence followed by period and space
            if current_entry:
                entry_sections.append((current_entry, current_generation))
                current_entry = []
            
            in_generation_header = False
            in_children_section = False
            current_entry.append(line)
        elif current_entry:
            # Continue with the current entry
            current_entry.append(line)
        
        i += 1
    
    # Add the last entry if it exists
    if current_entry:
        entry_sections.append((current_entry, current_generation))
    
    print(f"Found {len(entry_sections)} potential entry sections")
    
    # Process each entry section
    person_blocks = []
    skipped_entries = []
    
    for entry_lines, generation in entry_sections:
        try:
            # Skip empty entries
            if not entry_lines:
                continue
                
            # First line should contain the entry number and name
            first_line = entry_lines[0]
            match = entry_start_pattern.match(first_line) or alt_entry_start_pattern.match(first_line) or large_id_entry_pattern.match(first_line)
            
            if not match:
                # Skip this section if it doesn't start with a valid entry pattern
                skipped_entries.append(("Unknown", first_line[:30] + "...", "Invalid entry format"))
                continue
            
            entry_number, _, name_part = match.groups()
            entry_number = entry_number.strip()
            name = name_part.strip()
            
            # Join the rest of the lines as content
            content = "\n".join(entry_lines[1:])
            
            # Now we'll process this entry's content
            bio_lines = []
            marriage = ""
            children = []
            in_children = False
            multiple_marriages = []
            
            # Process line by line
            content_lines = content.splitlines()
            i = 0
            child_continuation = False
            current_child = None
            
            while i < len(content_lines):
                line = content_lines[i].strip()
                
                # Skip empty lines
                if not line:
                    i += 1
                    continue
                
                # Check for possible new entry pattern (ID with period) and exit if found
                if entry_start_pattern.match(line):
                    # This looks like a new entry starting - don't process here
                    break
                
                # Check for children section marker
                if re.search(r'^(?:(?:The )?[Cc]hild(?:ren)?|(?:The )?[Cc]hildren|The following child(?:ren)?) (?:from|of) this marriage', line):
                    in_children = True
                    i += 1
                    continue
                
                # For lines like "His/Her child was:" or "His/Her children were:"
                if re.search(r'^(?:His|Her) child(?:ren)? (?:was|were):', line):
                    in_children = True
                    i += 1
                    continue
                
                # Check for marriage line (only before children section)
                if (" married " in line.lower() or " next married " in line.lower()) and not in_children:
                    # Handle "next married" which indicates a new marriage
                    if "next married" in line.lower() and marriage:
                        # Store the existing marriage
                        if marriage:
                            multiple_marriages.append(marriage)
                        marriage = line
                    else:
                        # Check if the next line might be part of the marriage
                        if i + 1 < len(content_lines):
                            next_line = content_lines[i + 1].strip()
                            # Check for common marriage date/place patterns
                            is_marriage_continuation = (
                                re.match(r'^(?:on |in |about |circa |c\. )?\d{1,2}\s+[A-Za-z]+\s+\d{4}', next_line) or
                                re.match(r'^(?:on |in |about |circa |c\. )?\d{4}', next_line) or
                                next_line.startswith(", ") or
                                next_line.startswith("on ") or
                                next_line.startswith("in ") or
                                next_line.startswith("before ") or
                                next_line.startswith("after ")
                            )
                            
                            if is_marriage_continuation:
                                marriage = f"{line} {next_line}"
                                i += 2
                                continue
                        
                        marriage = line
                    
                    i += 1
                    continue
                
                # Process children lines
                if in_children:
                    # Reset in_children flag if we encounter what appears to be a new section
                    if entry_start_pattern.match(line):
                        # This looks like a new entry number, don't process here
                        in_children = False
                        break
                    
                    # Check for patterns
                    roman_match = re.match(r'^([ivxlcdm]+)\.(\s+)(.*)', line, re.IGNORECASE)
                    id_with_roman_match = re.match(r'^(\d{5,10})\s+([ivxlcdm]+)\.(\s+)(.*)', line, re.IGNORECASE)
                    
                    if id_with_roman_match:
                        # Child with ID and Roman numeral
                        cid, roman, space, child_text = id_with_roman_match.groups()
                        children.append((cid.strip(), hyperlink(child_text.strip()), True, True))
                        child_continuation = False
                        current_child = None
                    elif roman_match and len(roman_match.group(1)) <= 6:  # Limit length to avoid false positives
                        # This is a child entry with a Roman numeral
                        roman, space, child_text = roman_match.groups()
                        
                        # Check for number before name (numeric ID)
                        number_match = re.match(r'(?:(\d+)\s+)(.*)', child_text)
                        
                        if number_match:
                            # Child with a number ID
                            cid, cname = number_match.groups()
                            children.append((cid.strip(), hyperlink(cname.strip()), True, True))
                            child_continuation = False
                            current_child = None
                        elif "next married" in child_text.lower() or ("married" in child_text.lower() and not child_text.lower().startswith(("he", "she"))):
                            # This is a marriage line, not a child
                            if marriage:
                                multiple_marriages.append(marriage)
                            marriage = child_text
                            i += 1
                            continue
                        else:
                            # Child without number ID but still hyperlink the name
                            children.append(("--", hyperlink(child_text.strip()), True, False))
                            child_continuation = False
                            current_child = None
                    else:
                        # Special case for alternative formats
                        number_format = re.match(r'^\(?(\d+)\)?\s+(?:[ivxlcdm]+)\.?\s+(.*)', line, re.IGNORECASE)
                        
                        if number_format:
                            cid, cname = number_format.groups()
                            children.append((cid.strip(), hyperlink(cname.strip()), True, True))
                            child_continuation = False
                            current_child = None
                        elif "next married" in line.lower():
                            # This is a new marriage, store the existing one
                            if marriage:
                                multiple_marriages.append(marriage)
                            marriage = line
                            i += 1
                            continue
                        elif children:
                            # Add to the last child's description
                            # This is likely a continuation line for a child description
                            if not child_continuation:
                                # Start a new continuation child
                                children.append(("--", line.strip(), False, False))
                                child_continuation = True
                                current_child = len(children) - 1
                            else:
                                # Append to the existing continuation child
                                if current_child is not None and current_child < len(children):
                                    old_text = children[current_child][1]
                                    children[current_child] = (children[current_child][0], old_text + " " + line.strip(), False, False)
                        else:
                            # Not a proper child format, add to bio
                            bio_lines.append(line)
                    
                    i += 1
                    continue
                
                # Everything else goes to bio
                bio_lines.append(line)
                i += 1
            
            # Join bio lines with spaces, ensuring proper spacing
            bio = " ".join(bio_lines).strip()
            
            # Format URLs in bio and marriage text
            bio = re.sub(r'<(https?://[^>]+)>', r'\\url{\1}', bio)
            bio = re.sub(r'(https?://\S+)', r'\\url{\1}', bio)
            
            # Enhanced pattern for parent references in bio
            # First, try a more complete pattern for "son/daughter of X and Y"
            parent_pattern = re.compile(r'\b(son|daughter) of ([^.,;()]+) and ([^.,;()]+?)(?=[.,;()]|$)')
            bio_with_parents = parent_pattern.sub(
                lambda m: f"{m.group(1)} of {hyperlink(m.group(2).strip())} and {hyperlink(m.group(3).strip())}",
                bio
            )
            
            # Handle single parent references
            single_parent_pattern = re.compile(r'\b(son|daughter) of ([^.,;()]+?)(?=[.,;()]|$)')
            bio_with_parents = single_parent_pattern.sub(
                lambda m: f"{m.group(1)} of {hyperlink(m.group(2).strip())}",
                bio_with_parents
            )
            
            bio = bio_with_parents
            
            # Process all marriages
            if multiple_marriages:
                # Add the current marriage if it exists
                if marriage and marriage not in multiple_marriages:
                    multiple_marriages.append(marriage)
                
                # Use the first marriage as the primary one
                marriage = multiple_marriages[0]
                
                # Add subsequent marriages as separate paragraphs in the bio
                if len(multiple_marriages) > 1:
                    for additional_marriage in multiple_marriages[1:]:
                        # Only add if not already in the bio
                        if additional_marriage not in bio:
                            # Format the additional marriage for the bio
                            additional_marriage = additional_marriage.strip()
                            if additional_marriage.startswith("next married"):
                                bio += f" {additional_marriage}"
                            else:
                                bio += f" {name.split(',')[0].strip()} {additional_marriage}"
            
            # Format marriage with hyperlinks, ensuring proper spacing
            if marriage:
                marriage = marriage.strip()
                marriage = re.sub(r'<(https?://[^>]+)>', r'\\url{\1}', marriage)
                marriage = re.sub(r'(https?://\S+)', r'\\url{\1}', marriage)
                
                # Enhanced pattern for parent references in marriage text
                marriage = parent_pattern.sub(
                    lambda m: f"{m.group(1)} of {hyperlink(m.group(2).strip())} and {hyperlink(m.group(3).strip())}",
                    marriage
                )
                
                # Handle single parent references
                marriage = single_parent_pattern.sub(
                    lambda m: f"{m.group(1)} of {hyperlink(m.group(2).strip())}",
                    marriage
                )
                
                # Handle the marriage pattern itself
                # First, try to identify typical marriage patterns with dates
                marriage_date_pattern = re.compile(r'(married [^.,;]+) (on|about|in) ([^.,;]+)')
                marriage = marriage_date_pattern.sub(
                    lambda m: f"married {hyperlink(m.group(1).replace('married ', '').strip())} {m.group(2)} {m.group(3)}",
                    marriage
                )
                
                # Then handle the simpler marriage case without dates
                if " married " in marriage and not marriage_date_pattern.search(marriage):
                    parts = marriage.split(" married ", 1)
                    person_name = parts[0].strip()
                    rest = parts[1].strip()
                    
                    # Handle "X married Y" pattern
                    if ", " in rest and not any(marker in rest.split(", ")[0] for marker in ["on ", "in ", "about "]):
                        # This might be "Y, son/daughter of Z" or "Y, on date"
                        spouse_part, extra_info = rest.split(", ", 1)
                        
                        # Check if it's a parent reference - already processed above
                        if not re.match(r'(on|in|about)', extra_info):
                            marriage = f"{person_name} married {hyperlink(spouse_part.strip())}, {extra_info.strip()}"
                    elif not any(marker in rest for marker in ["on ", "in ", "about "]):
                        # Just a simple "X married Y" with no extra info
                        marriage = f"{person_name} married {hyperlink(rest.strip())}"
                
                # Remove any trailing periods or commas before command ends
                marriage = marriage.rstrip('.,')
            
            # Register this person
            person_registry.register_person(entry_number, name)
            
            # Create formatted block
            person_blocks.append(format_person_block(
                entry_number, 
                name, 
                bio, 
                marriage, 
                children, 
                generation
            ))
        
        except Exception as e:
            # Log errors but continue processing
            first_line = entry_lines[0] if entry_lines else "Unknown"
            entry_match = re.match(r'^(\d+)\.', first_line)
            entry_number = entry_match.group(1) if entry_match else "Unknown"
            skipped_entries.append((entry_number, first_line[:30] + "...", f"Error: {str(e)}"))
            print(f"Error processing entry {entry_number}: {str(e)}")
    
    # Second pass to ensure all hyperlinks are properly generated now that all entries are registered
    final_blocks = []
    for block in person_blocks:
        # Re-process hyperlinks in the block now that all entries are registered
        # Match both href and hyperlink patterns that need to be reprocessed
        block = re.sub(
            r'\\href{#}{\\textcolor{accent}{\\textbf{\\underline{([^}]+)}}}',
            lambda m: hyperlink(m.group(1)),
            block
        )
        block = re.sub(
            r'\\hyperlink{person}{\\textcolor{accent}{\\textbf{\\underline{([^}]+)}}}',
            lambda m: hyperlink(m.group(1)),
            block
        )
        
        # Fix the parent references that might have been missed
        block = re.sub(
            r'\b(son|daughter) of ([A-Z][^.,;]+?) and ([A-Z][^.,;]+?)(?=[.,;)]|\\)',
            lambda m: f"{m.group(1)} of {hyperlink(m.group(2).strip())} and {hyperlink(m.group(3).strip())}",
            block
        )
        
        # Fix single parent references
        block = re.sub(
            r'\b(son|daughter) of ([A-Z][^.,;]+?)(?=[.,;)]|\\)',
            lambda m: f"{m.group(1)} of {hyperlink(m.group(2).strip())}",
            block
        )
        
        # Remove trailing periods on marriage commands
        block = re.sub(
            r'\\marriage{([^}]+)}\.?',
            r'\\marriage{\1}',
            block
        )
        
        # Fix URLs in blocks to ensure they use \url command
        block = re.sub(r'<(https?://[^>]+)>', r'\\url{\1}', block)
        block = re.sub(r'(?<!\\url\{)(https?://\S+)(?!\})', r'\\url{\1}', block)
        
        final_blocks.append(block)
    
    # Write skipped entries to log file
    with open("skipped_entries.log", "w", encoding="utf-8") as f:
        for entry_number, name, reason in skipped_entries:
            f.write(f"Entry {entry_number}: {name} - {reason}\n")
    
    print(f"Successfully processed {len(person_blocks)} entries")
    print(f"Skipped {len(skipped_entries)} entries")
    
    return final_blocks

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
        person_blocks = parse_genealogy_data(raw_text)
        
        # Join person blocks into a single string
        latex_output = "\n".join(person_blocks)
        
        # Write the output file
        print(f"Writing to {output_file}...")
        with open(output_file, "w", encoding="utf-8") as file:
            file.write(latex_output)
        
        print(f"✅ LaTeX generation complete: saved to {output_file}")
        print(f"Generated {latex_output.count('\\entry{')} entries")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
