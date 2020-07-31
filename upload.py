from selenium import webdriver
from selenium.webdriver.common.keys import Keys  
from selenium.webdriver.chrome.options import Options 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
import upload_dropfile
import time
import logging

logger = logging.getLogger("Poddit")
stream_handler = logging.StreamHandler()
log_format = logging.Formatter('%(name)s - %(message)s')
stream_handler.setFormatter(log_format)
logger.addHandler(stream_handler)
logger.setLevel(logging.INFO)

"""
Usage:

    uploader = Uploader()  
    uploader.upload(
        filepath = some/file/path
        username=nicknacknerd
        password=nicknackpassword
        title="Episode Title"           # optional
        description="Show notes etc"    # optional
        )
"""

class Uploader:
    def __init__(self, podcast_host: str = "anchor"):
        self.driver = self.setup_driver()
        self.podcast_host = podcast_host
        self.episode_url = ""

    def setup_driver(self, visible: bool = False):
        options = Options()
        options.add_argument('window-size=1200x600')
        if( not visible):
            options.add_argument('headless')
        driver = webdriver.Chrome(options=options)
        return driver

    def upload(self, filepath: str, username: str, password: str, title: str = None, description: str = None) -> None:
        host_map = {
            'anchor': self._upload_to_anchor
        }
        try:
            if self.podcast_host in host_map:
                host_map[self.podcast_host](filepath, username, password)
        except Exception:
            logger.error("Oops something went wrong with the upload")

    def _upload_to_anchor(self, filepath: str, username: str, password: str, ep_title: str = "Episode Title", ep_description: str = "Nothing to say here") -> None:

        self.driver.get("http://www.anchor.fm/login")
        self.driver.implicitly_wait(15)

        # Login
        logger.info(f"Logging in as {username}")
        username_element = self.driver.find_element_by_id("email")
        password_element = self.driver.find_element_by_id("password")
        submit_button = self.driver.find_element_by_xpath('//*[@id="LoginForm"]/div[3]/button')
        username_element.send_keys(username)
        password_element.send_keys(password)
        submit_button.click()

        new_episode = WebDriverWait(self.driver, 15).until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, '//button[normalize-space()="New Episode"]')), 'new episode')
        time.sleep(3)       

        new_episode.click()
        

        file_dropzone = WebDriverWait(self.driver, 15).until(
            expected_conditions.visibility_of_element_located((By.XPATH, '//*[@id="app"]/div/div/div/div/div/div/div[2]/div[1]/div[2]'))
        )
        file_dropzone.drop_files([filepath])
        logger.info(f"uploading episode: {ep_title}")


        save_episode = WebDriverWait(self.driver, 1800).until(
            (expected_conditions.element_to_be_clickable(
                (By.XPATH, '//button[normalize-space()="Save episode"]'))))

        save_episode.click()

        episode_title = WebDriverWait(self.driver, 15).until(
            (expected_conditions.presence_of_element_located((By.ID, "title")))
        )

        episode_description = self.driver.find_element_by_class_name("public-DraftEditor-content")
        episode_title.send_keys(ep_title)
        episode_description.send_keys(ep_description)

        draftbutton = self.driver.find_element_by_xpath('//button[normalize-space()="Save as a draft"]')
        draftbutton.click()
        logger.info(f"Saving episode as a draft")

        edit_button = WebDriverWait(self.driver, 10000).until(
            expected_conditions.visibility_of_element_located(
                (By.XPATH, '//button[normalize-space()="Edit audio"]')
            )
        )

        self.episode_url = self.driver.current_url
        logger.info(f"Episode available at: {self.episode_url}")
        self.driver.quit()
        


if __name__ == "__main__":
    filepath = "/Users/anthonykeelan/Documents/NickNackNerd/Episode 5 - 3D Printing.mp3"
    filepath_short = "/Users/anthonykeelan/Documents/NickNackNerd/testclip.mp3"
    username = "enigma.ca@gmail.com"
    password = "bluemonkey"

    uploader = Uploader()
    uploader.upload(filepath_short, username, password)
    print(uploader.episode_url)

