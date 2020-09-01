# -*- coding: utf-8 -*-
"""
Created on Sat Jun 16 17:12:32 2018

@author: molp
"""

from functools import lru_cache

from os import listdir
from os.path import dirname, join

import numpy as np
from scipy import stats
import pandas as pd

import pickle
import sqlite3

from bokeh.io import curdoc
from bokeh.layouts import row, column, widgetbox, layout
from bokeh.models import ColumnDataSource, CustomJS, HoverTool, Div,  LogColorMapper, BasicTicker, PrintfTickFormatter, ColorBar, Range1d, FactorRange
from bokeh.models.widgets import Select, RadioButtonGroup, TableColumn, DataTable
from bokeh.plotting import figure, show

from io import StringIO
import base64

# creat dictionaries for plotting selections
with open(join(dirname(__file__), 'axis_map.pkl'), 'rb') as handle:
    axis_map = pickle.load(handle)
with open(join(dirname(__file__), 'library_map.pkl'), 'rb') as handle:
    library_map = pickle.load(handle)
with open(join(dirname(__file__), 'reverse_library_map.pkl'), 'rb') as handle:
    reverse_library_map = pickle.load(handle)

# create plot
att = 'MolWt'
data = pd.read_pickle(join(dirname(__file__),'heatmap_data/'+att+'.pkl'))
Hist = Hist =  np.array(data['hist'])
data_sort = pd.read_pickle(join(dirname(__file__),'heatmap_data/'+att+'-sort.pkl'))
data = data[list(data_sort.sort_values('mean').Library.values)]

Libs = list(data.columns)

# reshape to 1D array or rates with a month and year for each row.
normalized_data = (data-data.min())/(data.max()-data.min())
df = pd.DataFrame(normalized_data.stack(), columns=[att]).reset_index()

# this is the colormap from the original NYTimes plot
colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
mapper = LogColorMapper(palette=colors, low=0, high=1)

tooltips=[('MolWt', '@MolWt'), ('level_1', '@level_1')]

hover = HoverTool(tooltips="""
        <div>
                <div>@MolWt</div>
                <div>@level_1</div>
        </div>
        """
)

TOOLS = ["save,pan,box_zoom,reset,wheel_zoom",hover]

p = figure(title=att.format(Hist[0], Hist[-1]),
           x_range=[str(x) for x in Hist[:-1]], y_range=list(reversed(Libs)),
           x_axis_location="above", plot_width=900, plot_height=400,
           tools=TOOLS, toolbar_location='right')


p.grid.grid_line_color = None
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.axis.major_label_text_font_size = "5pt"
p.axis.major_label_standoff = 0
p.xaxis.major_label_orientation = np.pi / 3

p.rect(x="hist", y="Library", width=1, height=1,
       source=df,
       fill_color={'field': att, 'transform': mapper},
       line_color=None)

color_bar = ColorBar(color_mapper=mapper, major_label_text_font_size="5pt",
                     ticker=BasicTicker(desired_num_ticks=len(colors)),
                     formatter=PrintfTickFormatter(format="%d%%"),
                     label_standoff=6, border_line_color=None, location=(0, 0))
p.add_layout(color_bar, 'right')

property = Select(title="X Axis", options=sorted(list(axis_map.keys())), value="MolWt", width=400)

radio_button_group = RadioButtonGroup(
        labels=["mean", "median", "mode", "variance"], active=0, width=300)

data_table_source = ColumnDataSource(data_sort)

columns = [
        TableColumn(field="Library", title="Compound Library"),
        TableColumn(field="mean", title="Mean"),
        TableColumn(field="median", title="Median"),
        TableColumn(field="mode", title="Mode"),
        TableColumn(field="var", title="Variance")
    ]

data_table = DataTable(source=data_table_source, columns=columns, width=400, height=400)

# bokeh methods
def select_property(attr, old, new):
    global att
    att = axis_map[property.value]
    global data
    data = pd.read_pickle(join(dirname(__file__),'heatmap_data/'+att+'.pkl'))
    global data_sort
    data_sort = pd.read_pickle(join(dirname(__file__),'heatmap_data/'+att+'-sort.pkl'))
    sort_heatmap(attr, old, new)

def sort_heatmap(attr, old, new):
    sort_choices = ['mean', 'median', 'mode', 'variance']
    sort_choice = sort_choices[radio_button_group.active]
    global data_sort
    data_sort = data_sort.sort_values(sort_choice)

    data_table_source.data = data_table_source.from_df(data_sort)
    global Hist
    global data
    Hist =  np.array(data['hist'])
    data = data[list(data_sort.sort_values(sort_choice).Library.values)]
    global Libs
    Libs = list(data.columns)
    # reshape to 1D array or rates with a month and year for each row.
    normalized_data = (data-data.min())/(data.max()-data.min())
    global df
    df = pd.DataFrame(normalized_data.stack(), columns=[att]).reset_index()
    update()

def update():
    curdoc().clear()
    # this is the colormap from the original NYTimes plot
    global Hist
    global Libs
    global df
    X = []
    for h in Hist:
        for l in Libs:
            if len(X) < len(df):
                X.append(h)
    print(len(Libs), len(Hist), len(df), len(X))
    df["X"] = X

    colors = ["#75968f", "#a5bab7", "#c9d9d3", "#e2e2e2", "#dfccce", "#ddb7b1", "#cc7878", "#933b41", "#550b1d"]
    mapper = LogColorMapper(palette=colors, low=0, high=1)

    tooltips=[('X', '@X'), ('level_1', '@level_1')]

    hover = HoverTool(tooltips="""
            <div>
                    <div>@X</div>
                    <div>@level_1</div>
            </div>
            """
    )

    TOOLS = ["save,pan,box_zoom,reset,wheel_zoom",hover]

    p = figure(title=att.format(Hist[0], Hist[-1]),
               x_range=[str(x) for x in Hist[:-1]], y_range=list(reversed(Libs)),
               x_axis_location="above", plot_width=900, plot_height=400,
               tools=TOOLS, toolbar_location='right')

    p.grid.grid_line_color = None
    p.axis.axis_line_color = None
    p.axis.major_tick_line_color = None
    p.axis.major_label_text_font_size = "5pt"
    p.axis.major_label_standoff = 0
    p.xaxis.major_label_orientation = np.pi / 3
    p.rect(x="level_0", y="level_1", width=1, height=1,
           source=df,
           fill_color={'field': att, 'transform': mapper},
           line_color=None)

    color_bar = ColorBar(color_mapper=mapper, major_label_text_font_size="5pt",
                         ticker=BasicTicker(desired_num_ticks=len(colors)),
                         formatter=PrintfTickFormatter(format="%d%%"),
                         label_standoff=6, border_line_color=None, location=(0, 0))
    p.add_layout(color_bar, 'right')

    # page layout
    desc = Div(text=open(join(dirname(__file__), "description.html")).read(), width=1000)
    footer = Div(text=open(join(dirname(__file__), "footer.html"), encoding="utf8").read(), width=1200)

    sizing_mode = 'fixed'

    l = layout([
        [desc],
        [row(property, radio_button_group)],
        [row(p, data_table)],
        [footer]
    ], sizing_mode=sizing_mode)

    curdoc().add_root(l)

# callbacks
property.on_change('value', select_property)
radio_button_group.on_change('active', select_property)

curdoc().title = 'Commercial Fragment Libraries'

update()
