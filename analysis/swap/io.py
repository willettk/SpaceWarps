# ======================================================================

import swap

import os,cPickle,numpy as np
import pdb, heapq
from collections import Counter

# ======================================================================

"""
    NAME
        io

    PURPOSE
        Useful general functions to streamline file input and output.

    COMMENTS

    FUNCTIONS
        write_pickle(contents,filename):

        read_pickle(filename):

        write_list(sample, filename, item=None):
        
        read_list(filename):
     
        write_catalog(sample, filename, thresholds, kind=kind):

        rm(filename):

        write_config():

    BUGS

    AUTHORS
      This file is part of the Space Warps project, and is distributed
      under the MIT license by the Space Warps Science Team.
      http://spacewarps.org/

      SWAP io is modelled on that written for the
      Pangloss project, by Tom Collett (IoA) and Phil Marshall (Oxford).
      https://github.com/drphilmarshall/Pangloss/blob/master/pangloss/io.py

    HISTORY
      2013-04-17  Started Marshall (Oxford)
"""

#=========================================================================
# Read in an instance of a class, of a given flavour. Create an instance
# if the file does not exist.

def read_pickle(filename,flavour):

    try:
        F = open(filename,"rb")
        contents = cPickle.load(F)
        F.close()

        print "SWAP: read an old contents from "+filename

    except:

        if filename is None:
            print "SWAP: no "+flavour+" filename supplied."
        else:
            print "SWAP: "+filename+" does not exist."

        if 'bureau' in flavour:
            contents = swap.Bureau()
            print "SWAP: made a new",contents

        elif 'collection' in flavour:
            contents = swap.Collection()
            print "SWAP: made a new",contents

        elif flavour in ['database','metadata']:
            contents = None

    return contents

# ----------------------------------------------------------------------------
# Write out an instance of a class to file.

def write_pickle(contents,filename):

    F = open(filename,"wb")
    cPickle.dump(contents,F,protocol=2)
    F.close()

    return

# ----------------------------------------------------------------------------
# Write out a simple list of subject IDs, of subjects to be retired.

def write_list(sample, filename, item=None, source=None):

    count = 0
    F = open(filename,'w')
    for ID in sample.list():
        subject = sample.member[ID]
        string = None

        if item == 'retired_subject':
            if subject.state == 'inactive':
                if source == 'ML' and subject.retiredby == 'machine':
                    string = subject.ZooID
                elif subject.retiredby == 'swap':
                    string = subject.ZooID

        elif item == 'candidate':
            if subject.kind == 'test' and subject.status == 'detected':
                string = subject.location

        elif item == 'true_positive':
            if subject.kind == 'sim' and subject.status == 'detected':
                string = subject.location

        elif item == 'false_positive':
            if subject.kind == 'dud' and subject.status == 'detected':
                string = subject.location

        elif item == 'true_negative':
            if subject.kind == 'dud' and subject.status == 'rejected':
                string = subject.location

        elif item == 'false_negative':
            if subject.kind == 'sim' and subject.status == 'rejected':
                string = subject.location

        # Write a new line:
        if item is not None and string is not None:
            F.write('%s\n' % string)
            count += 1

    F.close()

    return count

# ----------------------------------------------------------------------------
# Read in a simple list of string items.

def read_list(filename):
    return np.atleast_1d(np.loadtxt(filename,dtype='string'))

# ----------------------------------------------------------------------------
# Write out a multi-column catalog of high probability candidates.

def write_catalog(sample,filename,thresholds,kind='test',source=None):

    Nsubjects = 0
    Nlenses = 0

    # Open a new catalog and write a header:
    F = open(filename,'w')
    F.write('%s\n' % "# zooid     P         Nclass  image")

    for ID in sample.list():
        subject = sample.member[ID]
        P = subject.mean_probability

        if source == 'ML':
            if kind=='rejected' and subject.state == 'inactive' and \
               subject.retiredby == 'machine':
                output = (subject.ZooID, P, subject.exposure, subject.location)
                # Write a new line:
                F.write('%s  %9.7f  %s       %s\n'\
                        %output)
                Nlenses += 1 

            elif kind=='detected' and subject.status == 'detected' and \
                 subject.retiredby == 'machine':
                output = (subject.ZooID, P, subject.exposure, subject.location)
                F.write('%s  %9.7f  %s       %s\n'%output)
                Nlenses += 1            

        else:
            if kind=='rejected' and subject.state == 'inactive' and \
               subject.retiredby == 'swap':
                output = (subject.ZooID, P, subject.exposure, subject.location)
                # Write a new line:
                F.write('%s  %9.7f  %s       %s\n'\
                        %output)
                Nlenses += 1 
                
            elif kind=='detected' and subject.status == 'detected' and \
                 subject.retiredby == 'swap':
                output = (subject.ZooID, P, subject.exposure, subject.location)
                F.write('%s  %9.7f  %s       %s\n'%output)
                Nlenses += 1            
                
            elif P > thresholds['rejection'] and subject.kind == kind:
                
                #zooid = subject.ZooID
                #png = subject.location
                #Nclass = subject.exposure
                output = (subject.ZooID, P, subject.exposure, subject.location)
                # Write a new line:
                F.write('%s  %9.7f  %s       %s\n'\
                        %output)
                Nlenses += 1
                
        Nsubjects += 1

    F.close()

    return Nlenses,Nsubjects

# ----------------------------------------------------------------------------

def get_new_filename(pars,flavour,source=None):

    # Usually, this is what we want filenames to look like:
    if source == 'ML': 
        stem = '%s_ML%s'%(pars['trunk'],flavour)
    else:  
        stem = '%s_%s'%(pars['trunk'],flavour)
    folder = pars['dir']
    ext = 'txt'
    # Pickles are an exception though!

    if flavour in ['bureau', 'collection', 'MLcollection', 'metadata',
                   'database', 'offline']:
        stem = pars['survey']+'_'+flavour
        ext = 'pickle'
        folder = '.'
    elif flavour in ['histories', 'trajectories', 'sample', 'probabilities']:
        ext = 'png'
    elif flavour in ['retire_these', 'candidates', 'training_true_positives', 
                     'training_false_positives', 'training_true_negatives', 
                     'training_false_negatives', 'candidate_catalog', 
                     'sim_catalog', 'dud_catalog', 'retired_catalog', 
                     'detected_catalog']:
        ext = 'txt'
        folder = pars['dir']
        
    else:
        raise Exception("SWAP: io: unknown flavour "+flavour)
      
        
    return folder+'/'+stem+'.'+ext

# ----------------------------------------------------------------------------
# Write configuration file given a dictionary of parameters:

def write_config(filename, pars):

    F = open(filename,'w')

    header = """
# ======================================================================
#
# Space Warps Analysis Pipeline configuration file.
#
# Lines starting with '#' are ignored; all other lines must contain a
# Name : Value pair to be read into the parameters dictionary.
#
# This file is part of the Space Warps project, and is distributed
# under the MIT license by the Space Warps Science Team.
# http://spacewarps.org/
#
# SWAP configuration is modelled on that written for the
# Pangloss project, by Tom Collett (IoA) and Phil Marshall (Oxford).
# https://github.com/drphilmarshall/Pangloss/blob/master/example/example.config
#
# ======================================================================
    """
    F.write(header)

    shortlist = ['survey', 
                 'start', 
                 'end', 
                 'increment',
                 'bureaufile', 
                 'samplefile', 
                 'metadatafile',
                 'MLsamplefile',
                 'MLbureaufile',
                 'stage', 
                 'verbose', 
                 'one_by_one', 
                 'report', 
                 'plot', 
                 'trunk',
                 'dir',
                 'repickle', 
                 'supervised', 
                 'supervised_and_unsupervised',
                 'initialPL', 
                 'initialPD', 
                 'agents_willing_to_learn',
                 'a_few_at_the_start',
                 'N_per_batch', 
                 'hasty', 
                 'skepticism', 
                 'use_marker_positions', 
                 'detection_threshold', 
                 'rejection_threshold',
                 'random_file', 
                 'dbspecies',
                 'offline',
                 'prior',
                 'machine',
                 'machine_threshold',
                 'evaluation_metrics',
                 'evaluation_criteria'
                 ]

    for keyword in shortlist:
        F.write('\n')
        F.write('%s: %s\n' % (keyword,str(pars[keyword])))

    F.write('\n')
    footer = '# ======================================================================'
    F.write(footer)

    F.close()

    return

# ----------------------------------------------------------------------------
# Remove file, if it exists, stay quiet otherwise:

def rm(filename):
    try:
        os.remove(filename)
    except OSError:
        pass
    return

# ======================================================================
