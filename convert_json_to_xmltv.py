import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import xml.dom.minidom
import os

# URL of the JSON EPG
JSON_EPG_URL = "https://ffchch.b-cdn.net/epg.json"

def fetch_json_epg():
    """Fetch JSON EPG data from the URL."""
    response = requests.get(JSON_EPG_URL)
    response.raise_for_status()
    return response.json()

def convert_to_xmltv(json_data):
    """Convert JSON EPG data to XMLTV format with channels at the top."""
    # Create the root element
    tv = ET.Element("tv")

    # First, add all channel elements
    for channel_id, channel_data in json_data.items():
        # Add channel
        channel = ET.SubElement(tv, "channel", id=channel_id)
        display_name = ET.SubElement(channel, "display-name")
        display_name.text = channel_id.replace("-", " ").title()
        display_name.set("lang", "en")

    # Then, add all programme elements
    for channel_id, channel_data in json_data.items():
        programs = channel_data.get("programs", [])
        for i, program in enumerate(programs):
            # Parse start time
            start_time = datetime.strptime(program["time"], "%Y-%m-%dT%H:%M:%SZ")
            
            # Determine end time
            if i < len(programs) - 1:
                # Use the start time of the next program as the end time
                next_program = programs[i + 1]
                end_time = datetime.strptime(next_program["time"], "%Y-%m-%dT%H:%M:%SZ")
            else:
                # For the last program, set end time to start time + 1 hour
                end_time = start_time + timedelta(hours=1)
            
            # Create programme element
            prog = ET.SubElement(
                tv,
                "programme",
                start=start_time.strftime("%Y%m%d%H%M%S +0000"),
                stop=end_time.strftime("%Y%m%d%H%M%S +0000"),
                channel=channel_id
            )
            
            # Add title
            title = ET.SubElement(prog, "title")
            title.text = program["title"]
            title.set("lang", "en")
            
            # Add description if available
            if program.get("description"):
                desc = ET.SubElement(prog, "desc")
                desc.text = program["description"]
                desc.set("lang", "en")
            
            # Add subtitle if available
            if program.get("subtitle"):
                sub_title = ET.SubElement(prog, "sub-title")
                sub_title.text = program["subtitle"]
                sub_title.set("lang", "en")
            
            # Add icon if available
            if program.get("thumbnail"):
                icon = ET.SubElement(prog, "icon", src=program["thumbnail"])

    return tv

def prettify_xml(xml_element):
    """Prettify XML element for readability."""
    rough_string = ET.tostring(xml_element, encoding="unicode")
    parsed = xml.dom.minidom.parseString(rough_string)
    return parsed.toprettyxml(indent="  ")

def main():
    # Fetch JSON data
    json_data = fetch_json_epg()
    
    # Convert to XMLTV
    xmltv_data = convert_to_xmltv(json_data)
    
    # Add generation timestamp comment
    generation_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    xml_comment = f"<!-- Generated at {generation_time} -->"
    
    # Write to XML file
    output_file = "epg.xml"
    with open(output_file, "w", encoding="utf-8") as f:
        pretty_xml = prettify_xml(xmltv_data)
        # Remove any extra XML declarations added by minidom
        if pretty_xml.startswith("<?xml"):
            pretty_xml = pretty_xml[pretty_xml.index("?>") + 2:].lstrip()
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_comment}\n{pretty_xml}')

if __name__ == "__main__":
    main()