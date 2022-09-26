#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys, getopt
import os, json, re
from solidity_parser import parser
from graphviz import Digraph

'''
parse arguments from cmd input
'''
def parseArg(argv):
    inputDir = ""
    outputDir = "./output"
    contractName = ""
    graph = False
    try:
        opts, args = getopt.getopt(argv, "hgi:o:n:", ["help", "graph", "inputDir=", "outputDir=", "contractName="])
    except getopt.GetoptError:
        print("python3 main.py -i <inputDir> -o <outputDir> -n <contractName>")
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("python3 main.py -i <inputDir> -o <outputDir> -n <contractName>")
            sys.exit()
        elif opt in ("-g", "--graph"):
            graph = True
        elif opt in ("-i", "--inputDir"):
            inputDir = arg
        elif opt in ("-o", "--outputDir"):
            outputDir = arg
        elif opt in ("-n", "--contractName"):
            contractName = arg
    if inputDir == "" or (contractName == "" and graph == False):
        print("python3 main.py -i <inputDir> -o <outputDir> -n <contractName>")
        sys.exit(2)
    elif not os.path.isdir(inputDir):
        print(inputDir, "is not a input dir")
        sys.exit(2)
    elif not os.path.isdir(outputDir):
        print(outputDir, "is not a output dir")
        sys.exit(2)
    elif contractName != "" and not os.path.exists(os.path.join(inputDir, contractName + ".sol")):
        print("contract", contractName, "do not exist")
        sys.exit(2)
    return inputDir, outputDir, contractName, graph

'''
parse solidity version from .sol file
'''
def parseVersion(filePath):
    fileUnits = parser.parse_file(filePath, loc=False)
    for item in fileUnits["children"]:
        if item["type"] == "PragmaDirective":
            return item["value"]
    return "unknown version"

'''
switch solc version by solc-select
'''
def switchVersion(version):
    cleanVersion = re.search('0\.[0-9\.]*', version).group(0)
    os.system("solc-select install " + cleanVersion)
    os.system("solc-select use " + cleanVersion)

'''
parse contract list with absolute path
'''
def parseContractList(inputDir):
    result = dict()
    inputFiles = os.listdir(inputDir)
    for inputFile in inputFiles:
        targetPath = os.path.join(inputDir, inputFile)
        targetPath = os.path.abspath(targetPath)
        if (not os.path.isdir(targetPath)) and re.match("[\S]*.sol", inputFile) != None:
            result[targetPath] = inputFile
        elif os.path.isdir(targetPath):
            nestResult = parseContractList(targetPath)
            for key, value in nestResult.items():
                result[key] = value
    return result

'''
parse import file list in relative path
'''
def parseImportList(filePath):
    fileUnits = parser.parse_file(filePath, loc=False)
    result = []
    for item in fileUnits["children"]:
        if item["type"] == "ImportDirective":
            result.append(item["path"])
    return result

'''
parse dependency
'''
def parseDependency(inputDir, outputDir, graph):
    result = parseContractList(inputDir)
    dot = Digraph(comment="The Dependency Graph", node_attr={'shape': 'record'})
    ## add node from the contract list
    for path, name in result.items():
        dot.node(name = path, label = "{%s|path: %s|version: %s}"%(name, path, parseVersion(path)))
    ## add graph from the import list
    for path, name in result.items():
        importFiles = parseImportList(path)
        dirName = os.path.dirname(path)
        for importFile in importFiles:
            realPath = os.path.join(dirName, importFile)
            for key in result.keys():
                if os.path.exists(realPath) and os.path.samefile(key, realPath):
                    realPath = key
                    break
            if realPath in result:
                dot.edge(realPath, path)
            else:
                dot.node(name = realPath, label = "{404|path: %s}"%realPath)
                dot.edge(realPath, path)
    if graph:
        dot.render(os.path.join(outputDir, "DependencyGraph.gv"), format='png', view=True)


if __name__ == "__main__":
    inputDir, outputDir, contractName, graph = parseArg(sys.argv[1:])

    ## print uml graph in outputDir
    if graph:
        parseDependency(inputDir, outputDir, graph)
        sys.exit(0)

    ## complie ${contractName}
    contractPath = os.path.join(inputDir, contractName + ".sol")
    targetPath = os.path.join(outputDir, contractName + ".json")
    if not os.path.exists(contractPath):
        print("no such file:", contractPath)
        sys.exit(2)
    version = parseVersion(contractPath)
    if version == "unknown version":
        print("unable to identify solidity version of", contractName)
        sys.exit(1)
    switchVersion(version)
    compileCommand = "solc --combined-json abi,bin,bin-runtime,srcmap,srcmap-runtime,ast " \
                     + contractPath + " > " \
                     + targetPath
    os.system(compileCommand)
