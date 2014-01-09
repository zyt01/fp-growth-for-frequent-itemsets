# encoding: utf-8

"""

"""

# TODO: refactor, where appropriate, comprehensions as generator expressions
# TODO: make build_tree a partial so 'htab' doesn't have to passed in
# TODO: above: add_nodes_ = partial(add_nodes, header_table=header_table)
# TODO: create variable to avoid repeated lookups for 'parent_node.children[item]'
# TODO: use CL.deque() where appropriate (in lieu of lists for htab.values() ?)
# TODO: write viz module comprised of python obj --> JSON translator + pygraphviz render
# TODO: create a new table (like header table) that stores the terminus node for each route
# TODO: a few of these fns i think are memoizable


import collections as CL
from operator import itemgetter
import functools as FT
import itertools as IT



# min_spt = 50000
# dfile = "/Users/dougybarbo/Projects/data-pipeline-II/kosarak.dat"
# with open(dfile, "r", encoding="utf-8") as fh:
# 	pdata = [ line.strip().split() for line in fh.readlines() ]


dataset1 = [
	['E', 'B', 'D', 'A'],
	['E', 'A', 'D', 'C', 'B'],
	['C', 'E', 'B', 'A'],
	['A', 'B', 'D'],
	['D'],
	['D', 'B'],
	['D', 'A', 'E'],
	['B', 'C'],
]


dataset2 = [
	['C', 'A', 'T', 'S'],
	['C', 'A', 'T', 'S', 'U', 'P'],
	['C', 'A', 'T'],
	['C', 'A', 'T', 'C', 'H'],
	['C', 'A', 'T', 'A', 'N'],
	['C', 'A', 'T', 'N', 'I', 'P'],
	['C', 'A', 'T', 'E', 'G', 'O', 'R', 'Y'],
	['C', 'A', 'T', 'I', 'O', 'N'],
	['C', 'A', 'T', 'A', 'P', 'U', 'L', 'T'],
	['C', 'A', 'T', 'C', 'H', 'Y'],
	['C', 'A', 'T', 'A', 'L', 'O', 'G'],
	['C', 'A', 'T', 'E', 'R'],
	['C', 'A', 'T', 'S'],
	['C', 'A', 'T', 'A', 'R', 'A', 'C', 'T'],
	['C', 'A', 'T', 'T', 'L', 'E'],
	['A', 'T', 'O', 'M'],
	['E', 'R', 'R', 'O', 'R'],
	['A', 'T', 'M'],
	['L', 'E', 'A', 'R', 'N'],
	['T', 'E', 'R', 'M'],
	['A', 'T', 'T', 'A', 'C', 'H']
]


#---------------------- building the fp-tree -----------------------#


def item_counter(dataset):
	"""
	returns: a dict whose keys are the unique items comprising the 
		transactions & whose values are the integer counts;
	pass in: raw data (nested list);
	"""
	# flatten the data (from list of sets to list of items)
	trans_flat = [item for trans in dataset for item in trans]
	ic = CL.defaultdict(int)
	for item in trans_flat:
		ic[item] += 1
	return ic


def get_items_below_min_spt(dataset, item_count, min_spt, trans_count):
	"""
	returns: list of the unique items whose frequency over the
		dataset is below some min_spt (float between 0 and 1, 
		('decimal percent')
	pass in: 
		(i) dataset
		(ii) dict w/ items for keys, values are item frequency;
		(iii) min_spt (float, eg, 0.03 means each item must appear in 
		at least 3% of the dataset);
	calls 'item_counter'
	"""
	ic = {k:v for k, v in item_count.items() if (v/trans_count) < min_spt}
	return list(ic.keys())


def build_min_spt_filter_str(excluded_items):
	"""
	returns: a str which, when 'eval' is called on it, is a
		a valid arg for 'IT.filterfalse' which is used in
		'filter_by_min_spt' to remove items below min_spt
	pass in: list of excluded items (returned by
		 'get_items_below_min_spt')
	"""
	excluded_items_expr = []
	str_templ = '(q=="{0}")'
	for item in excluded_items:
	    excluded_items_expr.append(str_templ.format(item))
	return " | ".join(excluded_items_expr)


def filter_by_min_spt(dataset, item_count, min_spt, trans_count):
		"""
		returns: 
			(i) filterd dataset (remove items w/ freq < min_spt);
			(ii) filtered item counter
		pass in:
			(i) dataset (the raw dataset);
			(ii) dict w/ items for keys, values are item frequency,
				returned by call to 'item_counter';
			(iii) min_spt (float, eg, 0.03 means each item must appear in 
			at least 3% of the dataset); 
			(iv) total number of transactions
		removes any item from every transaction if that item's total freq
		is below 'min_spt';
		to call this fn, bind the call to two variables, like so:
		filtered_trans, item_count_dict = filter_by_min_spt(...)
		"""
		excluded_items = get_items_below_min_spt(dataset, item_count, 
			min_spt, trans_count)
		if not excluded_items:
			# if all items are above min_spt, ie, there are no items to exclude
			# so just return original args
			return dataset, item_count
		else:
			# there is at least one item to exclude
			# now build the expression required by 'IT.filterfalse' from the
			# list of excluded items
			filter_str = build_min_spt_filter_str(excluded_items)
			# remove those items below min_spt threshold items
			tx = [IT.filterfalse(lambda q: eval(filter_str), trans) 
					for trans in dataset]
			ic = {k:v for k, v in item_count.items() if (v/trans_count) >= min_spt}
			return list(map(list, tx)), ic


def config_fptree_builder(dataset, trans_count, min_spt=None):
	"""
	returns: header table & dataset for input to build_tree;
	pass in: 
		(i) raw data (nested list of dataset);
		(ii) transaction count (length of original dataset)
		(iii) min_spt (float) fraction of total dataset in which an item
			must appear to be included in the fptree
	"""
	dataset = [ set(trans) for trans in dataset ]
	item_count = item_counter(dataset)
	
	if min_spt:
		dataset, item_count = filter_by_min_spt(dataset, item_count, 
								trans_count, min_spt)
	# to sort by decr frequency, then secondary (alpha) sort by key (incr),
	# sort first by secondary key, then again by primary key
	ic = sorted(((k, v) for k, v in item_count.items()), 
		key=itemgetter(0))
	ic = sorted(ic, key=itemgetter(1), reverse=True)
	sort_key = {t[0]: i for i, t in enumerate(ic)}
	fnx = lambda q: sorted(q, key=sort_key.__getitem__)
	dataset = map(fnx, dataset)
	# build header table from freq_items w/ empty placeholders for node pointer
	htable = CL.defaultdict(list)
	for k in item_count.keys():
	    htable[k].append(item_count[k])
	return htable, dataset
 
 
class TreeNode:

	def __init__(self, node_name, parent_node):
		self.name = node_name
		self.node_link = None
		self.count = 1
		self.parent = parent_node
		self.children = {} 

	def incr(self, freq=1):
		self.count += freq 
 
			
def add_nodes(trans, header_table, parent_node):
	"""
	pass in: 
		a transaction (list), 
		header table (dict)
		parent_node (instance of class TreeNode);
	returns: nothing, converts a single transaction to
		nodes in an fp-tree (or increments counts if exists)
		and updates the companion header table 
	"""
	while len(trans) > 0:
		item = trans.pop(0)
		# does this item appear in the same route?
		# if so it will have to be upsteam & adjacent given how the items
		# are sorted prior to tree building & given that the fp-tree is
		# built from the top down
		if item in parent_node.children.keys():
			parent_node.children[item].incr()
		else:
			# create the node & add it to the tree
			parent_node.children[item] = TreeNode(item, parent_node)
			this_node = parent_node.children[item]
			try:
				# is there at least one node pointer for this item 
				# in the header table?
				# ie, does this item appear in another route, or
				header_table[item][1]
				# if so:
				header_table[item][-1].node_link = this_node
				header_table[item].append(this_node)
			except IndexError:
				# this is the 1st time this item is seen by this fn
				# ie, no node pointer for this item in h/t, so add it
				header_table[item].append(this_node)
		this_node = parent_node.children[item]
		add_nodes(trans, header_table, this_node)


def build_fptree(dataset, trans_count, min_spt=None, root_node_name="root"):
	"""
	pass in: 
		(i) raw data (list of dataset; one transcation per list)
		(ii) transaction count in original dataset;
		(iii) minimum support (0=<min_spt>1)
		(iv) name of root node (str)
	returns: fptree;
	the 'main' fn in this module; instantiates fptree and builds it
	by calling 'add_node'; when called, bind result to 2 variables:
	one for thetree; the second for for the header table;
	"""
	fptree = TreeNode(root_node_name, None)
	root = fptree
	header_table, dataset = config_fptree_builder(dataset, trans_count, 
								min_spt)
	for trans in dataset:
		add_nodes(trans, header_table, root)
	header_table = {k:v[:2] for k, v in header_table.items()}
	return fptree, header_table


def fpt(tn):
	"""
	returns: None;
	pass in: an fptree node;
	convenience function for informal, node-by-node introspection
	of the fptree object; call unbound to variable
	"""
	print("count: {0}".format(tn.count))
	print("name: {0}".format(tn.name))
	print("children: {0}".format(list(tn.children.keys())))
	print("parent: {0}".format(tn.parent.name))


# these need to be in this module's namespace so i can use them in
# fptree_query
fptree, htab = build_fptree(dataset=dataset1, trans_count=len(dataset1))

if __name__ == '__main__':
	
	# returns complete fp-tree & header table
	fptree, htab = build_fptree(dataset=dataset1, trans_count=len(dataset1))

