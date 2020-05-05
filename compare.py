from CodeWarrior import Error
import json
import sys
import types

import httplib2 as httplib2

TYPE = 'TYPE'
PATH = 'PATH'
VALUE = 'VALUE'


class Diff(object):
    def __init__(self, first, second, with_values=False):
        self.difference = []
        self.seen = []
        not_with_values = not with_values
        self.check(first, second, with_values=with_values)

    def check(self, first, second, path='', with_values=False):
        if with_values and second is not None:
            if not isinstance(first, type(second)):
                message = '%s - %s, %s' % (path, type(first).__name__, type(second).__name__)
                self.save_diff(message, TYPE)

        if isinstance(first, dict):
            for key in first:
                if len(path) == 0:
                    new_path = key
                else:
                    new_path = "%s.%s" % (path, key)

                if isinstance(second, dict):
                    if second.has_key(key):
                        sec = second[key]
                    else:
                        self.save_diff(new_path, PATH)
                        sec = None

                    if sec is not None:
                        self.check(first[key], sec, path=new_path, with_values=with_values)
                else:
                    self.save_diff(new_path, PATH)
                    self.check(first[key], second, path=new_path, with_values=with_values)

        elif isinstance(first, list):
            for (index, item) in enumerate(first):
                new_path = "%s[%s]" % (path, index)
                sec = None
                if second is not None:
                    try:
                        sec = second[index]
                    except (IndexError, KeyError):
                        self.save_diff('%s - %s' % (new_path, type(item).__name__), TYPE)

                self.check(first[index], sec, path=new_path, with_values=with_values)

        else:
            if with_values and second is not None:
                if first != second:
                    self.save_diff('%s - %s | %s' % (path, first, second), VALUE)
            return

    def save_diff(self, diff_message, type_):
        if diff_message not in self.difference:
            self.seen.append(diff_message)
            self.difference.append((type_, diff_message))


def getContentFromUri(uri):
    h = httplib2.Http()
    resp, content = h.request(uri, "GET")
    return content


def getContentFromFile(filePath):
    return open(filePath, 'r').read()


def getContent(location):
    content = None
    if type(location) is types.DictType:
        return location
    if location.startswith("http"):
        content = getContentFromUri(location)
    else:
        content = getContentFromFile(location)
    if content is None:
        raise Error("Could not load content for " + location)
    return json.loads(content)


def compare(location1, location2):
    json1 = getContent(location1)
    json2 = getContent(location2)
    diff1 = Diff(json1, json2, True).difference
    diff2 = Diff(json2, json1, False).difference
    diffs = []
    for type, message in diff1:
        new_type = 'CHANGED'
        if type == PATH:
            new_type = 'REMOVED'
        diffs.append({'type': new_type, 'message': message})
    for type, message in diff2:
        diffs.append({'type': 'ADDED', 'message': message})
    return diffs


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit('Error compiling')
    location1 = sys.argv[1]
    location2 = sys.argv[2]
    diffs = compare(location1, location2)
    if len(diffs) > 0:
        print '\r\nFound differences comparing ' + location1 + ' and ' + location2
    for diff in diffs:
        print diff['type'] + ': ' + diff['message']
