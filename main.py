import os
import json
import re
from datetime import datetime

def sanitize_filename(name):
    """Sanitizes a string to be used as a valid filename."""
    # First, remove square brackets which are problematic for wikilinks
    name = name.replace('[', '').replace(']', '')
    # Then, remove other characters that are invalid in filenames
    return re.sub(r'[\\/*?:"<>|]', '_', name)

def wikify_text(text):
    """Converts {{...}} syntax to [[...]] wikilinks for Obsidian."""
    if not isinstance(text, str):
        return text
    # This regex finds {{text}} and converts it to [[text]]
    return re.sub(r'\{\{([^}]+)\}\}', r'[[\1]]', text)

def process_tools_file(tools_data, output_dir, all_tools, scraped_date):
    """
    Process the tools JSON data and create markdown files with Obsidian metadata.
    """
    print("Processing tools file...")
    for tool in tools_data.get('values', []):
        tool_name = tool.get('tool', 'Unnamed Tool')
        safe_tool_name = sanitize_filename(tool_name)
        all_tools.add(safe_tool_name)
        file_path = os.path.join(output_dir, f"{safe_tool_name}.md")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            # --- YAML Frontmatter ---
            f.write('---\n')
            f.write(f'title: "{tool_name}"\n')
            f.write(f'data-scraped: {scraped_date}\n')
            f.write('type: tool\n')
            
            # Create aliases from the names list, excluding the main tool name
            aliases = [name.get('name') for name in tool.get('names', []) if name.get('name') and name.get('name') != tool_name]
            if aliases:
                f.write('aliases:\n')
                for alias in aliases:
                    f.write(f'  - "{alias}"\n') # Quote aliases to handle special characters
            f.write('---\n\n')

            # --- Main Content ---
            f.write(f"# {tool_name}\n\n")

            if tool.get('names'):
                f.write("## Names\n")
                for name in tool.get('names', []):
                    f.write(f"- {name.get('name', '')}\n")
                f.write("\n")

            if tool.get('description'):
                f.write("## Description\n")
                f.write(f"{wikify_text(tool.get('description'))}\n\n")

            if tool.get('category'):
                f.write(f"**Category:** {tool.get('category')}\n\n")

            if tool.get('type'):
                f.write("## Type\n")
                for t in tool.get('type', []):
                    f.write(f"- {t}\n")
                f.write("\n")

            if tool.get('information'):
                f.write("## Information\n")
                for info in tool.get('information', []):
                    f.write(f"- {wikify_text(info)}\n")
                f.write("\n")

            if tool.get('mitre-attack'):
                f.write("## MITRE ATT&CK\n")
                for attack in tool.get('mitre-attack', []):
                    f.write(f"- {attack}\n")
                f.write("\n")

            if tool.get('malpedia'):
                f.write("## Malpedia\n")
                for mal in tool.get('malpedia', []):
                    f.write(f"- {mal}\n")
                f.write("\n")

            if tool.get('alienvault-otx'):
                f.write("## AlienVault OTX\n")
                for otx in tool.get('alienvault-otx', []):
                    f.write(f"- {otx}\n")
                f.write("\n")

def process_groups_file(groups_data, output_dir, all_groups, all_sectors, all_countries, all_tools, scraped_date):
    """
    Process the groups JSON data and create markdown files with Obsidian metadata.
    """
    print("Processing groups file...")
    for group in groups_data.get('values', []):
        actor_name = group.get('actor', 'Unnamed Group')
        safe_actor_name = sanitize_filename(actor_name)
        all_groups.add(safe_actor_name)
        file_path = os.path.join(output_dir, f"{safe_actor_name}.md")

        # Collect sectors and countries for this group
        sectors = group.get('observed-sectors', [])
        countries = group.get('country', [])
        for sector in sectors:
            all_sectors.add(sector)
        for country in countries:
            all_countries.add(country)

        with open(file_path, 'w', encoding='utf-8') as f:
            # --- YAML Frontmatter ---
            f.write('---\n')
            f.write(f'title: "{actor_name}"\n')
            f.write(f'data-scraped: {scraped_date}\n')
            f.write('type: group\n')

            aliases = [name.get('name') for name in group.get('names', []) if name.get('name') and name.get('name') != actor_name]
            if aliases:
                f.write('aliases:\n')
                for alias in aliases:
                    f.write(f'  - "{alias}"\n') # Use quotes for aliases to be safe
            
            if sectors:
                f.write('observed-sectors:\n')
                for sector in sectors:
                    f.write(f'  - "[[{sanitize_filename(sector)}]]"\n')
            
            if countries:
                f.write('observed-countries:\n')
                for country in countries:
                    f.write(f'  - "[[{sanitize_filename(country)}]]"\n')

            f.write('---\n\n')
            
            # --- Main Content ---
            f.write(f"# {actor_name}\n\n")

            if group.get('description'):
                f.write("## Description\n")
                f.write(f"{wikify_text(group.get('description'))}\n\n")

            if group.get('names'):
                f.write("## Names\n")
                f.write("| Name | Name Giver |\n")
                f.write("|---|---|\n")
                for name in group.get('names', []):
                    f.write(f"| {name.get('name', '')} | {name.get('name-giver', '')} |\n")
                f.write("\n")
            
            if sectors:
                f.write("## Observed Sectors\n")
                for sector in sectors:
                    f.write(f"- [[{sanitize_filename(sector)}]]\n")
                f.write("\n")

            if countries:
                f.write("## Observed Countries\n")
                for country in countries:
                    f.write(f"- [[{sanitize_filename(country)}]]\n")
                f.write("\n")

            if group.get('tools'):
                f.write("## Tools\n")
                for tool in group.get('tools', []):
                    f.write(f"- [[{sanitize_filename(tool)}]]\n")
                f.write("\n")

            if group.get('mitre-attack'):
                f.write("## MITRE ATT&CK\n")
                for attack in group.get('mitre-attack', []):
                    f.write(f"- {attack}\n")
                f.write("\n")
            
            if group.get('malpedia'):
                f.write("## Malpedia\n")
                for mal in group.get('malpedia', []):
                    f.write(f"- {mal}\n")
                f.write("\n")

            if group.get('alienvault-otx'):
                f.write("## AlienVault OTX\n")
                for otx in group.get('alienvault-otx', []):
                    f.write(f"- {otx}\n")
                f.write("\n")

            if group.get('activity'):
                f.write("## Activity\n")
                for act in group.get('activity', []):
                    f.write(f"- **{act.get('date', 'N/A')}:** {wikify_text(act.get('activity', ''))}\n")
                f.write("\n")

            if group.get('counter-operations'):
                f.write("## Counter Operations\n")
                for op in group.get('counter-operations', []):
                    f.write(f"- **{op.get('date', 'N/A')}:** {wikify_text(op.get('activity', ''))}\n")
                f.write("\n")
            
            if group.get('information'):
                f.write("## Information & Links\n")
                for info in group.get('information', []):
                    f.write(f"- {wikify_text(info)}\n")
                f.write("\n")

def create_index_file(output_dir, title, items):
    """Creates an index markdown file with a list of links."""
    file_path = os.path.join(output_dir, f"{sanitize_filename(title)}.md")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        for item in sorted(items):
            f.write(f"- [[{item}]]\n")

def create_placeholder_pages(output_dir, items, item_type):
    """Creates placeholder pages for items like sectors or countries."""
    for item in items:
        safe_name = sanitize_filename(item)
        file_path = os.path.join(output_dir, f"{safe_name}.md")
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('---\n')
                f.write(f'type: {item_type}\n')
                f.write('---\n\n')
                f.write(f'# {item}\n\n')
                f.write(f'A page for the {item_type} [[{item}]].\n')


def handle_malformed_json(file_path):
    """
    Tries to repair and load a malformed JSON file by fixing common errors
    like unquoted URLs and file truncation.
    """
    print(f"Attempting to repair and parse malformed JSON from '{file_path}'...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Step 1: Find lines that look like unquoted URLs and wrap them in quotes.
        url_pattern = re.compile(r'^(\s*)(https?://[^\s"]+)\s*$', re.MULTILINE)
        content_with_quoted_urls = url_pattern.sub(r'\1"\2",', content)
        
        # Step 2: Clean up trailing commas that might have been added or already existed.
        trailing_comma_pattern = re.compile(r',\s*([\]\}])', re.MULTILINE)
        repaired_content = trailing_comma_pattern.sub(r'\1', content_with_quoted_urls)
        
        data = json.loads(repaired_content)
        print("Successfully parsed repaired JSON.")
        return data

    except json.JSONDecodeError as e:
        print(f"Parsing after regex repair failed: {e}. All repair attempts failed.")
        return None
    except Exception as repair_error:
        print(f"An unexpected error occurred during the repair process. Error: {repair_error}")
        return None

def main():
    """
    Main function to load JSON files and initiate processing.
    """
    input_dir = 'inputs'
    output_dir = 'output'
    tools_file_path = os.path.join(input_dir, 'Threat Group Card - All tools.json')
    groups_file_path = os.path.join(input_dir, 'Threat Group Card - All groups.json')
    scraped_date = datetime.now().strftime('%Y-%m-%d')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    all_tools, all_groups, all_sectors, all_countries = set(), set(), set(), set()

    # Load and process the tools file
    print(f"--- Processing Tools ---")
    try:
        with open(tools_file_path, 'r', encoding='utf-8') as f:
            tools_data = json.load(f)
        process_tools_file(tools_data, output_dir, all_tools, scraped_date)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Initial processing failed: {e}. Attempting repair...")
        tools_data = handle_malformed_json(tools_file_path)
        if tools_data:
            process_tools_file(tools_data, output_dir, all_tools, scraped_date)
        else:
            print(f"Could not process '{tools_file_path}'.")

    # Load and process the groups file
    print(f"\n--- Processing Groups ---")
    try:
        with open(groups_file_path, 'r', encoding='utf-8') as f:
            groups_data = json.load(f)
        process_groups_file(groups_data, output_dir, all_groups, all_sectors, all_countries, all_tools, scraped_date)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Initial processing failed: {e}. Attempting repair...")
        groups_data = handle_malformed_json(groups_file_path)
        if groups_data:
            process_groups_file(groups_data, output_dir, all_groups, all_sectors, all_countries, all_tools, scraped_date)
        else:
            print(f"Could not process '{groups_file_path}'.")
    
    # Create placeholder pages and index files
    print("\n--- Finalizing Database ---")
    create_placeholder_pages(output_dir, all_sectors, 'sector')
    create_placeholder_pages(output_dir, all_countries, 'country')
    
    create_index_file(output_dir, 'index-tools', all_tools)
    create_index_file(output_dir, 'index-groups', all_groups)
    create_index_file(output_dir, 'index-sectors', all_sectors)
    create_index_file(output_dir, 'index-countries', all_countries)

    print("\nScript finished.")

if __name__ == "__main__":
    main()
