from dataclasses import dataclass, field
import requests
import datetime as dt
import textwrap

# Issues
# - Can't figure out how to add field metadata when default values are involved
# - Can't figure out how to appropriately implement inheritance because 
#      the parent builds the child, so while it seems obvious, I can't 
#      figure out how to pass the parent to the child without causing 
#      dependency problems.

#       ** CLASS STRUCTURES **       #
######################################

# Did not use a Data Class for the library due to the complexity of the class
class StarWarsLibrary:
    """ Star Wars Library Class """
    
    # Variables with _ _ underscores should only be accessible from within the class
    def __init__(self):
        self.__token = 'tt3896198'
        self.__api_key = '3ef42ac3'
        self.__star_path = 'https://swapi.dev/api/films'
        self.__omdb_path = f'http://www.omdbapi.com/?i={self.__token}&apikey={self.__api_key}&t=Star+Wars&y='
        self.__star_data = None
        self.__omdb_data = None
        self.__movie_dict = {}
        self.__templates = requests.get(
            'https://raw.githubusercontent.com/jedc4xer/web_scraping_exercises/main/star_wars_templates.txt').text.split(",")
        self.last_updated = dt.datetime.now() # This will get moved to a function that runs after a successful update
     
    # Allows a user to check out a movie object
    def get_characters(self):
        character_list = []
        for movie in self.__movie_dict:
            for character in self.__movie_dict[movie].characters:
                character_list.append([self.__movie_dict[movie].title, character.name])

        unique_characters = sorted(list(set([_[1] for _ in character_list])))
        character_dict = {_:[] for _ in unique_characters}
        for character in character_list:
            character_dict[character[1]].append(character[0])
        return unique_characters, character_dict
        
    def get_movies(self):

        passed = False
        while not passed:
            print(self.__templates[0])
            picked_method = input('How would you like to find your movie? >> ')
            if (picked_method.isnumeric() and int(picked_method) < 4):
                passed = True
            else:
                print("That was not a valid response.")
        picked_method = int(picked_method)
        if picked_method == 2:
            print('\n  * Available Characters * \n')
            unique_characters, character_dict = self.get_characters()
            picked_character = None
            passed = False
            while not passed:
                print(textwrap.fill(" | ".join(unique_characters),75))
                if picked_character is not None:
                    for character in character_dict:
                        if picked_character in character:
                            print(f'\n{character} can be found in:\n{sorted(character_dict[character])}')

                print("\nWhen you are finished, type 'exit menu'")
                picked_character = input("Choose a Character (case sensitive | partial allowed) >> ")
                if picked_character.lower() == 'exit menu':
                    break
        elif picked_method == 1:
            for movie in self.__movie_dict:
                print(movie)
            
            passed = False
            while not passed:
                print('To exit the menu, type "exit menu"')
                picked_movie = input('Which movie would you like to check out? >> ')
                if movie in self.__movie_dict:
                    print(self.__movie_dict[movie])
                    passed = True
                else:
                    print('Unable to find the movie.')
                if picked_movie.lower() == 'exit menu':
                    break
    
    # API Access Methods
    ######################################
    
    def access_star_wars_api(self):
        self.__star_data = requests.get(self.__star_path).json()['results']
        
    def access_omdb_api(self, year):
        self.__omdb_data = requests.get(self.__omdb_path + year).json()
        
    # Data Parsing
    ######################################
    
    def parse_omdb_data(self):
        omdb_data = self.__omdb_data
        movie_title = omdb_data['Title']
        box_office = omdb_data['BoxOffice'].replace(",","").replace("$","")
        rotten_rating = None
        for rating in omdb_data['Ratings']:
            if rating['Source'] == 'Rotten Tomatoes':
                rotten_rating = rating['Value']
        return [rotten_rating, box_office]
          
    # Data Update Methods    
    ######################################
    
    def update_movie_dict(self,new_movies):
        for movie in new_movies:
            self.__movie_dict[movie.title] = movie
        return self.__movie_dict
        
    def update_library(self):
        print('Checking for new movies.')
        self.access_star_wars_api()
        self.update_film_database()
    
    def update_film_database(self):
        """ 
        Primary Data Gathering Function 
        - Called by class.method()
        - Checks for available updates
        """
        
        films = []
        for i,film in enumerate(self.__star_data):
            # If the film is already collected, skip the film
            if film['title'] in self.__movie_dict:
                continue
            
            print(f'Parsing {film["title"]}')
            film_info = {
                'title': None, 
                'episode_id': None, 
                'opening_crawl': None, 
                'director': None, 
                'producer': None, 
                'release_date': None, 
                'characters': None, 
                'plot': None, 
                'rotten_tomatoes': None, 
                'box_office_gross': None    
                }
            
            for field in film_info.keys():
                if field in film:
                    film_info[field] = film[field]
                    
            year = film_info['release_date'][:4]
            self.access_omdb_api(year)
            omdb_data = self.parse_omdb_data()
            film_info['rotten_tomatoes'] = omdb_data[0]
            film_info['box_office_gross'] = omdb_data[1]
            film_obj = StarWarsFilms(*film_info.values())
            films.append(film_obj)
            print("######################")
            break # Temporary break to reduce api call load
        self.update_movie_dict(films)    
        

@dataclass
class StarWarsFilms:     
    
    # This __post_init__ method is checking the input data to see if it is valid.
    # (Might need to be a __init__ instead, but then I'll have to change the class structure)
    def __post_init__(self):
        if self.episode_id is None:
            raise Exception("An Episode ID is required!!")
        
        # This adjusts the character input to be complete character objects instead of links
        if self.characters is not None:
            updated_characters = []
            print(f'Getting details on {len(self.characters)} characters')
            for character in self.characters:
                char = self.get_characters(character)
                attrs = self.get_character_attributes(char)
                updated_characters.append(FilmCharacters(*attrs))
            self.characters = updated_characters
    
    title: str = None
    episode_id: int = None
    opening_crawl: str = None
    director: str = None
    producer: str = None
    release_date: str = None
    characters: list = None
    plot: str = None
    rotten_tomatoes: str = None
    box_office_gross: int = None #int = field(metadata={"units":"U.S. Dollars"})
    # Can't seem to use metadata with a default value
    
    def __repr__(self):
        return_string = f"""
          Title: {self.title}
          Released: {self.release_date}
          Director: {self.director}
          Producer: {self.producer}
          Characters: {len(self.characters)}
          Rotten Tomatoes: {self.rotten_tomatoes}
          Box Office: {self.box_office_gross}
        """
        return return_string
    
    def __lt__(self,other):
        if self.episode_id < other.episode_id:
            return True
        return False
    
    def __gt__(self,other):
        if self.episode_id > other.episode_id:
            return True
        return False
    
    def __eq__(self,other):
        if self.episode_id == othe.episode_idr:
            return True
        return False
    
    def __ge__(self,other):
        if self.episode_id >= other.episode_id:
            return True
        return False
    
    # This function is calling the api for the character information
    def get_characters(self, character):
        chars = requests.get(character).json()
        return chars
    
    def get_character_attributes(self,character):
        goal_list = [
            'name',
            'height',
            'mass',
            'hair_color',
            'eye_color',
            'birth_year',
            'gender'
        ]
        
        attr_list = []
        for attr in goal_list:
            if attr in character:
                attr_list.append(character[attr])
            else:
                attr_list.append(None)
        return attr_list
    
@dataclass
class FilmCharacters:
    name: str
    height: float
    mass: float = field(metadata={"units":"kilograms"})
    hair_color: str
    eye_color: str
    birth_year: str
    gender: str

    
build = StarWarsLibrary()
build.update_library()

passed = False
while not passed:
    print('Type "exit" to exit the program.')
    main_option = input('What would you like to do? >> ')
    if main_option.lower() == 'exit':
        break
    else:
        build.get_movies()

print('Thank you for visiting the Star Wars Library.\n\nHave a "force-fully" productive day!')