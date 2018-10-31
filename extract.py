#!/usr/bin/env python3
"""TODO(asanka): DO NOT SUBMIT without one-line documentation for extract.

TODO(asanka): DO NOT SUBMIT without a detailed description of extract.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from absl import app
from absl import flags
from absl import logging


from typing import List, Optional, Dict
from collections import namedtuple

import re

FLAGS = flags.FLAGS

flags.DEFINE_string('input', None, 'Name of file to parse')
flags.DEFINE_string('nq', None, 'Name of file to write NQuads to')

# Schema

class Token(object):
  """A token

  >>> Token('3*2').Type() == Token.REPETITION
  True
  >>> Token('"asdf"').Type() == Token.CHAR_VAL
  True
  >>> Token('(').Type() == Token.PUNCTUATION
  True
  >>> Token('<asdf>').Type() == Token.PROSE
  True
  >>> Token('=/').Type() == Token.DEFINED_AS
  True
  """

  RULENAME = 1
  PUNCTUATION = 2
  CHAR_VAL = 3
  NUM_VAL = 4
  BIN_VAL = 5
  DEC_VAL = 6
  HEX_VAL = 7
  PROSE = 8
  REPETITION = 9
  DEFINED_AS = 10

  REPETITION_CHARS = "01234567890*#" 
  DEFINED_AS_STRS = set(["=", ":=", "::=", "=/"])

  def __init__(self, val: str):
    assert val
    c = val[0]
    if c.isalpha():
      self._type = Token.RULENAME
    elif c == '"':
      self._type = Token.CHAR_VAL
    elif c == '%':
      self._type = Token.NUM_VAL
    elif c == 'b':
      self._type = Token.BIN_VAL
    elif c == 'd':
      self._type = Token.DEC_VAL
    elif c == 'x':
      self._type = Token.HEX_VAL
    elif c == '<':
      self._type = Token.PROSE
    elif c in Token.REPETITION_CHARS:
      self._type = Token.REPETITION
    elif val in Token.DEFINED_AS_STRS:
      self._type = Token.DEFINED_AS
    else:
      self._type = Token.PUNCTUATION

    self._value = val

  def Type(self):
    return self._type

  def Text(self):
    return self._value

  def __str__(self):
    return self._value

  def __eq__(self, other: 'Token'):
    return self._value == other._value

class Rule(object):

  def __init__(self, rfc: str, section: str, defn: List[Token]):
    assert len(defn) >= 3
    assert defn[0].Type() == Token.RULENAME
    assert defn[1].Type() == Token.DEFINED_AS

    self._name = defn[0].Text()
    self._rfc = rfc
    self._section = section
    self._defn = defn

  def Rfc(self) -> str:
    return self._rfc

  def Name(self) -> str:
    return self._name

  def Section(self) -> str:
    return self._section

  def Defn(self) -> List[Token]:
    return self._defn

  def __str__(self):
    s = ''
    for t in self._defn:
      if t.Type() == Token.REPETITION:
        s += t.Text()
      else:
        s += '{} '.format(t.Text())
    s += ' ; In RFC {} section {} as {}'.format(self._rfc, self._section, self._name)
    return s

  def __eq__(self, other):
    return self._defn == other._defn

class Schema(object):
  """N-Quad Schema"""

  def StrToToken(s : str) -> str:
    return s.replace(' ','-').lower()

  def Doc(r : int) -> str:
    return 'rfc:doc/{}'.format(r)

  def Section(r : int, s : str) -> str:
    return 'rfc:doc/{}/{}'.format(r, Schema.StrToToken(s))

  def Category(c : str) -> str:
    return 'rfc:category/{}'.format(Schema.StrToToken(c))

  def RuleName(t : str) -> str:
    return 'rfc:rulename/{}'.format(Schema.StrToToken(t))

  def RuleInstance(r : int, t : str) -> str:
    return 'rfc:rule/{}/{}'.format(r, Schema.StrToToken(t))

  def String(s : str) -> str:
    return '"{}"^^<xsd:string>'.format(s.replace('"', '\\"').replace('\n', '\\n'))

  def TextIs() -> str:
    return 'rfc:text-is'

  def Definition() -> str:
    return 'rfc:definition-is'

  def DefinedIn() -> str:
    return 'rfc:defined-in'

  def Updates() -> str:
    return 'rfc:updates'

  def UpdatedBy() -> str:
    return 'rfc:updated-by'

  def Obsoletes() -> str:
    return 'rfc:obsoletes'

  def ObsoletedBy() -> str:
    return 'rfc:obsoleted-by'

  def NormativeReference() -> str:
    return 'rfc:normative-reference'

  def InformativeReference() -> str:
    return 'rfc:informative-reference'

  def References() -> str:
    return 'rfc:references'

  def ReferencedBy() -> str:
    return 'rfc:referenced-by'

  def NQ(a : str, pred : str, c : str, label : str) -> str:
    return '{} {} {} {} .'.format(a,pred,c,label)

  def FromRule(r : Rule, l : str) -> List[str]:
    irfc = Schema.Doc(r.Rfc())
    isection = Schema.Section(r.Rfc(), r.Section())
    irulename = Schema.RuleName(r.Name())
    irule = Schema.RuleInstance(r.Rfc(), r.Name())

    nq = [
        Schema.NQ(irule, Schema.DefinedIn(), irfc, l),
        Schema.NQ(irule, Schema.DefinedIn(), isection, l),
        Schema.NQ(irule, Schema.TextIs(), Schema.String(str(r)), l),
        Schema.NQ(irulename, Schema.DefinedIn(), irfc, l),
        Schema.NQ(irulename, Schema.DefinedIn(), isection, l),
        Schema.NQ(irulename, Schema.Definition(), irule, l)
    ]
    nq.extend([Schema.NQ(irule, Schema.References(), Schema.RuleName(t.Text()), l) for
               t in r.Defn() if t.Type() == Token.RULENAME])
    nq.extend([Schema.NQ(Schema.RuleName(t.Text()), Schema.ReferencedBy(), irule, l) for
               t in r.Defn() if t.Type() == Token.RULENAME])
    return nq



class Parser(object):
  """Parse stuff

  >>> p = Parser()
  >>> [str(f) for f in p.AbnfTokenize('defined-as = *c-wsp ("=" / "=/") *c-wsp')]
  ['defined-as', '=', '*', 'c-wsp', '(', '"="', '/', '"=/"', ')', '*', 'c-wsp']

  >>> [str(f) for f in p.AbnfTokenize('    foo = 2*3token / ( "a" / "b" ); comment ')]
  ['foo', '=', '2*3', 'token', '/', '(', '"a"', '/', '"b"', ')']

  >>> [str(f) for f in p.AbnfTokenize(' something <this is <nested prose>> other')]
  ['something', '<this is <nested prose>>', 'other']

  >>> [str(f) for f in p.AbnfTokenize('3<foo>')]
  ['3', '<foo>']
  """

  def __init__(self):
    self._blanks = 1
    self._paragraph = [] # type: List[str]
    self._rfc = ""
    self._title = ""
    self._date = ""
    self._rules = {} # type: Dict[str, Rule]
    self._current_section = ""

  def AddLine(self, line: str):
    if line.isspace():
      if self._blanks > 0:
        # Continuation of some vertical space
        self._blanks += 1
        return

      if self._paragraph:
        self._ProcessParagraph()

      # End of last paragraph.
      self._blanks = 1

    else: # not whitespace

      if self._blanks > 0:
        # Start of new paragraph
        assert not self._paragraph

      self._blanks = 0
      self._paragraph.append(line.rstrip())

  def Done(self):
    if self._paragraph:
      self._ProcessParagraph()

  def WriteNQ(self, o):
    for (_, r) in self._rules.items():
      for s in Schema.FromRule(r, "g"):
        o.write('{}\n'.format(s))

  def AddRule(self, p: List[str]):
    if not self._rfc or not self._current_section:
      logging.warning("Rule found before RFC or section is known")
    tokens = [] # type: List[Token]
    for l in p:
      tokens.extend(self.AbnfTokenize(l))
    if len(tokens) < 3:
      logging.warning("Rejecting: {} in section {}".format(repr(p), self._current_section))
    rulename = tokens[0].Text()
    if tokens[1].Type() != Token.DEFINED_AS:
      logging.warning("Rejecting: {} in section {}".format(repr(p), self._current_section))
      return
    rule = Rule(self._rfc, self._current_section, tokens)
    if rulename in self._rules:
      if rule == self._rules[rulename]:
        logging.debug("Ignoring duplicate for {}".format(rulename))
      else:
        logging.info("Duplicate definition for {} (rule 1 wins):\n1: {}\n2: {}".format(rulename, str(self._rules[rulename]), str(rule)))
      return
    self._rules[rulename] = rule
    logging.debug("Rule: {}".format(str(rule)))

  def AbnfTokenize(self, line: str) -> List[Token]:
    tokens = [] # type: List[Token]
    this_token = ""
    prose_level = 0 
    quote_char = None # type: Optional[str]
    in_repeat = False
    valid = True

    for c in line:
      while valid:
        if quote_char is not None:
          this_token += c
          if c == quote_char:
            assert this_token
            quote_char = None
            tokens.append(Token(this_token))
            this_token = ''
        elif c in Token.REPETITION_CHARS and (not this_token or in_repeat):
          if not this_token:
            assert not in_repeat
            in_repeat = True
          this_token += c
        elif in_repeat:
          assert this_token
          in_repeat = False
          tokens.append(Token(this_token))
          this_token = ''
          continue
        elif c == '"':
          assert not this_token
          quote_char = c
          this_token += c
        elif c == '<':
          assert prose_level > 0 or not this_token
          prose_level += 1
          this_token += '<'
        elif c == '>':
          assert prose_level > 0, "in line: {}".format(line)
          prose_level -= 1
          this_token += '>'
          if prose_level == 0:
            tokens.append(Token(this_token))
            this_token = ''
        elif prose_level != 0:
          this_token += c
        elif c == ';':
          # Rest of the line is a comment.
          if this_token:
            tokens.append(Token(this_token))
          valid = False
          break
        elif c == ' ' or c == '\t':
          if this_token:
            tokens.append(Token(this_token))
            this_token = ''
        elif c in "()[]/":
          if this_token:
            tokens.append(Token(this_token))
          tokens.append(Token(c))
          this_token = ''
        else:
          this_token += c
        break
    if this_token:
      tokens.append(Token(this_token))
    return tokens

  def IsPossibleRule(self, line: str) -> bool:
    for token in line.split():
      if token in Token.DEFINED_AS_STRS:
        return True
    return False

  def GrammarBlock(self, block: List[str]):
    # We definitely know this is a grammar block
    p = [] # type: List[str]
    for line in block:
      if self.IsPossibleRule(line):
        if p:
          self.AddRule(p)
        p = [line]
      else:
        p.append(line)

    if p:
      self.AddRule(p)

  def _PossibleGrammar(self, block: List[str]):
    if self.IsPossibleRule(block[0]):
      try:
        self.GrammarBlock(block)
      except AssertionError as e:
        pass

  def _SectionHeading(self, block: List[str]):
    self._current_section = block[0].split()[0]

  def _Appendix(self, block: List[str]):
    self._current_section = ' '.join(block[0].split()[:2])

  def _PageHeader(self, block: List[str]):
    line = block[0]
    pieces = [p.strip() for p in line.split('   ') if p]
    if len(pieces) == 3:
      # Heading found
      rfc, self._title, self._date = pieces
    if rfc.startswith('RFC ') and rfc[4:].isdigit():
      self._rfc = int(rfc[4:])

  def _ProcessParagraph(self):
    assert len(self._paragraph) > 0

    block = self._paragraph
    self._paragraph = []

    first_line = block[0]
    assert len(first_line) > 0

    if first_line[0].isspace():
      # Indented block
      self._PossibleGrammar(block)
      return

    if first_line[0].isdigit():
      # Section heading
      self._SectionHeading(block)
      return

    if first_line.startswith("RFC "):
      # Page header
      self._PageHeader(block)

    if first_line.startswith("_Appendix ") or first_line.startswith("APPENDIX "):
      self._Appendix(block)


def main(argv):
  if len(argv) > 1:
    raise app.UsageError('Too many command-line arguments.')

  if FLAGS.input is None:
    raise app.UsageError('No input file')

  p = Parser()
  with open(FLAGS.input, 'r') as f:
    for line in f:
      p.AddLine(line)
  p.Done()

  if FLAGS.nq is not None:
    with open(FLAGS.nq, 'w') as f:
      p.WriteNQ(f)

if __name__ == '__main__':
  app.run(main)
