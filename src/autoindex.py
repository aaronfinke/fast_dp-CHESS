import shutil
import os

from xds_writer import write_xds_inp_autoindex, write_xds_inp_autoindex_p1_cell
from xds_reader import read_xds_idxref_lp
from run_job import run_job

from cell_spacegroup import spacegroup_to_lattice

from logger import write


def autoindex(metadata, input_cell=None):
    '''Perform the autoindexing, using metadata, get a list of possible
    lattices and record / return the triclinic cell constants (get these from
    XPARM.XDS).

    Parameters
    ----------
    metadata : dict
        relevant information about the experimental data

    input_cell : tuple, optional

    Returns
    -------
    tuple
        the unit cell that is used in the integrate process
    '''
    assert(metadata)

    xds_inp = 'AUTOINDEX.INP'

    if input_cell:
        write_xds_inp_autoindex_p1_cell(metadata, xds_inp, input_cell)
    else:
        write_xds_inp_autoindex(metadata, xds_inp)

    shutil.copyfile(xds_inp, 'XDS.INP')

    log = run_job('xds_par')

    with open('autoindex.log', 'w') as fout:
        fout.write(''.join(log))

    # sequentially check for errors... XYCORR INIT COLSPOT IDXREF

    for step in ['XYCORR', 'INIT', 'COLSPOT', 'IDXREF']:
        lastrecord = open('{}.LP'.format(step)).readlines()[-1]
        if '!!! ERROR !!!' in lastrecord:
            raise RuntimeError('error in {}: {}'.format(
                step, lastrecord.replace('!!! ERROR !!!', '').strip()))

    results = read_xds_idxref_lp('IDXREF.LP')

    # FIXME if input cell was given, verify that this is an allowed
    # permutation. If it was not, raise a RuntimeError. This remains to be
    # fixed

    write('All autoindexing results:')
    write('{:3s} {:6s} {:6s} {:6s} {:6s} {:6s} {:6s}'.format(
          'Lattice ', 'a', 'b', 'c', 'alpha', 'beta', 'gamma'))

    for r in reversed(sorted(results)):
        if not type(r) == type(1):
            continue
        cell = results[r][1]
        write('{:7s} {:6.2f} {:6.2f} {:6.2f} {:6.2f} {:6.2f} {:6.2f}'.format(
               spacegroup_to_lattice(r), cell[0], cell[1], cell[2],
               cell[3], cell[4], cell[5]))

    # should probably print this for debuging

    try:
        return results[1][1]
    except:
        raise RuntimeError('getting P1 cell for autoindex')
