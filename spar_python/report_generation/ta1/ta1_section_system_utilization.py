# *****************************************************************
#  Copyright 2014 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            mjr
#  Description:        System Utilizaiton section
# *****************************************************************

import logging
import os
# SPAR imports:
import spar_python.report_generation.ta1.ta1_section as section
import spar_python.report_generation.common.latex_classes as latex_classes

class Ta1SystemUtilizationSection(section.Ta1Section):
    """The supported query types section of the TA1 report"""
    
    
    def should_be_included(self):
        return self._config.perf_img_dir
    
    
    def _populate_output(self):
        # Initialize each resource to no graphs
        self._outp["cpu_resource_graphs"] = []
        self._outp["disk_resource_graphs"] = []
        self._outp["network_resource_graphs"] = []
        self._outp["ram_resource_graphs"] = []
        
        # add images
        self._add_images(self._config.perf_img_dir)
        
        # for any resource without images, set to None
        if len(self._outp["cpu_resource_graphs"]) == 0:
            self._outp["cpu_resource_graphs"] = None
        if len(self._outp["disk_resource_graphs"]) == 0:
            self._outp["disk_resource_graphs"] = None
        if len(self._outp["network_resource_graphs"]) == 0:
            self._outp["network_resource_graphs"] = None
        if len(self._outp["ram_resource_graphs"]) == 0:
            self._outp["ram_resource_graphs"] = None
        
        # Set overall existence of performance graphs
        if (self._outp["cpu_resource_graphs"] or self._outp["disk_resource_graphs"]
            or self._outp["network_resource_graphs"] or self._outp["ram_resource_graphs"]):
            self._outp["resource_graphs"] = True
        else:
            self._outp["resource_graphs"] = False
        
        
    def _add_images(self, directory):
        log = logging.getLogger(__file__)
        if (not os.isdir(directory)):
            log.fatal("performance monitoring image directory not a directory: %s" % (directory,))
            return
        for filename in os.listdir(directory):
            # only care about .png files
            if (not filename.endswith(".png")):
                log.info("Skipping non-image file: %s" % filename )
                continue
            if (filename.startswith("cpu")):
                image = latex_classes.LatexImage("cpu utilization", filename, os.path.join(directory, filename))
                self._outp["cpu_resource_graphs"].append(image.get_string())
            elif (filename.startswith("disk")):
                image = latex_classes.LatexImage("disk utilization", filename, os.path.join(directory, filename))
                self._outp["disk_resource_graphs"].append(image.get_string())
            elif (filename.startswith("network")):
                image = latex_classes.LatexImage("network utilization", filename, os.path.join(directory, filename))
                self._outp["network_resource_graphs"].append(image.get_string())
            elif (filename.startswith("ram")):
                image = latex_classes.LatexImage("ram utilization", filename, os.path.join(directory, filename))
                self._outp["ram_resource_graphs"].append(image.get_string())
            else:
                log.warn(".png with unknown prefix found: %s", filename)
        
            
            
        
            
