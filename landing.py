"""Create a landing page with buttons described in input json or csv files.

[
    {    # minimal button info
        "text": "CV",
        "fa icon": "home",
        "url": "https://lucas.bourneuf.net"
    },
    {   # maximal
        "text": "bakasp",
        "fa icon": "home",
        "url": "https://asp.bourneuf.net",
        "button width": "400",
        "color": "ForestGreen",
        "hovered color": "Pink",
        "fontsize": "25"
    },
]

Default button width, color, hovered_color and fontsize can be set with CLI options of that module.

See --help for details.

CSV file cannot (yet) provide the optional options, and is expected to be like:

    CV,home,https://lucas.bourneuf.net
    Bakasp,home,https://asp.bourneuf.net
    Bingo,home,https://bingo.bourneuf.net


Multiple input files may be given ; their links will all be added to the landing page.

example:

    python landing.py mylinks.json myothersimplelinks.csv otherlinks.json


"""

import os
import sys
import csv
import json
import argparse
from jinja2 import Environment, Template, PackageLoader, select_autoescape
from itertools import zip_longest, starmap
from markupsafe import Markup


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks

    >>> tuple(map(''.join, grouper('ABCDEFG', 3, 'x')))
    ('ABC', 'DEF', 'Gxx')
    >>> tuple(grouper('ABC', 2))
    (('A', 'B'), ('C', None))

    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def parse_cli() -> argparse.Namespace:
    """Simpler version"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('infiles', type=str, nargs='+', help='csv or json files containing buttons definition')
    parser.add_argument('--button-width', '-sx', type=int, help='CSS horizontal size for buttons', default=220)
    parser.add_argument('--button-height', '-sy', type=int, help='CSS vertical size for buttons', default=100)
    parser.add_argument('--button-color', '-bc', type=str, help='CSS color value for buttons', default='DarkOrange')
    parser.add_argument('--hover-button-color', '-hc', type=str, help='CSS color value for buttons when hovered', default='Orange')
    parser.add_argument('--max-button-per-line', '-l', type=int, help='maximal number of button per line', default=2)
    parser.add_argument('--fontsize', '-f', type=int, help='button text font size', default=20)
    parser.add_argument('--outdir', '-o', type=str, help='directory in which output files should be written', default='out/')
    parser.add_argument('--template-dir', '-t', type=str, help='directory in which template files should be found', default='templates/')
    return parser.parse_args()


def render_template(template_name, template_dir:str = 'templates/', target_dir:str = 'out/', **variables):
    assert os.path.exists(target_dir)

    with open(os.path.join(template_dir, template_name)) as fd:
        template = Template(fd.read(), autoescape=select_autoescape())

    with open(os.path.join(target_dir, template_name), 'w') as fd:
        fd.write(template.render(variables))


def convert_link_to_html(text, icon, url, width, fontsize, color, hovered_color, defaults:argparse.Namespace) -> str:
    style = []
    if width or fontsize or color:
        if width:
            style.append(f'width: {width}px;')
        if fontsize:
            style.append(f'font-size: {fontsize}px;')
        if color:
            style.append(f'background-color: {color};')
    style = f" style=\"{''.join(style)}\"" if style else ''
    if hovered_color:
        # style.append(f'.btn:hover {{ background-color: {hovered_color} }};')  # doesn't works, by HTML/CSS design
        #  use the javascript way
        style += f' onMouseOver=this.style.backgroundColor="{hovered_color}"'
        style += f' onMouseOut=this.style.backgroundColor="{color or defaults.button_color}"'
        # style.append(f'.btn:hover {{ background-color: {hovered_color} }};')  # doesn't works, by HTML/CSS design
    return f"""<a href="{url}"><button class="btn" {style}> <i class="fa-solid fa-{icon}"></i> &nbsp; {text} </button></a>"""

def json_repr_to_html(data: dict, defaults: dict) -> str:
    return convert_link_to_html(
        data.get('text', ''),
        data.get('fa icon', 'home'),
        data.get('url', '/'),
        data.get('button width'),
        data.get('fontsize'),
        data.get('color'),
        data.get('hovered color'),
        defaults
    )


def links_repr_from_file(infile: str) -> tuple:
    if infile.endswith('.csv'):
        with open(infile) as fd:
            return tuple({'text': a[0], 'fa icon': a[1], 'url': a[2]} for a in csv.reader(fd))
    if infile.endswith('.json'):
        with open(infile) as fd:
            return tuple(json.loads(fd.read()))
    raise NotImplementedError(f"Cannot handle file {infile} (not a json nor a csv)")


def convert_links_to_html(all_links, args: argparse.Namespace) -> str:
    html = []
    for line_links in grouper(all_links, args.max_button_per_line):
        html.append('\n'.join(json_repr_to_html(but_args, args) for but_args in line_links if but_args))
    return '<br/>'.join(html)



if __name__ == '__main__':
    args = parse_cli()
    links = sum(map(links_repr_from_file, args.infiles), ())
    render_template('index.html', buttons=Markup(convert_links_to_html(links, args)), template_dir=args.template_dir, target_dir=args.outdir)
    render_template('index.css', button_width=args.button_width, button_height=args.button_height, hover_button_color=args.hover_button_color, button_color=args.button_color)
