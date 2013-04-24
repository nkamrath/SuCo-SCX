import os
import Population
import Util
import Fitness
import random
import Analysis
import GeneTypes
from Population import Individual
import Crossover

def oneRun(constants, evaluation, sheet = None):
	
	created = []
	if "popType" in constants:
		pop = Util.moduleClasses(Population)[constants["popType"]](constants)
	else:
		pop = Population.Population(constants)

	best, evals, lastImproved = Population.Individual(), 0, 0
	rowCounter = 0
	while evals < constants["evals"] and best.fitness < constants["maxFitness"]:
		try:
			child = pop.next()
		except StopIteration:
			break
		evaluation(child)
		evals += 1
		if best < child:
			lastImproved = evals
			created.append((evals, child.fitness, child))
			best = child

	return created

def basic(constants):
	try: random.seed(constants["seed"])
	except KeyError: pass

	results = []

	for run in range(constants["runs"]):
		constants["runNumber"] = run
		evaluation = Util.moduleClasses(Fitness)[constants["problem"]](constants).eval
		results.append(oneRun(constants, evaluation))
	return Analysis.metaFilter(results, constants), results
	


if __name__ == '__main__':
	import sys
	config = Util.loadConfigurations(sys.argv[1:])
	filtered, raw = basic(config)
	print config["name"]
	with open("../LogFiles/" + config["name"] + ".csv", 'w') as f:
		f.write(str(filtered) + "\n")
		for run in raw:
			f.write(str(run) + "\n")
		print config["name"], "results: ", str(filtered)

   
