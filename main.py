import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
import os
import csv
from utils import user_credentials

class player():
    def __init__(self, id, first_name, last_name, gender, date_of_birth, email):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.dob = date_of_birth
        self.email = email

    #getters
    def get_id(self) -> int:
        return self.id
    
    def get_first_name(self) -> str:
        return self.first_name
    
    def get_last_name(self) -> str:
        return self.last_name
    
    def get_gender(self) -> str:
        return self.gender
    
    def get_dob(self) -> str:
        return self.dob
    
    def get_email(self) -> str:
        return self.email


class scraper():
    def __init__(self):
        self.date_of_creation = datetime.now().strftime("%Y-%m-%d")
        self.number_of_players_scraped = 0
        self.user_email = user_credentials.get("id")
        self.user_password = user_credentials.get("password")
        self.base_url = user_credentials.get("base_url")
        self.web_driver = None
        self.player_driver = None
        self.date_of_opening = datetime.strptime("01012025", "%d%m%Y") #real opening date is 01052023
        self.data = []

    #getters
    def get_date_of_creation(self) -> str:
        return self.date_of_creation
    
    def number_of_players_scraped(self) -> int:
        return self.number_of_players_scraped
    
    def login(self) -> bool:
        """
        Login the with user credentials

        Returns True if successful, False otherwise
        """
        email_input = self.web_driver.find_element(By.NAME, "Email")
        _email_input = self.player_driver.find_element(By.NAME, "Email")
        password_input = self.web_driver.find_element(By.NAME, "Password")
        _password_input = self.player_driver.find_element(By.NAME, "Password")
        email_input.send_keys(self.user_email)
        password_input.send_keys(self.user_password)
        _email_input.send_keys(self.user_email)
        _password_input.send_keys(self.user_password)
        self.web_driver.find_element(By.ID, "LoginButton").click()
        self.player_driver.find_element(By.ID, "LoginButton").click()
        self.web_driver.implicitly_wait(5) #sleep 5 seconds to account for latency
        self.player_driver.implicitly_wait(5) #sleep 5 seconds to account for latency
        try: 
            self.web_driver.find_element(By.CLASS_NAME, "logout")
            self.player_driver.find_element(By.CLASS_NAME, "logout")
            print("Login successful")
            return True
        except Exception as e:
            print(f"Error logging in, please check the credentials.")
            return False

    def navigate(self, target_date) -> WebElement:
        previous_button = self.web_driver.find_element(By.CSS_SELECTOR, "div.date-calendar div.calendar.standard-calendar a.prev")
        target_found = False
        while(target_found == False):
            try:
                desired_date = self.web_driver.find_element(By.CSS_SELECTOR, f"td[data-day='{target_date}']")
                target_found = True
                return desired_date
            except Exception:
                previous_button = self.web_driver.find_element(By.CSS_SELECTOR, "div.date-calendar div.calendar.standard-calendar a.prev")
                previous_button.click()

    def scrape_player_data(self, Thref):
        try:
            self.player_driver.get(Thref)
        except Exception as e:
            print(f"Failed to load player details.")
            return False

        first_name = self.player_driver.find_element(By.ID, "FirstName").get_attribute("value")
        last_name = self.player_driver.find_element(By.ID, "LastName").get_attribute("value") 
        email = self.player_driver.find_element(By.ID, "Email").get_attribute("value")
        height = self.player_driver.find_element(By.ID, "Height").get_attribute("value")
        phone_number = self.player_driver.find_element(By.ID, "PhoneNumber").get_attribute("value")
        DOB = self.player_driver.find_element(By.ID, "DateOfBirth").get_attribute("value")
        gender_dropdown = self.player_driver.find_element(By.ID, "Gender")
        __gender_dropdown = Select(gender_dropdown)
        gender = __gender_dropdown.first_selected_option.text
        data_dict = {'First name': first_name, 
                'Last name': last_name, 
                'Email': email, 
                'Height': height, 
                'Phone #': phone_number, 
                'Date of birth': DOB, 
                'Gender': gender, 
                'uuid': Thref }
        self.data.append(data_dict)

    def parse_results(self):
        results_table = self.web_driver.find_element(By.ID, "GameResultsTBody")

        try:
            games_list = results_table.find_elements(By.TAG_NAME, "tr")
        except Exception:
            print(f"No Results for current date selection.")
            return
        for game in games_list:
            data_id = game.get_attribute("data-id")
            try:
                players_container = game.find_element(By.TAG_NAME, "ul")
                players_list = players_container.find_elements(By.TAG_NAME, "li")
                for player in players_list:
                    player_profile_href = player.find_element(By.TAG_NAME, "a").get_attribute("href")
                    #TODO: Player data extraction here... 
                    self.scrape_player_data(Thref = player_profile_href)
            except Exception as e:
                print(f"No players found for Game ID: {data_id}")

    def analyze_game_results(self):
        self.web_driver.get(self.base_url + "/game-results")
        query_date = self.date_of_opening
        date_picker_display = self.web_driver.find_element(By.CSS_SELECTOR, ".display-value-container")
        #Target the date range input field by its ID
        while(query_date < datetime.now()):
            date_picker_display.click()
            dp_input = query_date.strftime("%d%m%Y")
            desired_date = self.navigate(dp_input)
            desired_date.click() 
            time.sleep(1.5)
            self.parse_results()
            query_date += timedelta(days=1)

    def write_to_file(self):
        with open('player_data.csv', 'w', newline='') as f:
            fieldnames = ['First name', 'Last name', 'Email', 'Height', 'Phone #', 'Date of birth', 'Gender', 'uuid']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.data)

    def scrape(self, headless = False):
        options = Options()
        if headless:
            options.add_argument('--headless')
        options.add_argument('--log-level=3')
        self.web_driver = webdriver.Chrome(options=options)
        self.player_driver = webdriver.Chrome(options=options)
        self.web_driver.get(self.base_url + "/login?r=%2F")
        self.player_driver.get(self.base_url + "/login?r=%2F")
        login_flag = self.login()

        if(login_flag):
            self.analyze_game_results()

        self.write_to_file()
            


if __name__ == "__main__":
    my_scraper = scraper()
    my_scraper.scrape()




