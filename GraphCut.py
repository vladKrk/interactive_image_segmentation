from PIL import Image
import networkx as nx
import math
import numpy as np
import maxflow

#Константы
SIGMA = 2
LAMBDA = 2
GROUPS = 17

def paintDfs(graph, image, s):
    n = height * width + 2
    queue = [s]
    Levels = [-1] * n
    Levels[s] = 0
    level = 0
    while(len(queue) != 0):
        currentV = queue.pop(0)
        for edge in graph.edges(currentV):
            if(graph[currentV][edge[1]]['capacity'] > 0 and Levels[edge[1]] == -1):
                Levels[edge[1]] = Levels[currentV] + 1
                queue.append(edge[1])
                to = edge[1]
                image[to//width][to%width][0] = image[to//width][to%width][1] = image[to//width][to%width][2] = 0
    return True


def findNeighbors(node):
    neighbors = []
    i = node // width
    j = node % width
    if(i > 0):
        neighbors.append(node - width)
        if(j > 0):
            neighbors.append(node - width - 1)
        if(j < width - 1):
            neighbors.append(node - width + 1)
    if(i < height - 1):
        neighbors.append(node + width)
        if(j > 0):
            neighbors.append(node + width - 1)
        if(j < width - 1):
            neighbors.append(node + width + 1)
    if(j > 0):
        neighbors.append(node - 1)
    if(j < width - 1):
        neighbors.append(node + 1)
    
    return neighbors

def norm_pdf(x, mu, sigma):
    factor = (1. / (abs(sigma) * math.sqrt(2 * math.pi)))
    return factor * math.exp( -(x-mu)**2 / (2. * sigma**2) )

def calculate_normal(image, points):
    values = [int(image[v // width][v % width][0]) for v in points]
    return np.mean(values), max(np.std(values), 0.00001)

def regional_cost(image, point, mean, std):
    prob = max(norm_pdf(int(image[point // width][point % width][0]), mean, std), 0.000000000001)
    return - LAMBDA * math.log(prob) 

def createHistogram(image, pixels):
    histogram = [0] * GROUPS
    for v in pixels:
        intensity = int(image[v // width][v % width][0])
        group = int(intensity * GROUPS / 256)
        histogram[group] += 1
    return histogram

def regionalCostObj(foregroundHistogram, flength, backgroundHistogram, blength, point, image):
    intensity = int(image[point // width][point % width][0])
    group = math.floor(intensity * GROUPS / 256)
    foregroundProbability = foregroundHistogram[group] / flength
    # backgroundProbability = 1 - foregroundProbability
    backgroundProbability = backgroundHistogram[group] / blength
    sumProb = foregroundProbability + backgroundProbability
    prob = 0
    if sumProb < 0.0000001:
        sumProb = 1
    
    prob = foregroundProbability / sumProb
    
    if (prob < 0.000001):
        return -LAMBDA * math.log(0.5)
    return -LAMBDA * math.log(prob)

def regionalCostBack(foregroundHistogram, flength, backgroundHistogram, blength, point, image):
    intensity = int(image[point // width][point % width][0])
    group = math.floor(intensity * GROUPS / 256)
    backgroundProbability = backgroundHistogram[group] / blength
    # foregroundProbability = 1 - backgroundProbability
    foregroundProbability = foregroundHistogram[group] / flength
    
    sumProb = foregroundProbability + backgroundProbability
    prob = 0
    if sumProb < 0.0000001:
        sumProb = 1
    
    prob = backgroundProbability / sumProb
    
    if (prob < 0.000001):
        return -LAMBDA * math.log(0.5)
    return -LAMBDA * math.log(prob)

def createGraph(image, backgroundPixels, foregroundPixels, Lambda, Sigma):

    global height, width
    height = image.shape[0]
    width = image.shape[1]

    global SIGMA, LAMBDA

    SIGMA = Sigma
    LAMBDA = Lambda

    V = int(image.size / 4) + 2
    s = V - 2
    t = V - 1
    imageGraph = nx.DiGraph()
    imageGraph.add_nodes_from([x for x in range(V)])

    #Считаем веса нетерминальных ребер
    for v in imageGraph.nodes():
        if(v == s or v == t):
            break
        neighbors = findNeighbors(v)
        for neighbor in neighbors:
            pixelsDelta = int(image[v // width][v % width][0]) - int(image[neighbor // width][neighbor % width][0])
            distance = math.sqrt((pixelsDelta) ** 2 + (v // width - neighbor // width) ** 2 + (v % width - neighbor % width) ** 2)
            B_pq = math.exp((- pixelsDelta ** 2 / (2 * SIGMA**2))) / distance
            imageGraph.add_edge(v, neighbor, capacity = B_pq)

        imageGraph.add_edge(s, v, capacity=0)
        imageGraph.add_edge(v, t, capacity=0)
    
    #Для каждой вершины графа, найти все ребра исходящие из этой вершины, просуммировать их веса, и взять максимальную из всех сум
    K = 1. + max(sum([x[2]['capacity'] for x in list(imageGraph.edges(v, data=True))]) for v in imageGraph.nodes())
    #Ищем среднюю интенсивность точек и отклонение от среднего среди точек фона и объекта
    obj_mean, obj_std = calculate_normal(image, foregroundPixels)
    bkg_mean, bkg_std = calculate_normal(image, backgroundPixels)

    foregroundHistogram = createHistogram(image, foregroundPixels)
    backgroundHistogram = createHistogram(image, backgroundPixels)

    #Заполняем ребер с терминальными вершинами в соответсвии с тем, какой тип у точки входа/выхода (фон, объект, неизвестно)
    for v in imageGraph.nodes():
        if(v == s or v == t):
            continue
        imageGraph[s][v]['capacity'] = 0 if v in foregroundPixels else K if v in backgroundPixels else regionalCostObj(foregroundHistogram, len(foregroundPixels), backgroundHistogram, len(backgroundPixels), v, image)
        imageGraph[v][t]['capacity'] = K if v in foregroundPixels else 0 if v in backgroundPixels else regionalCostBack(foregroundHistogram, len(foregroundPixels), backgroundHistogram, len(backgroundPixels), v, image)
        # imageGraph[s][v]['capacity'] = 0 if v in foregroundPixels else K if v in backgroundPixels else regional_cost(image, v, obj_mean, obj_std)
        # imageGraph[v][t]['capacity'] = K if v in foregroundPixels else 0 if v in backgroundPixels else regional_cost(image, v, bkg_mean, bkg_std)
    _, mincut = nx.minimum_cut(imageGraph, s, t)

    # for node in flow[1].nodes():
    #     if(node == s or node == t):
    #         break
    #     to = node
        
    #     image[to//width][to%width][0] = image[to//width][to%width][1] = image[to//width][to%width][2] = 255
    # for to in imageGraph.nodes():
    #     if(to == s or to == t):
    #         break
        
    #     image[to//width][to%width][0] = image[to//width][to%width][1] = image[to//width][to%width][2] = 255

    for to in mincut[0]:
        if(to == s or to == t):
            continue
        image[to//width][to%width][0] = image[to//width][to%width][1] = image[to//width][to%width][2] = 0
    for to in mincut[1]:
        if(to == s or to == t):
            continue
        image[to//width][to%width][0] = image[to//width][to%width][1] = image[to//width][to%width][2] = 255
