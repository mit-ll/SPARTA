import matplotlib
matplotlib.use('agg')
from pylab import *


class Data:
    def __init__(self, filename, plot_label):
        self.filename = filename
        self.plot_label = plot_label

all_data = (Data('c_api_results.csv', 'C API'),
        Data('cpp_stdout_buffer_results.csv', 'C++'),
        Data('event_loop_results.csv', 'Event Loop'),
        Data('py_results.csv', 'Python'))

def GetMeans(xs, vals):
    x = unique(xs)
    means = zeros(len(x))
    for i, xv in enumerate(x):
        means[i] = mean(vals[xs == xv])
    return (x, means)

for d in all_data:
    data = loadtxt(d.filename, skiprows=1, delimiter=',')
    (x, means) = GetMeans(data[:,0], data[:,2])
    print "x: ", str(x)
    print "means:", str(means)
    semilogx(x, means, label=d.plot_label)

legend()
savefig('results.png')
