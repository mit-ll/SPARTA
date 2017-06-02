# *****************************************************************
#  Copyright 2015 MIT Lincoln Laboratory  
#  Project:            SPAR
#  Authors:            omd
#  Description:        Inserter that writes in LineRaw format.
# 
#  Modifications:
#  Date          Name           Modification
#  ----          ----           ------------
#  23 Oct 2012   omd            Original version
# *****************************************************************

import os
import sys
import uuid
this_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.join(this_dir, '..', '..')
sys.path.append(base_dir)

import logging
import abc


import spar_python.common.aggregators.base_aggregator as base_aggregator
import spar_python.data_generation.output_ordering as oo
import spar_python.data_generation.spar_variables as sv

LOGGER = logging.getLogger(__name__)



class LineRawBase(base_aggregator.BaseAggregator):
    """
    
    A base-class for aggregators that write rows to file-like objects. The rows
    will be in LineRaw formatted data, delimited by INSERT/ENDINSERT pairs. 

    Currently, this base class has three concrete sub-classes: that opens
    files, one that opens named pipes, and one that writes to a file-like
    object provided to the constructor. (The last one is useful for
    unit tests, as it can be given a StringIO object.)
    
    """
    
    __metaclass__ = abc.ABCMeta
    
    def __init__(self, schema_file = None, var_order = None):
        """
        If var_order is present, it will govern the order in which
        values appear in a CSV row. If absent or None, then schema_file
        must be present and name a file which lists a variable order.
        """
        if var_order is None:
            var_order = oo.get_output_order(schema_file)
         
        self.__output_order = var_order
        return

    @abc.abstractmethod
    def start(self):
        """
        Perform state-creation.
        """
        pass


    def fields_needed(self):
        '''
        Return a set() containing the fields which will actually
        be written to file.
        '''
        return set(self.__output_order)


    def _write_row(self, file_obj, row_dict):
        """
        Given a row dictionary and a file-like object, write the row to the file
        in LineRaw format.
        """
        
        file_obj.write('INSERT\n')
        for i in self.__output_order:
            val = row_dict[i]
            line_raw_val = sv.VAR_CONVERTERS[i].to_line_raw(val)
            file_obj.write(line_raw_val)
            file_obj.write('\n')
        file_obj.write('ENDINSERT\n')
        return


        
    @staticmethod
    def reduce(_ignore_me, _ignore_me_too):
        '''
        Does nothing, returns None. Present only to implement map-reduce
        interface for aggregators.
        '''
        return None
    
    

    

class LineRawPipeAggregator(LineRawBase):
    """
    
    An aggregator that opens a named pipe once, writes all rows to it, and
    then closes it.
    
    """
    
    def __init__(self, 
                 base_filename = None,
                 buffer_size = 10**8,
                 schema_file = None,
                 var_order = None):
        """
        Notes on arguments:

        * base_filename: Even though this aggregator is creating pipes and not
        files, this argument has this particular name so that all the LineRawFoo
        aggregators have a uniform agurment-name, making the top-level
        file simpler.

        * buffer_size (optional). If present, will be used as buffer size on 
        when opening new files/FIFOs. This should be chosen to optimize speed
        of i/o.
          
        * If var_order is present, it will govern the order in which
        values appear in a CSV row. If absent or None, then schema_file
        must be present and name a file which lists a variable order.
        
        
        """
        super(LineRawPipeAggregator, self).__init__(schema_file, var_order)

        self.__base_pipename = base_filename
        self.__unique_pipename = None
        self.__file = None
        self.__buffer_size = buffer_size
        return


    def start(self):
        ''' 
        Creates and opens a named pipe for output. The name of the named pipe
        will be based on that given to the constructor, but will (always) have
        additional text added to the end to ensure its uniqueness.
        
        
        Why isn't this
        done once in the constructor? In that approach, the file will 
        be when the aggregator is created and passed to the mothership,
        which means all the workers will be writing to the same file. 
        '''
        
               
        own_pid = os.getpid()

            
        (path, ext) = os.path.splitext(self.__base_pipename)
        unique_id = uuid.uuid1()
        unique_pipename = "%s-%s%s"% (path, unique_id, ext)
            
        if os.path.isfile(unique_pipename):
            raise RuntimeError("File %s already exists.", 
                               unique_pipename)

        LOGGER.debug('PID %s trying to make named pipe %s...', 
                     own_pid, unique_pipename)
        os.mkfifo(unique_pipename)
        LOGGER.debug('PID %s made named pipe %s.', own_pid,
                     unique_pipename)
    
        LOGGER.debug('PID %s trying to open %s for writing', own_pid,
                         unique_pipename)
        file_obj = open(unique_pipename, 'w', self.__buffer_size)
        LOGGER.debug('PID %s opened %s for writing.', own_pid,
                          unique_pipename)
                
        self.__file = file_obj
        # Storing for later logger messages
        self.__unique_pipename = unique_pipename
        
        return



    def map(self, row_dict):
        """
        Write the data in row dict to the named pipe in LineRaw format 
        between and INSERT/ENDINSERT pair. This assumes that all data is line 
        mode unless the type of the data item is bytearray.
        
        Returns None.
        """
        self._write_row(self.__file, row_dict)


    def done(self):
        '''
        Flushes and clloses the underlying named pipe.
        '''
        LOGGER.debug('PID %s flushing %s.', 
                     os.getpid(), self.__unique_pipename)
        self.__file.flush()
        LOGGER.debug('PID %s closing %s.', 
                     os.getpid(), self.__unique_pipename)
        self.__file.close()
        return





class LineRawFileAggregator(LineRawBase):
    """
    
    An aggregator for writing rows to new files. Will open a new file for
    each batch, write the batch, and close the file (never to open it again).    
    """
    
    def __init__(self, 
                 base_filename = None,
                 buffer_size = 10**8,
                 rows_per_file = 1000,
                 schema_file = None,
                 var_order = None):
        """
        Notes on arguments:

        * buffer_size (optional). If present, will be used as buffer size on 
        when opening new files/FIFOs. This should be chosen to optimize speed
        of i/o.
          
        * rows_per_file should specify the number of rows to be written to 
        a single file before the file is closed and a new file opened.
          
        * If var_order is present, it will govern the order in which
        values appear in a CSV row. If absent or None, then schema_file
        must be present and name a file which lists a variable order.
        
        
        """
        super(LineRawFileAggregator, self).__init__(schema_file, var_order)

        self.__base_filename = base_filename
        self.__rows_per_file = rows_per_file
        self.__buffer_size = buffer_size
        self.__file = None
        self.__count = 0
        return


    def start(self):
        """
        Perform state-creation. 
        """
        self.__file = self._open_new_file()
        self.__count = 0
        return


    def _open_new_file(self):
        ''' 
        Opens a new file to which to write rows and returns the file handle.
        The name of the new file will be based on the filename provided to the
        constructor, but will (always) have additional characters to ensure
        uniqueness.
        
        Why isn't this done once in the constructor? In that approach, the file
        will be when the aggregator is created and passed to the mothership,
        which means all the workers will be writing to the same file. Instead,
        we call this in each worker, thus ensuring that each worker opens its
        own file.
        '''
                
               
        own_pid = os.getpid()

        # If wanted, append a unique ID to each file name. This is used to 
        # to keep workers from writing to the same file in multiprocess mode
            
        (path, ext) = os.path.splitext(self.__base_filename)
        unique_id = uuid.uuid1()
        filename = "%s-%s%s"% (path, unique_id, ext)
            
        if os.path.isfile(filename):
            raise RuntimeError("File %s already exists.", filename)
    
        LOGGER.debug('PID %s trying to open %s for writing', own_pid, filename)
        file_obj = open(filename, 'w', self.__buffer_size)
        LOGGER.debug('PID %s opened %s for writing.', own_pid, filename)
                
        return file_obj



    def map(self, row_dict):
        """
        Write the data in row dict to the file in LineRaw format between and
        INSERT/ENDINSERT pair. This assumes that all data is line mode unless
        the type of the data item is bytearray.
        
        Returns None.
        """
        
        # Note that this method is technically not pure. Specifically, 
        # it might have the side-effect of opening a file. However, this 
        # state-change will not affect the return-value of this method, and
        # so the impurity is hidden from client code. 
        #
        # But why have the impurity at all? Since we need to limit the 
        # number of rows in a file, we need to switch to a new file when 
        # we hit the limit in our old file. The natural place to do this is 
        # here.
        
        if self.__count >= self.__rows_per_file:
            self.__file.close()
            self.__file = self._open_new_file()
            self.__count = 0
        
        self._write_row(self.__file, row_dict)

        return None


    def done(self):
        '''
        Flushes and clloses the underlying line-raw file.
        '''
        self.__file.close()
        return
    
    
    
    

class LineRawHandleAggregator(LineRawBase):
    """
    
    An aggregator that takes a file object and writes all rows to it.
    
    Used primarily to unit-test those parts of line-raw aggregation that
    can be unit tested without actually writing to files or named pipes.
    
    """
    
    def __init__(self, 
                 file_obj,
                 schema_file = None,
                 var_order = None):
        """
        Notes on arguments:

          
        * If var_order is present, it will govern the order in which
        values appear in a CSV row. If absent or None, then schema_file
        must be present and name a file which lists a variable order.
        
        
        """
        super(LineRawHandleAggregator, self).__init__(schema_file, var_order)
        self.__file_obj = file_obj
        return


    def start(self):
        """
        Does nothing.
        """
        pass
    
    def done(self):
        """
        Closes the file object (necessary to flush the file for unit tests)  
        """
        self.__file_obj.close()


    def map(self, row_dict):
        """
        Write the data in row dict to the named pipe in LineRaw format 
        between and INSERT/ENDINSERT pair. This assumes that all data is line 
        mode unless the type of the data item is bytearray.
        
        Returns None.
        """
        self._write_row(self.__file_obj, row_dict)

    
