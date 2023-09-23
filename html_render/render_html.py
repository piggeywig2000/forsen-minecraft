import json
from pathlib import Path

print(Path(__file__).parent.parent.joinpath("www/index-forsen.html"))

with open(Path(__file__).parent.joinpath("renderdef.json")) as renderdef_json:
    renderdef = json.load(renderdef_json)

with open(Path(__file__).parent.joinpath("index.html")) as index_template_file:
    index_template = index_template_file.read()
    for streamer_key, streamer_data in renderdef["streamers"].items():
        with open(Path(__file__).parent.parent.joinpath(f"www/index-{streamer_key}.html"), 'w') as new_index_file:
            new_index = index_template
            new_index = new_index.replace("{key}", streamer_key)
            for swap_key, swap_value in {**streamer_data, **renderdef["globals"]}.items():
                new_index = new_index.replace("{" + swap_key + "}", swap_value)
            new_index_file.write(new_index)

print("Rendered index.html files")