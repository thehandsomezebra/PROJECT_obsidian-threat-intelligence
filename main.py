import os
import json
import re
from datetime import datetime

def normalize_name(name):
    """Removes surrounding square brackets from a name to ensure consistency."""
    if not isinstance(name, str):
        return str(name)
    # This removes all square brackets from the string.
    return name.replace('[', '').replace(']', '')

def sanitize_for_filename(name):
    """Sanitizes a string to be used as a valid filename."""
    # First, normalize the name to remove brackets, then sanitize for the filesystem.
    clean_name = normalize_name(name)
    return re.sub(r'[\\/*?:"<>|]', '_', clean_name)

def wikify_text(text):
    """Converts {{...}} syntax to [[...]] wikilinks for Obsidian."""
    if not isinstance(text, str):
        return text
    return re.sub(r'\{\{([^}]+)\}\}', r'[[\1]]', text)

def write_field(file_handle, key, value):
    """Intelligently writes a key-value pair to the markdown file."""
    if not value:
        return # Don't write empty fields

    header = key.replace('-', ' ').replace('_', ' ').title()
    file_handle.write(f"## {header}\n")

    if isinstance(value, list):
        if all(isinstance(i, str) for i in value):
            if key in ['country', 'observed-countries', 'observed-sectors', 'tools']:
                 for item in value:
                    # Use the sanitized (and normalized) name for the link
                    file_handle.write(f"- [[{sanitize_for_filename(item)}]]\n")
            else:
                for item in value:
                    file_handle.write(f"- {wikify_text(item)}\n")

        elif all(isinstance(i, dict) for i in value):
            if key in ['operations', 'counter-operations', 'activity']:
                for item in value:
                    date = item.get('date', 'N/A')
                    activity_text = item.get('activity', '')
                    file_handle.write(f"- **{date}:** {wikify_text(activity_text)}\n")
            else:
                if not value: return
                headers = sorted(value[0].keys())
                file_handle.write(f"| {' | '.join(h.title() for h in headers)} |\n")
                file_handle.write(f"|{'---|' * len(headers)}\n")
                for item in value:
                    row = [wikify_text(str(item.get(h, ''))) for h in headers]
                    file_handle.write(f"| {' | '.join(row)} |\n")
    else:
        file_handle.write(f"{wikify_text(str(value))}\n")
    
    file_handle.write("\n")


def process_record(record, output_dir, record_type, all_sets, scraped_date):
    """Generic function to process a single record (a tool or a group)."""
    main_name_key = "actor" if record_type == "group" else "tool"
    main_name = record.get(main_name_key, f"Unnamed {record_type}")
    safe_filename = sanitize_for_filename(main_name)
    file_path = os.path.join(output_dir, f"{safe_filename}.md")
    
    all_sets[f"all_{record_type}s"].add(safe_filename)

    if record_type == "group":
        for sector in record.get('observed-sectors', []): all_sets['all_sectors'].add(normalize_name(sector))
        for country in record.get('observed-countries', []): all_sets['all_countries'].add(normalize_name(country))
        for country in record.get('country', []): all_sets['all_countries'].add(normalize_name(country))

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('---\n')
        f.write(f'title: "{normalize_name(main_name)}"\n')
        f.write(f'data-scraped: {scraped_date}\n')
        f.write(f'type: {record_type}\n')
        
        aliases = [name.get('name') for name in record.get('names', []) if name.get('name') and name.get('name') != main_name]
        if aliases:
            f.write('aliases:\n')
            for alias in aliases: f.write(f'  - "{normalize_name(alias)}"\n')
        
        if 'country' in record and record['country']:
            f.write('country:\n')
            for item in record['country']:
                 f.write(f'  - "[[{sanitize_for_filename(item)}]]"\n')
        
        f.write('---\n\n')
        f.write(f"# {normalize_name(main_name)}\n\n")

        preferred_order = [
            'description', 'names', 'country', 'sponsor', 'motivation', 'first-seen', 'category', 'type',
            'observed-sectors', 'observed-countries', 'tools', 'operations', 'activity', 
            'counter-operations', 'information', 'mitre-attack', 'malpedia', 'alienvault-otx', 'playbook'
        ]
        
        processed_keys = {main_name_key}
        for key in preferred_order:
            if key in record:
                write_field(f, key, record[key])
                processed_keys.add(key)
        
        other_info_header_written = False
        for key, value in record.items():
            if key not in processed_keys and value:
                if not other_info_header_written:
                    f.write("## Other Information\n")
                    other_info_header_written = True
                write_field(f, key, value)

def create_index_file(output_dir, title, items):
    """Creates an index markdown file with a list of links."""
    file_path = os.path.join(output_dir, f"{sanitize_for_filename(title)}.md")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        for item in sorted(items): f.write(f"- [[{sanitize_for_filename(item)}]]\n")

def create_placeholder_pages(output_dir, items, item_type, scraped_date):
    """Creates placeholder pages for items like sectors or countries."""
    for item in items:
        clean_item_name = normalize_name(item)
        safe_name = sanitize_for_filename(clean_item_name)
        file_path = os.path.join(output_dir, f"{safe_name}.md")
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('---\n')
                f.write(f'title: "{clean_item_name}"\n')
                f.write(f'data-scraped: {scraped_date}\n')
                f.write(f'type: {item_type}\n')
                f.write('---\n\n')
                f.write(f'# {clean_item_name}\n\n')
                f.write(f'A page for the {item_type} [[{clean_item_name}]].\n')

def handle_malformed_json(file_path):
    """Tries to repair and load a malformed JSON file."""
    print(f"Attempting to repair and parse malformed JSON from '{file_path}'...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        url_pattern = re.compile(r'^(\s*)(https?://[^\s",]+)\s*$', re.MULTILINE)
        content = url_pattern.sub(r'\1"\2",', content)
        trailing_comma_pattern = re.compile(r',\s*([\]\}])', re.MULTILINE)
        content = trailing_comma_pattern.sub(r'\1', content)
        data = json.loads(content)
        print("Successfully parsed repaired JSON.")
        return data
    except Exception as e:
        print(f"Failed to repair and parse JSON. Error: {e}")
        return None

def main():
    """Main function to load JSON files and initiate processing."""
    input_dir, output_dir = 'inputs', 'output'
    scraped_date = datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(output_dir): os.makedirs(output_dir)

    all_sets = {
        "all_tools": set(), "all_groups": set(), 
        "all_sectors": set(), "all_countries": set()
    }

    file_configs = [
        {"path": os.path.join(input_dir, 'Threat Group Card - All tools.json'), "type": "tool"},
        {"path": os.path.join(input_dir, 'Threat Group Card - All groups.json'), "type": "group"}
    ]

    for config in file_configs:
        print(f"\n--- Processing {config['type'].title()}s ---")
        data = None
        try:
            with open(config['path'], 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Initial processing failed: {e}. Attempting repair...")
            data = handle_malformed_json(config['path'])
        
        if data:
            for record in data.get('values', []):
                process_record(record, output_dir, config['type'], all_sets, scraped_date)
        else:
            print(f"Could not process '{config['path']}'.")

    print("\n--- Finalizing Database ---")
    create_placeholder_pages(output_dir, all_sets['all_sectors'], 'sector', scraped_date)
    create_placeholder_pages(output_dir, all_sets['all_countries'], 'country', scraped_date)
    
    create_index_file(output_dir, 'index-tools', all_sets['all_tools'])
    create_index_file(output_dir, 'index-groups', all_sets['all_groups'])
    create_index_file(output_dir, 'index-sectors', all_sets['all_sectors'])
    create_index_file(output_dir, 'index-countries', all_sets['all_countries'])

    print("\nScript finished.")

if __name__ == "__main__":
    main()
