import copy
from collections import namedtuple
import metarelate.fuseki as fuseki
import metarelate
import sys

ppff = 'http://reference.metoffice.gov.uk/um/f3/UMField'
Stash = 'http://reference.metoffice.gov.uk/um/c4/stash/Stash'
fci = 'http://reference.metoffice.gov.uk/um/f3/lbfc'

cff = 'http://def.scitools.org.uk/cfdatamodel/Field'
cfsn = 'http://def.scitools.org.uk/cfdatamodel/standard_name'
cfln = 'http://def.scitools.org.uk/cfdatamodel/long_name'
cfun = 'http://def.scitools.org.uk/cfdatamodel/units'
cfpoints = 'http://def.scitools.org.uk/cfdatamodel/points'
cfdim_coord = 'http://def.scitools.org.uk/cfdatamodel/dim_coord'
cfDimCoord = 'http://def.scitools.org.uk/cfdatamodel/DimCoord'

marqh = '<http://www.metarelate.net/metOcean/people/marqh>'

pre = Prefixes()

afile = sys.argv[1]

userstr = sys.argv[2]
if userstr == 'marqh':
    user = marqh
elif userstr == 'nsav':
    user = nsav

def parse_file(fuseki_process, afile):
    """
    file lines should be of the form
    STASH(msi)|CFName|units|further_complexity
    with this as the header(the first line is skipped on this basis)

    this only runs if the complexity is set to
       n
    """
    record = namedtuple('record', 'stash cfname units complex')
    expected = 'STASH(msi)|CFName|units|further_complexity'
    with open(afile, 'r') as inputs:
        for line in inputs.readlines()[1:]:
            line = line.rstrip('\n')
            lsplit = line.split('|')
            if len(lsplit) != 4:
                raise ValueError('unexpected line splitting; expected:\n'
                                 '{}\ngot:\n{}'.format(expected, line))
            else:
                arecord = record(lsplit[0], lsplit[1], lsplit[2], lsplit[3])
            if arecord.complex == 'n':
                make_stash_mapping(fuseki_process, arecord.stash, arecord.name,
                                   arecord.units)

                
def cfname(fu_p, name, units):
    standard_name = '{p}{c}'.format(p=pre['cfnames'],
                                        c=cfname.standard_name)
    req = requests.get(standard_name)
    if req.status_code == 200:
        name = standard_name
        pred = cfsn
    else:
        name = long_name
        pred = cfln
    acfuprop = metarelate.StatementProperty(metarelate.Item(cfun,'units'),
                                            metarelate.Item(units))
    acfnprop = metarelate.StatementProperty(metarelate.Item(pred, pred.split('/')[-1]),
                                            metarelate.Item(name, name.split('/')[-1]))
    acfcomp = metarelate.Component(None, cff, [acfnprop, acfuprop])
    return acfcomp


def make_stash_mapping(fu_p, stashmsi, name, units, editor):
    stashuri = '{p}{c}'.format(p=pre['moStCon'], c=stashmsi)
    req = requests.get(stashuri)
    if req.status_code != 200:
        raise ValueError('unrecognised stash code: {}'.format(stash))
    astashprop = metarelate.StatementProperty(metarelate.Item(Stash,'stash'),
                                              metarelate.Item(stashuri, stashmsi))
    astashcomp = metarelate.Component(None, ppff, [astashprop])
    astashcomp.create_rdf(fu_p)
    acfcomp = cfname(fu_p, cfname)
    acfcomp.create_rdf(fu_p)

    amap = metarelate.Mapping(None, astashcomp, acfcomp,
                              editor=editor, reason='"new mapping"',
                              status='"Draft"')
    amap.create_rdf(fu_p)

with fuseki.FusekiServer() as fuseki_process:
    parse_batch(fuseki_process, afile)

