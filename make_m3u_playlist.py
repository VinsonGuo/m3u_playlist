import json
import requests

def fetch_json(url):
    """Fetch JSON data from a URL"""
    response = requests.get(url)
    response.raise_for_status()  # Raise exception for HTTP errors
    return response.json()

def create_m3u_playlist(output_file):
    print("Fetching data from remote sources...")

    # Fetch channel information
    channel_info_url = "https://iptv-org.github.io/api/channels.json"
    channel_info_data = fetch_json(channel_info_url)

    # Create a dictionary for quick lookup by channel name
    channel_info_dict = {}
    for channel in channel_info_data:
        channel_info_dict[channel["name"].lower()] = channel
        # Add alternative names for lookup
        for alt_name in channel.get("alt_names", []):
            channel_info_dict[alt_name.lower()] = channel

    # Fetch country metadata
    countries_metadata_url = "https://raw.githubusercontent.com/TVGarden/tv-garden-channel-list/refs/heads/main/channels/raw/countries_metadata.json"
    countries_metadata = fetch_json(countries_metadata_url)

    # Create M3U header
    m3u_content = "#EXTM3U\n"

    testCount = 0
    # Process each country
    for country_code in countries_metadata:
        # Skip countries without channels
        if not countries_metadata[country_code].get("hasChannels", False):
            continue
        testCount +=1
        if testCount == 10:
            break

        country_name = countries_metadata[country_code]["country"]
        country_json_url = f"https://raw.githubusercontent.com/TVGarden/tv-garden-channel-list/refs/heads/main/channels/raw/countries/{country_code.lower()}.json"

        try:
            # Fetch country channel data
            channels = fetch_json(country_json_url)
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

                # Format categories for the group-title
                group_title = country_name
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

        except requests.exceptions.HTTPError as e:
            print(f"Error fetching data for {country_code}: {e}")

    # Write to output file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    print(f"M3U playlist created successfully: {output_file}")
    print(f"Total number of channels processed: {m3u_content.count('#EXTINF')}")

if __name__ == "__main__":
    output_m3u_file = "all_channels.m3u"
    create_m3u_playlist(output_m3u_file)