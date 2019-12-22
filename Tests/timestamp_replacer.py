import json
from typing import List, Union
from mitmproxy import ctx, flow
from time import ctime
from dateutil.parser import parse


class TimestampReplacer:
    def __init__(self):
        self.count = 0
        self.keys = []

    def load(self, loader):
        loader.add_option(
            name='keys_to_replace',
            typespec=str,
            default='',
            help='''
            The keys inside a Posted Request's body whose value is a timestamp and needs to be replaced.
            Nested keys whould be written in dot notation.
            '''
        )
        loader.add_option(
            name='detect_timestamps',
            typespec=bool,
            default=False,
            help='''
            Set to True only if recording a mock file. Used to determine which keys need to be replaced in incoming
            request bodies during a mock playback.
            '''
        )
        loader.add_option(
            name='keys_filepath',
            typespec=str,
            help='''
            The path to the file that contains the problematic keys for the test playbook recording that resides
            in the same directory.
            '''
        )

    def request(self, flow: flow.Flow) -> None:
        self.count += 1
        if flow.request.method == 'POST':
            content = json.loads(flow.request.raw_content.decode())
            if ctx.options.detect_timestamps:
                self.keys.extend(self.get_problematic_keys(content))
            else:
                original_content = content.copy()
                body = content
                ctx.log.info('body pre-update:\n{}'.format(json.dumps(body, indent=4)))
                modified = False
                keys_to_replace = ctx.options.keys_to_replace.split() or []
                ctx.log.info('{}'.format(keys_to_replace))
                for key_path in keys_to_replace:
                    keys = key_path.split('.')
                    ctx.log.info('keypath parts: {}'.format(keys))
                    lastkey = keys[-1]
                    ctx.log.info('lastkey: {}'.format(lastkey))
                    for k in keys[:-1]:
                        if k in body:
                            body = body[k]
                            ctx.log.info('updated body: {}'.format(body))
                    if lastkey in body:
                        ctx.log.info('modifying request to "{}"'.format(flow.request.pretty_url))
                        ctx.log.info('original request body:\n{}'.format(json.dumps(original_content, indent=4)))
                        body[lastkey] = self.count
                        modified = True
                if modified:
                    ctx.log.info('modified request body:\n{}'.format(json.dumps(content, indent=4)))
                    flow.request.raw_content = json.dumps(content).encode()

    def get_problematic_keys(self, content: dict) -> List[str]:
        def travel_dict(obj: Union[dict, list], key_path='') -> List[str]:
            bad_key_paths = []
            if isinstance(obj, dict):
                for key, val in obj.items():
                    sub_key_path = '{}.{}'.format(key_path, key) if key_path else key
                    if isinstance(val, (list, dict)):
                        bad_key_paths.extend(travel_dict(val, sub_key_path))
                    else:
                        is_string = isinstance(val, str)
                        possible_timestamp = isinstance(val, int) and len(str(val)) >= 8
                        try:
                            if is_string or possible_timestamp:
                                if possible_timestamp:
                                    if len(str(val)) < 14:
                                        parse(ctime(val))
                                    else:
                                        parse(ctime(val / 1000.0))
                                else:
                                    parse(val)
                                # if it continues to the next line that means it successfully parsed the object
                                # and it's some sort of time-related object
                                bad_key_paths.append(sub_key_path)
                        except ValueError:
                            pass
            elif isinstance(obj, list):
                for i, val in enumerate(obj):
                    sub_key_path = '{}.{}'.format(key_path, i) if key_path else i
                    if isinstance(val, (list, dict)):
                        bad_key_paths.extend(travel_dict(val, sub_key_path))
                    else:
                        is_string = isinstance(val, str)
                        possible_timestamp = isinstance(val, int) and len(str(val)) >= 8
                        try:
                            if is_string or possible_timestamp:
                                if possible_timestamp:
                                    if len(str(val)) < 14:
                                        parse(ctime(val))
                                    else:
                                        parse(ctime(val / 1000.0))
                                else:
                                    parse(val)
                                # if it continues to the next line that means it successfully parsed the object
                                # and it's some sort of time-related object
                                bad_key_paths.append(sub_key_path)
                        except ValueError:
                            pass
            return bad_key_paths
        bad_keys = travel_dict(content)
        return bad_keys

    def done(self):
        if ctx.options.detect_timestamps:
            bad_keys_filepath = ctx.options.keys_filepath
            with open(bad_keys_filepath, 'w') as bad_keys_file:
                bad_keys_file.write(' '.join(self.keys))


addons = [TimestampReplacer()]
