"""
Bridge module

Michael Sube (@msube) 2018
"""

import logging
import re
import SquashedOrder

# ---------------------------------------------------------------------------------------
"""Constants
"""
CARDS = range(52)           # 0..51, Pik Ass = 51, Treff 2 = 0

RANKS = range(13)           # 0..12, 2 = 0, Ass = 12, card % len(RANKS) = rank
ACE   = RANKS[-1]
KING  = RANKS[-2]
QUEEN = RANKS[-3]
JACK  = RANKS[-4]
TEN   = RANKS[-5]

ROOMS = range(2)           # 0 = open, 1 = closed
OPEN = ROOMS[0]
OPEN = ROOMS[1]

LOSERS = range(13)
HCPS = range(41)

Ranks = dict(zip(RANKS, list('23456789') + ['10'] + list('BDKA')))
Results = dict(zip(range(-13,+14), [F"{i:+}" for i in range(-13,0)]
                                   + ['=']
                                   + [F"{i:+}" for i in range(+1,+14)]))

# ---------------------------------------------------------------------------------------

class Card:
    @staticmethod
    def card(suit, rank):
        return (suit.value * len(RANKS) + rank)
    @staticmethod
    def rank(card):
        return (card % len(RANKS))
    @staticmethod
    def suit(card):
        return Suit.get(card // len(RANKS))
    @staticmethod
    def str(card):
        return(F"{Card.suit(card)}{Ranks[Card.rank(card)]}")

class Suit:
    _index = {}
    @staticmethod
    def get(index):
        return __class__._index[index]

    def __init__(self, index, name, value):
        self._index = index
        assert index not in self.__class__._index
        self.__class__._index[index] = self
        self.name = name
        self.value = value
    def __lt__(self, other):
        return self._index < other._index
    def __str__(self):
        return self.name

    @property
    def index(self):
        return self._index

CLUBS    = Suit(0, '♣', 0)
DIAMONDS = Suit(1, '♦', 1)
HEARTS   = Suit(2, '♥', 2)
SPADES   = Suit(3, '♠', 3)

Suits = sorted(Suit._index.values())

class Denomination(Suit):
    _index = {}
    _index.update(Suit._index)
    @staticmethod
    def get(index):
        return __class__._index[index]

    def __init__(self, index, name):
        self._index = index
        assert index not in self.__class__._index
        self.__class__._index[index] = self
        self.name = name
    def __lt__(self, other):
        return self._index < other._index
    def __str__(self):
        return self.name

NT = Denomination(4, 'SA')

Denominations = sorted(Denomination._index.values())
Denominations_R = dict(zip(Denominations, list('TKCP') + ['N']))

class Direction:
    _index = {}
    @staticmethod
    def get(index):
        return __class__._index[index]

    def __init__(self, index, name, factor):
        self._index = index
        assert index not in self.__class__._index
        self.__class__._index[index] = self
        self.name = name
        self._positions = []
        self._factor = factor
    def __lt__(self, other):
        return self._index < other._index
    def __str__(self):
        return self.name
    @property
    def positions(self):
        return self._positions
    @positions.setter
    def positions(self, position):
        self._positions.append(position)
    @property
    def factor(self):
        return self._factor

NS = Direction(0, 'N/S', +1)
EW = Direction(1, 'O/W', -1)

Directions = sorted(Direction._index.values())

class Position():
    _index = {}
    @staticmethod
    def get(index):
        return __class__._index[index]

    def __init__(self, index, name, direction):
        self._index = index
        assert index not in self.__class__._index
        self.__class__._index[index] = self
        self.name = name
        self._direction = direction
        direction.positions = self
    def __lt__(self, other):
        return self._index < other._index
    def __str__(self):
        return self.name
    @property
    def direction(self):
        return self._direction

NORTH = Position(0, 'N', NS)
SOUTH = Position(1, 'S', NS)
EAST  = Position(2, 'O', EW)
WEST  = Position(3, 'W', EW)

Positions = sorted(Position._index.values())

class Vulnerable:
    _index = {}
    @staticmethod
    def get(index):
        return __class__._index[index]

    def __init__(self, index, name, directions):
        self._index = index
        assert index not in self.__class__._index
        self.__class__._index[index] = self
        self.name = name
        self._directions = directions
    def __lt__(self, other):
        return self._index < other._index
    def __str__(self):
        return self.name
    @property
    def directions(self):
        return self._directions

VUL_NONE = Vulnerable(0, 'None', set())
VUL_NS   = Vulnerable(1, 'N/S',  {NS})
VUL_EW   = Vulnerable(2, 'E/W',  {EW})
VUL_ALL  = Vulnerable(3, 'All',  {NS, EW})

Vulnerables = sorted(Vulnerable._index.values())

class Risk:
    _index = {}
    @staticmethod
    def get(index):
        return __class__._index[index]

    def __init__(self, index, name):
        self._index = index
        assert index not in self.__class__._index
        self.__class__._index[index] = self
        self.name = name
    def __lt__(self, other):
        return self._index < other._index
    def __str__(self):
        return self.name

UNDOUBLED = Risk(0, '')
DOUBLED   = Risk(1, 'x')
REDOUBLED = Risk(2, 'xx')

Risks = sorted(Risk._index.values())

class Room:
    @staticmethod
    def direction(room):
        return room & 1

# ---------------------------------------------------------------------------------------

class Contract:
    """ A contract is the end result from the bidding.
    level is 0 if all players passed.
    player, denomination and risk are valid if level > 0.
    """
    def __init__(self, declarer, level=0, denomination=None, risk=UNDOUBLED):
        self._declarer = declarer
        self._level = level
        self._denomination = denomination
        self._risk = risk

    def __bool__(self):
        return self._declarer is not None

    def __lt__(self, other):
        return (  self._level < other._level
               or self._level == other._level and self._denomination < other._denomination )

    def __repr__(self):
        return ( F"{self.declarer!s:2}"
                 F"{self._level}{self.denomination}"
                 F"{self._risk}")

    def __str__(self):
        if not self: return "  Pass"
        return ( F"{self._declarer!s:2}{self._level}{self._denomination}{self._risk}" )

    @property
    def direction(self):
        return [self._declarer.direction] if self else []

PASS = Contract(None)

class Score:
    """ A score is an entry on the scoreboard,
    showing who played which contract and what the result was.
    """
    def __init__(self, pairs, contract, result=None, value=0, points=None):
        self.pairs = pairs
        self.contract = contract
        self.result = result
        self.value = value
        self.points = points

    def __lt__(self, other):
        return self.value < other.value

    def __str__(self):
        direction = self.contract.direction if self.contract else []
        ns = F"({self.pairs[0]})" if EW in direction else F"{self.pairs[0]} "
        ew = F"({self.pairs[1]})" if NS in direction else F"{self.pairs[1]} "
        contract = F"{self.contract}"
        if self.contract:
            contract += F"{self.result:+3}" if self.result else " ="
        value = F"{self.value:+}" if self.contract else ""
        return F"{value:>5}{ns:>8}   {contract:12} {ew:>8}"

class Hand(dict):
    """ A hand holds the cards, the type and a rating.
    """
    def __init__(self, cards=None, suits=None):
        if cards: # list of cards
            suits = [[] for suit in Suits]
            for card in sorted(cards, reverse=True):
                suits[Card.suit(card).index].append(Card.rank(card))
        elif suits: # list of ranks per suit
            suits = [sorted(suit, reverse=True) for suit in suits]
        else:
            suits = [[] for suit in Suits]
        self.update(dict(zip(Suits, suits)))
        self._length = sum(len(ranks) for ranks in suits)
        self.rating = Rating(suits)
        self.type = Type(suits)

    def __bool__(self):
        return self._length == 13

    def __len__(self):
        return self._length

    def __str__(self):
        suits = [str(suit) + ''.join(Ranks[rank] for rank in self[suit]) for suit in sorted(Suits, reverse=True)]
        return ''.join(F"{suit:10}" for suit in suits)

    @property
    def cards(self): # combines suits into list of cards
        return list( sorted( (Card.card(suit, rank) for suit in Suits
                                                    for rank in self[suit]),
                             reverse=True ) )

    @property
    def suits(self): # returns a dictionary of the suits
        return { suit:self[suit] for suit in Suits }

class Rating:
    """ The rating holds informtion about a set of cards.
    """
    def __init__(self, suits=None):
        self.hcp = 0
        self.loser = 0
        self.ds = 0
        self.adjust = 0
        self.dp = 0
        if not suits: return
        # count HCPs
        self.hcp = sum(max(rank - TEN, 0) for ranks in suits for rank in ranks)
        # count loser
        self.loser = ( sum(min(len(ranks), 3) for ranks in suits)
                     - sum( rank > (ACE - min(len(ranks), 3))
                            for ranks in suits for rank in ranks) )
        # count A's and D's and adjust the losers
        numA = sum(rank == ACE for ranks in suits for rank in ranks[:1])
        numQ = sum(rank == QUEEN for ranks in suits if len(ranks) > 2
                                 for rank in ranks[:3])
        # extra D's are loser
        self.loser += max(numQ - numA, 0)
        # some extra A's reduce the losers
        self.loser -= (numA > 2) * max(numA - max(numQ, 2), 0)
        # count DS
        # AK = 2, AD = 1, KD = 1 : ([1]-'B')
        # Ax = 1, Kx = 1, Dx = 0 : ([0]-'D')/2
        self.ds = ( sum( max(ranks[1] - JACK, 0, (ranks[0] - QUEEN) / 2 )
                         for ranks in suits if len(ranks) > 1)
                  + sum( max(ranks[0] - KING, 0)
                         for ranks in suits if len(ranks) == 1))
        # compute adjustment for starter points
        numQ = sum(rank == QUEEN for ranks in suits for rank in ranks)
        numJ = sum(rank == JACK for ranks in suits for rank in ranks)
        numT = sum(rank == TEN for ranks in suits for rank in ranks)
        # +- overrated/underrated honors
        self.adjust = (numA + numT - numQ - numJ) // 3
        # + suit length
        self.adjust += sum(len(ranks) - 4 for ranks in suits if len(ranks) >= 4)
        # - double with honor, downgrade xJ, KD, Qx, Jx
        self.adjust -= sum( ( ranks[1] == JACK
                              or ranks == [KING, QUEEN]
                              or ranks[0] in [QUEEN, JACK] and ranks[1] < JACK )
                            for ranks in suits if len(ranks) == 2 )
        # - single honors, downgrade K, Q, J
        self.adjust -= sum( ranks[0] in [KING, QUEEN, JACK]
                            for ranks in suits if len(ranks) == 1 )
        # + suit quality (4+er mit min 3 von 5)
        self.adjust += sum( ranks[2] >= TEN for ranks in suits if len(ranks) > 3 )
        # compute distribution points
        self.dp = sum(max(3 - len(ranks), 0) for ranks in suits)

    def __add__(self, other):
        rating = self.__class__()
        rating.hcp = self.hcp + other.hcp
        rating.loser = self.loser + other.loser
        rating.ds = self.ds + other.ds
        rating.adjust = self.adjust + other.adjust
        rating.dp = self.dp + other.dp
        return rating

    def __str__(self):
        return ( F"{self.hcp:2} {self.loser:2}"
                 F" {int(self.ds):1}{'+' if (int(self.ds) < self.ds) else '':1}" )

class Type:
    """ A type hold information on how a set of cards is distributed across the suits.
    """
    def __init__(self, suits):
        self.type = [len(ranks) for ranks in suits] if suits else [0,0,0,0]
        self.isFlat = sum(max(3 - l, 0) for l in self.type) < 2

    def __add__(self, other):
        type = self.__class__()
        type.type = [x+y for x,y in zip(self.type, other.type)]
        return type

    def __str__(self):
        return ( ('= ' if self.isFlat else '  ')
               + ''.join((str(x) if x < 10 else '+') for x in self.type) )

# ---------------------------------------------------------------------------------------

class Board(dict):
    """ A board combines the hands, the scores and the board specific informations.
    """

    def __init__(self, id, hands=None, dd=None):
        super().__init__()
        self.id = id # integer
        self._dealer = Position.get(  (int(id) - 1) % 4  )

        self._vulnerable = Vulnerable.get(((int(id)-1)%4 + (int(id)-1)//4)%4)
        self._length = 0
        self.addHands(hands)
        self.dd = dd
        self._scores = []
        self.results = {}

    def __bool__(self):  # true iff all 4 hands are complete
        return self._length == 4

    def __len__(self): # number of complete hands
        return self._length

    def __str__(self):
        return ( F"Board: {self.id:2}  ({self.index})"
                  "\n\n"
                 F"{NS!s:3}: {self.rating(NS)}  "
                 F"{'*' if self._dealer == NORTH else ' '}"
                 F"{NORTH}: {self[NORTH].rating} {self[NORTH].type}  "
                 F"{EW!s:3}: {self.rating(EW)}  "
                 F"{'*' if self._dealer == EAST else ' '}"
                 F"{EAST}: {self[EAST].rating} {self[EAST].type}  "
                  "\n"
                 F"{'VUL' if NS in self._vulnerable.directions else '':15s}"
                 F"{'*' if self._dealer == SOUTH else ' '}"
                 F"{SOUTH}: {self[SOUTH].rating} {self[SOUTH].type}  "
                 F"{'VUL' if EW in self._vulnerable.directions else '':15s}"
                 F"{'*' if self._dealer == WEST else ' '}"
                 F"{WEST}: {self[WEST].rating} {self[WEST].type}  "
                 )

    def formatHeader():
        s = " Bd   gespielt  Score              FP Lo DS  Fit       FP Lo DS   Hand      FP Lo DS   Hand"
        return F"{s}\n{'-' * len(s)}"


    def formatForPair(self, pair):
        for score in self._scores:
            if not pair in score.pairs: continue
            dir = NS if pair == score.pairs[0] else EW
            result = F"{score.result:+}" if score.result else "="
            contract = F"{score.contract}{result:>2}" if score.contract else 'Pass'
            pos = Direction.positions(dir)
            declared = [' ', ' ', ' ']
            if score.contract.player in pos:
                declared[0] = '*'
                declared[1 if score.contract.player == pos[0] else 2] = '*'
            value = score.value if dir == NS else -score.value
            points = score.points if dir == NS else -score.points
            return ( F"{self.id:3}   {contract:9} {value:+5}  {int(points):+4}"
                   F"  {declared[0]:1}{Directions[dir]:3}: {self.rating(dir)}{self.type(dir)}"
                   F"  {declared[1]:1}{Positions[pos[0]]:1}: {self[pos[0]].rating}"
                   F" {self[pos[0]].type}"
                   F"  {declared[2]:1}{Positions[pos[1]]:1}: {self[pos[1]].rating}"
                   F" {self[pos[1]].type}"
                 )

    def playedBy(self, pair):
        for score in self._scores:
            if pair in score.pairs: return True

    def addScore(self, score):
        self._scores.append(score)

    def sortScores(self):
        self._scores.sort(reverse=True)

    def addHands(self, hands):
        if isinstance(hands, int):  # an index: 0 .. ~10**29
            hands = [Hand(cards=cards) for cards in SquashedOrder.seq52_13(hands)]
        if isinstance(hands, list):  # either passed in or computed from an index
            self.update(zip(Positions, hands))
        self._length = sum(bool(self[index]) for index in self)

    @property
    def scores(self):
        return sorted(self._scores, reverse=True)

    @property
    def hands(self): # returns a dictionary of the hands
        return { position: self[position] for position in Positions }

    def rating(self, dir):
        dir.positions
        positions = dir.positions
        return self[positions[0]].rating + self[positions[1]].rating

    @property
    def index(self):
        if not bool(self):  # can't compute index if cards are missing
            return None
        return SquashedOrder.index52_13([self[pos].cards for pos in Positions])

    def type(self, dir):
        positions = Direction.positions(dir)
        return self[positions[0]].type + self[positions[1]].type

# ---------------------------------------------------------------------------------------

if __name__ == '__main__':
    if 1:
        board = Board(21, 35817416954748550972957151064)
        board.addScore(Score([17,31], Contract(SOUTH, 4, SPADES, UNDOUBLED), -1, -50))
        board.addScore(Score([11,24], Contract(WEST, 5, CLUBS, DOUBLED), 0, 550))
        board.addScore(Score([11,24], Contract(EAST, 3, NT, REDOUBLED), 0, 1000))
        board.addScore(Score([11,24], PASS, 0, 0))
        print(board)
        print()
        for score in board.scores:
            print(score)
        print()
        for (position, hand) in board.hands.items():
            print(F"{position}:  {hand}")
        print()


    if 1:
        import random

        BOARDS = range(1,5)

        for boardId in BOARDS:
            deal = random.sample(CARDS, len(CARDS))
            handCards = ( deal[i:i+len(CARDS)//len(Positions)]
                          for i in range(0, len(CARDS), len(CARDS)//len(Positions)) )
            handCards = [x for x in handCards]
            hands = [ Hand(cards=cards) for cards in handCards ]
            board = Board(boardId, hands)
            print(board)
            print()
            hands = board.hands
            for position in hands:
                print(F"{position}: {hands[position]}")
            print()

            board.addScore(Score(['201','102'], Contract(SOUTH, 5, DIAMONDS, REDOUBLED), -1, -200, 12))
            board.addScore(Score(['201','102'], Contract(NORTH, 6, CLUBS, UNDOUBLED), 0, 920, 12))
            board.addScore(Score(['201','102'], PASS))
            print(board)
            print()
            for score in board.scores:
                print(score)
            print()

            s = board.index
            b = Board(board.id, hands=s)
            print(b)
            print()

        for i in range(0,5):
            print(Board(i, hands=i))
            print()



