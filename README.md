# CyberDefenders Radar

This is a Python tool that scrapes challenge data from the Cyber Defenders website and sorts them by the remaining score. It provides a command-line interface to fetch and display challenge information in a tabular format.

## Prerequisites

- Python 3.x
- Account on the [Cyber Defenders](https://cyberdefenders.org/) website
- Valid session token `__Secure-sessionid`

## Installation

1. Clone this repository or download the code.
2. Install the required Python packages mentioned above.
```shell
pip install -r requirements.txt
```

## Usage

Run the tool by executing the `scraper.py` file. Use the following command-line arguments to customize the scraper's behavior:

- `-t, --token <token>`: Specify a session token for authenticated scraping.
- `-a, --all`: Scrape all challenges (including completed challenges).
- `-d, --delay <delay>`: Set the delay between requests in seconds (default: 0.5).
- `--debug`: Enable debug logging for more detailed output.

Example usage:

```shell
python scraper.py -t <session_token> -d 1.0 --debug
```

The tool will scrape the challenge data from the Cyber Defenders website, sort them by the remaining score, and display the information in a tabular format.

## How It Works

The scraper follows these steps:

1. Fetch the challenge URLs from the website.
2. Fetch the challenge information for each URL.
3. Sort the challenges by the remaining score in descending order.
4. Display the challenge information in a tabular format.

## License

This project is licensed under the [BSD 3-Clause License](LICENSE).