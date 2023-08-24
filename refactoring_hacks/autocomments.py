# quick hack:
# grabs data from XML file describing opcodes from http://ref.x86asm.net
# then autocomments the cpux86 emulator code
#
# (super brittle hack)
#

from BeautifulSoup import BeautifulStoneSoup #thank you soup, fuck XML parsers
import json, re

#
# Let me reiterate how much I despise scraping data from XML
#
infile = open("x86reference.xml","r").read()
soup=BeautifulStoneSoup(infile)
onesies=soup.find('one-byte').findAll('pri_opcd')
twosies=soup.find('two-byte').findAll('pri_opcd')

def hexRepOfOp(op):
    i=int(op['value'],16)
    return f"0x0{hex(i)[2:]}".lower() if i < 16 else f"0x{hex(i)[2:]}".lower()
def mnem(op):
    return res.string if (res := op.find('mnem')) else ""
def src(op):
    return res.getText() if (res := op.find('syntax').find('src')) else ""
def dst(op):
    return res.getText() if (res := op.find('syntax').find('dst')) else ""
def note(op):
    return res.getText() if (res := op.find('note').find('brief')) else ""
def opstr(op):
    return f"{mnem(op)} {src(op)} {dst(op)} {note(op)}"

onedict = {hexRepOfOp(op): opstr(op) for op in onesies}
twodict = {hexRepOfOp(op): opstr(op) for op in twosies}
with open("onebyte_dict.json",'w') as outfile:
    json.dump(onedict,outfile)
with open("twobyte_dict.json",'w') as outfile:
    json.dump(twodict,outfile)
# now transform source file --------------------------------------------------------------------------------

# - for weird exec counting function
caseline = re.compile("(                        case )(0x[0-9a-f]+):.*")
def strip_1(str):
    return str
onebyte_start = 3176
twobyte_start = 3177
twobyte_end = 3546

# - for normal instruction format: 0xXX
#caseline = re.compile("(\s+case )(0x[0-9a-f]+):.*")
#def strip_1(str):
#    return str
#onebyte_start = 5662
#twobyte_start = 7551
#twobyte_end = 8291

# - for 16bit compat instruction format: 0x1XX
#caseline = re.compile("(\s+case )(0x1[0-9a-f]+):.*")
#def strip_1(str):
#    return "0x"+str[-2:]
#onebyte_start = 8472
#twobyte_start = 9245
#twobyte_end = 9647

emulatorlines = open("cpux86-ta.js","r").readlines()
newlines=[]
for i,line in enumerate(emulatorlines):
    if i < onebyte_start:
        newlines.append(line)
    if onebyte_start <= i < twobyte_start: #one-byte instructions
        if linematch := caseline.match(line):
            try:
                newlines.append(linematch.group(1)+linematch.group(2)+"://"+onedict[strip_1(linematch.group(2))]+"\n")
            except KeyError:
                newlines.append(line)
        else:
            newlines.append(line)
    if twobyte_start <= i < twobyte_end: #two-byte instructions
        if linematch := caseline.match(line):
            try:
                newlines.append(linematch.group(1)+linematch.group(2)+"://"+twodict[strip_1(linematch.group(2))]+"\n")
            except KeyError:
                newlines.append(line)
        else:
            newlines.append(line)
    if twobyte_end <= i:
        newlines.append(line)

with open("cpux86-ta-auto-annotated.js",'w') as outfile:
    outfile.writelines(newlines)
