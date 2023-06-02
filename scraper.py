import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import re
import logging
import argparse
import time
from tabulate import tabulate
from tqdm import tqdm
import csv

from Challenge import Challenge

# Argument parser
parser = argparse.ArgumentParser(description="Scrapes challenge data from the Cyber Defenders website to sort them by best score.")
parser.add_argument("-t", "--token", action="store", type=str, required=True, help="Session token to use for authenticated requests.")
parser.add_argument("-a", "--all", action="store_true", help="Scrape all challenges.")
parser.add_argument("-d", "--delay", action="store", type=float, default=0.5, help="Delay between requests in seconds. Default: 0.5")
parser.add_argument("-o", "--output", action="store", type=str, help="Output csv file to write to.")
parser.add_argument("--debug", action="store_true", help="Enable debug logging.")
args = parser.parse_args()

# Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if args.debug else logging.INFO)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG if args.debug else logging.INFO)
formatter = logging.Formatter("\033[1;34m%(levelname)s\033[0m - \033[1;37m%(message)s\033[0m")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


# Constants
URL = "https://cyberdefenders.org/blueteam-ctf-challenges/"
TOKEN_NAME = "__Secure-sessionid"
THROTTLE_DELAY = args.delay

# Globals
last_request_time = 0

session = requests.Session()
if args.token is not None:
    session.cookies.set(TOKEN_NAME, args.token)

def get_page(url, **kwargs):
    """Fetches the page at the provided url."""
    global last_request_time

    # Throttle requests
    time.sleep(max(0, THROTTLE_DELAY - (time.time() - last_request_time)))
    last_request_time = time.time()

    # Fetch the page
    page = session.get(url, **kwargs)
    if page.status_code != 200:
        logger.error(f"Failed to fetch page: {url}")
        return None

    return page

# Checks if the provided token is valid
page = get_page(URL)
if page is None:
    logger.error(f"Failed to fetch page: {URL}")
    raise Exception("Failed to check session token.")
soup = BeautifulSoup(page.content, "html.parser")
avatar_element = soup.find("div", class_="avatar")
if not avatar_element:
    logger.error("Invalid token provided. Using anonymous session.")
    raise Exception("Failed to check session token.")


def fetch_challenge_urls():
    """Fetches the URLs of all the challenges on the website."""

    page_num = 1
    challenge_urls = []

    # Loop through all the pages
    while True:
        # Fetch the page and parse it
        page = get_page(URL, params={"page": page_num})
        if page is None:
            logger.error(f"Failed to fetch page: {URL}")
            break
        soup = BeautifulSoup(page.content, "html.parser")

        # Check if the selected page is not equal to the current page_num
        selected_page_element = soup.find("li", class_="page-item active")
        if not selected_page_element:
            logger.error(f"No selected page element found for page: {page_num}")
            break
        selected_page_num_element = selected_page_element.find("span")
        if not selected_page_num_element or not selected_page_num_element.next_element:
            logger.error(f"No selected page number element found for page: {page_num}")
            break
        selected_page_num = selected_page_num_element.next_element.text.strip()
        if selected_page_num != str(page_num):
            logger.debug(f"Selected page number: {selected_page_num} does not match current page number: {page_num}. Stopping.")
            break

        # Get challenge links on the page
        challenges = soup.find_all("div", class_="card h-100 card-hover smooth-shadow-md")
        logger.debug(f"Found {len(challenges)} challenges on page: {page_num}")

        for challenge in challenges:

            challenge_link = challenge.find("a", class_="card-img-top stretched-link")

            # Check if the link has an href attribute
            if not challenge_link.has_attr("href"):
                continue

            # Check if the link is a valid challenge link
            if not re.search(r"/\d+/?$", challenge_link["href"]):
                logger.error(f"Invalid challenge link: {challenge_link['href']}")
                continue

            # Get challenge id from the link
            challenge_id = int(re.search(r"/(\d+)/?$", challenge_link["href"]).group(1))
            logger.debug(f"Found challenge id: {challenge_id}")

            # Check if the link is already in the list
            if challenge_id in challenge_urls:
                logger.error(f"Duplicate challenge id: {challenge_id}")
                raise Exception(f"Duplicate challenge id: {challenge_id}")
            
            if not args.all:
                # Check if the challenge is not completed

                footer = challenge.find("div", class_="card-footer")
                if not footer:
                    logger.error(f"No footer found for challenge: {challenge_id}")
                    continue

                progress_element = footer.find("span", class_="float-end")
                if not progress_element:
                    logger.error(f"No progress element found for challenge: {challenge_id}")
                    continue

                progress_text = progress_element.text.strip()
                if not re.search(r"\d+/\d+", progress_text):
                    logger.error(f"Invalid progress format for challenge: {challenge_id}\n\tprogress: {progress_text}")
                    continue

                progress = re.search(r"(\d+)/(\d+)", progress_text)
                if not progress or not progress.group(1) or not progress.group(2):
                    logger.error(f"Invalid progress format for challenge: {challenge_id}\n\tprogress: {progress_text}")
                    continue
                if progress.group(1) == progress.group(2):
                    logger.debug(f"Challenge {challenge_id} is completed.")
                    continue

            # All checks passed. Add the link to the list
            challenge_urls.append(urljoin(URL, str(challenge_id)))
        
        # Increment page number
        page_num += 1

    return challenge_urls

def fetch_challenge(challenge_url):
    """Fetches the challenge with the provided url."""

    return_challenge = Challenge(url=challenge_url)

    # Fetch the page and parse it
    page = get_page(challenge_url)
    if page is None:
        logger.error(f"Failed to fetch challenge url: {challenge_url}")
        return None
    soup = BeautifulSoup(page.content, "html.parser")

    # Get the challenge Title
    title_element = soup.find("h1", class_="text-sky")
    if not title_element:
        logger.error(f"No title element found for challenge: {challenge_url}")
    else:
        return_challenge.title = title_element.text.strip()
        logger.debug(f"Found challenge title: {return_challenge.title}")

    # Get the challenge Category
    category_element = soup.find("h2", class_="text-sky")
    if not category_element:
        logger.error(f"No category element found for challenge: {challenge_url}")
    else:
        return_challenge.category = category_element.text.strip()
        logger.debug(f"Found challenge category: {return_challenge.category}")

    # Get the challenge score_max and remaining_score
    score_element = soup.find("span", id="score")
    score = 0
    if not score_element :
        logger.error(f"No score element found for challenge: {challenge_url}")
    else:
        if not score_element.text.strip().isnumeric():
            logger.error(f"Invalid score format for challenge: {challenge_url}\n\tscore: {score_element.text.strip()}")
        else:
            score = int(score_element.text.strip())
            logger.debug(f"Found challenge score: {score}")

            score_max_element = score_element.next_sibling
            if not score_max_element:
                logger.error(f"No score_max element found for challenge: {challenge_url}")
            else:
                score_max_text = score_max_element.text.strip()
                score_max = re.search(r"(\d+)$", score_max_text)
                if not score_max or not score_max.group(1):
                    logger.error(f"Invalid score_max format for challenge: {challenge_url}\n\tscore_max: {score_max_text}")
                else:
                    return_challenge.score_max = int(score_max.group(1))
                    logger.debug(f"Found challenge score_max: {return_challenge.score_max}")
                    # Calculate remaining_score
                    return_challenge.remaining_score = return_challenge.score_max - score
                    logger.debug(f"Calculated challenge remaining_score: {return_challenge.remaining_score}")

    # Get the challenge questions_count and remaining_questions
    questions_element = soup.find("span", id="num_of_solved_questions")
    questions = 0
    if not questions_element:
        logger.error(f"No questions element found for challenge: {challenge_url}")
    else:
        if not questions_element.text.strip().isnumeric():
            logger.error(f"Invalid questions format for challenge: {challenge_url}\n\tquestions: {questions_element.text.strip()}")
        else:
            questions = int(questions_element.text.strip())
            logger.debug(f"Found challenge questions: {questions}")

            questions_count_element = questions_element.next_sibling
            if not questions_count_element:
                logger.error(f"No questions_count element found for challenge: {challenge_url}")
            else:
                questions_count_text = questions_count_element.text.strip()
                questions_count = re.search(r"(\d+)", questions_count_text)
                if not questions_count or not questions_count.group(1):
                    logger.error(f"Invalid questions_count format for challenge: {challenge_url}\n\tquestions_count: {questions_count_text}")
                else:
                    return_challenge.questions_count = int(questions_count.group(1))
                    logger.debug(f"Found challenge questions_count: {return_challenge.questions_count}")
                    # Calculate remaining_questions
                    return_challenge.remaining_questions = return_challenge.questions_count - questions
                    logger.debug(f"Calculated challenge remaining_questions: {return_challenge.remaining_questions}")

    # Get the challenge difficulty
    difficulty_element = soup.find("span", class_="badge")
    if not difficulty_element:
        logger.error(f"No difficulty element found for challenge: {challenge_url}")
    else:
        return_challenge.difficulty = difficulty_element.text.strip()
        logger.debug(f"Found challenge difficulty: {return_challenge.difficulty}")

    # Get the challenge tags
    tag_elements = soup.find_all("h3", class_="badge")
    if not tag_elements:
        logger.error(f"No tag elements found for challenge: {challenge_url}")
    else:
        return_challenge.tags = [tag.text.strip() for tag in tag_elements]
        logger.debug(f"Found challenge tags: {return_challenge.tags}")

    return return_challenge

def fetch_challenges():
    """Fetches all the challenges from the website and sorts them by remaining_score in descending order."""

    # Fetch all the challenge urls
    logger.info("Fetching challenge urls...")
    challenge_urls = fetch_challenge_urls()

    # Fetch all the challenges
    logger.info(f"Fetching {len(challenge_urls)} challenges data...")
    challenges = []
    for url in tqdm(challenge_urls, desc="Progression", unit="challenge"):
        challenge = fetch_challenge(url)
        if challenge:
            challenges.append(challenge)

    # Sort the challenges by remaining_score in descending order
    challenges.sort(key=lambda x: x.remaining_score, reverse=True)
    
    return challenges

if __name__ == "__main__":
    challenges = fetch_challenges()

    attributes = Challenge.get_attributes()
    data = [[getattr(challenge, attr) for attr in attributes] for challenge in challenges]
    
    print(tabulate(data, headers=attributes, tablefmt="pretty"))

    # Save the data to a csv file if output is specified
    if args.output:
        logger.info(f"Saving data to {args.output}...")
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=attributes, delimiter=";")
            writer.writeheader()
            for challenge in challenges:
                writer.writerow(challenge.get_dict())