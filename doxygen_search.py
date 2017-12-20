import os
import xml.etree.ElementTree
import sys
import argparse

class Index(object):
    def __init__(self, directory, fname="index.xml"):
        self.directory = directory
        index_fname = os.path.join(directory, fname)
        self.raw = xml.etree.ElementTree.parse(index_fname).getroot()
        self.files = []
        self.doc_items = {}

        for compound in self.raw:
            if compound.tag != "compound": continue
            if compound.attrib["kind"] != "file": continue
            if len(compound) == 0: continue

            ref_filename = self._filename_from_compound(compound)
            self.files.append(ref_filename)

            self.build_members(compound)

    def _filename_from_compound(self, compound):
        assert "refid" in compound.attrib
        ref = compound.attrib["refid"]
        filename = "%s.xml" % os.path.join(self.directory, ref)
        return filename

    def build_members(self, compound):
        for member in compound:
            if member.tag != "member": continue
            if len(member) != 1: continue #name tag only

            name = member[0].text
            if name not in self.doc_items:
                self.doc_items[name] = []

            attrib_kind = member.attrib["kind"]
            kind = attrib_kind if attrib_kind != "function" else "func"
            self.doc_items[name].append({"file": self._filename_from_compound(compound),
                                         "refid": member.attrib["refid"],
                                         "kind": kind})
            
class DocDefinition(object):
    def __init__(self, definition):
        self.definition = definition

    def _get_simple_tag(self, tag_name, default=None):
        tag = None
        for section in self.definition:
            if section.tag == tag_name:
                tag = section

        if tag == None: return default

        iterable = True
        try:
            _  = (x for x in tag)
        except TypeError:
            iterable = False

        if not iterable:
            print("here")
            return tag.text.strip()

        return tag[0].text.strip()

    def _nested_text(self, parent_tag, stop_tags=[]):
        texts = []
        tails = []

        if parent_tag is None:
            return ""

        for tag in parent_tag.iter():
            if tag.tag in stop_tags: break;
            
            text = tag.text
            tail = tag.tail

            if text: text = text.strip().strip("\n")
            if tail: tail = tail.strip().strip("\n")
            if text: texts.append(text)
            if tail: tails.append(tail)

        tails.reverse()
        return " ".join(texts + tails)
            
    def _params(self):
        params = {}

        for item in self.definition.iter("param"):
            name = self._nested_text(item.find("declname"))
            type = self._nested_text(item.find("type"))

            if not name or name.isspace(): continue
            params[name] = {"type": type, "descr": "No documentation available."}

        for item in self.definition.iter("parameteritem"):
            name = self._nested_text(item.find("parameternamelist"))
            descr = self._nested_text(item.find("parameterdescription"))

            if not name or name.isspace(): continue
            params[name]["descr"] = descr
            
        return params

    def brief(self):
        default = "No documentation available."
        return self._nested_text(self.definition.find("briefdescription"))

    def detail(self):
        stop_tags = ["parameterlist", "simplesect"]
        parent_tag = self.definition.find("detaileddescription")
        return self._nested_text(parent_tag, stop_tags)
    
    def full(self):
        brief = self.brief()
        detail = self.detail()
        params = self._params()

        param_strs = []
        for param, data in params.items():
            param_strs.append(("%s %s: %s" % (data["type"], param, data["descr"])))

        string = ""
        string += "Brief: %s\n" % brief if brief else ""
        string += " \nDetail: %s\n" % detail if detail else ""

        if not string or string.isspace():
            string = "No documentation available.\n"
        
        string += " \nParams: \n%s" % "\n".join(param_strs) if param_strs else ""

        return string

class DocFile(object):
    def __init__(self, fname):
        self.fname = fname
        self.xml_root = xml.etree.ElementTree.parse(fname).getroot()
        self.definition_root = self.xml_root.find("compounddef")
        self.sections = self.load_sections(self.definition_root)

    def load_sections(self, definition_root):
        sections = {}
        for section in definition_root:
            kind = section.attrib.get("kind")
            if not kind: continue
            sections[kind] = section

        return sections

    def get_definition(self, ref):
        kind = ref["kind"]
        section = self.sections[kind]

        for definition in section:
            if definition.attrib.get("id") != ref["refid"]: continue

            return DocDefinition(definition)
        return None

def parse_options(argv):
    parser = argparse.ArgumentParser(description='Description of your program')
    parser.add_argument('-s','--symbol',
                        help='The symbol to look up documentation for',
                        required=True)
    parser.add_argument('-t','--type',
                        help='The type of documentation to return',
                        default="full")
    parser.add_argument('-x','--xml',
                        help="The path to Doxygen's XML output",
                        default=os.path.join(os.getcwd(), 'xml'))
    return vars(parser.parse_args())

def main():
    options = parse_options(sys.argv)
    i = Index(options['xml'])
    s = i.doc_items.get(options['symbol'])

    if not s:
        print("No documentation available.\n")
        sys.exit(0)
    s = s[0]
    
    f = DocFile(s["file"])

    if options["type"] == "full":
        print(f.get_definition(s).full())
    else:
        print(f.get_definition(s).brief())

if __name__=='__main__':
    main()
