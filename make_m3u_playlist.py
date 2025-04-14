import json
import os
import requests

def read_json_file(file_path):
    """Read JSON data from a local file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_m3u_playlist(repo_path, output_file):
    print("Reading data from local repository...")

    # Path to the repository
    if not repo_path.endswith('/'):
        repo_path += '/'
    
    # Fetch channel information from IPTV-org API (still via HTTP)
    # This is kept as HTTP since it's not from the repository you've cloned
    channel_info_url = "https://iptv-org.github.io/api/channels.json"
    response = requests.get(channel_info_url)
    response.raise_for_status()
    channel_info_data = response.json()

    # Create a dictionary for quick lookup by channel name
    channel_info_dict = {}
    for channel in channel_info_data:
        channel_info_dict[channel["name"].lower()] = channel
        # Add alternative names for lookup
        for alt_name in channel.get("alt_names", []):
            channel_info_dict[alt_name.lower()] = channel

    # Read country metadata from local repo
    countries_metadata_path = os.path.join(repo_path, "channels/raw/countries_metadata.json")
    countries_metadata = read_json_file(countries_metadata_path)

    # Create M3U header
    m3u_content = "#EXTM3U\n"

    # Process each country
    for country_code in countries_metadata:
        # Skip countries without channels
        if not countries_metadata[country_code].get("hasChannels", False):
            continue

        country_name = countries_metadata[country_code]["country"]
        country_json_path = os.path.join(repo_path, f"channels/raw/countries/{country_code.lower()}.json")

        try:
            # Read country channel data from local file
            if os.path.exists(country_json_path):
                channels = read_json_file(country_json_path)
                print(f"Processing {country_name} ({country_code}) - {len(channels)} channels")
                
                # Process each channel
                for channel in channels:
                    channel_name = channel["name"]
                    language = channel["language"] if channel["language"] else "Unknown"

                    # Look up additional channel info
                    channel_id = channel["nanoid"]  # Default to nanoid
                    tvg_logo = ""
                    categories = []

                    # Try to find matching channel in channel_info_dict
                    channel_info = channel_info_dict.get(channel_name.lower())
                    if channel_info:
                        channel_id = channel_info.get("id", channel_id)
                        tvg_logo = channel_info.get("logo", "")
                        categories = channel_info.get("categories", [])

                    group_title = ""
                    if categories:
                        group_title = ";".join(categories)

                    # Add IPTV URLs
                    for url in channel["iptv_urls"]:
                        # Add channel info with enhanced metadata
                        m3u_content += f'#EXTINF:-1 tvg-id="{channel_id}" tvg-country="{country_code.upper()}" '
                        m3u_content += f'tvg-language="{language}" group-title="{group_title}" '
                        if tvg_logo:
                            m3u_content += f'tvg-logo="{tvg_logo}" '
                        m3u_content += f',{channel_name}\n'
                        m3u_content += f"{url}\n"
                        break

                    # Add YouTube URLs if no IPTV URLs are available
                    if not channel["iptv_urls"] and channel["youtube_urls"]:
                        for url in channel["youtube_urls"]:
                            m3u_content += f'#EXTINF:-1 tvg-id="{channel_id}" tvg-country="{country_code.upper()}" '
                            m3u_content += f'tvg-language="{language}" group-title="{group_title}" '
                            if tvg_logo:
                                m3u_content += f'tvg-logo="{tvg_logo}" '
                            m3u_content += f',{channel_name} (YouTube)\n'
                            m3u_content += f"{url}\n"
                            break
            else:
                print(f"File not found for {country_code}: {country_json_path}")

        except Exception as e:
            print(f"Error processing data for {country_code}: {e}")

    # Write to output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print(f"M3U playlist created successfully: {output_file}")
    print(f"Total number of channels processed: {m3u_content.count('#EXTINF')}")

if __name__ == "__main__":
    # Path to the cloned repository
    repo_path = "../tv-garden-channel-list"  # Change this to your local path
    output_m3u_file = "all_channels.m3u"
    create_m3u_playlist(repo_path, output_m3u_file)