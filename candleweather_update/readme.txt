Manifest.json and the python util script have long lists of city names. The scripts in this folder help create that code.


First, grab the latest list of city names to city numbers

https://worldweather.wmo.int/en/dataguide.html

currently: https://worldweather.wmo.int/en/json/full_city_list.txt

remove the extra line at the bottom. Then run the python script to generate the list that can be used in the json file.

python3 extract_city_names.py > for_json.txt

use that for_json file in manifest.json


The same thing for extract_lookup_table.py, which generates a python dictionary that can be used in util.py




After all this, the data is cleaned further manually to remove very long country and city names (Iran, Lua, Uk USA, Venezuela).

