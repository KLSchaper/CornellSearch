import os
import tarfile
import urllib
import shutil
import re
import nltk
import string

contents = os.listdir(os.path.curdir)
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
            print(tfi)
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
    #print(''.join(f.readlines()))
    latex_lines = f.readlines()

#print(latex_lines)
print('\n'.join([line[:-1] for line in latex_lines]))



def strip_comments(ll):
    """ returns lines of the latex file, except that comments, i.e. everything behind % on a

    line, are removed.
    """
    line_list = ll[:]
    for ind, line in enumerate(line_list):
        comment_pos = line.find('%')
        if comment_pos != -1:
            line_list[ind] = line[:line.find('%')]
        else:
            line_list[ind] = line[:-1]
    line_list = [line.strip() for line in line_list]
    line_list = [line for line in line_list if line]
    return line_list



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
    def __init__(self, name, linelist, level, headnode=False):
        self.headnode = headnode
        self.name = name
        self.linelist = linelist
        leveldelimiters, childnames =  section_delimiters(linelist, level)
        self.ld, self.cnames = leveldelimiters, childnames
        self.cn = []
        print(level, self.name)

        for i in range(len(self.ld)-1):
            print(level)
            self.cn = [Node(self.cnames[i], linelist[self.ld[i]:self.ld[i+1]], level+1)]
            self.other_keys = {}
        if headnode:
            for ind, line in enumerate(linelist):
                name, content = self.extract_tags(line, ind)
                self.other_keys[name] = content.translate(PUNCTUATION_TABLE)
            for k,v in self.other_keys.items():
                print(k, v, "\n")



    def extract_tags(self, line, ind):
        """

        KEYTAGS have format [["name", "latex_begin_tag", "latex_end_tag"], ...]
        """
        found_lbt = ""
        found_let = ""
        found_n = ""
        close = 0
        for n, lbt, let in KEYTAGS:
            i = line.find(lbt)

            if i != -1:
                print(lbt, line)
                close = self.find_closing(let, ind)
                found_lbt = lbt
                found_let = let
                found_n = n
                print(found_lbt)
                break

        return found_n, self.extract_tag_contents(" ".join(self.linelist[ind:close]), found_lbt, found_let)

    @staticmethod
    def extract_tag_contents(string, lbt, let):
        return string[len(lbt):-1*len(let)]


    def find_closing(self, closetag, startindex):
        if closetag == '}':
            brace_count = 0
            while True:
                print("startindex: ", startindex)
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
            while True:
                if self.linelist[startindex].find(closetag) != -1:
                    return startindex + 1
                else:
                    startindex += 1




class parsetree:
    """ treelike structure, contains nodes

    This parsetree will later be converted to JSON,
    For nor it contains lists with childnodes at each node, each of these childnodes is a lower level section
    This will be converted to the json format later (with perhaps an intermediary dictionary format)
    """
    def __init__(self, tex_dir, json_dir, subdir, documentID, overwrite):
        """

        :param linelist: list of lines from a latex file, stripped from comments and everything before
            the \makefile tag, as \newcommand shenanigans make life difficult otherwise.
        :param documentID: string, the filename
        """
        latex_lines = []
        tfname = os.path.join(os.path.join(tex_dir, subdir), documentID)
        jsubdir = os.path.join(json_dir, subdir)
        jfname = os.path.join(jsubdir, documentID)

        if os.path.exists(jfname):
            if not overwrite:
                print("already parsed, going to next")
                return
        else:
            os.mkdir(jsubdir)


        with open(tfname) as f:
            #print(''.join(f.readlines()))
            latex_lines = f.readlines()
        no_comments = strip_comments(latex_lines)

        self.headnode = Node(documentID, no_comments, 0, headnode=True)
        JSON = JSONify(self.headnode)


        with open(jfname, 'w') as f:
            print(str(JSON))
            f.write(str(JSON))

def JSON_unknown_cn(node):
    if type(node) == str:
        return node.translate(PUNCTUATION_TABLE) #remove punctuation
    else:
        return {node.name : [JSON_unknown_cn(cn) for cn in node.cn]}

def JSONify(node):
    base = {node.name : JSON_unknown_cn(node)}

    if node.headnode:
        base.update(node.other_keys)

    return base

def JSONify_str(node):
    return node.cn




# KEYTAGS have format ["name", "latex_begin_tag", "latex_end_tag"]
KEYTAGS = [["date","\date{", "}"],
           ["abstract","\\begin{abstract}", "\end{abstract}"],
           ["keywords", "{\\bf Key words:}", "."],
           ["author", "\\author{", "}"],
           ["keywords","\\it Key words:","\end"],
           ["content", "\\section{", "\end{document}"]
            ]

PUNCTUATION_TABLE = str.maketrans({key: None for key in string.punctuation})


tex_dir = 'unzipped'
docID = '0301005'
json_dir = 'json'
sub_dir = 'hep-th-2003'
doctree = parsetree(tex_dir, json_dir, sub_dir, docID, True)
