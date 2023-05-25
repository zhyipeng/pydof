from .enums import FieldType
from .parser import Parser


class PvfUtilityFormatter:

    def __init__(self, parser: Parser):
        self.parser = parser

    def render_header(self):
        return '#PVF_File'

    def render(self):
        data = ''
        for f in self.parser.origin:
            match f.tp:
                case FieldType.STR.value:
                    data += f'\t`{f.value}`'
                case FieldType.KEY.value:
                    if not f.value.startswith('[/'):
                        data += '\n'
                    data += f'\n{f.value}\n'
                case _:
                    data += f'\t{f.value}'

        return self.render_header() + data
