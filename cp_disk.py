'''
Copy disk-image programs
This program is made for a task of System Software.
Used Python3.6.2, pre-installed modules, and a module named "cp_util" I made.

This programs contains to compact data,
but not contains to refact inode.
'''
import sys
from cp_util import read_img
from cp_util import read_params
from cp_util import compact_data
from cp_util import rewrite_inode
from cp_util import update_bmaps



__author__  = "Katsunoshin Matsui<matsui.k.ai@m.titech.ac.jp>"
__version__ = "1.00"
__date__    = "1 Dec 2017"


BSIZE = 512


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python %s src_path dst_path' % sys.argv[0])
        sys.exit()

    src_path = sys.argv[1]
    dst_path = sys.argv[2]
    contents = read_img(src_path)
    blocks = [contents[BSIZE * i:BSIZE * (i + 1)]
              for i in range(len(contents) // BSIZE)]
    old_params = read_params(blocks[1])
    new_params = old_params
    sp = blocks[1]
    try:
        sp = read_img(dst_path, gets='super')
        print('There exists a file. Do you want to overwrite the file?(y/n):',
              end=' ')
        if input() != 'y':
            print('Stopped copying img.')
            sys.exit()
        new_params = read_params(sp)
    except SystemExit:
        sys.exit()
    except:
        pass
    logs = b'\x00' * BSIZE * new_params['n_logs']
    inodes = blocks[old_params['inode_start']:
                    old_params['inode_start'] + old_params['n_inode_blocks']]
    datas = blocks[old_params['datas_start']:
                   old_params['datas_start'] + old_params['n_datas']]
    datas, rewrite_table = compact_data(datas, old_params['datas_start'])
    inodes = rewrite_inode(inodes, rewrite_table)
    use_block = 2 + new_params['n_logs'] + \
        new_params['n_inode_blocks'] + new_params['n_bmaps'] + len(datas)
    bmaps = update_bmaps(use_block, new_params['n_bmaps'])
    copy_content = b'\x00' * BSIZE + sp + logs + inodes + bmaps + \
        datas + b'\x00' * BSIZE * (new_params['size'] - use_block)

    with open(dst_path, 'wb') as f:
        f.write(contents)
