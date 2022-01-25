from __future__ import division

# Standard Library
import os
import argparse
from up.utils.general.yaml_loader import load_yaml

# Import from local
from .subcommand import Subcommand
from up.utils.general.registry_factory import SUBCOMMAND_REGISTRY
from up.utils.general.log_helper import default_logger as logger
from up.utils.general.toadela_helper import to_adela
from up.utils.general.user_analysis_helper import send_info


__all__ = ['ToAdela']


@SUBCOMMAND_REGISTRY.register('to_adela')
class ToAdela(Subcommand):
    def add_subparser(self, name, parser):
        sub_parser = parser.add_parser(name,
                                       description='subcommand for to caffe',
                                       help='convert a model to caffe model')
        sub_parser.add_argument('--config',
                                dest='config',
                                required=True,
                                help='settings of detection in yaml format')
        sub_parser.add_argument("--release_json",
                                dest='release_json',
                                default="release.json",
                                help="release information")
        sub_parser.add_argument('--save_to',
                                dest='save_to',
                                default=None,
                                type=str,
                                help='path to save kestrel model')
        sub_parser.add_argument('--serialize',
                                dest='serialize',
                                action='store_true',
                                help='wether to do serialization, if your model runs on tensor-rt')
        sub_parser.add_argument('--cfg_type',
                                dest='cfg_type',
                                type=str,
                                default='up',
                                help='config type (up or pod)')
        sub_parser.add_argument('--opts',
                                help='options to replace yaml config',
                                default=None,
                                nargs=argparse.REMAINDER)

        sub_parser.set_defaults(run=_main)
        return sub_parser


def main(args):
    assert (os.path.exists(args.config)), args.config
    cfg = load_yaml(args.config, args.cfg_type)
    cfg['args'] = {
        'opts': args.opts
    }
    send_info(cfg, func="to_adela")
    to_adela(cfg, args.release_json, args.save_to, args.serialize)


def _main(args):
    logger.init_log()
    main(args)