"""This module contains the classes required for a PokeDex to retrieve
information from the PokeAPI and display it."""

import argparse
import aiohttp
import asyncio
from abc import ABC, abstractmethod
import os.path


def setup_request_commandline():
    """
    Sets up the command line arguments needed to create a PokeRequest.
    :return: a PokeRequest
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=['pokemon', 'ability', 'move'],
                        help="The type of Pokemon data that will be retrieved")

    parser.add_argument("input", help="The ID/name or text file of IDs/name "
                                      "that needs to be queried ")
    parser.add_argument("--expanded", action='store_true', help="Determines if"
                                                                " certain "
                                                                "attributes "
                                                                "are expanded")
    parser.add_argument("--output", default="print",
                        help="The output of the program. This is 'print' by "
                             "default, but can be set to a file name as well.")
    try:
        args = parser.parse_args()
        request_ = PokeRequest()
        request_.mode = args.mode
        request_.input = args.input
        request_.expanded = args.expanded
        request_.output = args.output
        return request_
    except Exception as e:
        print(f"Error! Could not read arguments.\n{e}")
        quit()


class PokeRequest:
    """A class representing the request that defines the parameters used
    to call the PokeAPI."""

    def __init__(self):
        self.mode = None
        self.input = None
        self.expanded = False
        self.output = None

    def __str__(self):
        return f"Mode: {self.mode}\nInput: {self.input}" \
               f"\nExpanded: {self.expanded}\nOutput: {self.output}"


class PokeDex:
    """This class uses the state of a PokeRequest to make call(s) to
    the PokeAPI and then displays the results."""

    def __init__(self):
        self.api_caller = PokeAPICaller()
        self.data_handler = DataHandler()
        self.file_handler = FileHandler()
        self.request = None

    def set_request(self, request_: PokeRequest):
        """
        Sets the PokeRequest for the PokeDex
        :param request_: a PokeRequest
        """
        self.request = request_

    def retrieve_file_input(self):
        """
        Retrieves the parameters used to define the API endpoints
        :return: a list
        """
        file_path = self.request.input
        return self.file_handler.handle_input_file(file_path)

    def call_poke_api(self, poke_param):
        """
        Makes a call to the PokeAPI with a specified URL parameter to
        retrieve a list of json data
        :param poke_param:a String
        :return:a list
        """
        multi_request_map = {
            'pokemon': self.api_caller.process_pokemon_requests,
            'ability': self.api_caller.process_ability_requests,
            'move': self.api_caller.process_move_requests
        }
        single_request_map = {
            'pokemon': self.api_caller.process_pokemon_request,
            'ability': self.api_caller.process_ability_request,
            'move': self.api_caller.process_move_request
        }
        params = poke_param
        if os.path.isfile(self.request.input):
            poke_data = \
                asyncio.run(multi_request_map[self.request.mode](params))
        else:
            poke_data = \
                [asyncio.run(single_request_map[self.request.mode](params))]
        return poke_data

    def create_poke_data(self, poke_data):
        """
        Uses a list of json data and creates a Pokemon Data object
        :param poke_data: a list
        :return: a PokeData
        """
        poke_data_map = {
            'pokemon': self.data_handler.create_pokemons,
            'ability': self.data_handler.create_abilities,
            'move': self.data_handler.create_moves,
            'expanded': self.data_handler.create_pokemons_expanded
        }
        if self.request.expanded and self.request.mode == 'pokemon':
            datum = poke_data_map['expanded'](poke_data)
        else:
            datum = poke_data_map[self.request.mode](poke_data)
        return datum

    def report_poke_data(self, datum):
        """
        Generates a report of the PokeData retrieved
        :param datum: a PokeData
        """
        dashes = "-" * 30
        if self.request.output == 'print':
            for data in datum:
                print(data)
                print(dashes)
        else:
            data_str = ''
            for data in datum:
                data_str += data.__str__() + '\n' + dashes + '\n'
            self.file_handler.handle_output_file(self.request.output, data_str)

    def start_pokedex(self):
        """
        Generate a report of PokeData based on a PokeRequest
        """
        if self.request:
            if os.path.isfile(self.request.input):
                poke_api_param = self.retrieve_file_input()
            else:
                poke_api_param = self.request.input
            try:
                poke_data_param = self.call_poke_api(poke_api_param)
            except Exception:
                print("Incorrect endpoint")
            else:
                poke_datum = self.create_poke_data(poke_data_param)
                self.report_poke_data(poke_datum)
        else:
            print("Please set a Poke Request!")


class FileHandler:
    """This class is responsible for handling input and output files for
    PokeData"""

    @staticmethod
    def handle_input_file(file_path: str) -> list:
        """
        Retrieves a list of parameters used to complete Poke API end points
        :param file_path: a String
        :return:a list
        """
        try:
            with open(file_path, mode='r+', encoding='utf-8') as input_file:
                content = [x.strip() for x in input_file.readlines()]
        except Exception:
            print("Unable to read from input file.. now stopping PokeDex")
            exit()
        else:
            return content

    @staticmethod
    def handle_output_file(file_path: str, datum):
        """
        Writes a report of the PokeData to a specified file
        :param file_path: a String
        :param datum: a list
        """
        try:
            with open(file_path, mode='w+', encoding='utf-8') as output_file:
                output_file.writelines(datum)
        except Exception:
            dashes = "-" * 30
            print("Unable to write to file. Now outputting to console:\n")
            for data in datum:
                print(data)
                print(dashes)
        else:
            print(f"Report successfully written to {file_path}!")


class PokeData(ABC):
    """An abstract class that all PokeData must inherit from"""

    @abstractmethod
    def __init__(self, name: str, id_: int):
        self.name = name
        self.id_ = id_

    @abstractmethod
    def __str__(self):
        pass


class Ability(PokeData):
    """Class of PokeData representing Pokemon Abilities"""

    def __init__(self, name: str, id_: int, generation: str, effect: str,
                 effect_short: str, pokemon: list):
        super().__init__(name, id_)
        self.generation = generation
        self.effect = effect
        self.effect_short = effect_short
        self.pokemon = pokemon

    def __str__(self):
        pokemon_str = '\n'.join(self.pokemon)
        return f"Name: {self.name}\nID: {self.id_}" \
               f"\nGeneration: {self.generation}\nEffect: {self.effect}" \
               f"\nEffect (Short): {self.effect_short}" \
               f"\nPokemon:\n{pokemon_str}"


class Moves(PokeData):
    """Class of PokeData representing Pokemon Moves"""

    def __init__(self, name: str, id_: int, generation: str, accuracy: int,
                 pp: int, power: int, type_: str, damage_class: str,
                 effect_short: str):
        super().__init__(name, id_)
        self.generation = generation
        self.accuracy = accuracy
        self.pp = pp
        self.power = power
        self.type_ = type_
        self.damage_class = damage_class
        self.effect_short = effect_short

    def __str__(self):
        return f"Name: {self.name}\nID: {self.id_}\n" \
               f"Generation: {self.generation}\nAccuracy: {self.accuracy}\n" \
               f"PP: {self.pp}\nPower: {self.power}\nType: {self.type_}\n" \
               f"Damage Type: {self.damage_class}\n" \
               f"Effect Short: {self.effect_short}"


class Pokemon(PokeData):
    """Class of PokeData representing Pokemon"""

    def __init__(self, name: str, id_: int, height: int, weight: int,
                 stats: list, types: list, abilities: list, moves: list):
        super().__init__(name, id_)
        self.height = height
        self.weight = weight
        self.stats = stats
        self.types = types
        self.abilities = abilities
        self.moves = moves

    def __str__(self):
        stat_str = ''
        type_str = ''
        ability_str = ''
        move_str = ''
        for type_ in self.types:
            type_str += f"{type_}\n"
        if isinstance(self.stats[0], Stats):
            for stat in self.stats:
                stat_str += f"{stat}\n"
            for ability in self.abilities:
                ability_str += f"{ability}\n\n"
            for move in self.moves:
                move_str += f"{move}\n\n"
        else:
            for stat in self.stats:
                stat_str += f"{stat[0]} - {stat[1]}\n"
            for ability in self.abilities:
                ability_str += f"{ability}\n\n"
            for move in self.moves:
                move_str += f"{move[0]} - {move[1]}\n"
        return f"Name: {self.name}\nID: {self.id_}\n" \
               f"Height: {self.height}\nWeight: {self.weight}\n\n" \
               f"Stats:\n{stat_str}\nTypes:\n{type_str}\n" \
               f"Abilities:\n{ability_str}Moves:\n{move_str}"


class Stats(PokeData):
    """Class of PokeData representing Pokemon Stats"""

    def __init__(self, name, id_, is_battle_only):
        super().__init__(name, id_)
        self.is_battle_only = is_battle_only

    def __str__(self):
        return f"Name: {self.name}\nID: {self.id_}\n" \
               f"Is Battle Only: {self.is_battle_only}"


class PokeAPICaller:
    """Class responbiel for making calls to the PokeAPI"""

    def __init__(self):
        self.ability_url = "https://pokeapi.co/api/v2/ability/{}/"
        self.pokemon_url = "https://pokeapi.co/api/v2/pokemon/{}/"
        self.move_url = "https://pokeapi.co/api/v2/move/{}/"

    @staticmethod
    async def get_data(url: str,
                       session: aiohttp.ClientSession) -> dict:
        """
        Retrieves data from a specified API endpoint URL
        :param url: a string
        :param session: a aio.httpClientSession
        :return: a dict
        """
        response = await session.request(method="GET", url=url)
        ability_json_dict = await response.json()
        return ability_json_dict

    async def process_multiple_url(self, urls: list) -> list:
        """
        Retrieves datum from a list of API endpoint URLs
        :param urls: a list
        :return: a list
        """
        async with aiohttp.ClientSession() as session:
            async_coroutines = [self.get_data(url, session) for url in urls]
            responses = await asyncio.gather(*async_coroutines)
            return responses

    async def process_ability_requests(self, requests: list) -> list:
        """
        Retrieves a list of json dicts containing information for Abilities
        :param requests: a list
        :return:a list
        """
        async with aiohttp.ClientSession() as session:
            async_coroutines = [self.get_data(self.ability_url.format(id_),
                                              session) for id_ in requests]
            responses = await asyncio.gather(*async_coroutines)
            return responses

    async def process_ability_request(self, id_) -> dict:
        """
        Retrieves a json dict containing information for an Ability
        :param id_: a String
        :return: a dict
        """
        async with aiohttp.ClientSession() as session:
            response = await self.get_data(self.ability_url.format(id_),
                                           session)
            return response

    async def process_move_requests(self, requests: list) -> list:
        """
        Retrieves a list of json dicts containing information for Moves
        :param requests: a list
        :return: a list
        """
        async with aiohttp.ClientSession() as session:
            async_coroutines = [self.get_data(self.move_url.format(id_),
                                              session) for id_ in requests]
            responses = await asyncio.gather(*async_coroutines)
            return responses

    async def process_move_request(self, id_) -> dict:
        """
        Retrieves a json dict containing information for a Move
        :param id_: a String
        :return: a dict
        """
        async with aiohttp.ClientSession() as session:
            response = await self.get_data(self.move_url.format(id_), session)
            return response

    async def process_pokemon_requests(self, requests: list) -> list:
        """
        Retrieves a list of json dicts containing information for Pokemon
        :param requests: a list
        :return: a list
        """
        async with aiohttp.ClientSession() as session:
            async_coroutines = [self.get_data(self.pokemon_url.format(id_),
                                              session) for id_ in requests]
            responses = await asyncio.gather(*async_coroutines)
            return responses

    async def process_pokemon_request(self, id_) -> dict:
        async with aiohttp.ClientSession() as session:
            response = await self.get_data(self.pokemon_url.format(id_),
                                           session)
            return response


class DataHandler:
    """This class is responsible for using json dict to create PokeData"""

    @staticmethod
    def create_ability(ability_data: dict) -> Ability:
        """
        Creates an Ability with a json dict for an ability
        :param ability_data: a dict
        :return: an Ability
        """
        name = ability_data["name"]
        id_ = ability_data["id"]
        generation = ability_data["generation"]["name"]
        effect = ability_data["effect_entries"][0]["effect"]
        effect_short = ability_data["effect_entries"][0]["short_effect"]
        pokemon = [pokemon["pokemon"]["name"] for pokemon
                   in ability_data["pokemon"]]
        return Ability(name, id_, generation, effect, effect_short, pokemon)

    def create_abilities(self, ability_datum: list) -> list:
        """
        Creates a list of Abilities with a list of json dict for abilities
        :param ability_datum: a list
        :return: a list
        """
        ability_list = [self.create_ability(ability_data) for ability_data
                        in ability_datum]
        return ability_list

    @staticmethod
    def create_move(move_data: dict) -> Moves:
        """
        Creates a Move with json dict for a move
        :param move_data: a dict
        :return: a Move
        """
        name = move_data["name"]
        id_ = move_data["id"]
        generation = move_data["generation"]["name"]
        accuracy = move_data["accuracy"]
        power = move_data["power"]
        pp = move_data["pp"]
        type_ = move_data["type"]["name"]
        damage_class = move_data["damage_class"]["name"]
        effect_short = move_data["effect_entries"][0]["short_effect"]
        return Moves(name, id_, generation, accuracy, power, pp, type_,
                     damage_class, effect_short)

    def create_moves(self, move_datum: list) -> list:
        """
        Creates a list of Moves with a list of json dict for moves
        :param move_datum: a list
        :return: a list
        """
        move_list = [self.create_move(move_data) for move_data
                     in move_datum]
        return move_list

    @staticmethod
    def create_pokemon(pokemon_data: dict):
        """
        Creates a Pokemon with a json dict for a Pokemon
        :param pokemon_data: a dict
        :return: a Pokemon
        """
        name = pokemon_data["name"]
        id_ = pokemon_data["id"]
        height = pokemon_data["height"]
        weight = pokemon_data["weight"]
        stats = [(stat["stat"]["name"], stat["base_stat"]) for
                 stat in pokemon_data["stats"]]
        types = [type_["type"]["name"] for type_ in pokemon_data["types"]]
        abilities = [ability["ability"]["name"] for ability
                     in pokemon_data["abilities"]]
        moves = [(move["move"]["name"],
                  move["version_group_details"][0]["level_learned_at"])
                 for move in pokemon_data["moves"]]
        return Pokemon(name, id_, height, weight, stats, types, abilities,
                       moves)

    def create_pokemons(self, pokemon_datum: list) -> list:
        """
        Creates a list of Pokemon with a list of json dict for Pokemon
        :param pokemon_datum: a list
        :return: a list
        """
        pokemon_list = [self.create_pokemon(pokemon_data) for pokemon_data
                        in pokemon_datum]
        return pokemon_list

    @staticmethod
    def create_stat(stat_data: dict):
        """
        Creates a Stat with a json dict for Stat
        :param stat_data: a dict
        :return: a Stat
        """
        name = stat_data["name"]
        id_ = stat_data["id"]
        is_battle_only = stat_data["is_battle_only"]
        return Stats(name, id_, is_battle_only)

    def create_stats(self, stat_datum):
        """
        Creates a list of Stats with a list of json dict for stats
        :param stat_datum: a list
        :return: a list
        """
        stat_list = [self.create_stat(stat_data) for stat_data
                     in stat_datum]
        return stat_list

    def create_pokemon_expanded(self, pokemon_data: dict):
        """
        Creates a Pokemon with expanded details with a json dict for Pokemon
        :param pokemon_data: a dict
        :return: a Pokemon
        """
        poke_request = PokeAPICaller()
        name = pokemon_data["name"]
        id_ = pokemon_data["id"]
        height = pokemon_data["height"]
        weight = pokemon_data["weight"]
        stats = [stat["stat"]["url"] for stat in pokemon_data["stats"]]
        stats = asyncio.run(poke_request.process_multiple_url(stats))
        stats = self.create_stats(stats)
        types = [type_["type"]["name"] for type_ in pokemon_data["types"]]
        abilities = [ability["ability"]["url"] for ability in
                     pokemon_data["abilities"]]
        abilities = asyncio.run(poke_request.process_multiple_url(abilities))
        abilities = self.create_abilities(abilities)
        moves = [move["move"]["url"] for move in pokemon_data["moves"]]
        moves = asyncio.run(poke_request.process_multiple_url(moves))
        moves = self.create_moves(moves)
        return Pokemon(name, id_, height, weight, stats, types, abilities,
                       moves)

    def create_pokemons_expanded(self, pokemon_datum: list) -> list:
        """
        Creates a list of Pokemon with expanded details with a list of
        json dict for Pokemon
        :param pokemon_datum:
        :return:
        """
        pokemon_list = [self.create_pokemon_expanded(pokemon_data) for
                        pokemon_data in pokemon_datum]
        return pokemon_list


def main(request_: PokeRequest):
    pokedex = PokeDex()
    pokedex.set_request(request_)
    pokedex.start_pokedex()


if __name__ == '__main__':
    request = setup_request_commandline()
    main(request)
