import os
import tarfile
import urllib
import shutil
import re
import nltk
import string
import json

<<<<<<< HEAD
=======
print(os.listdir())
print(os.listdir('unzipped'))



>>>>>>> 06004135719c8104127232c4c41fd319e6408505
DOCID_TO_DATE = dict()
contents = os.listdir()
# Should list among others: data_zipped, elasticserch-1.7.1, unzipped
# data_zipped should contain all hep-th-YYYY.tar.gz ziles
# unzipped should either be empty or filled with directories per year


def get_dataset():
    base = 'http://www.cs.cornell.edu/projects/kddcup/download/hep-th-'
    filebase = 'hep-th-'
    datafiles = [str(n) for n in range(1992, 2004)]
    for df in datafiles:
        testfile = urllib.request.URLopener()
        testfile.retrieve(base + df + '.tar.gz', 'data_zipped/' + filebase + df +'.tar.gz')


if 'unzipped' not in contents:
    os.mkdir('unzipped')
if 'data_zipped' not in contents:
    os.mkdir('data_zipped')
    if not len(os.listdir('data_zipped')):
        get_dataset()
if 'json' not in contents:
    os.mkdir('json')



zipped_folder = os.path.join(os.path.curdir, 'data_zipped')


def extract_tar():
    unzipped_folder = os.path.join(os.path.curdir, 'unzipped')
    datafiles = [str(n) for n in range(1991, 2004)]
    for tf in os.listdir(zipped_folder):
        tfi = os.path.join(zipped_folder, tf) # tarfile instance
        if True:
            if (tfi.endswith("tar.gz")):
                tar = tarfile.open(tfi, "r:gz")
                tar.extractall()
                tar.close()
            elif (tfi.endswith("tar")):
                tar = tarfile.open(tfi, "r:")
                tar.extractall()
                tar.close()
        shutil.move(tfi[-11:-7], os.path.join(unzipped_folder,tf[:-7]))

if not os.listdir('unzipped'):
    extract_tar()



testfile = 'unzipped/hep-th-2003/0301005'
latex_lines = []

with open(os.path.join(os.path.curdir, testfile)) as f:
    latex_lines = f.readlines()




def get_name_section(section_string, depth):
    """ returns (sub) section name, string

    :param section_string: string, latex_line with section tag on it
    :param depth: int, depth of section 0 = \section, 1 = \subsection etc.
    :return: string, either what is included in the section tag, or all of it that is included on that line

    # TODO:
      -  check for closing tag beforehand, such that complete names can be extracted, if the name spans multiple rows
      -  simplify function by replacing the string in find for start with levelname(depth) (works now but tired, so not risking)
    """
    start = section_string.find('\\' + 'sub'* (depth) + 'section{')
    end = section_string.find('}')
    truestart = start + 3*depth + 9 #adding the latex command to index
    return section_string[truestart:end]

def levelname(depth):
    """ returns string with appropriate (sub) section latex command for given depth

    :param depth: int
    """
    return '\\' + 'sub'*depth + 'section{'

def section_delimiters(linelist, level):
    """ returns two lists, delimiters for (sub) sections as indices of the list,

    and their accompanying names
    """
    indices = []
    names = []
    lvln = levelname(level)
    for i, line in enumerate(linelist):
        if line.find(lvln) != -1:
            indices.append(i)
            names.append(get_name_section(line, level))
    return indices + [-1], names


def read_slacdates(path):
    """ Returns a dictionary that links the id of a paper to the date it was
    published.

    :param path: string, the path to the slacdates file.
    """
    id_to_date = dict()

    with open(path) as slacdates:
        for row in slacdates:
            i = row.index(' ')
            ID = row[:i]
            date = row[i + 1 : -1]
            id_to_date[ID] = date

    return id_to_date

def read_slacdates(path):
    """ Returns a dictionary that links the id of a paper to the date it was
    published.
    :param path: string, the path to the slacdates file.
    """
    id_to_date = dict()

    with open(path) as slacdates:
        for row in slacdates:
            i = row.index(' ')
            ID = row[:i]
            date = row[i + 1 : -1]
            id_to_date[ID] = date

    return id_to_date

class Node:
    """ the basic unit that will be dictionaryfied, currently each node containstheir own name (section title),

    a list of subnodes and accompanying names.
    in the future the headnode (in the parsetree) will function as the main node, containing
    subnodes 'recursively', as well as being the location in which other keywords and values are placed
    (i.e. 'author':[authorlist], 'date':'date' (in multiple formats for search))

    each of these keyswords gives more options to the user later on, so if
    you have some 'free' time... (ha wouldn't you wish)
    this is a TODO as well

    I emphasize: if this is not done well, our search is going to seriously suck.

    """
    def __init__(self, name, linelist, linelist_abstr, level, headnode=False):
        self.tot_lines = len(linelist)
        self.headnode = headnode
        self.name = name
        self.linelist = linelist

        self.tot_lines_abstract = len(linelist_abstr)
        self.linelist_abstr = linelist_abstr
        leveldelimiters, childnames =  section_delimiters(linelist, level)
        self.ld, self.cnames = leveldelimiters, childnames
        self.cn = []

        if headnode:
            self.other_keys = {}
            tempkeys = KEYTAGS[:]
            tempkeynames = [tk[0] for tk in tempkeys]
            for ind, line in enumerate(linelist):
                name, content = self.extract_tags(line, ind, tempkeys)
                if name:
                    temp_n_ind = tempkeynames.index(name)
                    tempkeys.pop(temp_n_ind)
                    tempkeynames.pop(temp_n_ind)
                    content = LatexTags(content).remove()
                    self.other_keys[name] = content.translate(PUNCTUATION_TABLE)
            if 'content' in tempkeynames:
                everything = " ".join(linelist).translate(PUNCTUATION_TABLE)
                self.other_keys['content'] = everything
                self.parse_abstract()



    def extract_tags(self, line, ind, tempkeys, abstr=False):
        """

        KEYTAGS have format [["name", "latex_begin_tag", "latex_end_tag"], ...]
        """
        found_lbt = ""
        found_let = ""
        found_n = ""
        close = 0
        content = ""
        for i, keytag in enumerate(tempkeys):
            n, comb = keytag
            for lbt, let in comb:
                i = line.find(lbt)

                if i != -1:
                    try:
                        close = self.find_closing(let, ind, abstr=abstr)
                    except IndexError:
                        raise IndexError

                    found_lbt = lbt
                    found_let = let
                    found_n = n
                    if abstr:
                        content = " ".join(self.linelist_abstr[ind:close])
                    else:
                        content = " ".join(self.linelist[ind:close])
                    break

        return found_n, content


    def find_closing(self, closetag, startindex, abstr=False):


        # ABSTRACT FILE
        if abstr:
            if closetag == '}':
                brace_count = 0
                while startindex < self.tot_lines_abstract:
                    if self.linelist_abstr[startindex].find('{') != -1:
                        brace_count += 1
                    if self.linelist_abstr[startindex].find('}') != -1:
                        brace_count -= 1
                        if brace_count == 0:
                            return startindex + 1
                        else:
                            startindex += 1
                    else:
                        startindex += 1
            else:
                while startindex < self.tot_lines_abstract:
                    if self.linelist_abstr[startindex].find(closetag) != -1:
                        return startindex + 1
                    else:
                        startindex += 1


        # LATEX FILE
        else:
            if closetag == '}':
                brace_count = 0
                while startindex < self.tot_lines:
                    if self.linelist[startindex].find('{') != -1:
                        brace_count += 1
                    if self.linelist[startindex].find('}') != -1:
                        brace_count -= 1
                        if brace_count == 0:
                            return startindex + 1
                        else:
                            startindex += 1
                    else:
                        startindex += 1
            else:
                while startindex < self.tot_lines:
                    if self.linelist[startindex].find(closetag) != -1:
                        return startindex + 1
                    else:
                        startindex += 1


    def add_key(self, key, value):
        self.other_keys[key] = value

    def parse_abstract(self):
        tempkeys = ABSTR_KEYS[:]
        tempkeynames = [k[0] for k in tempkeys]
        for ind, line in enumerate(self.linelist_abstr):
            name, content = self.extract_tags(line, ind, tempkeys, abstr=True)
            if name:
                temp_n_ind = tempkeynames.index(name)
                tempkeys.pop(temp_n_ind)
                tempkeynames.pop(temp_n_ind)
                self.other_keys[name] = content.translate(PUNCTUATION_TABLE)


class LatexTags:

    def __init__(self, text):
        self.backslash = False
        self.brace = False
        self.dollar = False

        self.text = text
        i = self.text.find('\\begin{document}')
        if i > 0:
            self.text = self.text[i:]

        self.result = ""

    def pre_read_char(self, c):
        if c == '\\':
            self.backslash = True

        elif c == ' ' or c == '\n':
            self.backslash = False

        elif c == '}':
            self.brace = False

        elif c == '$':
            self.dollar = not self.dollar

    def post_read_char(self, c):
        if self.backslash and c == '{':
            self.brace = True

    def remove(self):
        for c in self.text:
            self.pre_read_char(c)

            if not (self.backslash or self.brace or self.dollar):
                self.result += c

            self.post_read_char(c)

        return self.result



class LatexTags:

    def __init__(self, text):
        self.backslash = False
        self.brace = False
        self.dollar = False

        self.text = text
        i = self.text.find('\\begin{document}')
        if i > 0:
            self.text = self.text[i:]

        self.result = ""

    def pre_read_char(self, c):
        if c == '\\':
            self.backslash = True

        elif c == ' ' or c == '\n':
            self.backslash = False

        elif c == '}':
            self.brace = False

        elif c == '$':
            self.dollar = not self.dollar

    def post_read_char(self, c):
        if self.backslash and c == '{':
            self.brace = True

    def remove(self):
        for c in self.text:
            self.pre_read_char(c)

            if not (self.backslash or self.brace or self.dollar):
                self.result += c

            self.post_read_char(c)

        return self.result

class parsetree:
    """ treelike structure, contains nodes

    This parsetree will later be converted to JSON,
    For nor it contains lists with childnodes at each node, each of these childnodes is a lower level section
    This will be converted to the json format later (with perhaps an intermediary dictionary format)
    """
    def __init__(self, tex_dir, json_dir, subdir, documentID, abstr_dir, overwrite=False, _print=False):
        """

        :param linelist: list of lines from a latex file, stripped from comments and everything before
            the \makefile tag, as \newcommand shenanigans make life difficult otherwise.
        :param documentID: string, the filename
        """
        latex_lines = []
        tfname = os.path.join(os.path.join(tex_dir, subdir), documentID)
        afname = os.path.join(os.path.join(abstr_dir, subdir[7:]), documentID+".abs")
        jsubdir = os.path.join(json_dir, subdir)
        jfname = os.path.join(jsubdir, documentID)

        if os.path.exists(jfname):
            if not overwrite:
                print("already parsed, going to next")
                return
        else:
            if not os.path.exists(jsubdir):
                os.mkdir(jsubdir)


        with open(tfname, 'r', encoding='utf-8') as f:
            latex_lines = f.readlines()

        with open(afname, 'r', encoding='utf-8') as f:
            abstr_lines = f.readlines()

        #self.headnode = Node(documentID, no_comments, 0, headnode=True)
<<<<<<< HEAD
        self.headnode = Node(documentID, latex_lines, abstr_lines, 0, headnode=True)
        self.headnode.other_keys['date'] = DOCID_TO_DATE[documentID]

=======
        self.headnode = Node(documentID, latex_lines, 0, headnode=True)
        self.headnode.other_keys['date'] = DOCID_TO_DATE[documentID]
>>>>>>> 06004135719c8104127232c4c41fd319e6408505
        JSON = JSONify(self.headnode)


        with open(jfname, 'w') as f:
            #print(str(json.dumps(JSON)))
            f.write(str(json.dumps(JSON)))


def JSON_unknown_cn(node):
    if type(node) == str:
        no_punct = node.translate(PUNCTUATION_TABLE) #remove punctuation
        return no_punct
    else:
        return {node.name : [JSON_unknown_cn(cn) for cn in node.cn]}

def JSONify(node):
    base = {node.name : JSON_unknown_cn(node)}
    if node.headnode:
        base.update(node.other_keys)
    return base

def JSONify_str(node):
    return node.cn






# KEYTAGS have format ["name", ["latex_begin_tag", "latex_end_tag"]]
KEYTAGS = [["date",[["date{", "}"], #9301009, 00010001
                    ["Date{", "}"], #9301008
                    ["%Date: ", "\n"]]], # 9201002, 9201003, 9201004 etc...
                                        # Kun je checken of 9301010 "Mon Jan  4 13:06:16 1993" geeft? Of empty/niks?,
           ["facet",[["\\it Key words:","\\end"], ["\\Key words:","\\end"], ["Key words", "."]]],
           ["content", [["\\section{", "\\end{document}"]]],
           ["introduction", [["\\newsec{", "\\newsec"],   # includes first line of section after intro
                             ["\\section{", "\\section{"] # includes first line of section after intro
                    ]
                ]
          ]

<<<<<<< HEAD
=======


PUNCTUATION_TABLE = str.maketrans({key: " " for key in string.punctuation})

DOCID_TO_DATE = read_slacdates('hep-th-slacdates')
>>>>>>> 06004135719c8104127232c4c41fd319e6408505

ABSTR_KEYS = [["author",[["Authors: ", "\n"], ]],
              ["title",[["Title: ", "\n"], ]],
              ["abstract",[["\\\\\\n  ", "\\\\"]]]]

PUNCTUATION_TABLE = str.maketrans({key: " " for key in string.punctuation})

DOCID_TO_DATE = read_slacdates('hep-th-slacdates')
json_dir = "json"
tex_dir = "unzipped"
abstr_dir = "abstracts"
sub_dir = "hep-th-2003"

faulty = []

for sd in os.listdir("unzipped"):
    for file in os.listdir(os.path.join(tex_dir, sd)):
        print(file)
        try:
            try:
                #tex_dir, json_dir, subdir, documentID, abstr_dir
                parsetree(tex_dir, json_dir, sd, file, abstr_dir, overwrite=True)
            except UnicodeDecodeError:
                faulty.append(file)
        except FileNotFoundError:
            faulty.append(file)

print(faulty)
