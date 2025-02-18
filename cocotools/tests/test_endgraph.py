from unittest import TestCase
from testfixtures import replace
from networkx import DiGraph
import nose.tools as nt

from cocotools import EndGraph, EndGraphError


# Deliberately not tested: add_edge.

#------------------------------------------------------------------------------
# Integration Tests
#------------------------------------------------------------------------------

class OrtTestCase(TestCase):

    def setUp(self):
        self.m = DiGraph()
        self.c = DiGraph()
        self.e = EndGraph()
        
    def test_unknown_input_does_not_pollute(self):
        self.m.add_edges_from([('A-1', 'B-1', {'RC': 'S', 'PDC': 0}),
                          ('B-1', 'A-1', {'RC': 'L', 'PDC': 0}),
                          ('A-2', 'B-1', {'RC': 'S', 'PDC': 0}),
                          ('B-1', 'A-2', {'RC': 'L', 'PDC': 0}),
                          ('A-3', 'B-2', {'RC': 'S', 'PDC': 0}),
                          ('B-2', 'A-3', {'RC': 'L', 'PDC': 0}),
                          ('A-4', 'B-2', {'RC': 'S', 'PDC': 0}),
                          ('B-2', 'A-4', {'RC': 'L', 'PDC': 0})])
        self.c.add_edge('A-2', 'A-3', EC_Source='P', EC_Target='P',
                        PDC_EC_Source=0, PDC_EC_Target=0, PDC_Site_Source=0,
                        PDC_Site_Target=0)
        self.e.add_translated_edges(self.m, self.c, 'B', 'original')
        self.assertEqual(self.e.number_of_edges(), 1)
        self.assertEqual(self.e['1']['2']['EC_Source'], 'P')
        self.assertEqual(self.e['1']['2']['EC_Target'], 'P')

#------------------------------------------------------------------------------
# Unit Tests
#------------------------------------------------------------------------------

def test_new_attributes_are_better():
    mock_endg = DiGraph()
    mock_endg.add_edge('A', 'B', {'PDC': 5, 'Connection': 'Unknown'})
    method = EndGraph._new_attributes_are_better.im_func
    nt.assert_false(method(mock_endg, 'A', 'B', {'Connection': 'Unknown'}))
    nt.assert_true(method(mock_endg, 'A', 'B', {'Connection': 'Present',
                                                'PDC': 2}))
    nt.assert_false(method(mock_endg, 'A', 'B', {'EC_Source': 'U',
                                                 'EC_Target': 'X'}))


def test_resolve_connections():
    resolve = EndGraph._resolve_connections.im_func
    nt.assert_equal(resolve(None, set(['Present'])), 'Present')
    nt.assert_equal(resolve(None, set(['Present', 'Absent'])), 'Present')
    nt.assert_equal(resolve(None, set(['Unknown', 'Absent', 'Present'])),
                    'Present')
    nt.assert_equal(resolve(None, set(['Present', 'Unknown'])), 'Present')
    nt.assert_equal(resolve(None, set(['Absent'])), 'Absent')
    nt.assert_equal(resolve(None, set(['Unknown'])), 'Unknown')
    

def test_get_mean_pdc():
    mock_conn = DiGraph()
    mock_conn.add_edge('A', 'B', PDC_EC_Source=5, PDC_EC_Target=10,
                       PDC_Site_Source=7, PDC_Site_Target=4)
    nt.assert_equal(EndGraph._get_mean_pdc.im_func(None, 'A', 'B', mock_conn),
                    6.5)


def test_translate_connection():
    translate = EndGraph._translate_connection.im_func
    nt.assert_equal(translate(None, 'S', 'L', 'Absent'), 'Unknown')
    nt.assert_equal(translate(None, 'L', 'O', 'Present'), 'Unknown')
    nt.assert_equal(translate(None, 'L', 'I', 'Absent'), 'Absent')


def test_get_rcs():
    nt.assert_equal(EndGraph._get_rcs.im_func(None, ('B-1', ['B-1']), None,
                                              [3]),
                    (['I'], [3, 0]))
    mock_mapp = DiGraph()
    mock_mapp.add_edge('A-1', 'B-1', RC='S', PDC=4)
    mock_mapp.add_edge('A-2', 'B-1', RC='O', PDC=6)
    nt.assert_equal(EndGraph._get_rcs.im_func(None, ('B-1', ['A-1', 'A-2']),
                                              mock_mapp, []),
                    (['S', 'O'], [4, 6]))
    mock_mapp.add_edge('A-3', 'B-1', RC='I', PDC=3)
    nt.assert_raises(EndGraphError, EndGraph._get_rcs.im_func, None,
                     ('B-1', ['A-1', 'A-2', 'A-3']), mock_mapp, [])


def mock_get_rcs(self, mapping, mapp, pdcs):
    new, old = mapping
    return ['S']*len(old), [3]*len(old)+pdcs


def mock_translate_connection(self, s_rc, t_rc, connection):
    return 'Present'


def mock_get_mean_pdc(self, source, target, conn):
    return 6


def mock_resolve_connections(self, connections):
    return 'Present'


@replace('cocotools.endgraph.EndGraph._get_rcs', mock_get_rcs)
@replace('cocotools.endgraph.EndGraph._translate_connection',
         mock_translate_connection)
@replace('cocotools.endgraph.EndGraph._get_mean_pdc', mock_get_mean_pdc)
@replace('cocotools.endgraph.EndGraph._resolve_connections',
         mock_resolve_connections)
def test_translate_attr_modified():
    mock_conn = DiGraph()
    mock_conn.add_edge('B-1', 'B-2', Connection='Present')
    translate = EndGraph._translate_attr_modified.im_func
    # PDCs that get averaged are 3 (RCs), 6 (existent conn edge), and
    # 18 (non-existent conn edge).
    nt.assert_equal(translate(EndGraph(), ('A-1', ['B-1', 'B-3']),
                              ('A-2', ['B-2']), None, mock_conn),
                    {'Connection': 'Present', 'PDC': 6.6})


def test_at_logic():
    at_logic = EndGraph._at_logic.im_func
    nt.assert_equal(at_logic(None, ['X', 'Np', 'U', 'C'],
                             ['S', 'O', 'O', 'S']), 'X')
    nt.assert_equal(at_logic(None, ['X'], ['L']), 'U')
    nt.assert_equal(at_logic(None, ['U', 'Np', 'Np', 'C'],
                             ['S', 'O', 'S', 'O']), 'P')


def test_take_most_extensive_ec():
    f = EndGraph._take_most_extensive_ec.im_func
    nt.assert_equal(f(None, {'B-1': ['N', 'Nc', 'C'], 'B-3': ['U']},
                      ['B-1', 'B-3'], {'B-2': ['Nc', 'U']}, ['B-2']),
                    (['C', 'U'], ['Nc']))


def mock_take_most_extensive_ec(self, orig_s_ecs, orig_sources, orig_t_ecs,
                                orig_targets):
    s_ecs = [v[0] for v in orig_s_ecs.itervalues()]
    t_ecs = [v[0] for v in orig_t_ecs.itervalues()]
    return s_ecs, t_ecs


def mock_at_logic(self, ecs, rcs):
    return ecs.pop()

    
@replace('cocotools.endgraph.EndGraph._get_rcs', mock_get_rcs)
@replace('cocotools.endgraph.EndGraph._get_mean_pdc', mock_get_mean_pdc)
@replace('cocotools.endgraph.EndGraph._take_most_extensive_ec',
         mock_take_most_extensive_ec)
@replace('cocotools.endgraph.EndGraph._at_logic', mock_at_logic)
def test_translate_attr_original():
    mock_conn = DiGraph()
    mock_conn.add_edge('B-1', 'B-2', {'EC_Source': 'N', 'EC_Target': 'Nc'})
    translate = EndGraph._translate_attr_original.im_func
    # PDCs that get averaged are 3 (RCs), 6 (existent conn edge), and
    # 18 (non-existent conn edge).
    nt.assert_equal(translate(EndGraph(), ('A-1', ['B-1', 'B-3']),
                              ('A-2', ['B-2']), None, mock_conn),
                    {'EC_Source': 'N', 'EC_Target': 'Nc', 'PDC': 6.6})


def test_translate_node():
    g = DiGraph()
    g.add_edges_from([('A-1', 'B-1'), ('A-1', 'C-1'), ('A-1', 'B-2')])
    translate_node = EndGraph._translate_node.im_func
    nt.assert_equal(translate_node(None, g, 'A-1', 'B'), ['B-2', 'B-1'])


def mock_translate_node(self, mapp, node, brain_map):
    return ['X']


@replace('cocotools.endgraph.EndGraph._translate_node', mock_translate_node)
def test_make_translation_dict():
    translate = EndGraph._make_translation_dict.im_func
    nt.assert_equal(translate(EndGraph(), None, 'A-1', 'B'), {'X': ['X']})
    nt.assert_equal(translate(EndGraph(), None, 'A-1', 'A'), {'A-1': ['A-1']})
