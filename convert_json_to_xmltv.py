import requests
import json
import xmltv
from datetime import datetime, timedelta
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
    """Convert JSON EPG data to XMLTV format."""
    # Initialize XMLTV structure
    tv = xmltv.TV()

    # Process each channel in the JSON data
    for channel_id, channel_data in json_data.items():
        # Add channel to XMLTV
        channel = xmltv.Channel(
            id=channel_id,
            display_name=[xmltv.DisplayName(text=channel_id.replace("-", " ").title(), lang="en")]
        )
        tv.channels.append(channel)

        # Process programs for the channel
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
            
            # Create programme entry
            prog = xmltv.Programme(
                start=start_time.strftime("%Y%m%d%H%M%S +0000"),
                stop=end_time.strftime("%Y%m%d%H%M%S +0000"),
                channel=channel_id,
                title=[xmltv.Title(text=program["title"], lang="en")],
                desc=[xmltv.Desc(text=program.get("description", ""), lang="en")] if program.get("description") else None,
                sub_title=[xmltv.SubTitle(text=program["subtitle"], lang="en")] if program.get("subtitle") else None,
                icon=[xmltv.Icon(src=program["thumbnail"])] if program.get("thumbnail") else None
            )
            tv.programmes.append(prog)

    return tv

def prettify_xml(xml_string):
    """Prettify XML string for readability."""
    parsed = xml.dom.minidom.parseString(xml_string)
    return parsed.toprettyxml(indent="  ")

def main():
    # Fetch JSON data
    json_data = fetch_json_epg()
    
    # Convert to XMLTV
    xmltv_data = convert_to_xmltv(json_data)
    
    # Write to XML file
    output_file = "epg.xml"
    with open(output_file, "w", encoding="utf-8") as f:
        xml_string = xmltv.write(xmltv_data)
        pretty_xml = prettify_xml(xml_string)
        f.write(pretty_xml)

if __name__ == "__main__":
    main()