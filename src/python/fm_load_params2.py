import argparse
import os.path as op
from pathlib import Path
import pandas as pd
import numpy as np
from utils_wgbs import validate_single_file, validate_file_list, \
        add_multi_thread_args, eprint, IllegalArgumentError

COS_CONF_PATH = op.join(op.join(Path(__file__).parent.parent.parent, 'supplemental'), 'find_markers_config.txt')
DEF_CONF_PATH = op.join(op.join(Path(__file__).parent.parent.parent, 'supplemental'), 'find_markers_defaults.txt')


class MFParams:
    def __init__(self, args):
        # load parameters from user defined config file
        self.load_config_file(args.config_file)
        # load parameters from argparse (they overwite the config file params)
        self.load_command_line_args(args)
        # laod defaults for missing parameters
        self.set_defaults()
        # validate parameters
        self.validate_args()

    def load_config_file(self, config_file):
        pdict = self.load_from_file(config_file)
        if pdict:
            for key, val in pdict.items():
                setattr(self, key, val)

    def load_command_line_args(self, args):
        adict = self.set_param_type(vars(args))
        for key, val in adict.items():
            if val is not None:
                setattr(self, key, val)

    def set_defaults(self):
        ddict = self.load_from_file(DEF_CONF_PATH)
        for key, val in ddict.items():
            if (not hasattr(self, key)) or (getattr(self, key) is None):
                setattr(self, key, val)

    @staticmethod
    def load_from_file(param_file):
        if not param_file:
            return
        validate_single_file(param_file)
        d = pd.read_csv(param_file, sep=':', comment='#',
                header=None, names=['val'], index_col=0,
                skipinitialspace=True).to_dict()['val']
        return MFParams.set_param_type(d)

    @staticmethod
    def set_param_type(cdict):
        rdict = {}
        for key, val in cdict.items():
            if type(val) == float and np.isnan(val):
                val = None
            elif type(val) == str and val.isdigit():
                val = int(val)
            elif type(val) == str and val.replace('.', '', 1).isdigit():
                val = float(val)
            rdict[key] = val
        return rdict

    def validate_args(self):

        # validate integers
        if self.min_cpg < 0:
            raise IllegalArgumentError('min_cpg must be non negative')
        if self.max_cpg < 1:
            raise IllegalArgumentError('max_cpg must larger than 0')
        if self.min_bp < 0:
            raise IllegalArgumentError('min_bp must be non negative')
        if self.max_bp < 2:
            raise IllegalArgumentError('max_bp must larger than 1')

        # validate the [0.0, 1.0] fractions
        for key in ('na_rate_tg', 'na_rate_bg', 'delta', 'tg_quant', \
                    'bg_quant', 'unmeth_thresh', 'meth_thresh', \
                    'unmeth_mean_thresh', 'meth_mean_thresh'):
            if not (1.0 >= getattr(self, key) >= 0):
                eprint(f'Invalid value for {key} ({val}): must be in ({low}, {high})')
                raise IllegalArgumentError()

        # validate hyper hypo:
        if self.only_hyper and self.only_hypo:
            eprint(f'at most one of (only_hyper, only_hypo) can be specified')
            raise IllegalArgumentError()

        # validate input files
        for key in ('methly_profile', 'groups_file'):
            val = getattr(self, key)
            if val is None:
                eprint(f'[wt fm] missing required parameter: {key}')
                raise IllegalArgumentError()
            validate_single_file(val)
            # change path to absolute path
            setattr(self, key, op.abspath(val))

def parse_args():
    parser = argparse.ArgumentParser(description='Find differentially methylated blocks')
    parser.add_argument('--config_file', '-p',
            help=f'find_markers config file see {COS_CONF_PATH} for example')
    parser.add_argument('--methly_profile', '-m', help='methylation profile path.')
    parser.add_argument('--groups_file', '-g', help='csv file of groups')
    parser.add_argument('--targets', nargs='+', help='find markers only for these groups (OR relation)')
    parser.add_argument('--background', nargs='+', help='find markers only against these groups (AND relation)')
    parser.add_argument('-o', '--out_dir', help='Output directory')
    parser.add_argument('--min_bp', type=int)
    parser.add_argument('--max_bp', type=int)
    parser.add_argument('--min_cpg', type=int)
    parser.add_argument('--max_cpg', type=int)
    parser.add_argument('--delta', type=float,
            help='Filter markers by beta values delta. range: [0.0, 1.0]')
    parser.add_argument('--only_hyper', action='store_true',
            help='Only consider hyper-methylated markers')
    parser.add_argument('--only_hypo', action='store_true',
            help='Only consider hypo-methylated markers')
    parser.add_argument('--top', type=int,
                        help='Output only the top TOP markers, under the constraints. [All]')
    parser.add_argument('--header', action='store_true', help='add header to output files')
    parser.add_argument('--tg_quant', type=float, help='quantile of target samples to ignore')
    parser.add_argument('--bg_quant', type=float, help='quantile of background samples to ignore')

    parser.add_argument('--unmeth_mean_thresh', type=float,
            help='average beta value for the unmethylated group')
    parser.add_argument('--meth_mean_thresh', type=float,
            help='average beta value for the methylated group')

    parser.add_argument('--unmeth_thresh', type=float,
            help='quantlie beta value for the unmethylated group')
    parser.add_argument('--meth_thresh', type=float,
            help='quantlie beta value for the methylated group')

    parser.add_argument('--na_rate_tg', type=float,
            help='rate of samples with insufficient coverage allowed in target samples')
    parser.add_argument('--na_rate_bg', type=float,
            help='rate of samples with insufficient coverage allowed in background samples')
    parser.add_argument('--verbose', '-v', action='store_true')
    add_multi_thread_args(parser)
    args = parser.parse_args()
    return args

