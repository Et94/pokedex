App Overview
----
Using arguments from the command line, this app will make a call to the PokeAPI to retrieve information of Pokemon Abilities, Pokemon Moves or Pokemon

Command Line Arguments
---
When executing the module from the command line, the user must provide the following arguments:

python pokedex.py {"pokemon" | "ability" | "move"} {"filename.txt" | "name" | "id"} [--expanded] [--output "filename.txt]

{"pokemon" | "ability" | "move"} - REQUIRED
---
This specifies the mode and the type of data retrieved when making a call to the PokeAPI

{"filename.txt" | "name" | "id"} - REQUIRED
---
The user must specify the name or ID of the Pokemon, Pokemon Move or Pokemon Ability. The user can also provide a .txt file of many names and/or IDs

[--expanded] - OPTIONAL
---
This optional tag will result in more detailed description of a Pokemon's Stats, Moves and Abilities. This tag is only applicable if the mode is set to "pokemon"

[--output "filename.txt] - OPTIONAL
---
This optional tag allows the app to generate a report of the data retrieved into a .txt file. The app will print the report to the console by default if the tag is not specified.