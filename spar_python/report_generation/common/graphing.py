# *****************************************************************
#  Copyright 2013 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            MZ
#  Description:        Class for graphing results from other analytics ocde
#                      
#                       
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  Aug 2         MZ             Original Version
#  Aug 12        SY             Refactored into classes
#             
# **************************************************************

# general imports:
import sys
import os

import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')

import matplotlib.markers as mrk
import matplotlib.pyplot as plt

import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import colorsys
import StringIO

DETAIL_2D = 300
# The number of input points to use when graphing the best-fit line
DETAIL_3D = 12
# The number of input points to use when graphing the best-fit surface
VALID_SCALES = ["log", "linear", "symlog"]
GOOD_POINTS = ['o','D','d','s','x','^','h','+','*','1','p','3','4','H']
ALL_POINTS = [i for i in mrk.MarkerStyle().markers]
BAD_POINTS = [val for val in ALL_POINTS if val not in GOOD_POINTS]

BIGNUMBER = 1000

class BadGraphingInputs(Exception): pass

def get_colors(num_colors):
    """
    Returns num_colors colors for use in 2-d graphing.
    """
    for index in xrange(num_colors):
        # finds the 3 (rgb) values for the ith color:
        col = [int(x) for x in colorsys.hsv_to_rgb(
            1. * index / num_colors, 1.0, 230)]
        # formats a string representing that color:
        yield "#{0:02x}{1:02x}{2:02x}".format(*col)

def comparison_percentile_graph(percentile_getter, y_label, y_scale='linear'):
    """
    Args:
        percentile_getter: a PercentileGetter object
        y_label: a label for the y-axis
        y_scale: The scale to use when graphing the output values
            possible values are 'linear','log', and 'symlog'
    Returns:
        A string representation of the graph, created by StringIO
    """
    performer_percentiles = percentile_getter.get_performer_percentiles()
    baseline_percentiles = percentile_getter.get_baseline_percentiles()
    return general_percentile_graph(
        datasets=[(performer_percentiles, "Performer Percentiles"),
                  (baseline_percentiles, "Baseline Percentiles")],
        y_label=y_label, y_scale=y_scale)

def general_percentile_graph(datasets, y_label, y_scale='linear'):
    """
    Args:
        datasets: A list of (y value list, data_set_name) tuples.
        y_label: a label for the y-axis
        y_scale: The scale to use when graphing the output values
            possible values are 'linear','log', and 'symlog'
    Returns:
        A string representation of the graph, created by StringIO
    """
    plt.close()
    fig = plt.figure()
    perf_plot = fig.add_subplot(211) # The regular 111 orientation cuts of the
                                     # line information.
    #perf_plot.set_title("Performer vs. Baseline query latency")
    perf_plot.set_ylabel(y_label)
    perf_plot.set_yscale(y_scale)
    if ((max([max(values) for (label, values) in datasets]) > BIGNUMBER)
        and (y_scale == 'linear')):
        plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    plt.xlim((0, 100))
    colors = get_colors(len(datasets))
    for (color, (values, label)) in zip(colors, datasets):
        assert len(values) == 100
        perf_plot.plot(xrange(100), values, 'o', color=color, label=label)
    perf_plot.legend(loc='upper center', bbox_to_anchor=(0.5, -0.10),
                     fancybox=True, shadow=True)
    string_fig = StringIO.StringIO()
    plt.savefig(string_fig, bbox_inches='tight')
    return string_fig.getvalue()

def graph2d(plot_name, datasets, x_label, y_label,
            x_scale='linear', y_scale='linear', drawlines=False):
    """
    Args:
        plot_name: The name of the plot.
        datasets: A list of (x value list, y value list, data_set_name,
            best_fit_function) tuples.
        x_label: The x-axis label
        y_label: The y-axis label
        x_scale: The scale to use when graphing the x_value values
            possible values are 'linear','log', and 'symlog'
        y_scale: The scale to use when graphing the output values
            possible values are 'linear','log', and 'symlog'
        drawlines: Boolean dictating whether lines are drawn between 
            adjacent points (default=False)
    Returns:
        A string representation of the graph, created by StringIO
    """
    assert x_scale in VALID_SCALES, 'Invalid x_scale argument'
    assert y_scale in VALID_SCALES, 'Invalid y_scale argument'
    plt.close()
    fig = plt.figure()
    plot = fig.add_subplot(211)
    plot.set_title(plot_name)
    plot.set_ylabel(y_label)
    plot.set_xlabel(x_label)
    plot.set_xscale(x_scale)
    plot.set_yscale(y_scale)
    num_datasets = len(datasets)
    colors = get_colors(num_datasets)
    mark_id = 0
    for (this_color, (x_value, y_value, name, best_fit_function)
         ) in zip(colors, datasets):
        if (drawlines):
            plot.plot(x_value, y_value, c=this_color, label=name,
                     marker=GOOD_POINTS[mark_id])
        else:
            plot.scatter(x_value, y_value, c=this_color, label=name,
                     marker=GOOD_POINTS[mark_id])

        max_x_val = max([max(i) for i in [datasets[j][0]
                                        for j in xrange(len(datasets))]])
        min_x_val = min([min(i) for i in [datasets[j][0]
                                        for j in xrange(len(datasets))]])
        max_y_val = max([max(i) for i in [datasets[j][1]
                                        for j in xrange(len(datasets))]])
        if(max_x_val > BIGNUMBER):
            plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
        if(max_y_val > BIGNUMBER):
            plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))

        if best_fit_function:
            best_fit_label = "%s (rsquared = %s)" % (
                best_fit_function.string,
                str(best_fit_function.get_rsquared(
                    inputs=[x_value], outputs=y_value)))
            plot.plot(
                np.linspace(min_x_val, max_x_val, DETAIL_2D),
                [best_fit_function.function([i]) for i in np.linspace(
                    min_x_val, max_x_val, DETAIL_2D)],
                color=this_color,
                label=best_fit_label)
        else:
            # for legend allignment, add an empty plot with a blank label:
            plot.plot([0], [0], c="w", linewidth=0, label=" ")
        if len(datasets) <= len(GOOD_POINTS):
            mark_id += 1
    plot.legend(
        loc='upper center', bbox_to_anchor=(0.5, -.20),
        fancybox=True, shadow=True, ncol=2)
    string_fig = StringIO.StringIO()
    plt.savefig(string_fig, bbox_inches='tight')
    return string_fig.getvalue()

def graph3d(plot_name,
            x_values, y_values, z_values,
            x_label, y_label, z_label,
            x_scale='linear', y_scale='linear', z_scale='linear',
            best_fit_function=None):
    """
    Args:
        plot_name: The name of the plot.
        x_values: List of values of the first independant variable
        y_values: List of values of the second independant variable
        z_values: List of values of the dependant variable
        x_label: The x-axis label
        y_label: The y-axis label
        z_label: The z-axis label
        x_scale: The scale to use when graphing x_value's values
            possible values are 'linear','log', and 'symlocng'
        y_scale: The scale to use when graphing y_value's values
            possible values are 'linear','log', and 'symlog'
        z_scale: The scale to use when graphing z_value's values
            possible values are 'linear','log', and 'symlog'
        best_fit_function (optional): The function to use to create
            a best-fit-surface. to compare to the value of the data.
    Returns:
        A string representation of the graph, created by StringIO
    """
    if ((not x_values) or (not y_values) or (not z_values)):
        raise BadGraphingInputs
    assert x_scale in VALID_SCALES, 'Invalid x_value_scale argument'
    assert y_scale in VALID_SCALES, 'Invalid y_value_scale argument'
    assert z_scale in VALID_SCALES, 'Invalid z_value_value_scale argument'
    plt.close()
    [color, best_fit_color] = get_colors(2)
    fig = plt.figure()
    regress_plot = fig.add_subplot(111, projection='3d')
    regress_plot.set_title(plot_name)
    xlabel = regress_plot.set_xlabel(x_label)
    ylabel = regress_plot.set_ylabel(y_label)
    zlabel = regress_plot.set_zlabel(z_label)
    regress_plot.set_xscale(x_scale)
    regress_plot.set_yscale(y_scale)
    regress_plot.set_zscale(z_scale)
    regress_plot.scatter(x_values, y_values, z_values,
                         c=color, label=plot_name)
    if(max(x_values) > BIGNUMBER):
            plt.ticklabel_format(style='sci', axis='x', scilimits=(0,0))
    if(max(y_values) > BIGNUMBER):
            plt.ticklabel_format(style='sci', axis='y', scilimits=(0,0))
    if(max(z_values) > BIGNUMBER):
            plt.ticklabel_format(style='sci', axis='z', scilimits=(0,0))
    if (best_fit_function) and all(
        [len(list(set(values))) > 1
         for values in [x_values, y_values, z_values]]):
        best_fit_label = "%s (rsquared = %s)" % (
            best_fit_function.string,
            str(best_fit_function.get_rsquared(
                inputs=[x_values, y_values], outputs=z_values)))
        sample_x_values = []
        sample_y_values = []
        for i in np.linspace(min(x_values), max(x_values), DETAIL_3D):
            for j in np.linspace(min(y_values), max(y_values), DETAIL_3D):
                sample_x_values.append(i)
                sample_y_values.append(j)
        sample_z_values = []
        for i in xrange(len(sample_x_values)):
            sample_z_values.append(best_fit_function.function(
                [sample_x_values[i], sample_y_values[i]]))
        regress_plot.plot_trisurf(sample_x_values, sample_y_values,
                                  sample_z_values,
                                  color=best_fit_color,
                                  label=best_fit_label)
        #regress_plot.legend(loc='upper center', bbox_to_anchor=(0.5, .20),
        #             fancybox=True, shadow=True)
    string_fig = StringIO.StringIO()
    plt.savefig(string_fig, bbox_extra_artists=[xlabel, ylabel, zlabel],
                bbox_inches='tight')
    return string_fig.getvalue()

def box_plot(plot_name, inputs, y_label=None, y_scale='linear'):
    """
    Args:
        plot_name: The name of the plot
        inputs: A list of tuples of the following form: (label, data), where
            label is the string corresponding to the list of data points, and
            data is the list of data points.
        y_label: The y-axis label
        y_scale: The scale to use when graphing y_value's values
            possible values are 'linear','log', and 'symlog'

    Returns:
        A string representation of the graph, created by StringIO
    """
    num_boxes = len(inputs)
    plt.close()
    fig, ax1 = plt.subplots(1, figsize=(num_boxes,6))
    plot = fig.add_subplot(111)
    plot.set_title(plot_name)
    if y_label: plot.set_ylabel(y_label)
    plot.set_yscale(y_scale)
    plot.boxplot([data for (label, data) in inputs])
    # set the x-tick names:
    x_tick_names = plt.setp(
        ax1, xticklabels=[label for (label, data) in inputs])
    plt.setp(x_tick_names, rotation=90, fontsize=8)
    # save the box plot:
    string_fig = StringIO.StringIO()
    plt.savefig(string_fig, bbox_inches='tight')
    return string_fig.getvalue()

def write_graph(path, graph):
    """
    Args:
        path: The path to write the graph to. Should be something like
            "<filename>.png".
        graph: The string representing a graph, recieved from one of the
            graphing functions.
    """
    graph_file = open(path,'w')
    graph_file.write(graph)
    graph_file.close()
