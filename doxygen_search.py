import os
import xml.etree.ElementTree

functions = {}

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

    def find_doc(self, doc_item):
        self.doc_raw = xml.etree.ElementTree.parse(doc_item["file"]).getroot()

        compound_def = self.doc_raw[0]
        assert compound_def.tag == "compounddef"

        section = self.find_doc_section(compound_def, doc_item["kind"])
        d = self.find_member_def(section, doc_item["refid"])
        return d

    def find_doc_section(self, compound_def, kind):
        for section in compound_def:
            if kind == section.attrib.get("kind"):
                return section

        import pdb; pdb.set_trace()
        return None

    def find_brief_doc(self, member_def):
        for section in member_def:
            if section.tag != "briefdescription":
                continue

            return section[0].text


    def find_member_def(self, section, ref):
        for x in section:
            if x.attrib["id"] == ref:
                return x

        import pdb; pdb.set_trace()

    def symbol_to_brief(self, symbol):
        doc_item = self.doc_items.get(symbol)[0]
        if not doc_item: return "No documentation available"

        doc = self.find_doc(doc_item)
        brief = self.find_brief_doc(doc)
        return brief.strip()
            

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
        self.definition_root = self.xml_root[0]
        assert self.definition_root.tag == "compounddef"
        
        self.sections = self.load_sections(self.definition_root)

    def load_sections(self, definition_root):
        sections = {}
        for section in definition_root:
            kind = section.attrib.get("kind")
            if not kind: continue
            sections[kind] = section

        return sections

    def get_doc_definition(self, ref):
        kind = ref["kind"]
        section = self.sections[kind]

        for definition in section:
            if definition.attrib.get("id") != ref["refid"]: continue

            return DocDefinition(definition)
        return None
def main():
    import sys
    path = sys.argv[1]
    symbol = sys.argv[2]

    i = Index(path)

    s = i.doc_items.get(symbol)
    if not s:
        print("No documentation available.")
        sys.exit(0)
    s = s[0]
    
    f = DocFile(s["file"])
    print(f.get_doc_definition(s).full())

if __name__=='__main__':
    main()
