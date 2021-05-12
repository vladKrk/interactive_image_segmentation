import networkx as nx
import sys
import time

global MAXN, INF
MAXN = 100; # число вершин
INF = 100001; # константа-бесконечность

def bfs(graph, G_F, n, s, t):
	queue = [s]
	global Levels
	Levels = [-1] * n
	Levels[s] = 0
	level = 0
	while(len(queue) != 0):
		currentV = queue.pop(0)
		for edge in G_F.edges(currentV):
			if(G_F[currentV][edge[1]]['weight'] > 0 and Levels[edge[1]] == -1):
				Levels[edge[1]] = Levels[currentV] + 1
				queue.append(edge[1])
			if(Levels[t] > 0):
				return True
	return Levels[t] > 0
			

def dfs(graph, G_F, k, cp):
	tmp = cp
	if(not cp):
		return 0
	if k == len(graph) - 1:
		return cp
	for edge in G_F.edges(k):
		to = edge[1]
		if (Levels[to] == Levels[k] + 1) and (G_F[k][to]['weight'] > 0):
			f = dfs(graph,G_F,to,min(tmp, G_F[k][to]['weight']))
			G_F[k][to]['weight'] = G_F[k][to]['weight'] - f
			if G_F.has_edge(to, k):
				G_F[to][k]['weight'] = G_F[to][k]['weight'] + f
			else:
				G_F.add_edge(to, k, weight=f)
			tmp = tmp - f
	return cp - tmp
	
def MaxFlow(graph,s,t):
	n = len(graph)
	G_F = graph.copy()
	flow = 0
	while(bfs(graph,G_F, n, s, t)):
		flow = flow + dfs(graph,G_F,s, INF)
	return flow, G_F

files = ['test_1.txt', 'test_2.txt', 'test_3.txt', 'test_4.txt', 'test_5.txt', 'test_6.txt', 
		 'test_d1.txt', 'test_d2.txt', 'test_d3.txt', 'test_d4.txt', 'test_d5.txt', 
		 'test_rd01.txt', 'test_rd02.txt', 'test_rd03.txt', 'test_rd04.txt',
		 'test_rl01.txt', 'test_rl02.txt', 'test_rl03.txt', 'test_rl04.txt', 'test_rl05.txt', 'test_rl06.txt', 'test_rl07.txt', 'test_rl08.txt', 'test_rl09.txt', 'test_rl10.txt']

#out of time: test_rd05.txt, test_rd06.txt, test_rd07.txt

sys.setrecursionlimit(1500)

for fname in files:
	path = './DinicTests/'
	with open(path + fname, "r") as f:
		n, m = map(int, f.readline().split(' '))
		graph = nx.DiGraph()
		for line in f:
			a, b, c = map(int, line.split(' '))
			graph.add_edge(a-1, b-1, weight=c)
		s, t = 0, n - 1

		start = time.time()
		print(str(files.index(fname)) + "." + fname + ":")
		print("\tMax flow: ", MaxFlow(graph, s, t)[0])
		print("\t%s seconds" % (time.time() - start))
