import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from datetime import datetime, timedelta
import argparse
import os
import csv
from utils import user_credentials

class scraper():
    def __init__(self, start_date, stop_date):
        self.date_of_creation = datetime.now().strftime("%Y-%m-%d")
        self.number_of_players_scraped = 0
        self.user_email = user_credentials.get("id")
        self.user_password = user_credentials.get("password")
        self.base_url = user_credentials.get("base_url")
        self.web_driver = None
        self.player_driver = None
        self.start_date = start_date
        self.stop_date = stop_date
        self.data = []
        self.players_parsed = {} #check for dupes

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
        self.players_parsed[Thref] = "True" 

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
                    #check if player data already extracted. Skip profile 
                    already_scraped_flag = self.players_parsed.get(player_profile_href)
                    if not(already_scraped_flag): #None-> if player not encountered by scraper before. Since player profile href is unique...
                        self.scrape_player_data(Thref = player_profile_href)
            except Exception:
                print(f"No players found for Game ID: {data_id}")

    def analyze_game_results(self):
        self.web_driver.get(self.base_url + "/game-results")
        query_date = self.start_date
        date_picker_display = self.web_driver.find_element(By.CSS_SELECTOR, ".display-value-container")
        #Target the date range input field by its ID
        while(query_date < self.stop_date):
            date_picker_display.click()
            dp_input = query_date.strftime("%d%m%Y")
            desired_date = self.navigate(dp_input)
            desired_date.click() 
            time.sleep(1.5)
            self.parse_results()
            query_date += timedelta(days=1)

    def write_to_file(self):
        start_time = self.start_date.strftime("%d-%m-%Y")
        stop_time = self.stop_date.strftime("%d-%m-%Y")
        csv_name = f"player_data_{start_time}_{stop_time}.csv"
        with open(os.path.join(os.getcwd(), csv_name), 'w', newline='', encoding='utf-8') as f:
            print(f"Writing player data to {csv_name}")
            fieldnames = ['First name', 'Last name', 'Email', 'Height', 'Phone #', 'Date of birth', 'Gender', 'uuid']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in self.data:
                try:
                    writer.writerow(row)
                except Exception as e:
                    print(f"Failed to write player data to file.\n\tERROR: {e}")
                    print("Saving list of players to backup file...")
                    with open(os.path.join(os.getcwd(), "backup_file.txt"), 'w', encoding='utf-8') as backup_file:
                        for row in self.data:
                            backup_file.write(f"{row}\n")


    def scrape(self, headless = True):
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
        total_num_players = len(self.data)
        print(f"Successfully collected data for {total_num_players} players.")
            


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape player data within specified date range.")
    parser.add_argument(
        "start_date",
        type=str,
        help="Start date in the format DDMMYYYY (e.g., 01052023)",
    )
    parser.add_argument(
        "stop_date",
        type=str,
        help="Stop date in the format DDMMYYYY (e.g., 01012025)",
    )

    args = parser.parse_args()

    try:
        start_date = datetime.strptime(args.start_date, "%d%m%Y") #01052023
        stop_date = datetime.strptime(args.stop_date, "%d%m%Y")  #01012025
    except ValueError:
        print("Error: Dates must be in the format DDMMYYYY (e.g., 01052023).")
        exit(1)

    if start_date >= stop_date:
        print("Error: Start date must be earlier than stop date.")
        exit(1)
    
    my_scraper = scraper(start_date= start_date, stop_date= stop_date)
    my_scraper.scrape(headless=False)




