import random
import Util
import copy
import Mutation

class Construct(object):
    def getValue(self, prev, length):
        raise Exception("A construct did not override getValue")

class Number(Construct):
    def __init__(self):
        self.value = random.random()

    def getValue(self, prev, length):
        return int(length * self.value)
    def __str__(self):
        return str(self.value)

class Random(Construct):
    def getValue(self, prev, length):
        return int(length * random.random())
    def __str__(self):
        return "RAND"

class Inline(Construct):
    def getValue(self, prev, length):
        if prev is None:
            return None
        return (prev + (length / 2)) % length
    def __str__(self):
        return "INLINE"

class Primitive(object):
    def __init__(self):
        constructTypes = Util.childClasses(Construct)
        constructTypes.remove(Inline)
        self.start = random.choice(constructTypes + [Inline])()
        self.end = random.choice(constructTypes + [Inline])()
        self.special = random.choice(constructTypes)()

    def getValues(self, genes):
        length = len(genes)
        start = self.start.getValue(None, length)
        end = self.end.getValue(start, length)
        if start is None:
            if end is None:
                # Both Inline
                start = end = random.randint(0, length - 1)
            else:
                start = self.start.getValue(end, length)
        return (start, end)

    def execute(self, genes):
        raise Exception("Primitive did not override execute")

    def weightedAverage(self, x, y, weight):
        return x * weight + y * (1 - weight)

    def __str__(self):
        return str(type(self)) + "Start:%s, End:%s, Special:%s" % (self.start, self.end, self.special)

class Swap(Primitive):
    def execute(self, genes):
        length = len(genes)
        start, end = self.getValues(genes)
        value = self.special.getValue(None, length) / float(length)
        width = int(length / random.uniform(2, length))

        startPiece = [genes[(start + i) % length] for i in range(width)]
        endPiece = [genes[(end + i) % length] for i in range(width)]

        for i in range(width):
            genes[(start + i) % length] = endPiece[i]
            genes[(end + i) % length] = startPiece[i]

class Merge(Primitive):

    def execute(self, genes):
        start, end = self.getValues(genes)
        weight = self.special.getValue(None, 10000) / 10000.0
        genes[start], genes[end] = (self.weightedAverage(genes[start], genes[end], weight),
                                    self.weightedAverage(genes[end], genes[start], weight))
class Crossover(object):
    def __init__(self, initialLength):
        primitives = Util.childClasses(Primitive)
        self.genes = [random.choice(primitives)() for iterator in range(initialLength)]

    def execute(self, genes):
        for primitive in self.genes:
            primitive.execute(genes)
        return genes

    def __str__(self):
        ret = "Crossover{"
        for primitive in self.genes:
            ret += str(primitive)
        ret += "}"
        return ret

    def fixedPointReproduction(self, other, constants):
        child = Crossover(0)
        p1genes = random.randint(0, len(self.genes))
        p2genes = random.randint(0, len(other.genes))
        over = p1genes + p2genes - 200
        if over > 0:
            p1genes -= over / 2
            p2genes -= over / 2
            # Ensure non negative
            p1genes = max(0, p1genes)
            p2genes = max(0, p2genes)
        child.genes = self.genes[:p1genes] + other.genes[p2genes:]
        if len(child.genes) == 0:
            child.genes = [random.choice((self.genes[0], other.genes[-1]))]
        return child

    def variableReproduction(self, other, constants):
        child = Crossover(0)
        myStart, otherStart = random.randint(0, len(self.genes)), random.randint(0, len(other.genes))
        child.genes = [self.genes[(myStart + i) % len(self.genes)] for i in range(random.randint(0, len(self.genes)))] + \
            [other.genes[(otherStart + i) % len(other.genes)] for i in range(random.randint(0, len(other.genes)))]
        if len(child.genes) == 0:
            child.genes = [random.choice(self.genes + other.genes)]
        while len(child.genes) > constants["dimensions"] * 2:
            del child.genes[random.randint(0, len(child.genes) - 1)]
        return child

    def randomReproduction(self, other, constants):
        return Crossover(random.randint(1, min(len(self.genes) + len(other.genes), constants["dimensions"] * 2)))

    def randomFixedLengthReproduction(self, other, constants={}):
        return Crossover((len(self.genes) + len(other.genes)) / 2)

    def randomLengthReproduction(self, other, constants):
        return Crossover(random.randint(1, constants["dimensions"] * 2))

def uniform(child, parents, constants={}):
    maxCommon = len(parents[0].genes)
    # maxCommon = min(len(parent.genes) for parent in parents)
    child.genes = [random.choice([parent.genes[g] for parent in parents]) for g in range(maxCommon)]
    # TODO Handle unequal length genes better

def npoint(child, parents, constants):
    numberOfPoints = constants["numberOfPoints"]
    maxCommon = min(len(parent.genes) for parent in parents)
    points = set(random.sample(range(maxCommon), min(numberOfPoints, maxCommon)))
    parent = 0
    child.genes = []
    for g in range(maxCommon):
        if g in points: parent += 1
        child.genes.append(parents[parent % len(parents)].genes[g])

def arithmetic(child, parents, constants={}):
    child.genes = [float(sum(values)) / len(values) for values in zip(*[parent.genes for parent in parents])]

def scx(child, parents, constants={}):
    if parents[0].crossover != None and parents[1].crossover != None:
        method = Util.classMethods(Crossover)[constants["scxRecombination"]]
        child.crossover = method(parents[0].crossover, (parents[1].crossover), constants)
        mutation = Util.moduleFunctions(Mutation)[constants["scxMutation"]]
        mutation(child, constants)
        child.genes = child.crossover.execute(parents[0].genes + parents[1].genes)
        child.genes = child.genes[:len(child.genes) / 2]
    else:
        raise Exception("Trying to SCX when parent's crossover is None")
        
        
def scxFromSupport(child, parents, scx, constants={}):
	if scx.crossover != None:
		child.genes = scx.crossover.execute(parents[0].genes + parents[1].genes)
		child.genes = child.genes[:len(child.genes) /2]
	else:
		raise Exception("SCX from support was None")
