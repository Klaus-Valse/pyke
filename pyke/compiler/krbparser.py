# $Id$
# coding=utf-8
# 
# Copyright © 2007 Bruce Frederiksen
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

""" See http://www.dabeaz.com/ply/ply.html for syntax of grammer definitions.
""" 

from __future__ import with_statement, absolute_import, division
from pyke import tmp_itertools as itertools
import contextlib
from ply import yacc
from pyke.compiler.scanner import tokens
from pyke.compiler import scanner

def p_file(p):
    ''' file : nls_opt parent_opt fc_rules bc_rules_opt
    '''
    p[0] = ('file', p[2], (tuple(p[3]), ()), p[4])

def p_file_fc_extras(p):
    ''' file : nls_opt parent_opt fc_rules fc_extras bc_rules_opt
    '''
    p[0] = ('file', p[2], (tuple(p[3]), p[4]), p[5])

def p_file_bc(p):
    ''' file : nls_opt parent_opt bc_rules_section
    '''
    p[0] = ('file', p[2], ((), ()), p[3])

def p_parent(p):
    ''' parent_opt : EXTENDING_TOK SYMBOL_TOK without_opt nls
    '''
    p[0] = ('parent', p[2], tuple(p[3]))

def p_second(p):
    ''' without_opt : WITHOUT_TOK without_names comma_opt
    '''
    p[0] = p[2]

def p_fourth(p):
    ''' when_opt : WHEN_TOK NL_TOK reset_plan_vars INDENT_TOK bc_predicates DEINDENT_TOK
    '''
    p[0] = p[5]

def p_reset_plan_vars(p):
    ''' reset_plan_vars :
    '''
    global plan_var, plan_var_number
    plan_var_number = 1
    plan_var = 'plan#%d' % plan_var_number
    p[0] = None

def p_inc_plan_vars(p):
    ''' inc_plan_vars :
    '''
    global plan_var, plan_var_number
    plan_var_number += 1
    plan_var = 'plan#%d' % plan_var_number
    p[0] = None

def p_fifth(p):
    ''' bc_extras_opt : BC_EXTRAS_TOK NL_TOK start_extra_statements INDENT_TOK python_extras_code nls DEINDENT_TOK
        fc_extras : FC_EXTRAS_TOK NL_TOK start_extra_statements INDENT_TOK python_extras_code nls DEINDENT_TOK
        plan_extras_opt : PLAN_EXTRAS_TOK NL_TOK start_extra_statements INDENT_TOK python_extras_code nls DEINDENT_TOK
        with_opt : WITH_TOK NL_TOK start_python_statements INDENT_TOK python_plan_code nls DEINDENT_TOK
    '''
    p[0] = p[5]

def p_none(p):
    ''' comma_opt :
	comma_opt : ','
        data : NONE_TOK
	nls : NL_TOK
	nls : nls NL_TOK
	nls_opt :
	nls_opt : nls
        parent_opt :
        plan_spec : nls
	rest_opt : comma_opt
    '''
    p[0] = None

def p_fc_rule(p):
    ''' fc_rule : SYMBOL_TOK ':' NL_TOK INDENT_TOK foreach_opt ASSERT_TOK NL_TOK INDENT_TOK assertions DEINDENT_TOK DEINDENT_TOK
    '''
    p[0] = ('fc_rule', p[1], p[5], tuple(p[9]))

def p_foreach(p):
    ''' foreach_opt : FOREACH_TOK NL_TOK INDENT_TOK fc_predicates DEINDENT_TOK
    '''
    p[0] = tuple(p[4])

def p_fc_predicate(p):
    ''' fc_predicate : SYMBOL_TOK '.' SYMBOL_TOK LP_TOK patterns_opt RP_TOK nls
    '''
    p[0] = ('fc_predicate', p[1], p[3], tuple(p[5]))

def p_python_eq(p):
    ''' python_predicate : pattern start_python_code '=' python_rule_code nls
    '''
    p[0] = ('python_eq', p[1], p[4])

def p_python_in(p):
    ''' python_predicate : pattern start_python_code IN_TOK python_rule_code nls
    '''
    p[0] = ('python_in', p[1], p[4])

def p_python_check(p):
    ''' python_predicate : start_python_code CHECK_TOK python_rule_code nls
    '''
    p[0] = ('python_check', p[3])

def p_assertion(p):
    ''' assertion : SYMBOL_TOK '.' SYMBOL_TOK LP_TOK patterns_opt RP_TOK NL_TOK
    '''
    p[0] = ('assert', p[1], p[3], tuple(p[5]))

def p_python_assertion(p):
    ''' assertion : PYTHON_TOK ':' nls start_python_assertion INDENT_TOK python_rule_code nls DEINDENT_TOK
    '''
    p[0] = ('python_assertion', p[4])

def p_bc_rule(p):
    ''' bc_rule : SYMBOL_TOK ':' NL_TOK INDENT_TOK USE_TOK goal when_opt with_opt DEINDENT_TOK
    '''
    p[0] = ('bc_rule', p[1], p[6], tuple(p[7]), tuple(p[8][0]), tuple(p[8][1]))

def p_empty_bc_rules_opt(p):
    ''' bc_rules_opt :
    '''
    p[0] = ((), (), ())

def p_bc_rules_section(p):
    ''' bc_rules_section : bc_rules bc_extras_opt plan_extras_opt
    '''
    p[0] = (tuple(p[1]), p[2], p[3])

def p_goal(p):
    ''' goal : SYMBOL_TOK LP_TOK patterns_opt RP_TOK taking_opt nls
    '''
    p[0] = ('goal', p[1], tuple(p[3]), p[5])

def p_name_sym(p):
    ''' name : SYMBOL_TOK
    '''
    p[0] = repr(p[1])

def p_name_pat_var(p):
    ''' name : PATTERN_VAR_TOK
    '''
    p[0] = "context.lookup_data(%s)" % p[1]

def p_bc_predicate1(p):
    ''' bc_predicate : name LP_TOK patterns_opt RP_TOK plan_spec
    '''
    p[0] = ('bc_predicate', False, None, p[1], tuple(p[3]), p[5])

def p_bc_predicate2(p):
    ''' bc_predicate : '!' name LP_TOK patterns_opt RP_TOK plan_spec
    '''
    p[0] = ('bc_predicate', True, None, p[2], tuple(p[4]), p[6])

def p_bc_predicate3(p):
    ''' bc_predicate : name '.' name LP_TOK patterns_opt RP_TOK plan_spec
    '''
    p[0] = ('bc_predicate', False, p[1], p[3], tuple(p[5]), p[7])

def p_bc_predicate4(p):
    ''' bc_predicate : '!' name '.' name LP_TOK patterns_opt RP_TOK plan_spec
    '''
    p[0] = ('bc_predicate', True, p[2], p[4], tuple(p[6]), p[8])

def p_as(p):
    ''' plan_spec : AS_TOK PATTERN_VAR_TOK nls
    '''
    p[0] = ('as', p[2][1:-1])

def p_step_code(p):
    ''' plan_spec : STEP_TOK NUMBER_TOK nls start_python_plan_call INDENT_TOK python_plan_code nls DEINDENT_TOK
    '''
    p[0] = ('plan_spec', p[2], plan_var, p[6][0], p[6][1])

def p_code(p):
    ''' plan_spec : nls start_python_plan_call INDENT_TOK python_plan_code nls DEINDENT_TOK
    '''
    p[0] = ('plan_spec', None, plan_var, p[4][0], p[4][1])

def p_start_python_code(p):
    ''' start_python_code :
    '''
    scanner.start_code(var_format = "context.lookup_data('%s')")
    p[0] = None

def p_start_python_plan_call(p):
    ''' start_python_plan_call :
    '''
    scanner.start_code(plan_name = plan_var, multiline = True)
    p[0] = None

def p_start_python_statements(p):
    ''' start_python_statements :
    '''
    scanner.start_code(multiline = True)
    p[0] = None

def p_start_extra_statements(p):
    ''' start_extra_statements :
    '''
    scanner.start_code(multiline = True, var_format = None)
    p[0] = None

def p_start_python_assertion(p):
    ''' start_python_assertion :
    '''
    scanner.start_code(multiline = True,
                       var_format = "context.lookup_data('%s')")
    p[0] = None

def p_python_rule_code(p):
    ''' python_rule_code : CODE_TOK
    '''
    p[0] = p[1]

def p_python_plan_code(p):
    ''' python_plan_code : CODE_TOK
    '''
    p[0] = p[1]

def p_python_extras_code(p):
    ''' python_extras_code : CODE_TOK
    '''
    p[0] = p[1][0]

def p_pattern_var(p):
    ''' variable : PATTERN_VAR_TOK
    '''
    p[0] = "contexts.variable(%s)" % p[1]

def p_anonymous_var(p):
    ''' variable : ANONYMOUS_VAR_TOK
    '''
    p[0] = "contexts.anonymous()"

def p_last(p):
    ''' bc_predicate : python_predicate
        bc_rules_opt : bc_rules_section
        data : NUMBER_TOK
	data : STRING_TOK
        fc_predicate : python_predicate
        pattern : pattern_proper
	pattern_proper : variable
        patterns_opt : patterns
	rest_opt : ',' '*' variable
    '''
    p[0] = p[len(p)-1]

def p_taking(p):
    ''' taking_opt : start_python_code TAKING_TOK python_rule_code
    '''
    p[0] = p[len(p)-1][0]

def p_quoted_last(p):
    ''' data : SYMBOL_TOK
    '''
    p[0] = "'" + p[len(p)-1] + "'"

def p_false(p):
    ''' data : FALSE_TOK
    '''
    p[0] = False

def p_true(p):
    ''' data : TRUE_TOK
    '''
    p[0] = True

def p_start_list(p):
    ''' assertions : assertion
        bc_predicates : bc_predicate
	bc_rules : bc_rule
        data_list : data
        fc_predicates : fc_predicate
        fc_rules : fc_rule
        patterns : pattern
        patterns_proper : pattern_proper
	without_names : SYMBOL_TOK
    '''
    p[0] = [p[1]]

def p_empty_tuple(p):
    ''' bc_extras_opt :
        data : LP_TOK RP_TOK
	foreach_opt :
        patterns_opt :
        plan_extras_opt :
	taking_opt :
        when_opt :
	without_opt :
    '''
    p[0] = ()

def p_double_empty_tuple(p):
    ''' with_opt :
    '''
    p[0] = (), ()

def p_append_list(p):
    ''' assertions : assertions assertion
	bc_predicates : bc_predicates inc_plan_vars bc_predicate
	bc_rules : bc_rules bc_rule
        data_list : data_list ',' data
	fc_predicates : fc_predicates fc_predicate
	fc_rules : fc_rules fc_rule
        patterns : patterns ',' pattern
        patterns_proper : patterns_proper ',' pattern
	without_names : without_names ',' SYMBOL_TOK
    '''
    p[1].append(p[len(p)-1])
    p[0] = p[1]

def p_pattern(p):
    ''' pattern : data '''
    p[0] = "pattern.pattern_literal(%s)" % str(p[1])

def p_pattern_tuple1(p):
    ''' pattern_proper : LP_TOK '*' variable RP_TOK '''
    p[0] = "pattern.pattern_tuple((), %s)" % p[3]

def p_pattern_tuple2(p):
    ''' pattern_proper : LP_TOK data_list ',' '*' variable RP_TOK '''
    p[0] = "pattern.pattern_tuple((%s), %s)" % \
               (' '.join("pattern.pattern_literal(%s)," % str(x) for x in p[2]),
                p[5])

def p_pattern_tuple3(p):
    ''' pattern_proper : LP_TOK data_list ',' patterns_proper rest_opt RP_TOK '''
    p[0] = "pattern.pattern_tuple((%s), %s)" % \
               (' '.join(itertools.chain((("pattern.pattern_literal(%s)," % str(x)
                                            for x in p[2]),
                                          (str(x) + ',' for x in p[4])))),
                p[5])

def p_pattern_tuple4(p):
    ''' pattern_proper : LP_TOK patterns_proper rest_opt RP_TOK '''
    p[0] = "pattern.pattern_tuple((%s), %s)" % \
               (' '.join(str(x) + ',' for x in p[2]),
                p[3])

def p_tuple(p):
    ''' data : LP_TOK data_list comma_opt RP_TOK '''
    p[0] = '(' + ' '.join(str(x) + ',' for x in p[2]) + ')'

def p_error(p):
    raise SyntaxError("%s(%d): syntax error at token %s" %
                          (scanner.lexer.filename, scanner.lexer.lineno, p))

parser = yacc.yacc(write_tables=0, debug=0)

def parse(filename, debug = 0):
    with contextlib.closing(file(filename)) as f:
        scanner.lexer.lineno = 1
        scanner.lexer.filename = filename
        scanner.debug = debug
        #parser.restart()
        return parser.parse(f.read(), lexer=scanner.lexer, debug=debug)

def run(filename):
    print "answer is", parse(filename)

def test():
    import doctest
    import sys
    sys.exit(doctest.testmod()[0])

if __name__ == "__main__":
    test()