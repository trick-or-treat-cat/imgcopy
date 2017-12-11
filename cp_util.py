'''
Utilities for copy disk image.
This program is made for a task of System Software.
Used Python3.6.2 and only pre-installed modules.

This programs contains utilities for copy disk image.
'''
import sys
import struct

__author__ = "Katsunoshin Matsui<matsui.k.ai@m.titech.ac.jp>"
__version__ = "1.00"
__date__ = "1 Dec 2017"


def read_img(img_path, gets='all', BSIZE=512):
    '''
    Read bytes from img at img_path.

    Parameters
    ----------
    img_path: string
        path for image to be read bytes
    gets: string, default = 'all'
        property for getting bytes, expected 'all' or 'super'
    BSIZE: integer, default = 512
        size of a data block

    Return
    ------
    byte-string, contents of binary file.
    '''
    with open(img_path, 'rb') as f:
        contents = f.read()
    if gets == 'all':
        return contents
    elif gets == 'super':
        return contents[BSIZE:BSIZE * 2]
    else:
        print('read_img: gets param is expected \'all\' or \'super\', got %s'
              % gets)
        sys.exit()


def read_params(file_contents, BSIZE=512, LSIZE=4, BYTE=8):
    '''
    Read params from byte-string.
    This method is used with byte-string, so not give path.

    Parameters
    ----------
    file_contents: byte-string
        path for image to be read bytes
    BSIZE: integer, default = 512
        size of a data block
    LSIZE: integer, default = 4
        size of a unsigned long
        Note: In Python, size of a unsigned long equal size of a integer
    BYTE: integer, default = 8
        size of a Byte
        Note: considering unusual enviroment, Byte is not 8 bits.

    Return
    ------
    dict, set of param names and value.
    '''
    params = list(struct.unpack(
        '<' + ('L' * (BSIZE // LSIZE)), file_contents)[0:7])
    params.append(params[6] - params[5])
    params.append((params[0] - 1) // (BSIZE * BYTE) + 1)
    params.append(params[6] + params[8])
    param_names = ['size', 'n_datas', 'n_inodes', 'n_logs', 'log_start',
                   'inode_start', 'bmap_start', 'n_inode_blocks',
                   'n_bmaps', 'datas_start']
    param_set = {param: value for param, value in zip(param_names, params)}
    return param_set


def compact_data(data_blocks, start, BSIZE=512):
    '''
    Compact and resize data-blocks.
    This method is used with byte-string, so not give path.

    Parameters
    ----------
    data_blocks: list of byte-string
        binary_data
    start: integer
        number of beginning of data blocks
    BSIZE: integer, default = 512
        size of a data block

    Return
    ------
    tuple, resized data blocks and table for changed block number
    '''
    new_number = now_block = start
    new_data = []
    rewrite_table = {0: 0}
    for data in data_blocks:
        if data != b'\x00' * BSIZE:
            new_data.append(data)
            rewrite_table[now_block] = new_number
            new_number += 1
        now_block += 1
    return b''.join(new_data), rewrite_table


def rewrite_inode(inode_blocks, rewrite_table,
                  BSIZE=512, NDIRECT=12, SSIZE=2, USIZE=4):
    '''
    Rewrite address number of pointer of inode
    This method is used with byte-string, so not give path.

    Parameters
    ----------
    inode_blocks: list of byte-string
        inode-contained blocks
    rewrite_table: dict
        table for changed data block ID
    BSIZE: integer, default = 512
        size of a data block
    NDIRECT: integer, default = 12
        number of datas inode has directly
    SSIZE: integer, default = 2
        size of a short
    USIZE: integer, default = 4
        size of a uint

    Return
    ------
    byte-string, rewritten inode blocks
    '''
    inodes = b''.join(inode_blocks)
    inodes = list(struct.unpack('<' + ('h' * 4 + 'I' * (NDIRECT + 2)) *
                                (len(inodes) //
                                 (SSIZE * 4 + USIZE * (NDIRECT + 2))),
                                inodes))
    inodes = [inodes[(NDIRECT + 6) * i:(NDIRECT + 6) * (i + 1)]
              for i in range(len(inodes) // (NDIRECT + 6))]
    new_inode = []
    for inode in inodes:
        inode[5:] = [rewrite_table[inode[i]] for i in range(5, NDIRECT + 6)]
        inode[:4] = [struct.pack('<h', inode[i]) for i in range(4)]
        inode[4:] = [struct.pack('<I', inode[i])
                     for i in range(4, NDIRECT + 6)]
        inode = b''.join(inode)
        new_inode.append(inode)
    return b''.join(new_inode)


def update_bmaps(use_block, nbmaps, BSIZE=512, BYTE=8):
    '''
    Make new bmap blocks

    Parameters
    ----------
    use_block: integer
        number of used blocks
    nbmaps: integer
        number of blocks for bmap
    BSIZE: integer, default = 512
        size of a data block
    BYTE: integer, default = 8
        size of a Byte
        Note: considering unusual enviroment, Byte is not 8 bits.

    Return
    ------
    byte-string, new bmap blocks
    '''
    new_bmaps = b'\xff' * (use_block // BYTE)
    re_bits = use_block % BYTE
    re_bmaps = 0
    for i in range(re_bits):
        re_bmaps += 2 ** i
    new_bmaps += struct.pack('<B', re_bmaps)
    new_bmaps += b'\x00' * (BSIZE * nbmaps - ((use_block - 1) // BYTE + 1))
    return new_bmaps
